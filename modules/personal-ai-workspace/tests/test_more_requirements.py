from src.config.config_loader import load_config
from src.grounding.evidence_checker import NO_EVIDENCE
from src.reading.metadata_extractor import extract_reading_metadata
from src.reading.topic_clusterer import cluster_topics
from src.tools.default_registry import build_registry


def test_semantic_search_and_ask_refusal():
    registry = build_registry(load_config())
    semantic = registry.call("search_kb", {"query": "retrieval generation", "mode": "semantic", "top_k": 2})
    assert semantic["success"]
    refused = registry.call("ask_kb", {"query": "火星基地预算是多少？", "collection": "personal"})
    assert NO_EVIDENCE in refused["answer"]


def test_reading_metadata_and_topic_cluster():
    meta = extract_reading_metadata("# Agent Safety\n\n2026 notes about dry-run confirmation.", "demo.md")
    assert meta["title"] == "Agent Safety"
    topics = cluster_topics([{"title": meta["title"], "summary": meta["summary"]}])
    assert topics

