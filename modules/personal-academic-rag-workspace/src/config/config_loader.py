from __future__ import annotations

from pathlib import Path
from typing import Any
import os

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_config(config_path: str | Path | None = None) -> dict[str, Any]:
    _load_dotenv_if_available()
    configured_path = config_path or os.getenv("PERSONAL_ACADEMIC_RAG_CONFIG")
    path = Path(configured_path) if configured_path else PROJECT_ROOT / "config.yaml"
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    with path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}
    config["_config_path"] = str(path)
    config["_project_root"] = str(PROJECT_ROOT)
    return config


def save_config(config: dict[str, Any], config_path: str | Path | None = None) -> None:
    path = Path(config_path or config.get("_config_path") or PROJECT_ROOT / "config.yaml")
    clean = {k: v for k, v in config.items() if not k.startswith("_")}
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(clean, f, allow_unicode=True, sort_keys=False)


def project_path(config: dict[str, Any], value: str | Path) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = Path(config["_project_root"]) / path
    return path.resolve()


def _load_dotenv_if_available() -> None:
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(env_path)
