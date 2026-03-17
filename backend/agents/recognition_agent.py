"""
RecognitionAgent — processes images and identifies architecture.

Uses the VisionService (CLIP + YOLOv8) to produce a structured
recognition result, then enriches it with graph-level metadata.
"""
from __future__ import annotations

from loguru import logger

from agents.state import AgentState
from services.vision_service import VisionService


class RecognitionAgent:
    """Wraps VisionService with agent-compatible interface."""

    def __init__(self, vision_service: VisionService) -> None:
        self._vision = vision_service

    async def run(self, state: AgentState) -> AgentState:
        """
        Input:  state['image'], state['result_id']
        Output: Fills recognition fields in state.
        """
        image = state.get("image")
        if image is None:
            return {**state, "error": "No image provided", "step": "recognition_failed"}

        logger.info(f"RecognitionAgent: processing image [{state.get('result_id', '?')}]")

        try:
            prediction = await self._vision.predict(image)

            return {
                **state,
                "building_name": prediction.building_name,
                "building_name_zh": prediction.building_name_zh,
                "architecture_style": prediction.architecture_style,
                "dynasty": prediction.dynasty,
                "dynasty_zh": prediction.dynasty_zh,
                "confidence_score": prediction.confidence_score,
                "structural_features": prediction.structural_features,
                "top_k": prediction.top_k,
                "step": "recognition_complete",
            }
        except Exception as exc:
            logger.error(f"RecognitionAgent error: {exc}", exc_info=True)
            return {**state, "error": str(exc), "step": "recognition_failed"}
