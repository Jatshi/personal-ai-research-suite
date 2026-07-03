import importlib.util

import pytest

from src.config.config_loader import load_config
from src.indexing.chroma_store import _distance_to_score, _metadata_for_chroma, chroma_enabled
from src.indexing.index_manager import ingest_path
from src.tools.kb_tools import search_kb_tool


def test_chroma_enabled_config_flag():
    assert chroma_enabled({"vector_store": {"backend": "chroma"}})
    assert not chroma_enabled({"vector_store": {"backend": "sqlite"}})


def test_chroma_metadata_is_primitive_only():
    meta = _metadata_for_chroma(
        {
            "doc_id": "d1",
            "collection": "personal",
            "file_name": "note.md",
            "page_number": None,
            "paragraph_number": 2,
            "section_title": {"bad": "object"},
        }
    )
    assert meta["doc_id"] == "d1"
    assert meta["paragraph_number"] == 2
    assert isinstance(meta["section_title"], str)
    assert "page_number" not in meta


def test_chroma_distance_score_is_bounded():
    assert _distance_to_score(0.0) == 1.0
    assert 0.0 < _distance_to_score(2.0) < 1.0


@pytest.mark.skipif(importlib.util.find_spec("chromadb") is None, reason="chromadb not installed")
def test_chroma_backend_ingest_and_search(tmp_path):
    config = load_config()
    config["app"]["data_dir"] = str(tmp_path / "data")
    config["vector_store"] = {
        "backend": "chroma",
        "persist_dir": str(tmp_path / "chroma"),
        "collection_prefix": "test_personal_ai_workspace",
    }
    docs = ingest_path(config, "examples/sample_docs/rag_intro.md", "chroma_test")
    assert docs and docs[0]["chunk_count"] >= 1
    results = search_kb_tool(config, {"query": "retrieval generation", "collection": "chroma_test", "mode": "semantic", "top_k": 3})
    assert results["success"]
    assert results["results"]
    assert results["results"][0]["metadata"]["vector_store"] == "chroma"
