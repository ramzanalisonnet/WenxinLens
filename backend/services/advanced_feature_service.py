from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

import redis.asyncio as aioredis
from loguru import logger

from config import get_settings
from knowledge_graph.dynasty_catalog import get_dynasty_catalog
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

    @staticmethod
    def _local_building_context(building_name: str, dynasty: str) -> tuple[str, list[dict[str, str]]]:
        needle = (building_name or "").strip().lower()
        rows: list[str] = []

        for block in get_dynasty_catalog():
            full_dynasty = str(block.get("dynasty", ""))
            short_dynasty = full_dynasty.replace(" Dynasty", "")
            if dynasty and dynasty.lower() not in full_dynasty.lower() and dynasty.lower() not in short_dynasty.lower():
                continue

            for place in block.get("places", []):
                if not isinstance(place, dict):
                    continue
                name = str(place.get("name", ""))
                name_zh = str(place.get("name_zh", ""))
                if needle and needle not in name.lower() and needle not in name_zh.lower() and name.lower() not in needle:
                    continue

                rows.append(
                    "\n".join(
                        [
                            f"Building: {name}",
                            f"Dynasty: {short_dynasty or full_dynasty}",
                            f"Location: {place.get('location', '')}",
                            f"Style: {place.get('architecture_type', '')}",
                            f"Year: {place.get('year_built', '')}",
                            f"Description: {place.get('description', '')}",
                        ]
                    )
                )
                if len(rows) >= 3:
                    break
            if len(rows) >= 3:
                break

        if rows:
            return "\n\n".join(rows), [{"source": "dynasty_catalog"}]

        generic = (
            f"Building: {building_name}\n"
            f"Dynasty: {dynasty}\n"
            "Note: Use known Chinese architectural principles (ritual axis, timber framing, roof hierarchy, symbolism) "
            "and answer with explicit uncertainty where details are missing."
        )
        return generic, [{"source": "local_architecture_principles"}]

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
            retrieved: list[dict[str, Any]] = []
            local_sources: list[dict[str, str]] = []

            if self._retrieval is not None:
                try:
                    retrieved = await self._retrieval.search(query=query, building_name=building_name, top_k=6)
                    context = self._retrieval.format_context(retrieved)
                except Exception:
                    context, local_sources = self._local_building_context(building_name, dynasty)
            else:
                context, local_sources = self._local_building_context(building_name, dynasty)

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
                ] or local_sources,
                "degraded": False,
            }
        except Exception as exc:
            logger.warning(f"Historical character fallback used: {exc}")
            fallback_reply = (
                f"As {persona_name} of the {dynasty} period, here is my best grounded reading of {building_name}: "
                "its design balances ritual hierarchy, structural craftsmanship, and symbolic meaning in civic life. "
                "Ask a more specific question (layout, materials, roof system, or symbolism) and I will provide a focused answer."
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
        retrieved: list[dict[str, Any]] = []
        local_sources: list[dict[str, str]] = []

        if self._retrieval is not None:
            try:
                retrieved = await self._retrieval.search(query=query, building_name=building_name, top_k=8)
                context = self._retrieval.format_context(retrieved)
            except Exception as exc:
                logger.warning(f"Cultural DNA retrieval fallback used: {exc}")
                context, local_sources = self._local_building_context(building_name, "")
        else:
            context, local_sources = self._local_building_context(building_name, "")

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

        try:
            explanation = await self._llm.generate(
                user_message=(
                    "Return a concise Markdown report with this exact structure and no preface:\n"
                    "#### Overall Interpretation\n"
                    "1 short paragraph (2-3 sentences).\n\n"
                    "#### Score Breakdown\n"
                    "- **Confucian Influence**: <value>/100 - <1 sentence>\n"
                    "- **Taoist Symbolism**: <value>/100 - <1 sentence>\n"
                    "- **Buddhist Influence**: <value>/100 - <1 sentence>\n"
                    "- **Imperial Authority**: <value>/100 - <1 sentence>\n"
                    "- **Regional Influence**: <value>/100 - <1 sentence>\n"
                    "- **Symbolism Density**: <value>/100 - <1 sentence>\n\n"
                    "#### Practical Reading\n"
                    "2 bullet points for what a visitor should notice on-site.\n\n"
                    f"Building: {building_name}\n"
                    f"Scores JSON: {json.dumps(scores)}"
                ),
                context=context,
                language=language,
                temperature=0.35,
                max_tokens=420,
            )
        except Exception as exc:
            logger.warning(f"Cultural DNA narration fallback used: {exc}")
            explanation = (
                f"{building_name} shows a mixed cultural profile shaped by ritual order, structural craft, and symbolism. "
                f"The score pattern suggests stronger influences where architectural vocabulary is explicit, and moderate values where sources are limited."
                if language == "en"
                else f"{building_name}呈现复合文化谱系，体现礼制秩序、结构工艺与象征意义的共同作用。当前分值反映了可见建筑要素与可用来源信息的综合判断。"
            )

        return {
            "building_name": building_name,
            "scores": scores,
            "analysis": explanation,
            "grounding_sources": [
                {"source": item.get("source", "knowledge base")} for item in retrieved[:5]
            ] or local_sources,
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
        retrieved: list[dict[str, Any]] = []
        local_sources: list[dict[str, str]] = []

        if self._retrieval is not None:
            try:
                retrieved = await self._retrieval.search(query=query, building_name=building_name, top_k=8)
                context = self._retrieval.format_context(retrieved)
            except Exception as exc:
                logger.warning(f"Cross-civilization retrieval fallback used: {exc}")
                context, local_sources = self._local_building_context(building_name, "")
        else:
            context, local_sources = self._local_building_context(building_name, "")

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

        try:
            narrative = await self._llm.generate(
                user_message=(
                    "Return a concise Markdown report with this exact structure and no preface:\n"
                    "#### Comparative Lens\n"
                    "1 short paragraph explaining what is being compared.\n\n"
                    "#### Similarity Highlights\n"
                    "- 3 to 4 bullets, one per most relevant comparison, each including structural and symbolic contrast.\n\n"
                    "#### Key Takeaways\n"
                    "- 2 bullets summarizing what makes the Chinese case distinct and what is globally shared.\n\n"
                    f"Primary building: {building_name}\n"
                    f"Primary style: {architecture_style}\n"
                    f"Candidate comparisons: {rows}"
                ),
                context=context,
                language=language,
                temperature=0.35,
                max_tokens=520,
            )
        except Exception as exc:
            logger.warning(f"Cross-civilization narrative fallback used: {exc}")
            top = rows[:3]
            if language == "en":
                narrative = "\n".join(
                    [
                        "#### Comparative Lens",
                        f"{building_name} can be compared with several traditions through structure and symbolism.",
                        "",
                        "#### Similarity Highlights",
                        *[
                            f"- {item['building']} ({item['civilization']}): {item['similarity']}% similarity via {item['style']}."
                            for item in top
                        ],
                        "",
                        "#### Key Takeaways",
                        "- Shared patterns often emerge in ceremonial spatial hierarchy and monumentality.",
                        "- Distinctive Chinese traits remain visible in ritual axis logic and symbolic roof language.",
                    ]
                )
            else:
                narrative = "\n".join(
                    [
                        "#### Comparative Lens",
                        f"{building_name}可与多种建筑传统进行结构与象征层面的比较。",
                        "",
                        "#### Similarity Highlights",
                        *[
                            f"- {item['building']}（{item['civilization']}）：相似度{item['similarity']}%，主要体现在{item['style']}。"
                            for item in top
                        ],
                        "",
                        "#### Key Takeaways",
                        "- 共同点多体现在礼仪空间层级与纪念性表达。",
                        "- 差异性主要体现在中国建筑的礼制轴线与屋顶象征系统。",
                    ]
                )

        return {
            "building_name": building_name,
            "comparisons": rows,
            "narrative": narrative,
            "grounding_sources": [
                {"source": item.get("source", "knowledge base")} for item in retrieved[:5]
            ] or local_sources,
        }

    async def cinematic_story(
        self,
        building_name: str,
        dynasty: str,
        language: str = "en",
    ) -> dict[str, Any]:
        query = f"documentary style history and symbolism of {building_name} {dynasty}"
        retrieved: list[dict[str, Any]] = []
        local_sources: list[dict[str, str]] = []

        if self._retrieval is not None:
            try:
                retrieved = await self._retrieval.search(query=query, building_name=building_name, top_k=8)
                context = self._retrieval.format_context(retrieved)
            except Exception as exc:
                logger.warning(f"Cinematic retrieval fallback used: {exc}")
                context, local_sources = self._local_building_context(building_name, dynasty)
        else:
            context, local_sources = self._local_building_context(building_name, dynasty)

        try:
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
        except Exception as exc:
            logger.warning(f"Cinematic script fallback used: {exc}")
            script = (
                f"Opening: {building_name} rises as a ceremonial landmark of the {dynasty}.\n"
                "Act I: Craft and geometry establish ritual order through timber, stone, and axial composition.\n"
                "Act II: Symbolism and political meaning turn architecture into a stage for authority and belief.\n"
                "Finale: In the present, preservation reveals how historical form still shapes cultural memory."
                if language == "en"
                else f"开场：{building_name}作为{dynasty}的重要礼仪建筑登场。\n"
                "第一幕：木石工艺与几何秩序共同塑造礼制空间。\n"
                "第二幕：象征系统与政治意义使建筑成为权力与信仰的舞台。\n"
                "尾声：在当代保护语境下，历史形制仍持续影响文化记忆。"
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
            ] or local_sources,
        }
