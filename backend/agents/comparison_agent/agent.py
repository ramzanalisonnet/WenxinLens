from __future__ import annotations

from agents.state import AgentState
from services.advanced_feature_service import AdvancedFeatureService


class ComparisonAgent:
    def __init__(self, feature_service: AdvancedFeatureService) -> None:
        self._features = feature_service

    async def run(self, state: AgentState) -> AgentState:
        building_name = state.get("building_name", "Unknown Building")
        style = state.get("architecture_style", "traditional chinese")
        language = state.get("language", "en")

        result = await self._features.cross_civilization_comparison(
            building_name=building_name,
            architecture_style=style,
            language=language,
        )
        return {**state, "cross_civilization": result}
