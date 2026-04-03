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


def _normalize_timeline_image_url(image_url: str | None) -> str | None:
    if isinstance(image_url, str) and image_url.startswith("/images/timeline-") and image_url.endswith(".svg"):
        return image_url[:-4] + ".jpg"
    return image_url


def _prefer_timeline_jpg(catalog: list[dict]) -> list[dict]:
    """Normalize timeline image URLs to JPG assets when legacy SVG links are returned."""
    for dynasty in catalog:
        places = dynasty.get("places", [])
        if not isinstance(places, list):
            continue
        for place in places:
            if not isinstance(place, dict):
                continue
            place["image_url"] = _normalize_timeline_image_url(place.get("image_url"))
    return catalog


def _search_catalog_fallback(query: str, dynasty: str | None, limit: int) -> list[dict]:
    needle = query.strip().lower()
    if not needle:
        return []

    catalog = _prefer_timeline_jpg(load_dynasty_catalog())
    results: list[dict] = []

    for block in catalog:
        full_dynasty = str(block.get("dynasty", ""))
        short_dynasty = full_dynasty.replace(" Dynasty", "")

        if dynasty and dynasty.lower() != "all":
            d = dynasty.lower()
            if d not in full_dynasty.lower() and d not in short_dynasty.lower():
                continue

        for place in block.get("places", []):
            if not isinstance(place, dict):
                continue

            haystack = " ".join(
                str(place.get(k, ""))
                for k in ("name", "name_zh", "location", "architecture_type", "description", "year_built")
            ).lower()

            if needle not in haystack:
                continue

            results.append(
                {
                    "name": place.get("name", ""),
                    "name_en": place.get("name", ""),
                    "name_zh": place.get("name_zh", ""),
                    "dynasty": short_dynasty,
                    "style": place.get("architecture_type", ""),
                    "architecture_type": place.get("architecture_type", ""),
                    "location": place.get("location", ""),
                    "year_built": place.get("year_built", ""),
                    "image_url": _normalize_timeline_image_url(place.get("image_url")),
                    "description": place.get("description", ""),
                    "details": place.get("details", []),
                }
            )

            if len(results) >= limit:
                return results

    return results


def _find_catalog_place(building_name: str) -> tuple[dict | None, str]:
    needle = building_name.strip().lower()
    for block in _prefer_timeline_jpg(load_dynasty_catalog()):
        full_dynasty = str(block.get("dynasty", ""))
        short_dynasty = full_dynasty.replace(" Dynasty", "")
        for place in block.get("places", []):
            if not isinstance(place, dict):
                continue
            name = str(place.get("name", ""))
            name_zh = str(place.get("name_zh", ""))
            if needle in name.lower() or needle in name_zh.lower() or name.lower() in needle:
                return place, short_dynasty
    return None, ""


def _building_fallback_from_catalog(building_name: str) -> BuildingKnowledge | None:
    place, dynasty = _find_catalog_place(building_name)
    if not place:
        return None

    details = place.get("details", [])
    if not isinstance(details, list):
        details = []

    return BuildingKnowledge(
        building_id=str(place.get("id", place.get("name", "unknown"))).lower().replace(" ", "_"),
        name=str(place.get("name", building_name)),
        name_zh=str(place.get("name_zh", place.get("name", building_name))),
        dynasty=dynasty,
        architect=None,
        location=str(place.get("location", "")),
        year_built=str(place.get("year_built", "")) or None,
        architectural_style=str(place.get("architecture_type", "")),
        materials=[],
        symbolism=[],
        historical_events=[],
        related_buildings=[],
        description=str(place.get("description", "")),
        description_zh=str(place.get("description", "")),
    )


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
    neo4j = getattr(request.app.state, "neo4j", None)
    if neo4j is None:
        fallback = _building_fallback_from_catalog(building_name)
        if fallback:
            return fallback
        raise HTTPException(status_code=404, detail=f"Building '{building_name}' not found in knowledge base")

    try:
        result = await neo4j.get_building(building_name)
    except Exception:
        result = None

    if not result:
        fallback = _building_fallback_from_catalog(building_name)
        if fallback:
            return fallback
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
    retrieval = getattr(request.app.state, "retrieval_service", None)
    if retrieval is None:
        return _search_catalog_fallback(q, dynasty, limit)

    try:
        return await retrieval.search(query=q, filters={"dynasty": dynasty} if dynasty else {}, top_k=limit)
    except Exception:
        return _search_catalog_fallback(q, dynasty, limit)


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
    neo4j = getattr(request.app.state, "neo4j", None)
    if neo4j is None:
        return GraphResponse(nodes=[{"id": building_name, "label": "Building", "name": building_name}], edges=[])

    try:
        graph = await neo4j.get_subgraph(building_name, depth=depth)
    except Exception:
        graph = {"nodes": [], "edges": []}

    if not graph.get("nodes"):
        graph = {"nodes": [{"id": building_name, "label": "Building", "name": building_name}], "edges": []}

    return GraphResponse(nodes=graph.get("nodes", []), edges=graph.get("edges", []))


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
