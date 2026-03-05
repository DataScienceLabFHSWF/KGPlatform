"""Light end-to-end smoke tests invoking the running platform APIs.

These are designed to run inside the workspace root; they expect the usual
Docker Compose environment defined at the top level.  Tests are tagged with
``integration`` so they can be skipped in quick local runs.

Usage:

```bash
# install httpx into the .venv first (``pip install httpx``)
PYTHONPATH=$PWD:repos/GraphQAAgent/src . .venv/bin/activate
pytest tests/integration -m integration
```

The first time the tests are executed they will simply bring up the
compose stack, wait a few seconds for services to become healthy, and
exercise a small number of endpoints (chat + history).  No teardown is
performed; the platform can be left running for subsequent manual
experiments.
"""
from __future__ import annotations

import os
import subprocess
import time

import pytest
import httpx

ROOT = os.path.abspath(os.getcwd())


def _maybe_start_compose() -> None:
    """Bring up compose services if they aren't already running."""
    # A quick ``docker compose ps`` will exit zero if the stack is up.
    try:
        subprocess.run(
            ["docker", "compose", "ps"],
            cwd=ROOT,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        subprocess.run(["docker", "compose", "up", "-d"], cwd=ROOT, check=True)
        # give a few seconds for services to start
        time.sleep(10)


@pytest.mark.integration

def test_chat_service_responds() -> None:
    _maybe_start_compose()
    # the platform exposes the chat endpoint under /api/v1 when running via
    # the KGPlatform wrapper service
    url = "http://localhost:8002/api/v1/chat"
    with httpx.Client(timeout=10.0) as client:
        resp = client.post(url, json={"message": "hello world", "stream": False})
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data


@pytest.mark.integration

def test_chat_history_works() -> None:
    _maybe_start_compose()
    # send a question and then fetch history via returned session id
    url = "http://localhost:8002/api/v1/chat"
    with httpx.Client(timeout=10.0) as client:
        resp = client.post(url, json={"message": "foo", "stream": False})
        assert resp.status_code == 200
        sid = resp.json()["session_id"]
        hist = client.get(f"http://localhost:8002/api/v1/chat/{sid}/history")
    assert hist.status_code == 200
    assert isinstance(hist.json(), list)
