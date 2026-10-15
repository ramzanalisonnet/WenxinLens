import json
from typing import Any

import hmac

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from pydantic import BaseModel, Field

from agents.orchestrator import OrchestratorAgent
from services.avatar_service import AvatarService
from config import get_settings
from middleware.auth import decode_access_token, get_current_user
from middleware.rate_limiter import limiter

router = APIRouter()
settings = get_settings()
_avatar_service = AvatarService()


class AvatarChatRequest(BaseModel):
    building_name: str = Field(default="Unknown Building", min_length=1, max_length=200)
    dynasty: str = Field(default="Unknown", min_length=1, max_length=80)
    character_type: str = Field(default="guide", min_length=1, max_length=40)
    message: str = Field(min_length=1, max_length=2000)
    language: str = Field(default="en", pattern="^(en|zh)$")


class AvatarTTSRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    character_type: str = Field(default="guide", min_length=1, max_length=40)
    language: str = Field(default="en", pattern="^(en|zh)$")


class AvatarChatResponse(BaseModel):
    character: str
    persona_name: str
    reply: str
    tone: str
    degraded: bool = False


class AvatarLipSyncRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    duration_ms: int | None = Field(default=None, ge=100, le=20000)


class AvatarLipSyncCue(BaseModel):
    start_ms: int
    end_ms: int
    viseme: str


class AvatarLipSyncResponse(BaseModel):
    provider: str
    duration_ms: int
    visemes: list[AvatarLipSyncCue]


def _get_orchestrator(request: Request) -> OrchestratorAgent:
    return OrchestratorAgent(
        vision_service=request.app.state.vision_service,
        retrieval_service=request.app.state.retrieval_service,
    )


@router.post("/chat", response_model=AvatarChatResponse)
@limiter.limit("20/minute")
async def avatar_chat(body: AvatarChatRequest, request: Request, current_user: dict = Depends(get_current_user)) -> dict[str, Any]:
    try:
        orchestrator = _get_orchestrator(request)
        return await _avatar_service.build_chat_response(
            orchestrator=orchestrator,
            building_name=body.building_name,
            dynasty=body.dynasty,
            character_type=body.character_type,
            user_message=body.message,
            language=body.language,
        )
    except Exception as exc:
        persona_name = {
            "emperor": "Emperor",
            "architect": "Chief Imperial Architect",
            "scholar": "Court Scholar",
            "guide": "Cultural Guide",
        }.get(body.character_type.lower(), "Historical Witness")
        return {
            "character": body.character_type,
            "persona_name": persona_name,
            "reply": (
                f"As {persona_name}, I can provide a brief interpretation of {body.building_name} while the deep generation pipeline recovers."
                if body.language == "en"
                else f"以{persona_name}身份，我可以在深度生成链路恢复期间为你简要解读{body.building_name}。"
            ),
            "tone": "degraded-safe",
            "degraded": True,
        }


@router.post("/tts")
@limiter.limit("10/minute")
async def avatar_tts(request: Request, body: AvatarTTSRequest, current_user: dict = Depends(get_current_user)) -> Response:
    try:
        audio_bytes, media_type = await _avatar_service.synthesize_character_speech(
            text=body.text,
            character_type=body.character_type,
            language=body.language,
        )
        return Response(content=audio_bytes, media_type=media_type)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Speech synthesis is temporarily unavailable.") from exc


@router.post("/stt")
@limiter.limit("10/minute")
async def avatar_stt(
    request: Request,
    audio: UploadFile = File(...),
    language: str | None = None,
    current_user: dict = Depends(get_current_user),
) -> dict[str, str]:
    max_bytes = settings.max_image_size_mb * 1024 * 1024
    if audio.size is not None and audio.size > max_bytes:
        raise HTTPException(status_code=413, detail="Audio upload exceeds the configured size limit.")
    try:
        payload = await audio.read(max_bytes + 1)
        if not payload:
            raise HTTPException(status_code=400, detail="Empty audio upload.")
        if len(payload) > max_bytes:
            raise HTTPException(status_code=413, detail="Audio upload exceeds the configured size limit.")
        text = await _avatar_service.transcribe_audio(payload, language=language)
        return {"text": text}
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Speech transcription is temporarily unavailable.") from exc


@router.post("/lipsync", response_model=AvatarLipSyncResponse)
@limiter.limit("30/minute")
async def avatar_lipsync(request: Request, body: AvatarLipSyncRequest, current_user: dict = Depends(get_current_user)) -> dict[str, Any]:
    try:
        return _avatar_service.build_lipsync_timeline(
            text=body.text,
            duration_ms=body.duration_ms,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Avatar lip-sync generation failed.") from exc


@router.websocket("/ws")
async def avatar_ws(websocket: WebSocket) -> None:
    # WebSocket routes do not execute FastAPI Depends; check credentials explicitly.
    authorization = websocket.headers.get("authorization", "")
    api_key = websocket.headers.get("x-api-key", "")
    allowed = False
    if api_key and settings.master_api_key and hmac.compare_digest(api_key, settings.master_api_key):
        allowed = True
    elif authorization.lower().startswith("bearer "):
        try:
            decode_access_token(authorization.split(" ", 1)[1].strip())
            allowed = True
        except Exception:
            allowed = False
    elif not settings.is_production:
        allowed = True
    if not allowed:
        await websocket.close(code=1008, reason="Authentication required")
        return
    await websocket.accept()
    try:
        await websocket.send_json({"type": "connected", "payload": {"message": "avatar websocket ready"}})
        while True:
            raw = await websocket.receive_text()
            if len(raw) > 16_384:
                await websocket.send_json({"type": "error", "payload": {"detail": "message too large"}})
                continue
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "payload": {"detail": "invalid json"}})
                continue

            event_type = data.get("type")
            payload = data.get("payload", {})

            if event_type == "user_input":
                await websocket.send_json({"type": "listening", "payload": {"state": "LISTENING"}})
                await websocket.send_json({"type": "thinking", "payload": {"state": "THINKING"}})
                await websocket.send_json({"type": "processing", "payload": payload})
            elif event_type == "audio_ready":
                await websocket.send_json({"type": "speaking", "payload": {"state": "SPEAKING"}})
            elif event_type == "animation_trigger":
                await websocket.send_json({"type": "animation", "payload": payload})
            else:
                await websocket.send_json({"type": "echo", "payload": payload})
    except WebSocketDisconnect:
        return
