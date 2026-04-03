"""
OrchestratorAgent — LangGraph-based pipeline coordinator.

Two primary workflows:
  1. analyze(image)     — Recognition → Retrieval → Explanation
  2. chat(message)      — Retrieval → Interaction

Uses LangGraph StateGraph to model agent transitions.
Falls back to sequential execution if LangGraph unavailable.
"""
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, AsyncIterator

from loguru import logger

if TYPE_CHECKING:
    from api.routes.recognition import RecognitionResult
    from api.routes.chat import ChatResponse

from agents.state import AgentState
from agents.recognition_agent import RecognitionAgent
from agents.retrieval_agent import RetrievalAgent
from agents.explanation_agent import ExplanationAgent
from agents.interaction_agent import InteractionAgent
from agents.time_reconstruction_agent import TimeReconstructionAgent
from agents.historical_character_agent import HistoricalCharacterAgent
from agents.cultural_dna_agent import CulturalDNAAgent
from agents.comparison_agent import ComparisonAgent
from agents.cinematic_agent import CinematicAgent
from services.vision_service import VisionService
from services.retrieval_service import RetrievalService
from services.advanced_feature_service import AdvancedFeatureService


class OrchestratorAgent:
    """
    Manages the multi-agent pipeline.

    Architecture:
        analyze workflow:
            RecognitionAgent → RetrievalAgent → ExplanationAgent → result

        chat workflow:
            RetrievalAgent → InteractionAgent → result
    """

    def __init__(
        self,
        vision_service: VisionService,
        retrieval_service: RetrievalService,
    ) -> None:
        self._recognition = RecognitionAgent(vision_service)
        self._retrieval = RetrievalAgent(retrieval_service)
        self._advanced_service = AdvancedFeatureService(retrieval_service)
        self._time_reconstruction = TimeReconstructionAgent(self._advanced_service)
        self._historical_character = HistoricalCharacterAgent(self._advanced_service)
        self._cultural_dna = CulturalDNAAgent(self._advanced_service)
        self._comparison = ComparisonAgent(self._advanced_service)
        self._cinematic = CinematicAgent(self._advanced_service)
        self._explanation = ExplanationAgent()
        self._interaction = InteractionAgent(retrieval_service)
        self._graph = self._build_graph()

    def _build_graph(self):
        """
        Build LangGraph StateGraph for the analysis pipeline.
        Returns None if LangGraph is unavailable (graceful degradation).
        """
        try:
            from langgraph.graph import StateGraph, END

            workflow = StateGraph(AgentState)  # type: ignore[arg-type]

            # Add nodes (each is an async callable)
            workflow.add_node("recognition", self._recognition.run)
            workflow.add_node("retrieval", self._retrieval.run)
            workflow.add_node("advanced_layer", self._run_advanced_layer)
            workflow.add_node("explanation_step", self._explanation.run)

            # Edges
            workflow.set_entry_point("recognition")
            workflow.add_edge("recognition", "retrieval")
            workflow.add_edge("retrieval", "advanced_layer")
            workflow.add_edge("advanced_layer", "explanation_step")
            workflow.add_edge("explanation_step", END)

            return workflow.compile()
        except ImportError:
            logger.warning("LangGraph not available — using sequential pipeline")
            return None

    # ── Public API ──────────────────────────────────────────────

    async def analyze(
        self,
        image,
        result_id: str,
        language: str = "en",
        detail_level: str = "standard",
    ) -> "RecognitionResult":
        """Full analysis pipeline: image → cultural explanation."""
        from api.routes.recognition import RecognitionResult
        initial_state: AgentState = {
            "image": image,
            "result_id": result_id,
            "language": language,
            "detail_level": detail_level,
            "user_message": "",
        }

        if self._graph:
            final_state: AgentState = await self._graph.ainvoke(initial_state)  # type: ignore[assignment]
        else:
            final_state = await self._run_sequential_analysis(initial_state)

        if final_state.get("error"):
            raise RuntimeError(str(final_state.get("error")))

        return self._build_recognition_result(final_state, result_id)

    async def chat(
        self,
        session_id: str,
        message: str,
        language: str = "en",
        building_context: str | None = None,
    ) -> "ChatResponse":
        """Chat pipeline: message → conversational response."""
        from api.routes.chat import ChatResponse
        state: AgentState = {
            "session_id": session_id,
            "user_message": message,
            "language": language,
            "building_context": building_context,
            "image": None,
        }

        state = await self._retrieval.run(state)
        state = await self._interaction.run(state)

        return ChatResponse(
            session_id=session_id,
            message=state.get("chat_response", ""),
            follow_up_questions=state.get("follow_up_questions", []),
            sources=state.get("sources", []),
            language=language,
        )

    async def run_advanced_features(
        self,
        building_name: str,
        dynasty: str,
        architecture_style: str,
        structural_features: list[str] | None = None,
        language: str = "en",
        user_message: str = "Why is this building culturally important?",
    ) -> dict[str, Any]:
        state: AgentState = {
            "building_name": building_name,
            "dynasty": dynasty,
            "architecture_style": architecture_style,
            "structural_features": structural_features or [],
            "language": language,
            "user_message": user_message,
        }
        final_state = await self._run_advanced_layer(state)
        return {
            "time_reconstruction": final_state.get("time_reconstruction", {}),
            "historical_character": final_state.get("historical_character", {}),
            "cultural_dna": final_state.get("cultural_dna", {}),
            "cross_civilization": final_state.get("cross_civilization", {}),
            "cinematic_story": final_state.get("cinematic_story", {}),
            "summary": final_state.get("advanced_feature_summary", ""),
        }

    async def run_historical_character_chat(
        self,
        building_name: str,
        dynasty: str,
        character_type: str,
        message: str,
        language: str = "en",
    ) -> dict[str, Any]:
        return await self._advanced_service.historical_character_reply(
            building_name=building_name,
            dynasty=dynasty,
            character_type=character_type,
            message=message,
            language=language,
        )

    async def chat_stream(
        self,
        session_id: str,
        message: str,
        language: str = "en",
        building_context: str | None = None,
    ) -> AsyncIterator[str]:
        """Stream chat response tokens."""
        async for chunk in self._interaction.stream(
            session_id=session_id,
            user_message=message,
            language=language,
            building_context=building_context,
        ):
            yield chunk

    # ── Private helpers ─────────────────────────────────────────

    async def _run_sequential_analysis(self, state: AgentState) -> AgentState:
        """Fallback sequential pipeline when LangGraph is unavailable."""
        state = await self._recognition.run(state)
        if state.get("error"):
            return state
        state = await self._retrieval.run(state)
        state = await self._run_advanced_layer(state)
        state = await self._explanation.run(state)
        return state

    async def _run_advanced_layer(self, state: AgentState) -> AgentState:
        """Run advanced feature agents concurrently and merge outputs."""
        jobs = [
            self._time_reconstruction.run({**state}),
            self._historical_character.run({**state}),
            self._cultural_dna.run({**state}),
            self._comparison.run({**state}),
            self._cinematic.run({**state}),
        ]
        results: list[Any] = await asyncio.gather(*jobs, return_exceptions=True)

        merged: AgentState = {**state}
        for item in results:
            if isinstance(item, Exception):
                logger.warning(f"Advanced layer agent failed: {item}")
                continue
            if not isinstance(item, dict):
                continue
            for key in (
                "time_reconstruction",
                "historical_character",
                "cultural_dna",
                "cross_civilization",
                "cinematic_story",
            ):
                if key in item:
                    value = item.get(key)
                    if isinstance(value, dict):
                        merged[key] = value

        building_name = state.get("building_name", "Unknown Building")
        dynasty = state.get("dynasty", "Unknown")
        language = state.get("language", "en")

        if not merged.get("time_reconstruction"):
            merged["time_reconstruction"] = {
                "building_name": building_name,
                "current_dynasty": dynasty,
                "snapshots": [],
                "grounding_sources": [],
                "degraded": True,
            }

        if not merged.get("historical_character"):
            merged["historical_character"] = {
                "character": "architect",
                "persona_name": "Chief Imperial Architect",
                "reply": (
                    f"As Chief Imperial Architect of the {dynasty} period, I can provide a brief interpretation of {building_name}. "
                    "Detailed retrieval is temporarily unavailable; please try again shortly for richer context."
                    if language == "en"
                    else f"以{dynasty}时期总建筑师的身份，我可以先对{building_name}做简要解读。当前详细检索暂不可用，请稍后再试。"
                ),
                "grounding_sources": [],
                "degraded": True,
            }

        if not merged.get("cultural_dna"):
            merged["cultural_dna"] = {
                "building_name": building_name,
                "scores": {
                    "confucian_influence": 0,
                    "taoist_symbolism": 0,
                    "buddhist_influence": 0,
                    "imperial_authority": 0,
                    "regional_influence": 0,
                    "symbolism_density": 0,
                },
                "analysis": (
                    "Cultural DNA analysis is temporarily unavailable; baseline values are shown."
                    if language == "en"
                    else "文化DNA分析暂不可用，当前显示基线数值。"
                ),
                "grounding_sources": [],
                "degraded": True,
            }

        if not merged.get("cross_civilization"):
            merged["cross_civilization"] = {
                "building_name": building_name,
                "comparisons": [],
                "narrative": (
                    "Cross-civilization comparison is temporarily unavailable."
                    if language == "en"
                    else "跨文明比较暂不可用。"
                ),
                "grounding_sources": [],
                "degraded": True,
            }

        if not merged.get("cinematic_story"):
            merged["cinematic_story"] = {
                "building_name": building_name,
                "script": (
                    "Cinematic story generation is temporarily unavailable."
                    if language == "en"
                    else "影视叙事生成功能暂不可用。"
                ),
                "scene_plan": [],
                "audio": {
                    "provider": "unavailable",
                    "status": "degraded",
                    "audio_url": "",
                },
                "grounding_sources": [],
                "degraded": True,
            }

        merged["advanced_feature_summary"] = (
            f"Advanced analysis includes timeline reconstruction, persona dialogue, cultural DNA, "
            f"cross-civilization comparison, and cinematic narrative for {state.get('building_name', 'this building')}."
        )
        merged["step"] = "advanced_features_complete"
        return merged

    @staticmethod
    def _build_recognition_result(state: AgentState, result_id: str) -> "RecognitionResult":
        from api.routes.recognition import RecognitionResult
        return RecognitionResult(
            result_id=result_id,
            building_name=state.get("building_name", "Unknown Building"),
            building_name_zh=state.get("building_name_zh", "未知建筑"),
            architecture_style=state.get("architecture_style", ""),
            dynasty=state.get("dynasty", ""),
            dynasty_zh=state.get("dynasty_zh", ""),
            confidence_score=state.get("confidence_score", 0.0),
            structural_features=state.get("structural_features", []),
            location=None,
            coordinates=None,
            description=state.get("explanation", ""),
            description_zh=state.get("explanation_zh", ""),
            cultural_significance=state.get("cultural_significance", ""),
            image_url=None,
        )
