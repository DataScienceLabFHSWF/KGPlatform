"""Streaming chat endpoint (SSE)."""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

router = APIRouter()

# Simple in-memory session store
_sessions: dict[str, list[dict]] = {}


class ChatMessage(BaseModel):
    role: str = Field(description="user | assistant | system")
    content: str


class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str
    strategy: str = "auto"
    language: str = "de"
    stream: bool = True


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    confidence: float
    reasoning_chain: list[str]
    provenance: list[dict]


@router.post("/chat")
async def chat(request: ChatRequest) -> StreamingResponse | ChatResponse:
    """Send a message and get a response (streaming or blocking)."""
    session_id = request.session_id or uuid.uuid4().hex[:12]

    if session_id not in _sessions:
        _sessions[session_id] = []

    _sessions[session_id].append({
        "role": "user",
        "content": request.message,
        "timestamp": datetime.now().isoformat(),
    })

    if request.stream:
        return StreamingResponse(
            _stream_response(session_id, request.message),
            media_type="text/event-stream",
        )

    # Non-streaming: call orchestrator directly
    # TODO: import and call KGRAG orchestrator
    answer = f"[Placeholder] Answer to: {request.message}"

    _sessions[session_id].append({
        "role": "assistant",
        "content": answer,
        "timestamp": datetime.now().isoformat(),
    })

    return ChatResponse(
        session_id=session_id,
        answer=answer,
        confidence=0.0,
        reasoning_chain=[],
        provenance=[],
    )


async def _stream_response(session_id: str, question: str):
    """SSE stream generator."""
    # TODO: wire to actual KGRAG orchestrator streaming
    tokens = f"[Placeholder] Streaming answer to: {question}".split()
    for token in tokens:
        data = json.dumps({"token": token + " ", "done": False})
        yield f"data: {data}\n\n"
        await asyncio.sleep(0.05)

    yield f"data: {json.dumps({'token': '', 'done': True})}\n\n"


@router.get("/chat/{session_id}/history")
async def get_history(session_id: str) -> list[dict]:
    """Get chat history for a session."""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return _sessions[session_id]
