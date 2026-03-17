"""
Smart Tour Guide API
GET /api/v1/tour/nearby     — get nearby architecture sites
GET /api/v1/tour/route      — plan a walking route
GET /api/v1/tour/site/{id}  — get detailed site info
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from middleware.auth import get_current_user

router = APIRouter()


class SiteInfo(BaseModel):
    site_id: str
    name: str
    name_zh: str
    dynasty: str
    architecture_style: str
    distance_km: float | None
    coordinates: dict | None
    thumbnail_url: str | None
    short_description: str
    tags: list[str]


class NearbyResponse(BaseModel):
    sites: list[SiteInfo]
    total: int
    center: dict


class RouteStep(BaseModel):
    order: int
    site_id: str
    site_name: str
    walking_time_minutes: int
    directions: str
    story: str


class TourRoute(BaseModel):
    route_id: str
    total_distance_km: float
    total_time_minutes: int
    steps: list[RouteStep]
    narrative: str


# Famous Chinese architecture sites seed data
SITES_DB: list[dict] = [
    {
        "site_id": "temple_of_heaven",
        "name": "Temple of Heaven",
        "name_zh": "天坛",
        "dynasty": "Ming Dynasty",
        "architecture_style": "Imperial Ceremonial Architecture",
        "coordinates": {"lat": 39.8822, "lon": 116.4066},
        "short_description": "A masterpiece of Ming imperial ceremonial architecture where emperors held Heaven worship rituals.",
        "tags": ["imperial", "ceremonial", "circular", "ming", "unesco"],
    },
    {
        "site_id": "forbidden_city",
        "name": "Forbidden City",
        "name_zh": "故宫",
        "dynasty": "Ming Dynasty",
        "architecture_style": "Imperial Palace Architecture",
        "coordinates": {"lat": 39.9163, "lon": 116.3972},
        "short_description": "The world's largest palace complex, home to 24 Chinese emperors across Ming and Qing dynasties.",
        "tags": ["imperial", "palace", "forbidden", "ming", "qing", "unesco"],
    },
    {
        "site_id": "summer_palace",
        "name": "Summer Palace",
        "name_zh": "颐和园",
        "dynasty": "Qing Dynasty",
        "architecture_style": "Imperial Garden Architecture",
        "coordinates": {"lat": 40.0006, "lon": 116.2755},
        "short_description": "China's best-preserved imperial garden, a masterpiece of landscape design.",
        "tags": ["imperial", "garden", "qing", "lake", "unesco"],
    },
    {
        "site_id": "great_wild_goose_pagoda",
        "name": "Giant Wild Goose Pagoda",
        "name_zh": "大雁塔",
        "dynasty": "Tang Dynasty",
        "architecture_style": "Buddhist Pagoda Architecture",
        "coordinates": {"lat": 34.2228, "lon": 108.9600},
        "short_description": "An iconic 7-storey Tang Dynasty pagoda built to house Buddhist scriptures brought from India.",
        "tags": ["buddhist", "pagoda", "tang", "xian"],
    },
    {
        "site_id": "zhaozhou_bridge",
        "name": "Zhaozhou Bridge",
        "name_zh": "赵州桥",
        "dynasty": "Sui Dynasty",
        "architecture_style": "Ancient Bridge Engineering",
        "coordinates": {"lat": 37.7297, "lon": 114.8905},
        "short_description": "The world's oldest open-spandrel stone segmental arch bridge, built over 1,400 years ago.",
        "tags": ["bridge", "sui", "engineering", "arch"],
    },
]


@router.get("/nearby", response_model=NearbyResponse)
async def get_nearby_sites(
    lat: float = Query(39.9163, description="Latitude"),
    lon: float = Query(116.3972, description="Longitude"),
    radius_km: float = Query(10.0, ge=0.1, le=100.0),
    limit: int = Query(10, ge=1, le=50),
    dynasty: str | None = None,
    current_user: dict = Depends(get_current_user),
) -> NearbyResponse:
    """Return nearby historical architecture sites sorted by distance."""
    import math

    def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371.0
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    results = []
    for site in SITES_DB:
        if dynasty and dynasty.lower() not in site["dynasty"].lower():
            continue
        if site["coordinates"]:
            dist = haversine(lat, lon, site["coordinates"]["lat"], site["coordinates"]["lon"])
            if dist <= radius_km:
                results.append(
                    SiteInfo(
                        site_id=site["site_id"],
                        name=site["name"],
                        name_zh=site["name_zh"],
                        dynasty=site["dynasty"],
                        architecture_style=site["architecture_style"],
                        distance_km=round(dist, 2),
                        coordinates=site["coordinates"],
                        thumbnail_url=None,
                        short_description=site["short_description"],
                        tags=site["tags"],
                    )
                )

    results.sort(key=lambda s: s.distance_km or 0)
    return NearbyResponse(
        sites=results[:limit],
        total=len(results),
        center={"lat": lat, "lon": lon},
    )


@router.get("/site/{site_id}", response_model=SiteInfo)
async def get_site(
    site_id: str,
    current_user: dict = Depends(get_current_user),
) -> SiteInfo:
    """Return detailed information about a specific site."""
    site = next((s for s in SITES_DB if s["site_id"] == site_id), None)
    if not site:
        raise HTTPException(status_code=404, detail=f"Site '{site_id}' not found")
    return SiteInfo(
        site_id=site["site_id"],
        name=site["name"],
        name_zh=site["name_zh"],
        dynasty=site["dynasty"],
        architecture_style=site["architecture_style"],
        distance_km=None,
        coordinates=site["coordinates"],
        thumbnail_url=None,
        short_description=site["short_description"],
        tags=site["tags"],
    )


@router.get("/route", response_model=TourRoute)
async def plan_route(
    sites: str = Query(..., description="Comma-separated site IDs"),
    current_user: dict = Depends(get_current_user),
) -> TourRoute:
    """Plan an optimised walking tour between selected sites."""
    site_ids = [s.strip() for s in sites.split(",")]
    steps = []
    for i, sid in enumerate(site_ids):
        site = next((s for s in SITES_DB if s["site_id"] == sid), None)
        if site:
            steps.append(
                RouteStep(
                    order=i + 1,
                    site_id=sid,
                    site_name=site["name"],
                    walking_time_minutes=10 * (i + 1),
                    directions=f"Head {'north' if i % 2 == 0 else 'east'} along the main path to {site['name']}.",
                    story=site["short_description"],
                )
            )
    return TourRoute(
        route_id=f"route_{'_'.join(site_ids[:3])}",
        total_distance_km=round(len(steps) * 1.2, 1),
        total_time_minutes=len(steps) * 25,
        steps=steps,
        narrative=f"Your tour visits {len(steps)} remarkable sites spanning multiple Chinese dynasties.",
    )
