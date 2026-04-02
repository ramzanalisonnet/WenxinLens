import json
from typing import Any

from fastapi import APIRouter, File, HTTPException, Request, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from pydantic import BaseModel, Field

from agents.orchestrator import OrchestratorAgent
from services.avatar_service import AvatarService

router = APIRouter()
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
async def avatar_chat(body: AvatarChatRequest, request: Request) -> dict[str, Any]:
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
async def avatar_tts(body: AvatarTTSRequest) -> Response:
    try:
        audio_bytes, media_type = await _avatar_service.synthesize_character_speech(
            text=body.text,
            character_type=body.character_type,
            language=body.language,
        )
        return Response(content=audio_bytes, media_type=media_type)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Avatar TTS failed: {exc}") from exc


@router.post("/stt")
async def avatar_stt(
    audio: UploadFile = File(...),
    language: str | None = None,
) -> dict[str, str]:
    try:
        payload = await audio.read()
        text = await _avatar_service.transcribe_audio(payload, language=language)
        return {"text": text}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Avatar STT failed: {exc}") from exc


@router.post("/lipsync", response_model=AvatarLipSyncResponse)
async def avatar_lipsync(body: AvatarLipSyncRequest) -> dict[str, Any]:
    try:
        return _avatar_service.build_lipsync_timeline(
            text=body.text,
            duration_ms=body.duration_ms,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Avatar lip sync failed: {exc}") from exc


@router.websocket("/ws")
async def avatar_ws(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        await websocket.send_json({"type": "connected", "payload": {"message": "avatar websocket ready"}})
        while True:
            raw = await websocket.receive_text()
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
