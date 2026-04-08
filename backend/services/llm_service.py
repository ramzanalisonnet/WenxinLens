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
import random
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
Respond in the language requested by the user.

Formatting requirements for every response:
- Use concise, well-structured Markdown.
- Start with a short direct answer (1-2 sentences).
- Then provide 3-6 bullet points with concrete details.
- Use short section headers (e.g., "#### Key Points") when helpful.
- Avoid long unbroken paragraphs and avoid repeating the same point."""

SYSTEM_PROMPT_ZH = """您是文心镜（WenxinLens），一位精通中国古代建筑的AI文化导赏员。
您深入了解中国历史、建筑哲学、文化象征意义和遗产保护。
您的职责是：
1. 提供准确、内容丰富的文化解说
2. 将建筑特色与更广泛的历史和哲学背景相联系
3. 讲述关于建筑及其创造者的引人入胜的故事
4. 用亲切的对话方式回答问题，同时保持学术准确性
5. 让全球受众能够接触并感受中国文化遗产的魅力

请始终基于提供的背景信息作答。若信息不确定，请明确说明。

格式要求（每次回复都遵循）：
- 使用简洁、结构化的 Markdown。
- 先给出 1-2 句直接结论。
- 然后给出 3-6 条要点式条目，包含具体信息。
- 必要时使用简短小标题（如“#### 关键要点”）。
- 避免大段连续文字，避免重复表述。"""


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

        provider_chain = [self._provider]
        for p in ("openai", "qwen", "ollama"):
            if p not in provider_chain:
                provider_chain.append(p)

        last_exc: Exception | None = None
        for provider in provider_chain:
            try:
                if provider == "openai":
                    return await self._openai_generate(messages, temperature, max_tokens)
                if provider == "qwen":
                    return await self._qwen_generate(messages, temperature, max_tokens)
                return await self._ollama_generate(messages, temperature, max_tokens)
            except Exception as exc:
                last_exc = exc
                logger.warning(f"LLM provider '{provider}' failed, trying next provider: {exc}")

        if last_exc is not None:
            logger.error(f"All LLM providers failed: {last_exc}", exc_info=True)
        return self._contextual_fallback(user_message=user_message, context=context, language=language)

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
        api_key = (settings.openai_api_key or "").strip()

        # Support OpenRouter keys even when provider resolves to "openai".
        if api_key.startswith("sk-or-v1"):
            return await self._openrouter_generate(
                api_key=api_key,
                model=settings.openai_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=api_key)
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
        api_key = (settings.openai_api_key or "").strip()

        if api_key.startswith("sk-or-v1"):
            # Keep streaming contract simple for OpenRouter fallback: emit one full chunk.
            response = await self._openrouter_generate(
                api_key=api_key,
                model=settings.openai_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            yield response
            return

        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=api_key)
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
        api_key = (settings.dashscope_api_key or "").strip()

        # Support OpenRouter-style keys transparently while keeping the same env variable.
        if api_key.startswith("sk-or-v1"):
            return await self._openrouter_generate(
                api_key=api_key,
                model=settings.qwen_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        import dashscope  # type: ignore[import-untyped]
        from dashscope import Generation  # type: ignore[import-untyped]

        dashscope.api_key = api_key
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

    async def _openrouter_generate(
        self,
        api_key: str,
        model: str,
        messages: list[dict],
        temperature: float,
        max_tokens: int,
    ) -> str:
        import httpx

        site_url = settings.openrouter_site_url
        app_name = settings.openrouter_app_name

        fallbacks_raw = settings.openrouter_fallback_models
        fallback_models = [m.strip() for m in fallbacks_raw.split(",") if m.strip()]
        resilience_models = [
            "qwen/qwen3.6-plus:free",
            "nvidia/nemotron-3-super-120b-a12b:free",
            "openai/gpt-4o-mini",
        ]

        model_chain: list[str] = [model]
        model_chain.extend([m for m in fallback_models if m not in model_chain])
        model_chain.extend([m for m in resilience_models if m not in model_chain])

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": site_url,
            "X-Title": app_name,
        }

        last_exc: Exception | None = None
        for candidate_model in model_chain:
            for attempt in range(3):
                payload = {
                    "model": candidate_model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }

                try:
                    async with httpx.AsyncClient(timeout=120.0) as client:
                        response = await client.post(
                            "https://openrouter.ai/api/v1/chat/completions",
                            json=payload,
                            headers=headers,
                        )
                        response.raise_for_status()
                        data = response.json()

                    content = (
                        data.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content", "")
                    )

                    if not content:
                        raise RuntimeError(f"OpenRouter returned empty content: {data}")

                    if candidate_model != model:
                        logger.warning(f"OpenRouter fallback model used: {candidate_model} (requested: {model})")
                    return str(content)
                except httpx.HTTPStatusError as exc:
                    last_exc = exc
                    status_code = exc.response.status_code if exc.response is not None else 0

                    if status_code == 429 and attempt < 2:
                        retry_after = 0.0
                        if exc.response is not None:
                            header_val = exc.response.headers.get("Retry-After")
                            try:
                                retry_after = float(header_val) if header_val else 0.0
                            except Exception:
                                retry_after = 0.0
                        backoff = max(1.5 * (2 ** attempt), retry_after) + random.uniform(0.1, 0.5)
                        logger.warning(
                            f"OpenRouter rate-limited on {candidate_model} (attempt {attempt + 1}/3), retrying in {backoff:.1f}s"
                        )
                        await asyncio.sleep(backoff)
                        continue

                    # Move to next model for common model-selection/quota failures.
                    if status_code in {400, 402, 404, 429, 502, 503}:
                        break
                    raise
                except Exception as exc:
                    last_exc = exc
                    break

        if last_exc:
            raise last_exc
        raise RuntimeError("OpenRouter request failed without specific error")

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
    def _contextual_fallback(user_message: str, context: str, language: str) -> str:
        clean_question = LLMService._sanitize_user_message(user_message)
        snippet = (context or "").strip().replace("\n", " ")[:260]
        points_en, points_zh = LLMService._heuristic_points(clean_question)

        if language == "zh":
            if snippet:
                return (
                    "#### 快速解读\n"
                    "以下内容基于当前可用的建筑知识与通用历史规律整理。\n\n"
                    "#### 关键要点\n"
                    f"- 你的问题：{clean_question[:120]}\n"
                    f"- 可用背景：{snippet}\n"
                    f"- {points_zh[0]}\n"
                    f"- {points_zh[1]}\n"
                    f"- {points_zh[2]}"
                )
            return (
                "#### 快速解读\n"
                "以下为基于通用建筑史框架的结构化回答。\n\n"
                "#### 关键要点\n"
                f"- 你的问题：{clean_question[:120]}\n"
                f"- {points_zh[0]}\n"
                f"- {points_zh[1]}\n"
                f"- {points_zh[2]}"
            )

        if snippet:
            return (
                "#### Quick Reading\n"
                "This answer is generated from currently available architectural context and historical priors.\n\n"
                "#### Key Points\n"
                f"- Your question: {clean_question[:120]}\n"
                f"- Available context: {snippet}\n"
                f"- {points_en[0]}\n"
                f"- {points_en[1]}\n"
                f"- {points_en[2]}"
            )
        return (
            "#### Quick Reading\n"
            "Here is a structured answer based on core Chinese architectural principles.\n\n"
            "#### Key Points\n"
            f"- Your question: {clean_question[:120]}\n"
            f"- {points_en[0]}\n"
            f"- {points_en[1]}\n"
            f"- {points_en[2]}"
        )

    @staticmethod
    def _sanitize_user_message(user_message: str) -> str:
        text = (user_message or "").strip()
        if not text:
            return ""

        marker_en = "Respond in structured Markdown"
        marker_zh = "请用结构化Markdown回答"
        idx_en = text.find(marker_en)
        idx_zh = text.find(marker_zh)
        indices = [i for i in (idx_en, idx_zh) if i >= 0]
        if indices:
            text = text[: min(indices)].strip()

        text = text.splitlines()[0].strip() if text.splitlines() else text
        return text

    @staticmethod
    def _heuristic_points(question: str) -> tuple[list[str], list[str]]:
        q = (question or "").lower()

        if "roof" in q or "symbol" in q:
            en = [
                "Roof form and color usually encode ritual rank and cosmological meaning.",
                "Axial composition and elevation often express authority and ceremonial hierarchy.",
                "Decorative motifs (animals, colors, brackets) often map to moral or political symbolism.",
            ]
            zh = [
                "屋顶形制与色彩通常对应礼制等级与宇宙观象征。",
                "中轴线与高差组织常用于表达权力与仪式层级。",
                "脊饰、色彩与斗拱等细部常承载政治与伦理象征。",
            ]
            return en, zh

        if "material" in q or "wood" in q or "timber" in q:
            en = [
                "Timber framing is central for flexibility, seismic resilience, and modular expansion.",
                "Material selection often balances durability, climate adaptation, and ritual aesthetics.",
                "Joinery and bracket systems distribute load while preserving ornate roof profiles.",
            ]
            zh = [
                "木构体系核心优势在于柔性抗震与模数化扩展能力。",
                "材料选择通常兼顾耐久性、气候适应与礼制审美。",
                "榫卯与斗拱在维持大屋顶形态的同时完成有效传力。",
            ]
            return en, zh

        en = [
            "Chinese monumental architecture commonly integrates ritual order, engineering logic, and symbolism.",
            "Spatial hierarchy (axis, courtyards, gates) often reflects social and political structure.",
            "Style differences across dynasties are usually visible in roof type, bracket complexity, and ornament.",
        ]
        zh = [
            "中国大型建筑通常将礼制秩序、工程逻辑与象征系统结合在一起。",
            "轴线、院落与门阙层级往往对应社会与政治结构。",
            "不同朝代的风格差异常体现在屋顶、斗拱复杂度与装饰语汇上。",
        ]
        return en, zh
