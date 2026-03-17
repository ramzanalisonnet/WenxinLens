"""
DocumentProcessor — ingests raw documents and prepares them for the RAG pipeline.

Pipeline:
  Raw document (PDF / TXT / HTML / Markdown)
    → Text extraction
    → Cleaning
    → Language detection
    → Chunking (recursive character splitter)
    → Metadata enrichment
    → Output: list[Document] ready for VectorStore.upsert()
"""
from __future__ import annotations

import re
import uuid
from pathlib import Path
from typing import Iterator

from loguru import logger

from config import get_settings
from rag.vector_store import Document

settings = get_settings()


class DocumentProcessor:
    """Converts raw content into structured Document chunks."""

    def __init__(
        self,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ) -> None:
        self.chunk_size = chunk_size or settings.rag_chunk_size
        self.chunk_overlap = chunk_overlap or settings.rag_chunk_overlap

    # ── Ingestion ────────────────────────────────────────────────

    def process_file(self, file_path: str | Path, building: str = "", dynasty: str = "") -> list[Document]:
        """Process a single file into chunks."""
        path = Path(file_path)
        suffix = path.suffix.lower()

        if suffix == ".pdf":
            text = self._extract_pdf(path)
        elif suffix in {".html", ".htm"}:
            text = self._extract_html(path)
        elif suffix in {".txt", ".md"}:
            text = path.read_text(encoding="utf-8")
        else:
            logger.warning(f"Unsupported file type: {suffix}, reading as plain text")
            text = path.read_text(encoding="utf-8")

        return self._chunk_and_create(
            text=text,
            source=path.name,
            building=building,
            dynasty=dynasty,
        )

    def process_text(
        self,
        text: str,
        source: str,
        building: str = "",
        dynasty: str = "",
        language: str = "en",
    ) -> list[Document]:
        """Process a plain text string into chunks."""
        return self._chunk_and_create(text, source, building, dynasty, language)

    # ── Internal helpers ─────────────────────────────────────────

    def _chunk_and_create(
        self,
        text: str,
        source: str,
        building: str,
        dynasty: str,
        language: str = "en",
    ) -> list[Document]:
        text = self._clean_text(text)
        language = self._detect_language(text) if not language else language
        chunks = list(self._recursive_split(text, self.chunk_size, self.chunk_overlap))
        docs = []
        for i, chunk in enumerate(chunks):
            if len(chunk.strip()) < 50:
                continue
            docs.append(
                Document(
                    doc_id=str(uuid.uuid4()),
                    text=chunk,
                    source=source,
                    building=building,
                    dynasty=dynasty,
                    language=language,
                )
            )
        logger.debug(f"Processed '{source}' → {len(docs)} chunks")
        return docs

    @staticmethod
    def _clean_text(text: str) -> str:
        # Normalize whitespace
        text = re.sub(r"\r\n", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" {2,}", " ", text)
        # Remove non-printable characters (preserve CJK)
        text = re.sub(r"[^\x20-\x7E\u4E00-\u9FFF\u3400-\u4DBF\n\t]", " ", text)
        return text.strip()

    @staticmethod
    def _detect_language(text: str) -> str:
        """Simple heuristic: count CJK characters."""
        cjk_count = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
        return "zh" if cjk_count / max(len(text), 1) > 0.1 else "en"

    def _recursive_split(
        self, text: str, chunk_size: int, overlap: int
    ) -> Iterator[str]:
        """Recursive character splitting — respects paragraph and sentence boundaries."""
        separators = ["\n\n", "\n", "。", ".", "；", ";", "，", ",", " ", ""]

        def split_with_sep(s: str, sep: str) -> list[str]:
            return [p for p in s.split(sep) if p.strip()]

        def _split(s: str, seps: list[str]) -> list[str]:
            if not seps or len(s) <= chunk_size:
                return [s]
            sep = seps[0]
            parts = split_with_sep(s, sep)
            result = []
            current = ""
            for part in parts:
                if len(current) + len(part) + len(sep) <= chunk_size:
                    current = (current + sep + part).lstrip(sep)
                else:
                    if current:
                        result.append(current)
                    if len(part) > chunk_size:
                        result.extend(_split(part, seps[1:]))
                        current = ""
                    else:
                        current = part
            if current:
                result.append(current)
            return result

        chunks = _split(text, separators)

        # Apply overlap
        result = []
        for i, chunk in enumerate(chunks):
            if i > 0 and overlap > 0 and i < len(chunks):
                prev_end = chunks[i - 1][-overlap:]
                chunk = prev_end + " " + chunk
            result.append(chunk.strip())
        return iter(result)

    @staticmethod
    def _extract_pdf(path: Path) -> str:
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)

    @staticmethod
    def _extract_html(path: Path) -> str:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(path.read_text(encoding="utf-8"), "lxml")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        return soup.get_text(separator="\n")
