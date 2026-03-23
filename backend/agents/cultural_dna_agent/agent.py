from __future__ import annotations

from agents.state import AgentState
from services.advanced_feature_service import AdvancedFeatureService


class CulturalDNAAgent:
    def __init__(self, feature_service: AdvancedFeatureService) -> None:
        self._features = feature_service

    async def run(self, state: AgentState) -> AgentState:
        building_name = state.get("building_name", "Unknown Building")
        style = state.get("architecture_style", "traditional chinese")
        features = state.get("structural_features", [])
        language = state.get("language", "en")

        result = await self._features.cultural_dna_profile(
            building_name=building_name,
            architecture_style=style,
            structural_features=features,
            language=language,
        )
        return {**state, "cultural_dna": result}
