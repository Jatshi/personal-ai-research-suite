from __future__ import annotations

import copy
from typing import Any

from src.evaluation.rag_evaluator import eval_rag


def compare_configs(
    config: dict[str, Any],
    dataset: str,
    config_a: dict[str, Any],
    config_b: dict[str, Any],
) -> dict[str, Any]:
    left = _apply_overrides(config, config_a)
    right = _apply_overrides(config, config_b)
    report_a = eval_rag(left, dataset)
    report_b = eval_rag(right, dataset)
    keys = sorted(set(report_a["metrics"]) & set(report_b["metrics"]))
    return {
        "engine": "builtin_ab",
        "config_a": config_a,
        "config_b": config_b,
        "metrics_a": report_a["metrics"],
        "metrics_b": report_b["metrics"],
        "delta_b_minus_a": {key: round(float(report_b["metrics"][key]) - float(report_a["metrics"][key]), 4) for key in keys},
        "records_a": report_a["records"],
        "records_b": report_b["records"],
    }


def _apply_overrides(config: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(config)
    for section, values in overrides.items():
        if isinstance(values, dict) and isinstance(result.get(section), dict):
            result[section].update(values)
        else:
            result[section] = values
    return result
