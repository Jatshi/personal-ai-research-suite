from __future__ import annotations

from pathlib import Path

from src.code_intel.code_search import search_code_files
from src.code_intel.repo_summary import summarize_module, summarize_repo
from src.code_intel.repo_tree import build_tree
from src.code_intel.todo_finder import find_todo_markers
from src.safety.path_guard import PathGuard
from src.utils.file_utils import language_for_extension


class CodeTools:
    def __init__(self, guard: PathGuard, ignored_dirs: list[str], allowed_extensions: list[str]) -> None:
        self.guard = guard
        self.ignored_dirs = set(ignored_dirs)
        self.allowed_extensions = set(allowed_extensions)

    def _repo(self, repo_path: str) -> Path:
        marker = "examples/workspace/"
        normalized = repo_path.replace("\\", "/").lstrip("./")
        if normalized.startswith(marker):
            repo_path = normalized[len(marker) :]
        root = self.guard.validate(repo_path, must_exist=True)
        if not root.is_dir():
            raise ValueError("repo_path must be directory")
        return root

    def list_repo_tree(self, repo_path: str, max_depth: int = 3, include_files: bool = True) -> dict:
        root = self._repo(repo_path)
        return {"repo_path": str(root), "tree": build_tree(root, self.ignored_dirs, max_depth, include_files)}

    def search_code(self, repo_path: str, query: str, extensions: list[str] | None = None, limit: int = 50) -> dict:
        return search_code_files(self._repo(repo_path), query, self.ignored_dirs, extensions or list(self.allowed_extensions), limit)

    def read_code_file(self, repo_path: str, file_path: str, max_chars: int = 12000) -> dict:
        root = self._repo(repo_path)
        path = self.guard.validate(root / file_path, must_exist=True)
        if path.suffix.lower() not in self.allowed_extensions:
            raise ValueError(f"Unsupported code extension: {path.suffix}")
        text = path.read_text(encoding="utf-8", errors="ignore")
        return {"path": str(path.relative_to(root)), "language": language_for_extension(path.suffix), "line_count": len(text.splitlines()), "content": text[:max_chars], "truncated": len(text) > max_chars}

    def summarize_module(self, repo_path: str, module_path: str, max_files: int = 20) -> dict:
        root = self._repo(repo_path)
        module = self.guard.validate(root / module_path, must_exist=True)
        return summarize_module(root, module, self.ignored_dirs, max_files)

    def find_todos(self, repo_path: str, markers: list[str] | None = None) -> dict:
        return find_todo_markers(self._repo(repo_path), self.ignored_dirs, markers or ["TODO", "FIXME", "HACK", "NOTE"])

    def generate_repo_summary(self, repo_path: str, max_depth: int = 3) -> dict:
        return summarize_repo(self._repo(repo_path), self.ignored_dirs, max_depth)

    def generate_issue_draft(self, title_hint: str, context: str, related_files: list[str] | None = None) -> dict:
        return {"title": title_hint.strip().capitalize(), "body": f"## Context\n{context}\n\n## Related files\n" + "\n".join(f"- {f}" for f in (related_files or [])), "labels": ["triage"]}

    def generate_pr_description(self, change_summary: str, files_changed: list[str] | None = None, testing_notes: str = "") -> dict:
        return {"title": change_summary[:80], "description": f"## Summary\n{change_summary}\n\n## Files changed\n" + "\n".join(f"- {f}" for f in (files_changed or [])) + f"\n\n## Testing\n{testing_notes or 'Not provided.'}", "checklist": ["Tests pass", "Docs updated if needed", "Security reviewed"]}
