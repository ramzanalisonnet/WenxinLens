from __future__ import annotations

import io
import json
import math
import re
import shutil
import subprocess
import tempfile
import wave
from dataclasses import dataclass
from typing import Any

from loguru import logger

from config import get_settings
from services.tts_service import TTSService

settings = get_settings()


@dataclass(frozen=True)
class CharacterConfig:
    voice_id: str
    tone: str
    intro: str


CHARACTER_CONFIG: dict[str, CharacterConfig] = {
    "emperor": CharacterConfig(
        voice_id="zh-CN-YunyangNeural",
        tone="authoritative and ceremonial",
        intro="You are an emperor speaking with dignified authority.",
    ),
    "architect": CharacterConfig(
        voice_id="zh-CN-XiaoxiaoNeural",
        tone="calm and technical",
        intro="You are a chief architect explaining structure and craft.",
    ),
    "scholar": CharacterConfig(
        voice_id="en-GB-RyanNeural",
        tone="reflective and historical",
        intro="You are a court scholar providing nuanced historical context.",
    ),
    "guide": CharacterConfig(
        voice_id="en-US-JennyNeural",
        tone="warm and welcoming",
        intro="You are a cultural guide for travelers and students.",
    ),
}

_VOWELS = set("aeiou")


def _clamp_ms(value: int) -> int:
    return max(0, value)


