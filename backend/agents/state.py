"""
Shared state types for all agents.
"""
from __future__ import annotations

from typing import Optional, TypedDict

from PIL.Image import Image


class AgentState(TypedDict, total=False):
    # Input
    image: Optional[Image]
    user_message: str
    session_id: str
    result_id: str
    language: str
    detail_level: str
    building_context: Optional[str]

    # Recognition output
    building_name: str
    building_name_zh: str
    architecture_style: str
    dynasty: str
    dynasty_zh: str
    confidence_score: float
    structural_features: list[str]
    top_k: list[dict]

    # Retrieval output
    retrieved_chunks: list[dict]
    graph_context: list[dict]
    formatted_context: str

    # Explanation output
    explanation: str
    explanation_zh: str
    cultural_significance: str
    follow_up_questions: list[str]

    # Chat output
    chat_response: str
    sources: list[dict]

    # Advanced feature layer output
    time_reconstruction: dict
    historical_character: dict
    cultural_dna: dict
    cross_civilization: dict
    cinematic_story: dict
    advanced_feature_summary: str

    # Control
    error: Optional[str]
    step: str
