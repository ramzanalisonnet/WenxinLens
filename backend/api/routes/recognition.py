"""
Architecture Recognition API
POST /api/v1/recognition/analyze  — upload image, get recognition result
GET  /api/v1/recognition/{id}     — retrieve previous result from cache
"""

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


async def _get_or_init_vision_service(request: Request) -> VisionService:
    """Ensure a usable VisionService exists even when fast-startup skipped heavy init."""
    existing = getattr(request.app.state, "vision_service", None)
    if existing is not None:
        return existing

    # Lazily initialize once and cache in app state so recognition works in FAST_STARTUP mode.
    vision_service = VisionService()
    await vision_service.initialize()
    request.app.state.vision_service = vision_service
    return vision_service


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
    allowed_types = {"image/jpeg", "image/png", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported image media type. Allowed: JPEG, PNG, WebP.",
        )
    if file.size is not None and file.size > settings.max_image_size_mb * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image too large. Maximum size: {settings.max_image_size_mb} MB",
        )


# ─── Routes ───────────────────────────────────────────────────

@router.post("/analyze", response_model=RecognitionResult)
@limiter.limit("10/minute")
async def analyze_image(
    request: Request,
    image: UploadFile = File(description="Architecture image (JPEG/PNG/WebP)"),
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

    max_bytes = settings.max_image_size_mb * 1024 * 1024
    # Bound the read even when Content-Length is absent or UploadFile.size is unknown.
    image_bytes = await image.read(max_bytes + 1)
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty image file")
    if len(image_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image too large. Maximum size: {settings.max_image_size_mb} MB",
        )

    result_id = hashlib.sha256(image_bytes).hexdigest()[:16]
    try:
        with Image.open(io.BytesIO(image_bytes)) as probe:
            if probe.format not in {"JPEG", "PNG", "WEBP"}:
                raise HTTPException(status_code=415, detail="Image content must be JPEG, PNG, or WebP.")
            if probe.width < 64 or probe.height < 64:
                raise HTTPException(status_code=400, detail="Image dimensions must be at least 64 x 64 pixels.")
            if probe.width * probe.height > 25_000_000:
                raise HTTPException(status_code=413, detail="Image dimensions are too large.")
            probe.verify()
        with Image.open(io.BytesIO(image_bytes)) as decoded:
            decoded.load()
            pil_image = decoded.convert("RGB")
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning(f"Rejected invalid image upload: {type(exc).__name__}")
        raise HTTPException(status_code=400, detail="Could not decode the uploaded image.") from exc

    try:
        vision_service = await _get_or_init_vision_service(request)
        orchestrator = OrchestratorAgent(
            vision_service=vision_service,
            retrieval_service=request.app.state.retrieval_service,
        )

        result = await orchestrator.analyze(
            image=pil_image,
            result_id=result_id,
            language=language,
            detail_level=detail_level,
            include_advanced=False,
            fast_mode=True,
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
