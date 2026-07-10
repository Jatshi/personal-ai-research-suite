from __future__ import annotations

from src.config.config_loader import load_config
from src.evaluation.ab_testing import compare_configs
from src.indexing.index_manager import ingest_path


def test_ab_compare_keeps_base_config_unchanged(tmp_path):
    config = load_config()
    config["app"]["data_dir"] = str(tmp_path / "data")
    ingest_path(config, "examples/sample_docs", "personal")
    before = config["retrieval"]["top_k"]
    report = compare_configs(
        config,
        "examples/sample_eval/phase6_rag_eval.jsonl",
        {"retrieval": {"top_k": 2}},
        {"retrieval": {"top_k": 5}},
    )
    assert report["engine"] == "builtin_ab"
    assert "retrieval_hit_rate" in report["delta_b_minus_a"]
    assert config["retrieval"]["top_k"] == before
