# Knowledge graph builder (ontology-based)

This folder runs the [Neo4j LLM Graph Builder](https://neo4j.com/labs/genai-ecosystem/llm-graph-builder/) (Apache-2.0, version `v0.8.7`). It runs with **Ollama only, so no API keys are needed**.

It is **Phase 1**: a prototype to test our ontology and the extraction quality on real documents. Phase 2 will move the extraction step into the main ingestion pipeline.

## What it does

1. Splits a file into chunks.
2. Asks the LLM (Ollama) to find entities and relationships in each chunk, limited to the types in our ontology.
3. Writes the result to Neo4j:
   - `Document` -[`PART_OF`]- `Chunk` -[`NEXT_CHUNK`]-> `Chunk`
   - `Chunk` -[`HAS_ENTITY`]-> `__Entity__`, plus the extracted relationships between entities
4. Optional clean-up: similarity links between chunks, entity embeddings and search indexes.

## Important: it uses its own Neo4j

- This stack starts a **separate** Neo4j. Do not point it at the main application Neo4j.
- Reason: both use the label `Chunk`. Their chunks would show up in the graph search tools of the main application.

## Setup (same on a shared server and on a laptop)

You need: `git`, `sh` (Git Bash is fine on Windows), and `podman-compose` or `docker compose`.

```bash
cd kg-builder
sh setup.sh                  # clones upstream at the pinned tag, creates .env
# edit .env: KG_OLLAMA_MODEL, KG_NEO4J_PASSWORD, ports, KG_BACKEND_PUBLIC_URL
podman-compose up -d --build # or: docker compose up -d --build
```

Then open `http://<host>:<KG_FRONTEND_PORT>`. The first build takes a while because it installs LibreOffice, Tesseract and the embedding model.

### Shared server

- `KG_OLLAMA_URL` = the shared Ollama server.
- Set `KG_STACK_NAME` and all ports to values nobody else uses. The server is shared.
- `KG_BACKEND_PUBLIC_URL=http://<server-host>:<KG_BACKEND_PORT>`

### Laptop

- Install Ollama and pull a model: `ollama pull <model>`.
- `KG_OLLAMA_URL=http://host.docker.internal:11434`
- Keep the default ports and `KG_BACKEND_PUBLIC_URL=http://localhost:8000`.
- Small laptop models extract worse than the server models. Use the laptop for development, and judge quality on the server.

## The ontology

- Format: `ontology/schema.example.json`. Copy it to `ontology/schema.json` and edit it.
- `nodes`: allowed entity types.
- `relationships`: allowed `[Source, REL, Target]` triples. Both ends must be in `nodes`.
- `additional_instructions`: extra text for the LLM, e.g. German naming rules.
- **The example file is only a placeholder.** The real ontology comes from the domain experts.
- In the web UI, the same node and relationship types can also be entered in the extraction schema settings.

## Using it from your own pipeline

There are three options. All of them work outside the shared server.

1. **Web UI.** Upload files, set the schema, look at the graph.
2. **HTTP API with `client/kg_client.py`.** Needs only Python and `requests`:
   ```bash
   pip install requests
   export KG_API_URL=http://localhost:8000     # backend, as seen from your machine
   export KG_NEO4J_PASSWORD=...                # same as in .env
   python client/kg_client.py health
   python client/kg_client.py build docs/*.pdf --schema ontology/schema.json
   python client/kg_client.py post-process
   ```
   You can also import `upload()`, `extract()` and `load_schema()` from it in your own Python code.
3. **Read Neo4j directly.** Connect to `bolt://<host>:<KG_NEO4J_BOLT_PORT>` and query `__Entity__` and `HAS_ENTITY`.

Note: `KG_NEO4J_URI` in the client is the Neo4j address **as the backend container sees it** (default `bolt://neo4j:7687`). The backend connects to Neo4j, not the client.

## Known limits and risks

- **Not tested yet on a live stack.** I wrote this from the upstream `v0.8.7` source. Test it first on the shared server and on one laptop.
- **Tool calling.** The backend always tries structured output with Ollama models, so a model without tool-calling support can fail or return empty graphs. Choose a model that supports tools.
- **Network on a restricted server.** The build needs GitHub, PyPI, npm, apt and Hugging Face. Neo4j downloads APOC on first start. If the server can't reach these hosts, build the images on a machine that can and push them to an internal registry. Or set up proxies or mirrors.
- **Embeddings.** v0.8.7 only accepts `all-MiniLM-L6-v2` (384 dims) for local embeddings. It is not our `multilingual-e5-large-instruct`. This is fine for the prototype because the DB is separate. It is one reason for Phase 2.
- **Community detection** needs the Neo4j GDS plugin. It is not set up here.
- **Own chunking.** Upstream does its own file loading and chunking, without our OCR step or our section structure. Phase 2 will reuse the existing `Chunk`s of the main pipeline instead.
