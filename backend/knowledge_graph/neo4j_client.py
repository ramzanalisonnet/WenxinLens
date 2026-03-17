"""
Neo4j Knowledge Graph Client

Graph schema:
  Nodes:
    (:Building {id, name, name_zh, location, year_built, description})
    (:Dynasty  {id, name, name_zh, period_start, period_end})
    (:Style    {id, name, name_zh})
    (:Material {id, name, origin})
    (:Symbolism{id, concept, description})
    (:Person   {id, name, role})     — architects, emperors, craftsmen
    (:Event    {id, name, year, description})
    (:Location {id, city, province, lat, lon})

  Relationships:
    (Building)-[:BUILT_IN]->(Dynasty)
    (Building)-[:HAS_STYLE]->(Style)
    (Building)-[:USES_MATERIAL]->(Material)
    (Building)-[:SYMBOLIZES]->(Symbolism)
    (Building)-[:BUILT_BY]->(Person)
    (Building)-[:LOCATED_IN]->(Location)
    (Building)-[:ASSOCIATED_WITH]->(Event)
    (Building)-[:INFLUENCED_BY]->(Building)
    (Building)-[:SIMILAR_TO]->(Building)
"""
from __future__ import annotations

import asyncio
from typing import Optional

from loguru import logger

from config import get_settings

settings = get_settings()


