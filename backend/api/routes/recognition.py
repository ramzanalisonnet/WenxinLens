"""
Architecture Recognition API
POST /api/v1/recognition/analyze  — upload image, get recognition result
GET  /api/v1/recognition/{id}     — retrieve previous result from cache
"""
from __future__ import annotations

import hashlib
import io
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from loguru import logger
from PIL import Image
from pydantic import BaseModel, Field

from config import get_settings
from middleware.auth import get_current_user
from middleware.rate_limiter import limiter
from services.vision_service import VisionService
from agents.orchestrator import OrchestratorAgent

settings = get_settings()
router = APIRouter()


# ─── Schemas ──────────────────────────────────────────────────

class RecognitionResult(BaseModel):
    result_id: str
    building_name: str
    building_name_zh: str
    architecture_style: str
    dynasty: str
    dynasty_zh: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    structural_features: list[str]
    location: str | None
    coordinates: dict | None
    description: str
    description_zh: str
    cultural_significance: str
    image_url: str | None


# ─── Helpers ──────────────────────────────────────────────────

def _validate_image(file: UploadFile) -> None:
    allowed_types = {"image/jpeg", "image/png", "image/webp", "image/heic"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported image type: {file.content_type}. Allowed: JPEG, PNG, WebP, HEIC",
        )
    if file.size and file.size > settings.max_image_size_mb * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image too large. Maximum size: {settings.max_image_size_mb} MB",
        )


# ─── Routes ───────────────────────────────────────────────────

@router.post("/analyze", response_model=RecognitionResult)
@limiter.limit("10/minute")
async def analyze_image(
    request: Request,
    image: Annotated[UploadFile, File(description="Architecture image (JPEG/PNG/WebP)")],
    language: str = "en",
    detail_level: str = "standard",
    current_user: dict = Depends(get_current_user),
) -> RecognitionResult:
    """
    Analyze an uploaded architecture image.

    Returns building identification, dynasty, architectural style,
    confidence scores, and a rich cultural description.
    """
    _validate_image(image)

    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty image file")

    # Compute deterministic result_id from image content
    result_id = hashlib.sha256(image_bytes).hexdigest()[:16]

    try:
        pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not decode image: {exc}") from exc

    try:
        vision_service: VisionService = request.app.state.vision_service
        orchestrator = OrchestratorAgent(
            vision_service=vision_service,
            retrieval_service=request.app.state.retrieval_service,
        )

        result = await orchestrator.analyze(
            image=pil_image,
            result_id=result_id,
            language=language,
            detail_level=detail_level,
        )
        logger.info(
            f"Recognition [{result_id}]: {result.building_name} "
            f"confidence={result.confidence_score:.2f}"
        )
        return result
    except Exception as exc:
        logger.error(f"Recognition failed [{result_id}]: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Recognition pipeline error") from exc


@router.get("/styles", summary="List supported architectural styles")
async def list_styles() -> dict:
    """Return the catalogue of recognisable architectural styles."""
    return {
        "styles": [
            {"id": "imperial_palace", "name": "Imperial Palace Architecture", "name_zh": "皇家宫殿建筑",
             "examples": ["Forbidden City", "Summer Palace"]},
            {"id": "temple", "name": "Temple Architecture", "name_zh": "寺庙建筑",
             "examples": ["Temple of Heaven", "Shaolin Temple"]},
            {"id": "pagoda", "name": "Pagoda Architecture", "name_zh": "塔楼建筑",
             "examples": ["Giant Wild Goose Pagoda", "Lingxiao Pagoda"]},
            {"id": "garden", "name": "Classical Garden", "name_zh": "古典园林",
             "examples": ["Humble Administrator's Garden", "Lingering Garden"]},
            {"id": "folk_dwelling", "name": "Folk Dwelling", "name_zh": "民居建筑",
             "examples": ["Hakka Tulou", "Siheyuan Courtyard"]},
            {"id": "city_gate", "name": "City Gate & Fortress", "name_zh": "城门城楼",
             "examples": ["Nanjing City Wall", "Xi'an City Wall"]},
            {"id": "bridge", "name": "Ancient Bridge", "name_zh": "古桥建筑",
             "examples": ["Zhaozhou Bridge", "Lugou Bridge"]},
            {"id": "pavilion", "name": "Pavilion & Tower", "name_zh": "亭台楼阁",
             "examples": ["Yellow Crane Tower", "Tengwang Pavilion"]},
        ]
    }
