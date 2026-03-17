"""
TTSService — Text-to-Speech synthesis.

Providers (priority order based on config):
  1. Azure Cognitive Services TTS
  2. ElevenLabs
  3. Coqui TTS (local, open-source)
"""
from __future__ import annotations

import asyncio
import io
from xml.sax.saxutils import escape as xml_escape

from loguru import logger

from config import get_settings

settings = get_settings()


class TTSService:
    """Unified TTS interface with provider abstraction."""

    async def synthesize(
        self,
        text: str,
        language: str = "en",
        voice_id: str = "default",
        speed: float = 1.0,
        pitch: float = 1.0,
    ) -> bytes:
        """Synthesize text to MP3 bytes."""
        if settings.tts_provider == "azure" and settings.azure_tts_key:
            return await self._azure_synthesize(text, language, voice_id, speed)
        elif settings.tts_provider == "elevenlabs" and settings.elevenlabs_api_key:
            return await self._elevenlabs_synthesize(text, voice_id)
        else:
            return await self._coqui_synthesize(text, language)

    async def _azure_synthesize(
        self, text: str, language: str, voice_id: str, speed: float
    ) -> bytes:
        import azure.cognitiveservices.speech as speechsdk  # type: ignore[import-untyped]

        voice_map = {
            ("en", "default"): "en-US-JennyNeural",
            ("zh", "default"): "zh-CN-XiaoxiaoNeural",
        }
        voice = voice_id if voice_id != "default" else voice_map.get((language, "default"), "en-US-JennyNeural")

        ssml = f"""<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis'
                    xmlns:mstts='https://www.w3.org/2001/mstts' xml:lang='{language}'>
            <voice name='{voice}'>
                <prosody rate='{speed:.1f}'>
                    {xml_escape(text)}
                </prosody>
            </voice>
        </speak>"""

        loop = asyncio.get_running_loop()
        audio_bytes = await loop.run_in_executor(None, lambda: self._azure_call(ssml))
        return audio_bytes

    def _azure_call(self, ssml: str) -> bytes:
        import azure.cognitiveservices.speech as speechsdk  # type: ignore[import-untyped]

        speech_config = speechsdk.SpeechConfig(
            subscription=settings.azure_tts_key,
            region=settings.azure_tts_region,
        )
        speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Audio16Khz128KBitRateMonoMp3
        )

        buffer = io.BytesIO()
        audio_config = speechsdk.audio.AudioOutputConfig(stream=speechsdk.audio.PushAudioOutputStream(
            speechsdk.audio.PushAudioOutputStreamCallback()
        ))

        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
        result = synthesizer.speak_ssml_async(ssml).get()
        if result is None:
            raise RuntimeError("Azure TTS: no synthesis result returned")

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            return bytes(result.audio_data)
        raise RuntimeError(f"Azure TTS failed: {result.cancellation_details}")

    async def _elevenlabs_synthesize(self, text: str, voice_id: str) -> bytes:
        import httpx
        voice = "21m00Tcm4TlvDq8ikWAM" if voice_id == "default" else voice_id
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{voice}",
                headers={"xi-api-key": settings.elevenlabs_api_key},
                json={"text": text, "model_id": "eleven_multilingual_v2"},
            )
            response.raise_for_status()
            return response.content

    async def _coqui_synthesize(self, text: str, language: str) -> bytes:
        """Fallback to Coqui TTS (local inference)."""
        try:
            from TTS.api import TTS  # type: ignore[import-untyped]
            loop = asyncio.get_running_loop()

            def _run():
                tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2")
                buf = io.BytesIO()
                tts.tts_to_file(text=text, file_path=buf, language=language[:2])
                return buf.getvalue()

            return await loop.run_in_executor(None, _run)
        except Exception as exc:
            logger.error(f"Coqui TTS failed: {exc}")
            raise RuntimeError("No TTS provider available") from exc