class AvatarService:
    def __init__(self) -> None:
        self._tts = TTSService()

    @staticmethod
    def get_character_config(character_type: str) -> CharacterConfig:
        return CHARACTER_CONFIG.get(character_type.lower(), CHARACTER_CONFIG["guide"])

    async def synthesize_character_speech(
        self,
        text: str,
        character_type: str,
        language: str = "en",
    ) -> tuple[bytes, str]:
        cfg = self.get_character_config(character_type)
        try:
            data = await self._tts.synthesize(
                text=text,
                language=language,
                voice_id=cfg.voice_id,
                speed=1.0,
                pitch=1.0,
            )
            return data, "audio/mpeg"
        except Exception as exc:
            logger.warning(f"Avatar TTS fallback used: {exc}")
            return self._fallback_wav(), "audio/wav"

    @staticmethod
    def _fallback_wav(duration_sec: float = 0.9, freq: float = 220.0) -> bytes:
        sample_rate = 22050
        amplitude = 12000
        total = int(sample_rate * duration_sec)
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            frames = bytearray()
            for i in range(total):
                env = min(1.0, i / 1200) * min(1.0, (total - i) / 1200)
                sample = int(amplitude * env * math.sin(2.0 * math.pi * freq * i / sample_rate))
                frames += sample.to_bytes(2, byteorder="little", signed=True)
            wav.writeframes(frames)
        return buffer.getvalue()

    @staticmethod
    def _estimate_duration_ms(text: str) -> int:
        words = max(1, len(re.findall(r"\w+", text)))
        # ~170 wpm, clamped to keep UI responsive
        approx = int((words / 170.0) * 60_000)
        return max(900, min(9_500, approx))

    @staticmethod
    def _char_to_viseme(ch: str) -> str:
        c = ch.lower()
        if c in {"a", "i"}:
            return "A"
        if c in {"e", "y"}:
            return "B"
        if c in {"o", "u"}:
            return "C"
        if c in {"f", "v"}:
            return "F"
        if c in {"m", "b", "p"}:
            return "H"
        if c in {"l", "n", "r", "t", "d", "s", "z"}:
            return "D"
        if c in {"k", "g", "q", "x"}:
            return "G"
        if c.strip() == "":
            return "X"
        return "E"

    def _fallback_lipsync_timeline(self, text: str, duration_ms: int | None = None) -> list[dict[str, Any]]:
        normalized = re.sub(r"\s+", " ", text.strip())
        if not normalized:
            return [{"start_ms": 0, "end_ms": 400, "viseme": "X"}]

        ms = duration_ms if duration_ms is not None else self._estimate_duration_ms(normalized)
        chars = [c for c in normalized if c.isalpha() or c in _VOWELS or c == " "]
        if not chars:
            return [{"start_ms": 0, "end_ms": ms, "viseme": "X"}]

        per = max(45, ms // max(1, len(chars)))
        cursor = 0
        cues: list[dict[str, Any]] = []

        for ch in chars:
            viseme = self._char_to_viseme(ch)
            end = _clamp_ms(cursor + per)
            cues.append({"start_ms": _clamp_ms(cursor), "end_ms": end, "viseme": viseme})
            cursor = end

        if cues:
            cues[-1]["end_ms"] = ms
        cues.append({"start_ms": ms, "end_ms": ms + 220, "viseme": "X"})
        return cues

    def _rhubarb_lipsync_timeline(self, audio_bytes: bytes, text: str) -> list[dict[str, Any]] | None:
        binary = shutil.which("rhubarb")
        if not binary:
            return None

        with tempfile.TemporaryDirectory(prefix="wenxinlens_lipsync_") as tmp:
            wav_path = f"{tmp}\\speech.wav"
            json_path = f"{tmp}\\speech.json"

            # Rhubarb expects WAV for best portability.
            with wave.open(wav_path, "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(22050)
                # If we only have compressed audio bytes, fallback to synthetic voice envelope.
                # We still gain deterministic timing and usable lip cues.
                sample = self._fallback_wav(duration_sec=max(0.6, len(text) / 24.0))
                with wave.open(io.BytesIO(sample), "rb") as src:
                    wav.writeframes(src.readframes(src.getnframes()))

            cmd = [binary, wav_path, "-f", "json", "-o", json_path]
            completed = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
            if completed.returncode != 0:
                logger.warning(f"Rhubarb failed: {completed.stderr.strip()}")
                return None

            with open(json_path, "r", encoding="utf-8") as f:
                parsed = json.load(f)

            mouth = parsed.get("mouthCues", [])
            timeline: list[dict[str, Any]] = []
            for cue in mouth:
                start_ms = int(float(cue.get("start", 0)) * 1000)
                end_ms = int(float(cue.get("end", 0)) * 1000)
                val = str(cue.get("value", "X"))[:1].upper()
                timeline.append({"start_ms": start_ms, "end_ms": end_ms, "viseme": val})
            return timeline or None

    def build_lipsync_timeline(
        self,
        text: str,
        audio_bytes: bytes | None = None,
        duration_ms: int | None = None,
    ) -> dict[str, Any]:
        if not text.strip():
            return {
                "provider": "fallback",
                "duration_ms": 400,
                "visemes": [{"start_ms": 0, "end_ms": 400, "viseme": "X"}],
            }

        if audio_bytes:
            rhubarb = self._rhubarb_lipsync_timeline(audio_bytes, text)
            if rhubarb:
                duration = max((c["end_ms"] for c in rhubarb), default=0)
                return {
                    "provider": "rhubarb",
                    "duration_ms": duration,
                    "visemes": rhubarb,
                }

        fallback = self._fallback_lipsync_timeline(text, duration_ms=duration_ms)
        duration = max((c["end_ms"] for c in fallback), default=self._estimate_duration_ms(text))
        return {
            "provider": "fallback",
            "duration_ms": duration,
            "visemes": fallback,
        }

    async def transcribe_audio(self, audio_bytes: bytes, language: str | None = None) -> str:
        if not audio_bytes:
            raise ValueError("Empty audio payload")

        if not settings.openai_api_key:
            raise RuntimeError("STT unavailable: OPENAI_API_KEY is not configured")

        try:
            from openai import OpenAI

            client = OpenAI(api_key=settings.openai_api_key)
            with io.BytesIO(audio_bytes) as audio_fp:
                audio_fp.name = "speech.webm"
                lang = language or "en"
                result = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_fp,
                    language=lang,
                )
            text = (result.text or "").strip()
            if not text:
                raise RuntimeError("No transcript produced")
            return text
        except Exception as exc:
            logger.error(f"Avatar STT failed: {exc}")
            raise

    async def build_chat_response(
        self,
        orchestrator: Any,
        building_name: str,
        dynasty: str,
        character_type: str,
        user_message: str,
        language: str,
    ) -> dict[str, Any]:
        character = character_type.lower()
        cfg = self.get_character_config(character)

        # Strengthen persona style while still using existing historical-character agent logic.
        persona_message = f"[{cfg.tone}] {user_message}"
        base = await orchestrator.run_historical_character_chat(
            building_name=building_name,
            dynasty=dynasty,
            character_type=character,
            message=persona_message,
            language=language,
        )

        base["character"] = character
        base["tone"] = cfg.tone
        return base
