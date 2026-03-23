from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

import redis.asyncio as aioredis
from loguru import logger

from config import get_settings
from services.llm_service import LLMService
from services.retrieval_service import RetrievalService

settings = get_settings()


@dataclass
class TimeSnapshot:
    dynasty: str
    prompt: str
    image_url: str
    explanation: str


class AdvancedFeatureService:
    def __init__(self, retrieval_service: RetrievalService) -> None:
        self._retrieval = retrieval_service
        self._llm = LLMService()
        self._redis: aioredis.Redis | None = None

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = await aioredis.from_url(
                settings.redis_url,
                password=settings.redis_password or None,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._redis

    async def _cache_get(self, key: str) -> dict[str, Any] | None:
        try:
            redis = await self._get_redis()
            raw = await redis.get(key)
            return json.loads(raw) if raw else None
        except Exception as exc:
            logger.warning(f"AdvancedFeature cache get failed: {exc}")
            return None

    async def _cache_set(self, key: str, value: dict[str, Any], ttl: int = 3600) -> None:
        try:
            redis = await self._get_redis()
            await redis.setex(key, ttl, json.dumps(value, ensure_ascii=False))
        except Exception as exc:
            logger.warning(f"AdvancedFeature cache set failed: {exc}")

    @staticmethod
    def _stable_key(prefix: str, payload: dict[str, Any]) -> str:
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:24]
        return f"wenxinlens:advanced:{prefix}:{digest}"

    async def build_time_reconstruction(
        self,
        building_name: str,
        dynasty: str,
        structural_features: list[str],
        snapshots: list[str] | None = None,
        language: str = "en",
    ) -> dict[str, Any]:
        target_snapshots = snapshots or ["Tang", "Song", "Ming", "Qing"]
        key = self._stable_key(
            "time_reconstruction",
            {
                "building_name": building_name,
                "dynasty": dynasty,
                "structural_features": structural_features,
                "snapshots": target_snapshots,
                "language": language,
            },
        )
        cached = await self._cache_get(key)
        if cached:
            return cached

        query = f"timeline evolution of {building_name} architecture by dynasty"
        retrieved = await self._retrieval.search(query=query, building_name=building_name, top_k=6)
        context = self._retrieval.format_context(retrieved)

        output: list[dict[str, str]] = []
        for era in target_snapshots:
            feature_text = ", ".join(structural_features) if structural_features else "timber frame"
            prompt = (
                f"A detailed reconstruction of {building_name} during the {era} Dynasty, "
                f"traditional Chinese architecture, {feature_text}"
            )
            explain_prompt = (
                f"Summarize how {building_name} would likely appear in {era} Dynasty and what changed from {dynasty}."
            )
            explanation = await self._llm.generate(
                user_message=explain_prompt,
                context=context,
                language=language,
                temperature=0.5,
                max_tokens=300,
            )
            image_token = hashlib.sha1(f"{building_name}:{era}:{prompt}".encode("utf-8")).hexdigest()[:12]
            output.append(
                {
                    "dynasty": era,
                    "prompt": prompt,
                    "image_url": f"/generated/time-reconstruction/{image_token}.png",
                    "explanation": explanation,
                }
            )

        result = {
            "building_name": building_name,
            "current_dynasty": dynasty,
            "snapshots": output,
            "grounding_sources": [
                {
                    "source": item.get("source", "knowledge base"),
                    "score": item.get("score", 0),
                }
                for item in retrieved[:5]
            ],
            "generation_backend": "sdxl-controlnet-ready",
            "cached": False,
        }
        await self._cache_set(key, result, ttl=7200)
        return result

    async def historical_character_reply(
        self,
        building_name: str,
        dynasty: str,
        character_type: str,
        message: str,
        language: str = "en",
    ) -> dict[str, Any]:
        persona_name = {
            "emperor": "Emperor",
            "architect": "Chief Imperial Architect",
            "worker": "Master Builder",
            "scholar": "Court Scholar",
        }.get(character_type.lower(), "Historical Witness")

        try:
            query = f"{building_name} {dynasty} emperor architect scholar worker history"
            retrieved = await self._retrieval.search(query=query, building_name=building_name, top_k=6)
            context = self._retrieval.format_context(retrieved)

            system = (
                f"You are {persona_name}, living in {dynasty}. Speak in first person, remain historically grounded, "
                f"and mention uncertainty explicitly when sources are incomplete."
            )
            reply = await self._llm.generate(
                user_message=f"Building: {building_name}\nUser asks: {message}",
                context=context,
                language=language,
                system_override=system,
                temperature=0.7,
                max_tokens=500,
            )

            return {
                "character": character_type,
                "persona_name": persona_name,
                "reply": reply,
                "grounding_sources": [
                    {"source": item.get("source", "knowledge base")} for item in retrieved[:4]
                ],
                "degraded": False,
            }
        except Exception as exc:
            logger.warning(f"Historical character fallback used: {exc}")
            fallback_reply = (
                f"As {persona_name} of the {dynasty} period, I can share a concise view: "
                f"{building_name} was shaped by ritual order, craftsmanship, and social meaning. "
                "Detailed archival references are temporarily unavailable, but you can continue asking and I will respond with best-effort historical context."
                if language == "en"
                else f"以{dynasty}时期的{persona_name}身份，我可以先给出简要说明：{building_name}体现了礼制秩序、工艺技术与社会意义。"
                "当前详细史料检索暂不可用，但你可以继续提问，我会以尽可能可靠的历史语境作答。"
            )
            return {
                "character": character_type,
                "persona_name": persona_name,
                "reply": fallback_reply,
                "grounding_sources": [],
                "degraded": True,
            }

    async def cultural_dna_profile(
        self,
        building_name: str,
        architecture_style: str,
        structural_features: list[str],
        language: str = "en",
    ) -> dict[str, Any]:
        query = f"cultural symbolism confucian taoist buddhist imperial {building_name} {architecture_style}"
        retrieved = await self._retrieval.search(query=query, building_name=building_name, top_k=8)
        context = self._retrieval.format_context(retrieved)

        joined = " ".join([architecture_style] + structural_features).lower()
        conf = 70 + (8 if "axis" in joined or "symmetry" in joined else 0)
        tao = 58 + (10 if "garden" in joined or "landscape" in joined else 0)
        bud = 54 + (12 if "pagoda" in joined or "temple" in joined else 0)
        imp = 66 + (15 if "palace" in joined or "imperial" in joined else 0)
        reg = 52 + (8 if "regional" in joined else 0)
        sym = 60 + (10 if len(structural_features) >= 4 else 0)

        scores = {
            "confucian_influence": min(conf, 95),
            "taoist_symbolism": min(tao, 95),
            "buddhist_influence": min(bud, 95),
            "imperial_authority": min(imp, 98),
            "regional_influence": min(reg, 90),
            "symbolism_density": min(sym, 95),
        }

        explanation = await self._llm.generate(
            user_message=(
                f"Explain this Cultural DNA profile for {building_name} using these scores: {json.dumps(scores)}"
            ),
            context=context,
            language=language,
            temperature=0.5,
            max_tokens=500,
        )

        return {
            "building_name": building_name,
            "scores": scores,
            "analysis": explanation,
            "grounding_sources": [
                {"source": item.get("source", "knowledge base")} for item in retrieved[:5]
            ],
        }

    async def cross_civilization_comparison(
        self,
        building_name: str,
        architecture_style: str,
        language: str = "en",
    ) -> dict[str, Any]:
        candidates = [
            {"name": "Horyu-ji", "civilization": "Japanese", "style": "pagoda/temple timber"},
            {"name": "Qutub Complex", "civilization": "Indian-Islamic", "style": "stone courtyard + minaret"},
            {"name": "Notre-Dame de Paris", "civilization": "European Gothic", "style": "vertical vaulted cathedral"},
            {"name": "Topkapi Palace", "civilization": "Ottoman", "style": "imperial court architecture"},
        ]

        query = f"compare {building_name} {architecture_style} with japanese indian islamic gothic baroque"
        retrieved = await self._retrieval.search(query=query, building_name=building_name, top_k=8)
        context = self._retrieval.format_context(retrieved)

        rows: list[dict[str, Any]] = []
        base = hashlib.sha1(f"{building_name}:{architecture_style}".encode("utf-8")).hexdigest()
        for idx, item in enumerate(candidates):
            score = 55 + (int(base[idx * 2: idx * 2 + 2], 16) % 36)
            rows.append(
                {
                    "building": item["name"],
                    "civilization": item["civilization"],
                    "style": item["style"],
                    "similarity": score,
                }
            )

        rows.sort(key=lambda x: x["similarity"], reverse=True)

        narrative = await self._llm.generate(
            user_message=(
                f"Provide a grounded comparison of {building_name} ({architecture_style}) with these references: {rows}. "
                "Cover structure, philosophy, materials, symbolism, and engineering techniques."
            ),
            context=context,
            language=language,
            temperature=0.55,
            max_tokens=600,
        )

        return {
            "building_name": building_name,
            "comparisons": rows,
            "narrative": narrative,
            "grounding_sources": [
                {"source": item.get("source", "knowledge base")} for item in retrieved[:5]
            ],
        }

    async def cinematic_story(
        self,
        building_name: str,
        dynasty: str,
        language: str = "en",
    ) -> dict[str, Any]:
        query = f"documentary style history and symbolism of {building_name} {dynasty}"
        retrieved = await self._retrieval.search(query=query, building_name=building_name, top_k=8)
        context = self._retrieval.format_context(retrieved)

        script = await self._llm.generate(
            user_message=(
                f"Generate a cinematic documentary script for {building_name}. "
                "Include intro, construction era, cultural meaning, and modern relevance."
            ),
            context=context,
            language=language,
            temperature=0.75,
            max_tokens=900,
        )

        scenes = [
            {"scene": 1, "title": "Introduction", "focus": "Setting and opening atmosphere"},
            {"scene": 2, "title": "Construction", "focus": f"Dynasty context: {dynasty}"},
            {"scene": 3, "title": "Cultural Meaning", "focus": "Ritual symbolism and philosophy"},
            {"scene": 4, "title": "Modern Relevance", "focus": "Conservation and global significance"},
        ]

        token = hashlib.sha1(f"{building_name}:{dynasty}:{language}".encode("utf-8")).hexdigest()[:14]
        return {
            "building_name": building_name,
            "script": script,
            "scene_plan": scenes,
            "audio": {
                "provider": settings.tts_provider,
                "status": "tts-ready",
                "audio_url": f"/generated/cinematic/{token}.mp3",
            },
            "grounding_sources": [
                {"source": item.get("source", "knowledge base")} for item in retrieved[:6]
            ],
        }
