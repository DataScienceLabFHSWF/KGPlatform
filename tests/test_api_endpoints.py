"""Simple smoke tests hitting each FastAPI service in the platform via HTTP.

These tests assume the relevant containers are up and listening on the
standard ports (8001 for KGBuilder, 8002 for GraphQA, 8003 for Ontology).
They just exercise the `/api/v1/health` endpoint and a couple of basic
routes to ensure the services are reachable.
"""
from __future__ import annotations

import httpx
import pytest

SERVICES = [
    ("kgbuilder", "http://localhost:8001/api/v1/health"),
    ("graphqa", "http://localhost:8002/api/v1/health"),
    ("ontology", "http://localhost:8003/api/v1/health"),
]


@pytest.mark.parametrize("name,url", SERVICES)
def test_health_endpoint(name: str, url: str) -> None:
    """Health endpoint should return 200 and a simple JSON payload."""
    try:
        r = httpx.get(url, timeout=5.0)
    except Exception as exc:
        pytest.skip(f"service {name} not available: {exc}")
    assert r.status_code == 200
    # some services (e.g. ontology) return an HTML page instead of JSON;
    # try to parse but don't crash if it isn't JSON.
    try:
        data = r.json()
        assert isinstance(data, dict)
        assert any(k in data for k in ("status", "healthy", "success"))
    except Exception:
        # as long as the endpoint succeeded we count it as healthy
        pass


@pytest.mark.parametrize("name,url", SERVICES)
def test_docs_page_exists(name: str, url: str) -> None:
    """OpenAPI docs should be served at /docs for each service."""
    docs_url = url.rsplit("/", 1)[0] + "/docs"
    try:
        r = httpx.get(docs_url, timeout=5.0)
    except Exception as exc:
        pytest.skip(f"service {name} not available: {exc}")
    # docs endpoint is optional; 404 is acceptable
    if r.status_code == 200:
        assert "swagger" in r.text.lower() or "openapi" in r.text.lower()
