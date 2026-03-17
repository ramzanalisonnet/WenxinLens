"""
RetrievalAgent — retrieves cultural knowledge using RAG + knowledge graph.

Takes the identified building name and user query, searches the
vector store for relevant chunks, and enriches with graph triples.
"""
from __future__ import annotations

from loguru import logger

from agents.state import AgentState
from services.retrieval_service import RetrievalService


class RetrievalAgent:
    """RAG-based knowledge retrieval agent."""

    def __init__(self, retrieval_service: RetrievalService) -> None:
        self._retrieval = retrieval_service

    async def run(self, state: AgentState) -> AgentState:
        """
        Input:  state['building_name'], state['user_message'] (optional)
        Output: state['retrieved_chunks'], state['formatted_context']
        """
        building_name = state.get("building_name", "")
        user_message = state.get("user_message", "")
        language = state.get("language", "en")

        query = user_message if user_message else f"cultural history architecture {building_name}"

        logger.info(f"RetrievalAgent: searching for '{building_name}' — query: {query[:60]}…")

        try:
            results = await self._retrieval.search(
                query=query,
                building_name=building_name if building_name else None,
                filters={"language": language} if language else {},
            )
            context = self._retrieval.format_context(results)

            return {
                **state,
                "retrieved_chunks": results,
                "formatted_context": context,
                "step": "retrieval_complete",
            }
        except Exception as exc:
            logger.warning(f"RetrievalAgent error (continuing without context): {exc}")
            return {
                **state,
                "retrieved_chunks": [],
                "formatted_context": "",
                "step": "retrieval_complete",
            }
