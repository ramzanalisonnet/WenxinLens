"""
InteractionAgent — handles multi-turn conversation with context memory.

Features:
  - Maintains conversation history via ChatService (Redis)
  - Injects building context and retrieved knowledge into each turn
  - Generates contextual, educational responses
  - Supports streaming
"""
from __future__ import annotations

from typing import AsyncIterator

from loguru import logger

from agents.state import AgentState
from services.chat_service import ChatService
from services.llm_service import LLMService
from services.retrieval_service import RetrievalService


class InteractionAgent:
    """Stateful conversational agent for the cultural guide feature."""

    def __init__(self, retrieval_service: RetrievalService) -> None:
        self._retrieval = retrieval_service
        self._llm = LLMService()
        self._chat_service = ChatService()

    async def run(self, state: AgentState) -> AgentState:
        """
        Input:  state['user_message'], state['session_id'], state['building_context']
        Output: state['chat_response'], state['follow_up_questions']
        """
        session_id = state.get("session_id", "default")
        user_message = state.get("user_message", "")
        language = state.get("language", "en")
        building_context = state.get("building_context")
        context = state.get("formatted_context", "")

        if not user_message:
            return {**state, "chat_response": "", "step": "interaction_skipped"}

        # Get conversation history
        history = await self._chat_service.get_history(session_id)

        # Store user message
        await self._chat_service.add_message(session_id, "user", user_message)

        # If we have a building context result_id, retrieve it
        if building_context and not context:
            results = await self._retrieval.search(
                query=user_message,
                building_name=building_context,
            )
            context = self._retrieval.format_context(results)

        # Build messages with history
        messages = self._build_messages(history, user_message, context, language)

        logger.info(f"InteractionAgent: [{session_id}] '{user_message[:50]}…'")

        try:
            response = await self._llm.generate(
                user_message=user_message,
                context=context,
                language=language,
                temperature=0.8,
                history=history,
            )

            # Store assistant response
            await self._chat_service.add_message(session_id, "assistant", response)

            # Generate follow-ups
            follow_ups = self._generate_suggestions(user_message, language)

            return {
                **state,
                "chat_response": response,
                "sources": [{"text": r.get("text", "")[:100], "source": r.get("source", "")}
                            for r in (state.get("retrieved_chunks") or [])[:3]],
                "follow_up_questions": follow_ups,
                "step": "interaction_complete",
            }
        except Exception as exc:
            logger.error(f"InteractionAgent error: {exc}", exc_info=True)
            fallback = ("I'm sorry, I encountered an issue. Please ask your question again."
                        if language == "en"
                        else "抱歉，我遇到了问题。请再次提问。")
            return {**state, "chat_response": fallback, "step": "interaction_failed"}

    async def stream(
        self,
        session_id: str,
        user_message: str,
        language: str = "en",
        building_context: str | None = None,
    ) -> AsyncIterator[str]:
        """Stream a response token by token."""
        history = await self._chat_service.get_history(session_id)
        await self._chat_service.add_message(session_id, "user", user_message)

        context = ""
        if building_context:
            results = await self._retrieval.search(query=user_message, building_name=building_context)
            context = self._retrieval.format_context(results)

        messages = self._build_messages(history, user_message, context, language)
        full_response = []

        async for chunk in self._llm.stream(messages, language=language):
            full_response.append(chunk)
            yield chunk

        await self._chat_service.add_message(session_id, "assistant", "".join(full_response))

    def _build_messages(
        self,
        history: list[dict],
        user_message: str,
        context: str,
        language: str,
    ) -> list[dict]:
        from services.llm_service import SYSTEM_PROMPT_EN, SYSTEM_PROMPT_ZH
        system = SYSTEM_PROMPT_ZH if language == "zh" else SYSTEM_PROMPT_EN
        messages = [{"role": "system", "content": system}]
        if context:
            messages.append({"role": "user", "content": f"Background knowledge:\n\n{context}"})
            messages.append({"role": "assistant", "content": "I have reviewed this cultural context."})
        messages.extend(history[-8:])  # Last 4 turns
        messages.append({"role": "user", "content": user_message})
        return messages

    @staticmethod
    def _generate_suggestions(user_message: str, language: str) -> list[str]:
        suggestions_en = [
            "What materials were used to build this?",
            "Are there similar buildings elsewhere in China?",
            "What rituals or ceremonies took place here?",
        ]
        suggestions_zh = [
            "这座建筑用了什么材料建造？",
            "中国其他地方有类似的建筑吗？",
            "这里曾举行过哪些仪式或典礼？",
        ]
        return suggestions_zh if language == "zh" else suggestions_en
