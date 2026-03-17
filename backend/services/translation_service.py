"""
TranslationService — multilingual support via LLM or NLLB-200.
"""
from __future__ import annotations

import asyncio
from loguru import logger


NLLB_LANG_CODES = {
    "en": "eng_Latn",
    "zh": "zho_Hans",
    "ja": "jpn_Jpan",
    "ko": "kor_Hang",
    "fr": "fra_Latn",
    "es": "spa_Latn",
    "de": "deu_Latn",
}


class TranslationService:
    def __init__(self) -> None:
        self._nllb_model = None
        self._nllb_tokenizer = None

    async def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        if source_lang == target_lang:
            return text
        try:
            return await self._nllb_translate(text, source_lang, target_lang)
        except Exception as exc:
            logger.warning(f"NLLB translation failed, falling back to LLM: {exc}")
            return await self._llm_translate(text, source_lang, target_lang)

    async def _nllb_translate(self, text: str, source_lang: str, target_lang: str) -> str:
        src = NLLB_LANG_CODES.get(source_lang, "eng_Latn")
        tgt = NLLB_LANG_CODES.get(target_lang, "zho_Hans")

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: self._nllb_sync(text, src, tgt))

    def _nllb_sync(self, text: str, src: str, tgt: str) -> str:
        from transformers import pipeline  # type: ignore[import-untyped]
        if self._nllb_model is None:
            self._nllb_model = pipeline(  # type: ignore[call-overload]
                "translation",  # type: ignore[arg-type]
                model="facebook/nllb-200-distilled-600M",
                device=-1,
            )
        result = self._nllb_model(text, src_lang=src, tgt_lang=tgt, max_length=512)
        return result[0]["translation_text"]

    async def _llm_translate(self, text: str, source_lang: str, target_lang: str) -> str:
        from services.llm_service import LLMService
        llm = LLMService()
        lang_names = {"en": "English", "zh": "Chinese (Simplified)"}
        src_name = lang_names.get(source_lang, source_lang)
        tgt_name = lang_names.get(target_lang, target_lang)
        prompt = f"Translate the following text from {src_name} to {tgt_name}. Return only the translation, no explanations:\n\n{text}"
        return await llm.generate(user_message=prompt, language=target_lang)
