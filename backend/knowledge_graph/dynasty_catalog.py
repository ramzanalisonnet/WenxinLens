from __future__ import annotations

from typing import Any


DYNASTY_CATALOG: list[dict[str, Any]] = [
    {
        "dynasty": "Tang Dynasty",
        "dynasty_zh": "唐朝",
        "period": "618-907 CE",
        "places": [
            {
                "id": "tang_giant_wild_goose_pagoda",
                "name": "Giant Wild Goose Pagoda",
                "name_zh": "大雁塔",
                "location": "Xi'an, Shaanxi",
                "coordinates": {"lat": 34.2186, "lon": 108.9642},
                "architecture_type": "Buddhist Pagoda",
                "year_built": "652",
                "image_url": "/images/timeline-tang.jpg",
                "description": "A Tang-era brick pagoda built to preserve Buddhist scriptures brought from India.",
                "details": [
                    "Seven-story square plan",
                    "Early mature Tang masonry system",
                    "Major center of scripture translation",
                ],
            },
            {
                "id": "tang_daming_palace",
                "name": "Daming Palace Ruins",
                "name_zh": "大明宫遗址",
                "location": "Xi'an, Shaanxi",
                "coordinates": {"lat": 34.2936, "lon": 108.9803},
                "architecture_type": "Imperial Palace Complex",
                "year_built": "634",
                "image_url": "/images/timeline-tang.jpg",
                "description": "The political heart of Tang imperial rule and a benchmark for East Asian palace planning.",
                "details": [
                    "Grand axial composition",
                    "Monumental ceremonial halls",
                    "Influenced regional capital design",
                ],
            },
        ],
    },
    {
        "dynasty": "Song Dynasty",
        "dynasty_zh": "宋朝",
        "period": "960-1279 CE",
        "places": [
            {
                "id": "song_yingxian_wooden_pagoda",
                "name": "Fogong Temple Wooden Pagoda",
                "name_zh": "应县木塔",
                "location": "Ying County, Shanxi",
                "coordinates": {"lat": 39.5651, "lon": 113.1903},
                "architecture_type": "Timber Pagoda",
                "year_built": "1056",
                "image_url": "/images/timeline-song.jpg",
                "description": "The tallest surviving ancient wooden pagoda, showcasing advanced Song timber engineering.",
                "details": [
                    "Pure timber frame system",
                    "Complex dougong bracket layers",
                    "Excellent seismic resilience",
                ],
            },
            {
                "id": "song_liuhe_pagoda",
                "name": "Liuhe Pagoda",
                "name_zh": "六和塔",
                "location": "Hangzhou, Zhejiang",
                "coordinates": {"lat": 30.2083, "lon": 120.1482},
                "architecture_type": "Pagoda and Flood-control Landmark",
                "year_built": "970",
                "image_url": "/images/timeline-song.jpg",
                "description": "A pagoda overlooking the Qiantang River, blending practical signaling use and Buddhist symbolism.",
                "details": [
                    "Brick-wood hybrid structure",
                    "River defense visual marker",
                    "Song aesthetic proportioning",
                ],
            },
        ],
    },
    {
        "dynasty": "Yuan Dynasty",
        "dynasty_zh": "元朝",
        "period": "1271-1368 CE",
        "places": [
            {
                "id": "yuan_white_stupa",
                "name": "White Stupa of Miaoying Temple",
                "name_zh": "妙应寺白塔",
                "location": "Beijing",
                "coordinates": {"lat": 39.9271, "lon": 116.3738},
                "architecture_type": "Lamaist Stupa",
                "year_built": "1271",
                "image_url": "/images/timeline-yuan.jpg",
                "description": "A landmark Yuan monument reflecting Tibetan Buddhist architectural influence in Dadu.",
                "details": [
                    "Nepal-Tibetan stylistic fusion",
                    "Urban skyline religious marker",
                    "Cross-cultural imperial patronage",
                ],
            },
            {
                "id": "yuan_beijing_drum_tower",
                "name": "Beijing Drum Tower",
                "name_zh": "北京鼓楼",
                "location": "Beijing",
                "coordinates": {"lat": 39.9424, "lon": 116.3939},
                "architecture_type": "Timekeeping Civic Tower",
                "year_built": "1272",
                "image_url": "/images/timeline-yuan.jpg",
                "description": "Originally built in Yuan Dadu, used with the Bell Tower to regulate urban time and order.",
                "details": [
                    "High timber platform form",
                    "Civic governance function",
                    "Integral to capital planning",
                ],
            },
        ],
    },
    {
        "dynasty": "Ming Dynasty",
        "dynasty_zh": "明朝",
        "period": "1368-1644 CE",
        "places": [
            {
                "id": "ming_forbidden_city",
                "name": "Forbidden City",
                "name_zh": "故宫",
                "location": "Beijing",
                "coordinates": {"lat": 39.9163, "lon": 116.3972},
                "architecture_type": "Imperial Palace Architecture",
                "year_built": "1406",
                "image_url": "/images/timeline-ming.jpg",
                "description": "The largest surviving palace complex in China, representing mature Ming imperial planning.",
                "details": [
                    "Strict axial symmetry",
                    "High-standard timber halls",
                    "Ritual hierarchy in courtyards",
                ],
            },
            {
                "id": "ming_temple_of_heaven",
                "name": "Temple of Heaven",
                "name_zh": "天坛",
                "location": "Beijing",
                "coordinates": {"lat": 39.8822, "lon": 116.4065},
                "architecture_type": "Imperial Ritual Complex",
                "year_built": "1420",
                "image_url": "/images/timeline-ming.jpg",
                "description": "Ceremonial architecture for imperial Heaven worship with symbolic geometric planning.",
                "details": [
                    "Circular-square cosmology symbolism",
                    "Acoustic and ritual landscape design",
                    "Blue glazed tile iconography",
                ],
            },
        ],
    },
    {
        "dynasty": "Qing Dynasty",
        "dynasty_zh": "清朝",
        "period": "1644-1912 CE",
        "places": [
            {
                "id": "qing_summer_palace",
                "name": "Summer Palace",
                "name_zh": "颐和园",
                "location": "Beijing",
                "coordinates": {"lat": 39.9996, "lon": 116.2755},
                "architecture_type": "Imperial Garden Architecture",
                "year_built": "1750",
                "image_url": "/images/timeline-qing.jpg",
                "description": "An imperial garden integrating Kunming Lake and Longevity Hill into a large symbolic landscape.",
                "details": [
                    "Garden-city spatial composition",
                    "Long Corridor painted narratives",
                    "Landscape framing and borrowed views",
                ],
            },
            {
                "id": "qing_mukden_palace",
                "name": "Mukden Palace",
                "name_zh": "沈阳故宫",
                "location": "Shenyang, Liaoning",
                "coordinates": {"lat": 41.7958, "lon": 123.4455},
                "architecture_type": "Early Qing Palace Complex",
                "year_built": "1625",
                "image_url": "/images/timeline-qing.jpg",
                "description": "A key early Qing palace blending Manchu traditions with established Han palace typologies.",
                "details": [
                    "Multi-ethnic decorative language",
                    "Distinctive octagonal hall forms",
                    "Transition marker in Qing court architecture",
                ],
            },
        ],
    },
]


def get_dynasty_catalog() -> list[dict[str, Any]]:
    return DYNASTY_CATALOG


def get_places_by_dynasty(dynasty: str) -> list[dict[str, Any]]:
    needle = dynasty.strip().lower()
    for block in DYNASTY_CATALOG:
        value = str(block.get("dynasty", "")).lower()
        if needle in value or value in needle:
            return list(block.get("places", []))
    return []
