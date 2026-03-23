from __future__ import annotations

from agents.state import AgentState
from services.advanced_feature_service import AdvancedFeatureService


class HistoricalCharacterAgent:
    def __init__(self, feature_service: AdvancedFeatureService) -> None:
        self._features = feature_service

    async def run(self, state: AgentState) -> AgentState:
        building_name = state.get("building_name", "Unknown Building")
        dynasty = state.get("dynasty", "Unknown")
        language = state.get("language", "en")
        user_message = state.get("user_message", "Tell me why this building was built.")

        result = await self._features.historical_character_reply(
            building_name=building_name,
            dynasty=dynasty,
            character_type="architect",
            message=user_message,
            language=language,
        )
        return {**state, "historical_character": result}
