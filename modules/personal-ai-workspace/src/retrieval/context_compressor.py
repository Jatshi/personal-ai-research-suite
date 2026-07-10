from __future__ import annotations

from typing import Any

from src.generation.llm_client import BaseLLMClient
from src.utils.text_utils import first_sentences


def compress_context(
    query: str,
    chunks: list[dict[str, Any]],
    mode: str,
    max_chars: int,
    llm: BaseLLMClient | None = None,
) -> tuple[list[dict[str, Any]], dict[str, int | str]]:
    before = sum(len(chunk.get("text", "")) for chunk in chunks)
    if mode == "none":
        return chunks, {"mode": mode, "before_chars": before, "after_chars": before}
    selected: list[dict[str, Any]] = []
    remaining = max_chars
    seen: set[str] = set()
    for chunk in chunks:
        text = chunk.get("text", "")
        fingerprint = " ".join(text.lower().split()[:20])
        if fingerprint in seen or remaining <= 0:
            continue
        seen.add(fingerprint)
        item = dict(chunk)
        if mode == "extractive" and llm is not None:
            extracted = llm.generate(f"Extract only sentences relevant to: {query}", [{"text": text, "file_name": chunk.get("file_name", "")}])
            item["text"] = extracted.strip() or first_sentences(text, min(remaining, 600))
        else:
            item["text"] = first_sentences(text, remaining)
        item["text"] = item["text"][:remaining]
        item["compressed_from_chunk_id"] = chunk.get("chunk_id")
        selected.append(item)
        remaining -= len(item["text"])
    after = sum(len(chunk.get("text", "")) for chunk in selected)
    return selected, {"mode": mode, "before_chars": before, "after_chars": after}
