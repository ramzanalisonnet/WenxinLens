from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from loguru import logger
from pydantic import BaseModel, Field

from agents.orchestrator import OrchestratorAgent
router = APIRouter()


class AdvancedFeatureRequest(BaseModel):
    building_name: str = Field(min_length=1, max_length=200)
    dynasty: str = Field(default="Unknown", min_length=1, max_length=80)
    architecture_style: str = Field(default="traditional chinese", min_length=1, max_length=120)
    structural_features: list[str] = Field(default_factory=list)
    language: str = Field(default="en", pattern="^(en|zh)$")
    user_message: str = Field(
        default="Why is this building culturally important?",
        min_length=1,
        max_length=2000,
    )


class HistoricalCharacterRequest(BaseModel):
    building_name: str = Field(min_length=1, max_length=200)
    dynasty: str = Field(min_length=1, max_length=80)
    character_type: str = Field(default="architect", min_length=1, max_length=40)
    message: str = Field(min_length=1, max_length=2000)
    language: str = Field(default="en", pattern="^(en|zh)$")


def _get_orchestrator(request: Request) -> OrchestratorAgent:
    return OrchestratorAgent(
        vision_service=request.app.state.vision_service,
        retrieval_service=request.app.state.retrieval_service,
    )


@router.post("/all")
async def run_all_features(
    body: AdvancedFeatureRequest,
    request: Request,
) -> dict:
    orchestrator = _get_orchestrator(request)
    try:
        return await orchestrator.run_advanced_features(
            building_name=body.building_name,
            dynasty=body.dynasty,
            architecture_style=body.architecture_style,
            structural_features=body.structural_features,
            language=body.language,
            user_message=body.user_message,
        )
    except Exception as exc:
        logger.error(f"Advanced features failed: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Advanced feature pipeline error") from exc


@router.post("/historical-character")
async def historical_character_chat(
    body: HistoricalCharacterRequest,
    request: Request,
) -> dict:
    orchestrator = _get_orchestrator(request)
    try:
        result = await orchestrator.run_historical_character_chat(
            building_name=body.building_name,
            dynasty=body.dynasty,
            character_type=body.character_type,
            message=body.message,
            language=body.language,
        )
        return result
    except Exception as exc:
        logger.error(f"Historical character chat failed (serving fallback): {exc}", exc_info=True)
        persona_name = {
            "emperor": "Emperor",
            "architect": "Chief Imperial Architect",
            "worker": "Master Builder",
            "scholar": "Court Scholar",
        }.get(body.character_type.lower(), "Historical Witness")
        return {
            "character": body.character_type,
            "persona_name": persona_name,
            "reply": (
                f"As {persona_name} from the {body.dynasty} period, I can still provide a brief interpretation of {body.building_name}. "
                "The deep generation pipeline is temporarily unavailable. Please try again shortly for richer detail."
                if body.language == "en"
                else f"以{body.dynasty}时期的{persona_name}身份，我仍可为你简要解读{body.building_name}。当前深度生成链路暂不可用，请稍后再试获取更完整内容。"
            ),
            "grounding_sources": [],
            "degraded": True,
        }
