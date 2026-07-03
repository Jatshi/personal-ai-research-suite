from __future__ import annotations

import shutil
from pathlib import Path


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".md", ".txt"}


def ensure_within(base: Path, target: Path) -> Path:
    base = base.resolve()
    target = target.resolve()
    if base != target and base not in target.parents:
        raise ValueError(f"Path is outside workspace: {target}")
    return target


def iter_supported_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path] if path.suffix.lower() in SUPPORTED_EXTENSIONS else []
    files: list[Path] = []
    for ext in SUPPORTED_EXTENSIONS:
        files.extend(path.rglob(f"*{ext}"))
    return sorted(files)


def copy_into_workspace(source: Path, raw_dir: Path, collection: str) -> Path:
    target_dir = raw_dir / collection
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / source.name
    if target.exists():
        stem, suffix = source.stem, source.suffix
        i = 1
        while target.exists():
            target = target_dir / f"{stem}_{i}{suffix}"
            i += 1
    shutil.copy2(source, target)
    return target

