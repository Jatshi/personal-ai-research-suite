from __future__ import annotations

from src.config.config_loader import load_config
from src.indexing.index_manager import ingest_path
from src.multi_agent.research_crew import run_research_crew


def test_research_crew_runs_all_roles(tmp_path):
    config = load_config()
    config["app"]["data_dir"] = str(tmp_path / "data")
    ingest_path(config, "examples/sample_docs", "personal")
    result = run_research_crew(config, "RAG retrieval", "personal")
    assert result["success"]
    assert [step["agent"] for step in result["steps"]] == ["Reader", "Method", "Experiment", "Critic", "Writer"]
    assert result["final_note"]
