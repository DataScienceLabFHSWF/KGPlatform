"""HTTP client helpers for inter-service communication."""

from __future__ import annotations

import os

import httpx


def get_service_url(service: str) -> str:
    """Resolve service URL from environment."""
    urls = {
        "kgbuilder": os.getenv("KGBUILDER_API_URL", "http://kgbuilder-api:8001"),
        "graphqa": os.getenv("GRAPHQA_API_URL", "http://graphqa-api:8002"),
        "ontology": os.getenv("ONTOLOGY_API_URL", "http://ontology-api:8003"),
    }
    return urls.get(service, "")


async def call_service(
    service: str,
    method: str,
    path: str,
    json: dict | None = None,
    timeout: float = 30.0,
) -> dict:
    """Make an HTTP call to a sibling service."""
    base_url = get_service_url(service)
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.request(method, f"{base_url}{path}", json=json)
        resp.raise_for_status()
        return resp.json()
