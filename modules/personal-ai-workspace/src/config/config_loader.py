from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    load_dotenv(project_root() / ".env", override=False)
    config_path = Path(path or os.getenv("PERSONAL_AI_CONFIG") or project_root() / "config.yaml")
    if not config_path.is_absolute():
        config_path = project_root() / config_path
    with config_path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}
    config["_project_root"] = str(project_root())
    config["_config_path"] = str(config_path.resolve())
    return config


def save_config(config: dict[str, Any], path: str | Path | None = None) -> None:
    config = dict(config)
    config.pop("_project_root", None)
    config.pop("_config_path", None)
    config_path = Path(path) if path else project_root() / "config.yaml"
    with config_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, allow_unicode=True, sort_keys=False)


def resolve_project_path(config: dict[str, Any], value: str | Path) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = Path(config["_project_root"]) / path
    return path.resolve()
