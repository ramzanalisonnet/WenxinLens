"""
Voice / TTS API
POST /api/v1/voice/synthesize — convert text to speech
GET  /api/v1/voice/voices     — list available voices
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from config import get_settings
from middleware.auth import get_current_user
from services.tts_service import TTSService

settings = get_settings()
router = APIRouter()

_tts_service: TTSService | None = None


def _get_tts() -> TTSService:
    global _tts_service
    if _tts_service is None:
        _tts_service = TTSService()
    return _tts_service


class SynthesizeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    language: str = "en"  # "en" | "zh"
    voice_id: str = "default"
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    pitch: float = Field(default=1.0, ge=0.5, le=2.0)


class VoiceInfo(BaseModel):
    voice_id: str
    name: str
    language: str
    gender: str
    description: str


@router.post("/synthesize")
async def synthesize_speech(
    body: SynthesizeRequest,
    current_user: dict = Depends(get_current_user),
) -> Response:
    """Convert text to MP3 audio using the configured TTS provider."""
    tts = _get_tts()
    try:
        audio_bytes = await tts.synthesize(
            text=body.text,
            language=body.language,
            voice_id=body.voice_id,
            speed=body.speed,
            pitch=body.pitch,
        )
        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={"Content-Disposition": "attachment; filename=narration.mp3"},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"TTS synthesis failed: {exc}") from exc


@router.get("/voices", response_model=list[VoiceInfo])
async def list_voices(
    language: str | None = None,
    current_user: dict = Depends(get_current_user),
) -> list[VoiceInfo]:
    """Return available TTS voices, optionally filtered by language."""
    voices = [
        VoiceInfo(voice_id="zh-CN-XiaoxiaoNeural", name="Xiaoxiao", language="zh", gender="female",
                  description="Warm, expressive Mandarin female voice"),
        VoiceInfo(voice_id="zh-CN-YunyangNeural", name="Yunyang", language="zh", gender="male",
                  description="Professional Mandarin male voice"),
        VoiceInfo(voice_id="en-US-JennyNeural", name="Jenny", language="en", gender="female",
                  description="Friendly American English female voice"),
        VoiceInfo(voice_id="en-GB-RyanNeural", name="Ryan", language="en", gender="male",
                  description="Calm British English male voice"),
    ]
    if language:
        voices = [v for v in voices if v.language == language]
    return voices
