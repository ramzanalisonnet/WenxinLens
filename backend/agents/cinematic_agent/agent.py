from __future__ import annotations

from agents.state import AgentState
from services.advanced_feature_service import AdvancedFeatureService


class CinematicAgent:
    def __init__(self, feature_service: AdvancedFeatureService) -> None:
        self._features = feature_service

    async def run(self, state: AgentState) -> AgentState:
        building_name = state.get("building_name", "Unknown Building")
        dynasty = state.get("dynasty", "Unknown")
        language = state.get("language", "en")

        result = await self._features.cinematic_story(
            building_name=building_name,
            dynasty=dynasty,
            language=language,
        )
        return {**state, "cinematic_story": result}
