"""
RetrievalService — semantic retrieval from Milvus vector store + Neo4j graph.

Handles:
  - query embedding
  - vector similarity search
  - knowledge graph context enrichment
  - result re-ranking
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from loguru import logger

from config import get_settings
from rag.vector_store import VectorStore
from knowledge_graph.neo4j_client import Neo4jClient

settings = get_settings()


@dataclass
class RetrievalResult:
    text: str
    source: str
    score: float
    metadata: dict


class RetrievalService:
    def __init__(self, vector_store: VectorStore, neo4j: Neo4jClient) -> None:
        self._vector_store = vector_store
        self._neo4j = neo4j
        self._embedder = None

    def _get_embedder(self):
        if self._embedder is None:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading embedding model …")
            self._embedder = SentenceTransformer(
                settings.embedding_model,
                device=settings.embedding_device,
            )
        return self._embedder

    async def search(
        self,
        query: str,
        building_name: str | None = None,
        filters: dict | None = None,
        top_k: int | None = None,
    ) -> list[dict]:
        """
        Perform semantic search combining:
        1. Dense vector search in Milvus
        2. Graph context from Neo4j
        Returns merged, ranked results.
        """
        top_k = top_k or settings.rag_top_k

        # Embed query
        import asyncio
        loop = asyncio.get_running_loop()
        embedder = self._get_embedder()
        query_vec = await loop.run_in_executor(None, lambda: embedder.encode(query).tolist())

        # Vector search
        vector_results: list[RetrievalResult] = []
        try:
            vector_results = await self._vector_store.search(
                query_vector=query_vec,
                top_k=top_k,
                filters=filters,
            )
        except Exception as exc:
            logger.warning(f"Vector search failed: {exc}")

        # Graph context enrichment
        graph_context: list[dict] = []
        if building_name:
            try:
                graph_context = await self._neo4j.get_building_context(building_name)
            except Exception as exc:
                logger.warning(f"Graph enrichment failed: {exc}")

        # Merge
        results = [
            {
                "text": r.text,
                "source": r.source,
                "score": r.score,
                "metadata": r.metadata,
                "type": "vector",
            }
            for r in vector_results
        ]
        for ctx in graph_context:
            results.append({**ctx, "type": "graph", "score": 0.9})

        # Sort by score descending
        results.sort(key=lambda x: x.get("score", 0), reverse=True)
        return results[:top_k]

    def format_context(self, results: list[dict]) -> str:
        """Format retrieval results into a RAG context string for LLM injection."""
        if not results:
            return ""
        parts = []
        for i, r in enumerate(results, 1):
            source = r.get("source", "knowledge base")
            text = r.get("text", "")
            parts.append(f"[Source {i}: {source}]\n{text}")
        return "\n\n".join(parts)
