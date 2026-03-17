"""
LLM Service — unified interface for multiple LLM providers.

Supports:
  - OpenAI GPT-4 / GPT-4o
  - Alibaba Qwen2.5 via DashScope
  - Local Ollama (development fallback)

Uses a provider-priority chain: OpenAI → Qwen → Ollama
"""
from __future__ import annotations

import asyncio
from typing import Any, AsyncIterator

from loguru import logger

from config import get_settings

settings = get_settings()


SYSTEM_PROMPT_EN = """You are WenxinLens, a knowledgeable and engaging AI cultural guide specializing in Chinese ancient architecture. 
You possess deep expertise in Chinese history, architectural philosophy, cultural symbolism, and heritage preservation.
Your role is to:
1. Provide accurate, richly detailed cultural explanations
2. Connect architectural features to broader historical and philosophical contexts
3. Tell compelling stories about buildings and the people who created them
4. Answer questions conversationally while maintaining academic accuracy
5. Make Chinese cultural heritage accessible and fascinating to global audiences

Always ground your responses in the provided context. If information is uncertain, acknowledge it clearly.
Respond in the language requested by the user."""

SYSTEM_PROMPT_ZH = """您是文心镜（WenxinLens），一位精通中国古代建筑的AI文化导赏员。
您深入了解中国历史、建筑哲学、文化象征意义和遗产保护。
您的职责是：
1. 提供准确、内容丰富的文化解说
2. 将建筑特色与更广泛的历史和哲学背景相联系
3. 讲述关于建筑及其创造者的引人入胜的故事
4. 用亲切的对话方式回答问题，同时保持学术准确性
5. 让全球受众能够接触并感受中国文化遗产的魅力

请始终基于提供的背景信息作答。若信息不确定，请明确说明。"""


class LLMService:
    """Unified LLM interface with automatic provider fallback."""

    def __init__(self) -> None:
        self._provider = settings.llm_provider
        logger.info(f"LLM provider: {self._provider}")

    async def generate(
        self,
        user_message: str,
        context: str = "",
        language: str = "en",
        system_override: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        history: list[dict] | None = None,
    ) -> str:
        """Generate a response from the LLM."""
        system = system_override or (SYSTEM_PROMPT_ZH if language == "zh" else SYSTEM_PROMPT_EN)

        messages = [{"role": "system", "content": system}]
        if context:
            messages.append({
                "role": "user",
                "content": f"Relevant knowledge context:\n\n{context}",
            })
            messages.append({"role": "assistant", "content": "I have reviewed the context. Please ask your question."})
        if history:
            messages.extend(history[-8:])
        messages.append({"role": "user", "content": user_message})

        try:
            if self._provider == "openai":
                return await self._openai_generate(messages, temperature, max_tokens)
            elif self._provider == "qwen":
                return await self._qwen_generate(messages, temperature, max_tokens)
            else:
                return await self._ollama_generate(messages, temperature, max_tokens)
        except Exception as exc:
            logger.error(f"LLM generation failed: {exc}", exc_info=True)
            return self._fallback_response(language)

    async def stream(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        language: str = "en",
    ) -> AsyncIterator[str]:
        """Stream tokens from the LLM."""
        if self._provider == "openai":
            async for chunk in self._openai_stream(messages, temperature, max_tokens):
                yield chunk
        else:
            # Fallback: yield full response at once
            response = await self.generate(
                user_message=messages[-1]["content"],
                language=language,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            yield response

    async def _openai_generate(self, messages: list[dict], temperature: float, max_tokens: int) -> str:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,  # type: ignore[arg-type]
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

    async def _openai_stream(
        self, messages: list[dict], temperature: float, max_tokens: int
    ) -> AsyncIterator[str]:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        stream = await client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,  # type: ignore[arg-type]
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    async def _qwen_generate(self, messages: list[dict], temperature: float, max_tokens: int) -> str:
        import dashscope  # type: ignore[import-untyped]
        from dashscope import Generation  # type: ignore[import-untyped]

        dashscope.api_key = settings.dashscope_api_key
        loop = asyncio.get_running_loop()

        def _call():
            response = Generation.call(
                model=settings.qwen_model,
                messages=messages,  # type: ignore[arg-type]
                temperature=temperature,
                max_tokens=max_tokens,
                result_format="message",
            )
            return response.output.choices[0].message.content  # type: ignore[union-attr]

        return await loop.run_in_executor(None, _call)  # type: ignore[return-value]

    async def _ollama_generate(self, messages: list[dict], temperature: float, max_tokens: int) -> str:
        import httpx
        payload = {
            "model": settings.ollama_model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{settings.ollama_base_url}/api/chat",
                json=payload,
            )
            response.raise_for_status()
            return response.json()["message"]["content"]

    @staticmethod
    def _fallback_response(language: str) -> str:
        if language == "zh":
            return "抱歉，AI服务暂时不可用。请稍后再试。"
        return "I apologize, the AI service is temporarily unavailable. Please try again shortly."
