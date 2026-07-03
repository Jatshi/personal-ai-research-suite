from __future__ import annotations

from collections import Counter
from pathlib import Path

from src.code_intel.symbol_extractor import extract_symbols


def summarize_repo(root: Path, ignored_dirs: set[str], max_depth: int = 3) -> dict:
    langs = Counter()
    configs = []
    tests = []
    entry_points = []
    top_dirs = [p.name for p in root.iterdir() if p.is_dir() and p.name not in ignored_dirs and not p.name.startswith(".")]
    for path in root.rglob("*"):
        if not path.is_file() or any(part in ignored_dirs or part.startswith(".") for part in path.relative_to(root).parts):
            continue
        langs[path.suffix or "no_ext"] += 1
        if path.name.lower() in {"pyproject.toml", "requirements.txt", "package.json", "config.py", "config.yaml", "README.md".lower()}:
            configs.append(str(path.relative_to(root)))
        if "test" in path.parts or path.name.startswith("test_"):
            tests.append(str(path.relative_to(root)))
        if path.name in {"app.py", "main.py", "index.js"}:
            entry_points.append(str(path.relative_to(root)))
    return {
        "repo_path": str(root),
        "summary": f"Repository with {sum(langs.values())} files across {len(langs)} extension groups.",
        "languages": dict(langs),
        "top_level_dirs": top_dirs,
        "entry_points": entry_points,
        "test_dirs": sorted(set(str(Path(t).parts[0]) for t in tests if Path(t).parts)),
        "config_files": configs,
        "risk_warnings": [],
    }


def summarize_module(root: Path, module: Path, ignored_dirs: set[str], max_files: int = 20) -> dict:
    files = [p for p in module.rglob("*") if p.is_file() and not any(part in ignored_dirs or part.startswith(".") for part in p.relative_to(root).parts)][:max_files]
    functions: list[str] = []
    classes: list[str] = []
    imports: list[str] = []
    for f in files:
        symbols = extract_symbols(f)
        functions.extend(symbols["functions"])
        classes.extend(symbols["classes"])
        imports.extend(symbols["imports"])
    return {"module_path": str(module.relative_to(root)), "summary": f"Module contains {len(files)} analyzed files, {len(functions)} functions, {len(classes)} classes.", "files_analyzed": [str(f.relative_to(root)) for f in files], "main_functions": functions, "main_classes": classes, "dependencies": sorted(set(imports)), "notes": []}

