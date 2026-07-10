from __future__ import annotations

import copy

import pytest

from src.api.workbench_service import plan_settings_update
from src.config.config_loader import load_config


def test_settings_plan_is_dry_run_and_does_not_mutate_input():
    config = load_config()
    before = copy.deepcopy(config["retrieval"])
    plan = plan_settings_update(config, {"retrieval": {"top_k": 7}})
    assert plan["diff"]["retrieval.top_k"] == {"before": before["top_k"], "after": 7}
    assert config["retrieval"] == before


def test_settings_plan_rejects_secret_and_invalid_weight_changes():
    config = load_config()
    with pytest.raises(ValueError, match="Unsupported setting"):
        plan_settings_update(config, {"llm": {"api_key_env": "LEAK"}})
    with pytest.raises(ValueError, match="sum to 1.0"):
        plan_settings_update(config, {"retrieval": {"bm25_weight": 0.9, "vector_weight": 0.9}})
