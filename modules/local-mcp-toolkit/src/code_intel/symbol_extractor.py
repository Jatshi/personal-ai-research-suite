from __future__ import annotations

import ast
import re
from pathlib import Path


def extract_symbols(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="ignore")
    functions: list[str] = []
    classes: list[str] = []
    imports: list[str] = []
    if path.suffix == ".py":
        try:
            tree = ast.parse(text)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    functions.append(node.name)
                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                elif isinstance(node, ast.Import):
                    imports.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.append(node.module)
        except SyntaxError:
            pass
    else:
        functions.extend(re.findall(r"\bfunction\s+([A-Za-z_][A-Za-z0-9_]*)", text))
        classes.extend(re.findall(r"\bclass\s+([A-Za-z_][A-Za-z0-9_]*)", text))
    return {"functions": functions, "classes": classes, "imports": sorted(set(imports))}

