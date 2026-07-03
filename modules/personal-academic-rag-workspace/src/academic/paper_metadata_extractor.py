from __future__ import annotations

import re
from pathlib import Path

from src.models import Chunk
from src.utils.text_utils import normalize_text


class PaperMetadataExtractor:
    def extract(self, chunks: list[Chunk]) -> dict:
        text = normalize_text("\n".join(c.text for c in chunks[:5]))
        filename = chunks[0].metadata.get("filename", "") if chunks else ""
        lines = [l.strip() for l in re.split(r"[\n。]", text) if l.strip()]
        title = next((l for l in lines if 8 <= len(l) <= 180), Path(filename).stem)
        year = self._first_match(r"\b(19|20)\d{2}\b", text)
        doi = self._first_match(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+", text)
        abstract = self._between(text, r"abstract", r"(keywords|introduction|1\s+introduction)")[:1200]
        keywords = self._keywords(text)
        authors = self._authors(lines, title)
        venue = self._first_match(r"(IEEE|ACM|Nature|Science|Sensors|Neurocomputing|Journal|Conference)[^,.]{0,80}", text)
        return {
            "title": title,
            "authors": authors,
            "abstract": abstract,
            "keywords": keywords,
            "year": year or "",
            "venue": venue or "",
            "doi": doi or "",
            "file_path": chunks[0].metadata.get("source_path", "") if chunks else "",
            "filename": filename,
        }

    @staticmethod
    def _first_match(pattern: str, text: str) -> str:
        m = re.search(pattern, text, flags=re.I)
        return m.group(0) if m else ""

    @staticmethod
    def _between(text: str, start: str, end: str) -> str:
        m = re.search(start + r"[:\s]*(.*?)" + end, text, flags=re.I | re.S)
        return normalize_text(m.group(1)) if m else ""

    @staticmethod
    def _keywords(text: str) -> list[str]:
        m = re.search(r"keywords?[:\s]*(.{0,300})", text, flags=re.I)
        if not m:
            return []
        raw = re.split(r"[.;\n]", m.group(1))[0]
        return [x.strip() for x in re.split(r"[,;，；]", raw) if x.strip()][:8]

    @staticmethod
    def _authors(lines: list[str], title: str) -> list[str]:
        try:
            idx = lines.index(title)
            candidate = lines[idx + 1]
        except Exception:
            candidate = ""
        if not candidate or len(candidate) > 220:
            return []
        return [x.strip() for x in re.split(r",| and |，", candidate) if x.strip()][:12]

