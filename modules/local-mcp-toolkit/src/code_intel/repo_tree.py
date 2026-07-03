from __future__ import annotations

from pathlib import Path


def build_tree(root: Path, ignored_dirs: set[str], max_depth: int = 3, include_files: bool = True) -> dict:
    root = root.resolve()

    def node(path: Path, depth: int) -> dict:
        item = {"name": path.name, "path": str(path.relative_to(root)), "type": "dir" if path.is_dir() else "file"}
        if path.is_dir() and depth < max_depth:
            children = []
            for child in sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
                if child.name in ignored_dirs or child.name.startswith("."):
                    continue
                if child.is_file() and not include_files:
                    continue
                children.append(node(child, depth + 1))
            item["children"] = children
        return item

    return node(root, 0)

