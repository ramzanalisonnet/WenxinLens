from __future__ import annotations

from agents.state import AgentState
from services.advanced_feature_service import AdvancedFeatureService


class TimeReconstructionAgent:
    def __init__(self, feature_service: AdvancedFeatureService) -> None:
        self._features = feature_service

    async def run(self, state: AgentState) -> AgentState:
        building_name = state.get("building_name", "Unknown Building")
        dynasty = state.get("dynasty", "Unknown")
        features = state.get("structural_features", [])
        language = state.get("language", "en")

        result = await self._features.build_time_reconstruction(
            building_name=building_name,
            dynasty=dynasty,
            structural_features=features,
            language=language,
        )
        return {**state, "time_reconstruction": result}
