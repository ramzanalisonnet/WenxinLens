"""
Knowledge Graph Query API
GET /api/v1/knowledge/building/{name}    — fetch knowledge graph data for a building
GET /api/v1/knowledge/search             — full-text search
GET /api/v1/knowledge/dynasty/{dynasty}  — list buildings by dynasty
GET /api/v1/knowledge/graph/relations    — graph relations for visualization
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

from knowledge_graph.dynasty_catalog import (
    get_dynasty_catalog as load_dynasty_catalog,
    get_places_by_dynasty,
)
from middleware.auth import get_current_user

router = APIRouter()


def _prefer_timeline_jpg(catalog: list[dict]) -> list[dict]:
    """Normalize timeline image URLs to JPG assets when legacy SVG links are returned."""
    for dynasty in catalog:
        places = dynasty.get("places", [])
        if not isinstance(places, list):
            continue
        for place in places:
            if not isinstance(place, dict):
                continue
            image_url = place.get("image_url")
            if isinstance(image_url, str) and image_url.startswith("/images/timeline-") and image_url.endswith(".svg"):
                place["image_url"] = image_url[:-4] + ".jpg"
    return catalog


class BuildingKnowledge(BaseModel):
    building_id: str
    name: str
    name_zh: str
    dynasty: str
    architect: str | None
    location: str
    year_built: str | None
    architectural_style: str
    materials: list[str]
    symbolism: list[str]
    historical_events: list[str]
    related_buildings: list[str]
    description: str
    description_zh: str


class GraphRelation(BaseModel):
    source: str
    target: str
    relation: str


class GraphResponse(BaseModel):
    nodes: list[dict]
    edges: list[GraphRelation]


@router.get("/building/{building_name}", response_model=BuildingKnowledge)
async def get_building_knowledge(
    request: Request,
    building_name: str,
    language: str = "en",
    current_user: dict = Depends(get_current_user),
) -> BuildingKnowledge:
    """Fetch comprehensive cultural knowledge for a building from the graph database."""
    neo4j = request.app.state.neo4j
    result = await neo4j.get_building(building_name)
    if not result:
        raise HTTPException(status_code=404, detail=f"Building '{building_name}' not found in knowledge base")
    return result


@router.get("/search", response_model=list[dict])
async def search_knowledge(
    request: Request,
    q: str = Query(..., min_length=2, max_length=200, description="Search query"),
    language: str = "en",
    dynasty: str | None = None,
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
) -> list[dict]:
    """Semantic search across the knowledge base."""
    retrieval = request.app.state.retrieval_service
    results = await retrieval.search(query=q, filters={"dynasty": dynasty} if dynasty else {}, top_k=limit)
    return results


@router.get("/dynasty/{dynasty}", response_model=list[dict])
async def get_dynasty_buildings(
    request: Request,
    dynasty: str,
    current_user: dict = Depends(get_current_user),
) -> list[dict]:
    """List all buildings from a specific dynasty."""
    neo4j = getattr(request.app.state, "neo4j", None)
    if neo4j is None:
        return get_places_by_dynasty(dynasty)
    buildings = await neo4j.get_buildings_by_dynasty(dynasty)
    return buildings


@router.get("/graph/relations", response_model=GraphResponse)
async def get_graph_relations(
    request: Request,
    building_name: str = Query(...),
    depth: int = Query(2, ge=1, le=3),
    current_user: dict = Depends(get_current_user),
) -> GraphResponse:
    """
    Return a subgraph centered on a building for interactive visualization.
    Traverses up to `depth` hops in Neo4j.
    """
    neo4j = request.app.state.neo4j
    graph = await neo4j.get_subgraph(building_name, depth=depth)
    return graph


@router.get("/dynasties", summary="List all dynasties in the knowledge base")
async def list_dynasties(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> list[dict]:
    dynasties = [
        {"id": "shang", "name": "Shang Dynasty", "name_zh": "商朝", "period": "1600–1046 BCE"},
        {"id": "zhou", "name": "Zhou Dynasty", "name_zh": "周朝", "period": "1046–256 BCE"},
        {"id": "qin", "name": "Qin Dynasty", "name_zh": "秦朝", "period": "221–206 BCE"},
        {"id": "han", "name": "Han Dynasty", "name_zh": "汉朝", "period": "206 BCE – 220 CE"},
        {"id": "tang", "name": "Tang Dynasty", "name_zh": "唐朝", "period": "618–907 CE"},
        {"id": "song", "name": "Song Dynasty", "name_zh": "宋朝", "period": "960–1279 CE"},
        {"id": "yuan", "name": "Yuan Dynasty", "name_zh": "元朝", "period": "1271–1368 CE"},
        {"id": "ming", "name": "Ming Dynasty", "name_zh": "明朝", "period": "1368–1644 CE"},
        {"id": "qing", "name": "Qing Dynasty", "name_zh": "清朝", "period": "1644–1912 CE"},
    ]
    return dynasties


@router.get("/dynasty-catalog", summary="Dynasty architecture catalog with places")
async def get_dynasty_catalog(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> list[dict]:
    neo4j = getattr(request.app.state, "neo4j", None)
    if neo4j is None:
        return _prefer_timeline_jpg(load_dynasty_catalog())
    return _prefer_timeline_jpg(await neo4j.get_dynasty_catalog())
