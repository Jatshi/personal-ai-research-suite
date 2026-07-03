from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_config(tmp_path: Path) -> dict:
    workspace = ROOT / "data" / "test_runs" / tmp_path.name
    return {
        "_project_root": str(ROOT),
        "app": {"name": "test", "workspace_dir": str(workspace)},
        "chunking": {"chunk_size": 240, "chunk_overlap": 30},
        "retrieval": {"default_mode": "hybrid", "top_k": 5, "bm25_weight": 0.4, "vector_weight": 0.6, "rerank_top_k": 10, "min_confidence": 0.2},
        "embedding": {"backend": "mock", "model_name": "mock", "dimension": 64},
        "llm": {"backend": "mock", "model_name": "mock", "temperature": 0.2, "max_tokens": 1000},
        "academic": {"enable_section_detection": True, "enable_metadata_extraction": True},
        "logging": {"level": "INFO", "log_file": str(tmp_path / "app.log")},
    }
