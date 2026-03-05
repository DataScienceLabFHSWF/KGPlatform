"""Unit tests for the GraphQA API chat route with telemetry."""
from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from services.graphqa_api.routes.chat import router as chat_router
from kgrag.telemetry import langsmith


def test_chat_route_uses_tracing(monkeypatch):
    """Ensure the tracing context manager is entered during request handling."""
    class DummyCM:
        def __init__(self):
            self.entered = False

        def __enter__(self):
            self.entered = True
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    dummy = DummyCM()
    # the route module imported the helper directly so patch its symbol
    import services.graphqa_api.routes.chat as chat_mod
    monkeypatch.setattr(chat_mod, "tracing_context", lambda *args, **kw: dummy)

    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(chat_router)
    client = TestClient(app)
    sid = uuid.uuid4().hex[:12]
    resp = client.post("/chat", json={"session_id": sid, "message": "hi", "stream": False})
    assert resp.status_code == 200
    assert resp.json()["session_id"] == sid
    assert dummy.entered
