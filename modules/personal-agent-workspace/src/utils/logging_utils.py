from __future__ import annotations

import logging
from pathlib import Path


def setup_logging(log_dir: str | Path, level: str = "INFO") -> None:
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=[logging.FileHandler(Path(log_dir) / "app.log", encoding="utf-8"), logging.StreamHandler()],
    )

