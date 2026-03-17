"""
VectorStore — Milvus-backed vector database with FAISS fallback.

Collection schema:
  id        : VARCHAR(64)  — document chunk ID
  text      : VARCHAR(4096) — chunk content
  source    : VARCHAR(256)  — document source
  building  : VARCHAR(256)  — associated building
  dynasty   : VARCHAR(128)  — dynasty tag
  language  : VARCHAR(8)    — "en" | "zh"
  embedding : FLOAT_VECTOR(1024) — BGE-Large embedding

Hybrid search: dense vector + optional metadata filters.
"""
from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass
from typing import Optional

from loguru import logger

from config import get_settings

settings = get_settings()

COLLECTION_NAME = settings.milvus_collection
EMBEDDING_DIM = settings.embedding_dim


@dataclass
class Document:
    doc_id: str
    text: str
    source: str
    building: str = ""
    dynasty: str = ""
    language: str = "en"
    embedding: Optional[list[float]] = None


class VectorStore:
    """
    Milvus-based dense vector store.
    Falls back to FAISS in-memory if Milvus is unavailable.
    """

    def __init__(self) -> None:
        self._client = None
        self._faiss_index = None
        self._faiss_docs: list[Document] = []
        self._use_faiss = False
        self._embedder = None

    async def initialize(self) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._connect)

    def _connect(self) -> None:
        try:
            from pymilvus import MilvusClient, CollectionSchema, FieldSchema, DataType, connections

            connections.connect(host=settings.milvus_host, port=settings.milvus_port)
            from pymilvus import utility
            if not utility.has_collection(COLLECTION_NAME):
                self._create_collection()
            self._client = "milvus"
            logger.info(f"Connected to Milvus at {settings.milvus_host}:{settings.milvus_port}")
        except Exception as exc:
            logger.warning(f"Milvus unavailable ({exc}), switching to FAISS in-memory store")
            self._init_faiss()

    def _create_collection(self) -> None:
        from pymilvus import Collection, CollectionSchema, FieldSchema, DataType, connections

        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=64, is_primary=True),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=4096),
            FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=256),
            FieldSchema(name="building", dtype=DataType.VARCHAR, max_length=256),
            FieldSchema(name="dynasty", dtype=DataType.VARCHAR, max_length=128),
            FieldSchema(name="language", dtype=DataType.VARCHAR, max_length=8),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=EMBEDDING_DIM),
        ]
        schema = CollectionSchema(fields=fields, description="WenxinLens architecture knowledge")
        collection = Collection(name=COLLECTION_NAME, schema=schema)
        collection.create_index(  # type: ignore[no-untyped-call]
            field_name="embedding",
            index_params={
                "index_type": "HNSW",
                "metric_type": "COSINE",
                "params": {"M": 16, "efConstruction": 256},
            },
        )
        collection.load()
        logger.info(f"Created Milvus collection: {COLLECTION_NAME}")

    def _init_faiss(self) -> None:
        try:
            import faiss
            self._faiss_index = faiss.IndexFlatIP(EMBEDDING_DIM)  # Inner product = cosine after normalize
            self._use_faiss = True
            logger.info("FAISS in-memory vector store initialized")
        except ImportError:
            logger.warning("Neither Milvus nor FAISS available — running without vector search")

    def _get_embedder(self):
        if self._embedder is None:
            from sentence_transformers import SentenceTransformer
            self._embedder = SentenceTransformer(settings.embedding_model, device=settings.embedding_device)
        return self._embedder

    def _embed_texts(self, texts: list[str]) -> list[list[float]]:
        import numpy as np
        embedder = self._get_embedder()
        vecs = embedder.encode(texts, normalize_embeddings=True, batch_size=32)
        return vecs.tolist()

    async def upsert(self, documents: list[Document]) -> int:
        """Embed and insert/update documents. Returns count inserted."""
        if not documents:
            return 0

        loop = asyncio.get_running_loop()
        texts = [d.text for d in documents]
        embeddings = await loop.run_in_executor(None, lambda: self._embed_texts(texts))

        for doc, emb in zip(documents, embeddings):
            doc.embedding = emb
            if not doc.doc_id:
                doc.doc_id = str(uuid.uuid4())

        if self._use_faiss:
            return self._faiss_upsert(documents)
        elif self._client == "milvus":
            return self._milvus_upsert(documents)
        return 0

    def _milvus_upsert(self, documents: list[Document]) -> int:
        from pymilvus import Collection
        collection = Collection(COLLECTION_NAME)
        data = {
            "id": [d.doc_id for d in documents],
            "text": [d.text[:4090] for d in documents],
            "source": [d.source for d in documents],
            "building": [d.building for d in documents],
            "dynasty": [d.dynasty for d in documents],
            "language": [d.language for d in documents],
            "embedding": [d.embedding for d in documents],
        }
        collection.insert(list(data.values()))
        collection.flush()
        return len(documents)

    def _faiss_upsert(self, documents: list[Document]) -> int:
        import numpy as np
        vecs = np.array([d.embedding for d in documents], dtype="float32")
        self._faiss_index.add(vecs)  # type: ignore[union-attr]
        self._faiss_docs.extend(documents)
        return len(documents)

    async def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        filters: dict | None = None,
    ) -> list:
        """Perform approximate nearest neighbour search."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, lambda: self._search_sync(query_vector, top_k, filters)
        )

    def _search_sync(
        self, query_vector: list[float], top_k: int, filters: dict | None
    ) -> list:
        if self._use_faiss:
            return self._faiss_search(query_vector, top_k)
        elif self._client == "milvus":
            return self._milvus_search(query_vector, top_k, filters)
        return []

    def _milvus_search(
        self, query_vector: list[float], top_k: int, filters: dict | None
    ) -> list:
        import json
        from pymilvus import Collection
        from services.retrieval_service import RetrievalResult

        collection = Collection(COLLECTION_NAME)
        collection.load()

        expr = None
        if filters:
            clauses = [f'{k} == "{v}"' for k, v in filters.items() if v]
            if clauses:
                expr = " and ".join(clauses)

        results = collection.search(  # type: ignore[call-arg]
            data=[query_vector],
            anns_field="embedding",
            param={"metric_type": "COSINE", "params": {"ef": 128}},
            limit=top_k,
            expr=expr,
            output_fields=["text", "source", "building", "dynasty"],
        )
        return [
            RetrievalResult(
                text=hit.entity.get("text", ""),
                source=hit.entity.get("source", ""),
                score=float(hit.score),
                metadata={
                    "building": hit.entity.get("building", ""),
                    "dynasty": hit.entity.get("dynasty", ""),
                },
            )
            for hit in results[0]  # type: ignore[index]
        ]

    def _faiss_search(self, query_vector: list[float], top_k: int) -> list:
        import numpy as np
        from services.retrieval_service import RetrievalResult

        if not self._faiss_docs:
            return []
        q = np.array([query_vector], dtype="float32")
        distances, indices = self._faiss_index.search(q, min(top_k, len(self._faiss_docs)))  # type: ignore[union-attr]
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(self._faiss_docs):
                continue
            doc = self._faiss_docs[idx]
            results.append(
                RetrievalResult(
                    text=doc.text,
                    source=doc.source,
                    score=float(dist),
                    metadata={"building": doc.building, "dynasty": doc.dynasty},
                )
            )
        return results
