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
from services.vision_service import VisionService
from services.retrieval_service import RetrievalService


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
            workflow.add_node("explanation", self._explanation.run)

            # Edges
            workflow.set_entry_point("recognition")
            workflow.add_edge("recognition", "retrieval")
            workflow.add_edge("retrieval", "explanation")
            workflow.add_edge("explanation", END)

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
        state = await self._explanation.run(state)
        return state

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
