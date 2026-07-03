from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    _load_dotenv_if_available(PROJECT_ROOT / ".env")
    config_path = Path(path) if path else PROJECT_ROOT / "config.yaml"
    with config_path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}
    config["_project_root"] = str(PROJECT_ROOT)
    config["_config_path"] = str(config_path)
    return config


def _load_dotenv_if_available(path: Path) -> None:
    if not path.exists():
        return
    try:
        from dotenv import load_dotenv
    except Exception:
        return
    load_dotenv(path)


def save_config(config: dict[str, Any], path: str | Path | None = None) -> None:
    config_path = Path(path or config.get("_config_path") or PROJECT_ROOT / "config.yaml")
    clean = {k: v for k, v in config.items() if not k.startswith("_")}
    with config_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(clean, f, allow_unicode=True, sort_keys=False)


def resolve_project_path(config: dict[str, Any], value: str | Path) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = Path(config["_project_root"]) / path
    return path.resolve()
