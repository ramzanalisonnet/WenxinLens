"""
ExplanationAgent — generates rich cultural explanations using LLMs.

Injection prompt structure:
  System: WenxinLens cultural guide persona
  Context: [retrieved knowledge chunks]
  User: "Explain {building_name} in {detail_level} detail"

Supports three detail levels:
  tourist   — approachable, story-driven, ~200 words
  standard  — balanced historical + cultural, ~400 words
  academic  — scholarly, cites architectural principles, ~600 words
"""
from __future__ import annotations

from loguru import logger

from agents.state import AgentState
from services.llm_service import LLMService


EXPLANATION_TEMPLATES = {
    "tourist": (
        "Please provide an engaging, accessible explanation of {building} "
        "suitable for a first-time visitor. Use vivid storytelling, mention "
        "2-3 fascinating facts, and highlight what makes this place special. "
        "Keep it around 200 words."
    ),
    "standard": (
        "Provide a comprehensive cultural explanation of {building}, covering: "
        "1) Historical background and construction, "
        "2) Architectural style and key structural features, "
        "3) Cultural and philosophical symbolism, "
        "4) Notable stories or historical events associated with it. "
        "Target length: 400 words."
    ),
    "academic": (
        "Provide a scholarly architectural analysis of {building}, including: "
        "1) Historical and dynastic context with specific dates, "
        "2) Architectural typology and its place in Chinese architectural history, "
        "3) Structural system (dougong, bay system, roof form), "
        "4) Cultural semiotic significance and ritual function, "
        "5) Comparison with contemporary buildings of the same style, "
        "6) Conservation status and scholarly debates. "
        "Target: 600+ words with precise architectural terminology."
    ),
}

FOLLOW_UP_TEMPLATES = {
    "en": (
        "Based on the building just discussed, suggest 3 thought-provoking follow-up "
        "questions that a curious visitor might ask. Return as a JSON array of strings."
    ),
    "zh": (
        "根据刚才讨论的建筑，提出3个好奇游客可能会问的深思熟虑的后续问题。以JSON字符串数组形式返回。"
    ),
}


class ExplanationAgent:
    """Generates structured cultural explanations using an LLM."""

    def __init__(self) -> None:
        self._llm = LLMService()

    async def run(self, state: AgentState) -> AgentState:
        """
        Input:  recognition fields + formatted_context
        Output: state['explanation'], state['explanation_zh'], state['follow_up_questions']
        """
        building_name = state.get("building_name", "this building")
        building_name_zh = state.get("building_name_zh", "这座建筑")
        dynasty = state.get("dynasty", "")
        style = state.get("architecture_style", "")
        features = state.get("structural_features", [])
        context = state.get("formatted_context", "")
        advanced_summary = state.get("advanced_feature_summary", "")
        language = state.get("language", "en")
        detail_level = state.get("detail_level", "standard")

        if advanced_summary:
            context = f"{context}\n\n[Advanced Feature Layer]\n{advanced_summary}" if context else advanced_summary

        template = EXPLANATION_TEMPLATES.get(detail_level, EXPLANATION_TEMPLATES["standard"])
        prompt_en = template.format(building=f"{building_name} ({dynasty}, {style})")

        # Features preamble
        if features:
            features_text = ", ".join(features[:4])
            prompt_en += f"\n\nKey structural features observed: {features_text}."

        logger.info(f"ExplanationAgent: generating {detail_level} explanation for {building_name}")

        try:
            explanation = await self._llm.generate(
                user_message=prompt_en,
                context=context,
                language=language,
                temperature=0.75,
            )

            # Generate Chinese version if English was primary
            explanation_zh = ""
            if language == "en":
                prompt_zh = EXPLANATION_TEMPLATES.get(detail_level, EXPLANATION_TEMPLATES["standard"]).format(
                    building=f"{building_name_zh}（{dynasty}，{style}）"
                )
                explanation_zh = await self._llm.generate(
                    user_message=prompt_zh,
                    context=context,
                    language="zh",
                    temperature=0.75,
                )
            elif language == "zh":
                explanation_zh = explanation
                explanation = await self._llm.generate(
                    user_message=prompt_en,
                    context=context,
                    language="en",
                    temperature=0.75,
                )

            # Generate follow-up questions
            follow_ups = await self._generate_follow_ups(building_name, language, context)

            # Cultural significance (brief)
            cultural_significance = await self._llm.generate(
                user_message=f"In one sentence, what is the greatest cultural significance of {building_name}?",
                context=context,
                language=language,
                temperature=0.5,
                max_tokens=150,
            )

            return {
                **state,
                "explanation": explanation,
                "explanation_zh": explanation_zh,
                "cultural_significance": cultural_significance,
                "follow_up_questions": follow_ups,
                "step": "explanation_complete",
            }
        except Exception as exc:
            logger.error(f"ExplanationAgent error: {exc}", exc_info=True)
            return {
                **state,
                "explanation": f"Information about {building_name} is currently being processed.",
                "explanation_zh": f"关于{building_name_zh}的信息正在处理中。",
                "cultural_significance": "",
                "follow_up_questions": [],
                "step": "explanation_failed",
            }

    async def _generate_follow_ups(
        self, building_name: str, language: str, context: str
    ) -> list[str]:
        prompt = FOLLOW_UP_TEMPLATES.get(language, FOLLOW_UP_TEMPLATES["en"])
        full_prompt = f"Building: {building_name}\n\n{prompt}"
        try:
            import json
            raw = await self._llm.generate(
                user_message=full_prompt,
                context=context,
                language=language,
                temperature=0.8,
                max_tokens=300,
            )
            # Extract JSON array
            start = raw.find("[")
            end = raw.rfind("]") + 1
            if start >= 0 and end > start:
                questions = json.loads(raw[start:end])
                return questions[:3]
        except Exception:
            pass
        return [
            f"Who built {building_name}?",
            f"What is the symbolic meaning of the roof design?",
            f"How was {building_name} used in ceremonies?",
        ]
