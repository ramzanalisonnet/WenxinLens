"""
Interactive Chat API
POST /api/v1/chat/message      — send a message to the AI cultural guide
POST /api/v1/chat/session      — create a new chat session
GET  /api/v1/chat/session/{id} — get session history
DELETE /api/v1/chat/session/{id} — clear session
"""
from __future__ import annotations

import uuid
from typing import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from loguru import logger
from pydantic import BaseModel, Field

from middleware.auth import get_current_user
from middleware.rate_limiter import limiter
from services.chat_service import ChatService

router = APIRouter()


# ─── Schemas ──────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str
    timestamp: str | None = None


class ChatRequest(BaseModel):
    session_id: str
    message: str = Field(min_length=1, max_length=2000)
    language: str = "en"
    building_context: str | None = None  # result_id from recognition
    stream: bool = False


class ChatResponse(BaseModel):
    session_id: str
    message: str
    follow_up_questions: list[str]
    sources: list[dict]
    language: str


class SessionResponse(BaseModel):
    session_id: str
    created_at: str
    message_count: int
    messages: list[ChatMessage]


# ─── Routes ───────────────────────────────────────────────────

@router.post("/session", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_session(
    request: Request,
    language: str = "en",
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Create a new chat session."""
    if language not in {"en", "zh"}:
        raise HTTPException(status_code=422, detail="language must be en or zh")
    session_id = str(uuid.uuid4())
    chat_service = ChatService()
    await chat_service.create_session(session_id=session_id, language=language, user=current_user)
    return {"session_id": session_id, "language": language}


@router.post("/message", response_model=None)
@limiter.limit("30/minute")
async def send_message(
    request: Request,
    body: ChatRequest,
    current_user: dict = Depends(get_current_user),
) -> ChatResponse | StreamingResponse:
    """
    Send a message to the AI cultural guide.

    If `stream=true`, returns a Server-Sent Events stream.
    """
    chat_service = ChatService()
    session = await chat_service.get_session(body.session_id)
    if not session or session.owner_sub != str(current_user.get("sub", "")):
        # Return 404 for both missing and foreign sessions to avoid leaking IDs.
        raise HTTPException(status_code=404, detail="Session not found or access denied")
    if body.language not in {"en", "zh"}:
        raise HTTPException(status_code=422, detail="language must be en or zh")

    from agents.orchestrator import OrchestratorAgent

    orchestrator = OrchestratorAgent(
        vision_service=request.app.state.vision_service,
        retrieval_service=request.app.state.retrieval_service,
    )

    if body.stream:
        async def event_stream() -> AsyncIterator[str]:
            async for chunk in orchestrator.chat_stream(
                session_id=body.session_id,
                message=body.message,
                language=body.language,
                building_context=body.building_context,
            ):
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    try:
        response = await orchestrator.chat(
            session_id=body.session_id,
            message=body.message,
            language=body.language,
            building_context=body.building_context,
        )
        return response
    except Exception as exc:
        logger.error(f"Chat error [{body.session_id}]: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Chat pipeline error") from exc


@router.get("/session/{session_id}", response_model=SessionResponse)
async def get_session(
    request: Request,
    session_id: str,
    current_user: dict = Depends(get_current_user),
) -> SessionResponse:
    """Retrieve chat history for a session."""
    chat_service = ChatService()
    session = await chat_service.get_session(session_id)
    if not session or session.owner_sub != str(current_user.get("sub", "")):
        raise HTTPException(status_code=404, detail="Session not found or access denied")
    return SessionResponse(
        session_id=session.session_id,
        created_at=session.created_at,
        message_count=session.message_count,
        messages=[ChatMessage(**m) for m in session.messages],
    )


@router.delete("/session/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    request: Request,
    session_id: str,
    current_user: dict = Depends(get_current_user),
) -> None:
    """Clear a chat session."""
    chat_service = ChatService()
    session = await chat_service.get_session(session_id)
    if not session or session.owner_sub != str(current_user.get("sub", "")):
        raise HTTPException(status_code=404, detail="Session not found or access denied")
    await chat_service.delete_session(session_id)
