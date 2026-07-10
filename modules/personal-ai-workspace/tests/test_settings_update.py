from __future__ import annotations

import copy

import pytest

from src.api.workbench_service import plan_settings_update, update_settings
from src.config.config_loader import load_config, save_config


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


def test_confirmed_settings_update_writes_clean_config(tmp_path):
    config = load_config()
    config["app"]["data_dir"] = str(tmp_path / "data")
    config["observability"]["log_dir"] = str(tmp_path / "logs")
    config_path = tmp_path / "config.yaml"
    config["_config_path"] = str(config_path)
    save_config(config, config_path)

    response = update_settings(config, {"retrieval": {"top_k": 7}}, confirm=True)

    assert response["executed"] is True
    reloaded = load_config(config_path)
    assert reloaded["retrieval"]["top_k"] == 7
    assert "_config_path" not in config_path.read_text(encoding="utf-8")
