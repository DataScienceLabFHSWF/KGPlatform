"""
Small client for the LLM Graph Builder backend.

Use it from any pipeline (on the shared server or not) to send files and build the graph
with our ontology. Only needs Python 3.9+ and `requests`.

    python kg_client.py build file1.pdf file2.pdf --schema ../ontology/schema.json
    python kg_client.py post-process
    python kg_client.py health

Settings come from environment variables (see DEFAULTS below).
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import uuid
from pathlib import Path

import requests

DEFAULTS = {
    # Where the backend API is, as seen from where this script runs.
    "KG_API_URL": "http://localhost:8000",
    # Where Neo4j is, as seen from the BACKEND container (not from this script).
    "KG_NEO4J_URI": "bolt://neo4j:7687",
    "KG_NEO4J_USER": "neo4j",
    "KG_NEO4J_PASSWORD": "",
    "KG_NEO4J_DATABASE": "neo4j",
    # Fixed model name from docker-compose.yaml. The real Ollama model is set there.
    "KG_MODEL": "ollama_kg",
}

# Same chunk settings the web UI sends by default.
CHUNK_SETTINGS = {"token_chunk_size": 200, "chunk_overlap": 20, "chunks_to_combine": 1}

# Upstream task names for the clean-up step after extraction.
POST_PROCESS_TASKS = [
    "materialize_text_chunk_similarities",
    "enable_hybrid_search_and_fulltext_search_in_bloom",
    "materialize_entity_similarities",
]


def setting(name: str) -> str:
    return os.environ.get(name, DEFAULTS[name])


def credentials() -> dict:
    # The backend tries to base64-decode the password (the web UI encodes it).
    # We encode it too, so a plain password is never decoded by mistake.
    password = base64.b64encode(setting("KG_NEO4J_PASSWORD").encode()).decode()
    return {
        "uri": setting("KG_NEO4J_URI"),
        "userName": setting("KG_NEO4J_USER"),
        "password": password,
        "database": setting("KG_NEO4J_DATABASE"),
    }


def post(path: str, data: dict, files: dict | None = None) -> dict:
    # No timeout: extraction of a long file can take many minutes.
    resp = requests.post(f"{setting('KG_API_URL')}{path}", data=data, files=files, timeout=None)
    resp.raise_for_status()
    body = resp.json()
    if body.get("status") != "Success":
        raise RuntimeError(f"{path} failed: {body.get('message')} {body.get('error') or ''}")
    return body


def load_schema(path: Path) -> dict:
    """Turn our ontology JSON into the comma-separated strings the backend expects."""
    schema = json.loads(path.read_text(encoding="utf-8"))
    nodes = schema["nodes"]
    for src, rel, dst in schema["relationships"]:
        if src not in nodes or dst not in nodes:
            raise ValueError(f"({src}, {rel}, {dst}): both ends must be listed in 'nodes'")
    return {
        "allowedNodes": ",".join(nodes),
        "allowedRelationship": ",".join(part for triple in schema["relationships"] for part in triple),
        "additional_instructions": schema.get("additional_instructions", ""),
    }


def upload(file_path: Path) -> None:
    # Send the whole file as one piece (chunk 1 of 1).
    with file_path.open("rb") as fh:
        post(
            "/upload",
            data={
                **credentials(),
                "chunkNumber": 1,
                "totalChunks": 1,
                "originalname": file_path.name,
                "model": setting("KG_MODEL"),
                "uploadId": uuid.uuid4().hex,
            },
            files={"file": (file_path.name, fh)},
        )


def extract(file_name: str, schema: dict) -> dict:
    body = post(
        "/extract",
        data={
            **credentials(),
            **CHUNK_SETTINGS,
            **schema,
            "model": setting("KG_MODEL"),
            "source_type": "local file",
            "file_name": file_name,
        },
    )
    return body.get("data") or {}


def build(files: list[Path], schema_path: Path | None) -> None:
    schema = load_schema(schema_path) if schema_path else {}
    if not schema:
        print("No --schema given: the model may create any node or relationship type.")
    for f in files:
        print(f"[{f.name}] upload ...")
        upload(f)
        print(f"[{f.name}] extract ... (this can take a while)")
        result = extract(f.name, schema)
        print(f"[{f.name}] done: {result.get('entityNodeCount', '?')} entities, "
              f"{result.get('entityEntityRelCount', '?')} relationships, {result.get('chunkNodeCount', '?')} chunks")


def post_process() -> None:
    post("/post_processing", data={**credentials(), "tasks": json.dumps(POST_PROCESS_TASKS)})
    print("post-processing done")


def health() -> None:
    resp = requests.get(f"{setting('KG_API_URL')}/health", timeout=10)
    print(resp.status_code, resp.text)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="upload files and extract the graph")
    b.add_argument("files", nargs="+", type=Path)
    b.add_argument("--schema", type=Path, help="ontology JSON (see ontology/schema.example.json)")
    sub.add_parser("post-process", help="similarity links + indexes after extraction")
    sub.add_parser("health", help="check that the backend is up")
    args = parser.parse_args()

    if args.cmd != "health" and not setting("KG_NEO4J_PASSWORD"):
        print("Set KG_NEO4J_PASSWORD first.", file=sys.stderr)
        return 2
    if args.cmd == "build":
        build(args.files, args.schema)
    elif args.cmd == "post-process":
        post_process()
    else:
        health()
    return 0


if __name__ == "__main__":
    sys.exit(main())