class Neo4jClient:
    """Async wrapper around the Neo4j Python driver."""

    def __init__(self) -> None:
        self._driver = None

    async def connect(self) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._connect_sync)

    def _connect_sync(self) -> None:
        try:
            from neo4j import GraphDatabase
            self._driver = GraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password),
            )
            self._driver.verify_connectivity()
            logger.info(f"Neo4j connected at {settings.neo4j_uri}")
            # Seed graph if empty
            with self._driver.session() as session:
                row = session.run("MATCH (n) RETURN count(n) AS c").single()  # type: ignore[arg-type]
                count = row["c"] if row else 0
                if count == 0:
                    logger.info("Neo4j is empty — seeding knowledge graph …")
                    self._seed_graph(session)
        except Exception as exc:
            logger.warning(f"Neo4j unavailable: {exc} — using mock data")
            self._driver = None

    def _seed_graph(self, session) -> None:
        """Create initial knowledge graph nodes and relationships."""
        cypher = """
        // Dynasties
        MERGE (:Dynasty {id: 'ming', name: 'Ming Dynasty', name_zh: '明朝', period: '1368–1644'})
        MERGE (:Dynasty {id: 'qing', name: 'Qing Dynasty', name_zh: '清朝', period: '1644–1912'})
        MERGE (:Dynasty {id: 'tang', name: 'Tang Dynasty', name_zh: '唐朝', period: '618–907'})
        MERGE (:Dynasty {id: 'sui',  name: 'Sui Dynasty',  name_zh: '隋朝', period: '581–618'})
        MERGE (:Dynasty {id: 'song', name: 'Song Dynasty', name_zh: '宋朝', period: '960–1279'})

        // Styles
        MERGE (:Style {id: 'imperial_ceremonial', name: 'Imperial Ceremonial Architecture', name_zh: '皇家祭祀建筑'})
        MERGE (:Style {id: 'imperial_palace',     name: 'Imperial Palace Architecture',        name_zh: '皇家宫殿建筑'})
        MERGE (:Style {id: 'buddhist_pagoda',     name: 'Buddhist Pagoda Architecture',         name_zh: '佛教塔楼建筑'})
        MERGE (:Style {id: 'imperial_garden',     name: 'Imperial Garden Architecture',          name_zh: '皇家园林建筑'})
        MERGE (:Style {id: 'folk_dwelling',       name: 'Folk Dwelling Architecture',              name_zh: '民居建筑'})

        // Buildings
        MERGE (toh:Building {id: 'temple_of_heaven',
            name: 'Temple of Heaven', name_zh: '天坛',
            location: 'Beijing', year_built: '1420',
            description: 'Imperial complex for Heaven worship rituals'})
        MERGE (fc:Building {id: 'forbidden_city',
            name: 'Forbidden City', name_zh: '故宫',
            location: 'Beijing', year_built: '1406',
            description: 'Imperial palace for 24 emperors'})
        MERGE (gwgp:Building {id: 'great_wild_goose_pagoda',
            name: 'Giant Wild Goose Pagoda', name_zh: '大雁塔',
            location: 'Xian', year_built: '652',
            description: 'Tang Dynasty Buddhist pagoda housing scriptures'})
        MERGE (sp:Building {id: 'summer_palace',
            name: 'Summer Palace', name_zh: '颐和园',
            location: 'Beijing', year_built: '1750',
            description: 'Imperial summer garden complex'})
        MERGE (zb:Building {id: 'zhaozhou_bridge',
            name: 'Zhaozhou Bridge', name_zh: '赵州桥',
            location: 'Hebei', year_built: '605',
            description: "World's oldest open-spandrel stone arch bridge"})

        // Persons
        MERGE (yongle:Person {id: 'yongle_emperor', name: 'Yongle Emperor', name_zh: '永乐帝', role: 'Emperor'})
        MERGE (li_chun:Person {id: 'li_chun', name: 'Li Chun', name_zh: '李春', role: 'Master Craftsman'})
        MERGE (xuanzang:Person {id: 'xuanzang', name: 'Xuanzang', name_zh: '玄奘', role: 'Buddhist Monk'})

        // Symbolisms
        MERGE (heaven:Symbolism {id: 'heaven_worship', concept: 'Heaven Worship', concept_zh: '天人合一'})
        MERGE (imperial:Symbolism {id: 'imperial_power', concept: 'Imperial Power', concept_zh: '皇权象征'})
        MERGE (buddhism:Symbolism {id: 'buddhism', concept: 'Buddhist Devotion', concept_zh: '佛教信仰'})
        MERGE (longevity:Symbolism {id: 'longevity', concept: 'Longevity and Harmony', concept_zh: '长寿和谐'})

        // ── Relationships ──────────────────────────────────────
        WITH toh, fc, gwgp, sp, zb, yongle, li_chun, xuanzang,
             heaven, imperial, buddhism, longevity

        MATCH (ming:Dynasty {id: 'ming'})
        MATCH (qing:Dynasty {id: 'qing'})
        MATCH (tang:Dynasty {id: 'tang'})
        MATCH (sui:Dynasty  {id: 'sui'})
        MATCH (s_ic:Style   {id: 'imperial_ceremonial'})
        MATCH (s_ip:Style   {id: 'imperial_palace'})
        MATCH (s_bp:Style   {id: 'buddhist_pagoda'})
        MATCH (s_ig:Style   {id: 'imperial_garden'})

        MERGE (toh)-[:BUILT_IN]->(ming)
        MERGE (toh)-[:HAS_STYLE]->(s_ic)
        MERGE (toh)-[:SYMBOLIZES]->(heaven)
        MERGE (toh)-[:BUILT_BY]->(yongle)
        MERGE (toh)-[:SIMILAR_TO]->(fc)

        MERGE (fc)-[:BUILT_IN]->(ming)
        MERGE (fc)-[:HAS_STYLE]->(s_ip)
        MERGE (fc)-[:SYMBOLIZES]->(imperial)
        MERGE (fc)-[:BUILT_BY]->(yongle)

        MERGE (gwgp)-[:BUILT_IN]->(tang)
        MERGE (gwgp)-[:HAS_STYLE]->(s_bp)
        MERGE (gwgp)-[:SYMBOLIZES]->(buddhism)
        MERGE (gwgp)-[:ASSOCIATED_WITH]->(xuanzang)

        MERGE (sp)-[:BUILT_IN]->(qing)
        MERGE (sp)-[:HAS_STYLE]->(s_ig)
        MERGE (sp)-[:SYMBOLIZES]->(longevity)

        MERGE (zb)-[:BUILT_IN]->(sui)
        MERGE (zb)-[:BUILT_BY]->(li_chun)
        """
        session.run(cypher)
        logger.info("Knowledge graph seeded with initial data")

    async def close(self) -> None:
        if self._driver:
            self._driver.close()

    async def get_building(self, building_name: str) -> Optional[dict]:
        """Fetch building node with all related entities."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._get_building_sync, building_name)

    def _get_building_sync(self, building_name: str) -> Optional[dict]:
        if not self._driver:
            return self._mock_building(building_name)
        query = """
        MATCH (b:Building)
        WHERE toLower(b.name) CONTAINS toLower($name) OR toLower(b.name_zh) CONTAINS toLower($name)
        OPTIONAL MATCH (b)-[:BUILT_IN]->(d:Dynasty)
        OPTIONAL MATCH (b)-[:HAS_STYLE]->(s:Style)
        OPTIONAL MATCH (b)-[:USES_MATERIAL]->(m:Material)
        OPTIONAL MATCH (b)-[:SYMBOLIZES]->(sym:Symbolism)
        OPTIONAL MATCH (b)-[:BUILT_BY]->(p:Person)
        OPTIONAL MATCH (b)-[:SIMILAR_TO]->(related:Building)
        RETURN b, collect(DISTINCT d.name) AS dynasties,
               collect(DISTINCT s.name) AS styles,
               collect(DISTINCT m.name) AS materials,
               collect(DISTINCT sym.concept) AS symbolisms,
               collect(DISTINCT p.name) AS persons,
               collect(DISTINCT related.name) AS related_buildings
        LIMIT 1
        """
        with self._driver.session() as session:
            result = session.run(query, name=building_name).single()  # type: ignore[arg-type]
            if not result:
                return None
            b = result["b"]
            return {
                "building_id": b.get("id", ""),
                "name": b.get("name", ""),
                "name_zh": b.get("name_zh", ""),
                "dynasty": result["dynasties"][0] if result["dynasties"] else "",
                "architect": result["persons"][0] if result["persons"] else None,
                "location": b.get("location", ""),
                "year_built": b.get("year_built", None),
                "architectural_style": result["styles"][0] if result["styles"] else "",
                "materials": result["materials"],
                "symbolism": result["symbolisms"],
                "historical_events": [],
                "related_buildings": result["related_buildings"],
                "description": b.get("description", ""),
                "description_zh": b.get("description_zh", ""),
            }

    async def get_building_context(self, building_name: str) -> list[dict]:
        """Return graph triples as text for LLM context injection."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._get_context_sync, building_name)

    def _get_context_sync(self, building_name: str) -> list[dict]:
        if not self._driver:
            return []
        query = """
        MATCH (b:Building)
        WHERE toLower(b.name) CONTAINS toLower($name)
        MATCH (b)-[r]->(target)
        RETURN b.name AS building, type(r) AS relation, 
               coalesce(target.name, target.concept, target.name_zh) AS target_entity
        LIMIT 20
        """
        with self._driver.session() as session:
            results = session.run(query, name=building_name).data()  # type: ignore[arg-type]
        context_items = []
        for row in results:
            rel = row["relation"].replace("_", " ").lower()
            text = f"{row['building']} {rel} {row['target_entity']}."
            context_items.append({"text": text, "source": "knowledge_graph", "type": "graph"})
        return context_items

    async def get_buildings_by_dynasty(self, dynasty: str) -> list[dict]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._get_by_dynasty_sync, dynasty)

    def _get_by_dynasty_sync(self, dynasty: str) -> list[dict]:
        if not self._driver:
            return []
        query = """
        MATCH (b:Building)-[:BUILT_IN]->(d:Dynasty)
        WHERE toLower(d.name) CONTAINS toLower($dynasty) OR d.id CONTAINS toLower($dynasty)
        RETURN b.id AS id, b.name AS name, b.name_zh AS name_zh,
               d.name AS dynasty, b.location AS location, b.year_built AS year_built
        """
        with self._driver.session() as session:
            return session.run(query, dynasty=dynasty).data()  # type: ignore[arg-type]

    async def get_subgraph(self, building_name: str, depth: int = 2) -> dict:
        """Return nodes and edges for graph visualization."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._get_subgraph_sync, building_name, depth)

    def _get_subgraph_sync(self, building_name: str, depth: int) -> dict:
        if not self._driver:
            return {"nodes": [], "edges": []}
        # depth is clamped to [1,4] to prevent abuse; used as literal not as param
        depth = max(1, min(depth, 4))
        query = (
            "MATCH path = (b:Building)-[*1.."
            + str(depth)
            + "]-(related) "
            "WHERE toLower(b.name) CONTAINS toLower($name) "
            "UNWIND nodes(path) AS n "
            "UNWIND relationships(path) AS r "
            "RETURN collect(DISTINCT { "
            "    id: coalesce(n.id, n.name), "
            "    label: labels(n)[0], "
            "    name: coalesce(n.name, n.concept, n.id) "
            "}) AS nodes, "
            "collect(DISTINCT { "
            "    source: coalesce(startNode(r).name, startNode(r).concept), "
            "    target: coalesce(endNode(r).name, endNode(r).concept), "
            "    relation: type(r) "
            "}) AS edges"
        )
        with self._driver.session() as session:
            result = session.run(query, name=building_name).single()  # type: ignore[arg-type]
            if not result:
                return {"nodes": [], "edges": []}
            return {"nodes": result["nodes"], "edges": result["edges"]}

    @staticmethod
    def _mock_building(building_name: str) -> dict:
        return {
            "building_id": "mock",
            "name": building_name,
            "name_zh": building_name,
            "dynasty": "Ming Dynasty",
            "architect": None,
            "location": "Beijing",
            "year_built": "1420",
            "architectural_style": "Imperial Architecture",
            "materials": ["Wood", "Stone", "Glazed Tile"],
            "symbolism": ["Imperial Power", "Heaven-Earth Connection"],
            "historical_events": [],
            "related_buildings": [],
            "description": f"A magnificent example of Chinese imperial architecture.",
            "description_zh": "中国皇家建筑的杰出代表。",
        }
