from __future__ import annotations

from pathlib import Path

from src.safety.audit_log import JsonlLog
from src.safety.dry_run import write_operation_plan
from src.safety.path_guard import PathGuard
from src.safety.prompt_injection_guard import scan_prompt_injection
from src.utils.file_utils import TEXT_EXTENSIONS, modified_at


class FilesystemTools:
    def __init__(self, guard: PathGuard, audit_log: JsonlLog, allowed_extensions: list[str], max_read_chars: int = 12000) -> None:
        self.guard = guard
        self.audit_log = audit_log
        self.allowed_extensions = set(allowed_extensions)
        self.max_read_chars = max_read_chars

    def list_files(self, path: str = ".", recursive: bool = False, extensions: list[str] | None = None, limit: int = 100) -> dict:
        root = self.guard.validate(path, must_exist=True)
        if not root.is_dir():
            raise ValueError("path must be a directory")
        exts = set(extensions or self.allowed_extensions)
        iterator = root.rglob("*") if recursive else root.iterdir()
        files = []
        for p in iterator:
            if len(files) >= limit:
                break
            if p.is_file() and exts and p.suffix.lower() not in exts:
                continue
            self.guard.validate(p, must_exist=True)
            stat = p.stat()
            files.append({"path": str(p.relative_to(self.guard.workspace_dir)), "name": p.name, "extension": p.suffix, "size_bytes": stat.st_size, "modified_at": modified_at(p), "is_dir": p.is_dir()})
        return {"root": str(root), "files": files}

    def read_file(self, path: str, max_chars: int | None = None) -> dict:
        p = self.guard.validate(path, must_exist=True)
        if not p.is_file():
            raise ValueError("path must be a file")
        if p.suffix.lower() not in TEXT_EXTENSIONS:
            raise ValueError(f"Only text-like files can be read, got {p.suffix}")
        max_chars = max_chars or self.max_read_chars
        text = p.read_text(encoding="utf-8", errors="ignore")
        scan = scan_prompt_injection(text)
        return {"path": str(p.relative_to(self.guard.workspace_dir)), "content": text[:max_chars], "truncated": len(text) > max_chars, "prompt_injection_warning": scan}

    def search_files(self, query: str, path: str = ".", search_content: bool = True, extensions: list[str] | None = None, limit: int = 50) -> dict:
        root = self.guard.validate(path, must_exist=True)
        exts = set(extensions or self.allowed_extensions)
        matches = []
        for p in root.rglob("*"):
            if len(matches) >= limit:
                break
            if not p.is_file() or (exts and p.suffix.lower() not in exts):
                continue
            self.guard.validate(p, must_exist=True)
            if query.lower() in p.name.lower():
                matches.append({"path": str(p.relative_to(self.guard.workspace_dir)), "match_type": "filename", "line_number": None, "snippet": p.name})
            if search_content and p.suffix.lower() in TEXT_EXTENSIONS:
                for i, line in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
                    if query.lower() in line.lower():
                        matches.append({"path": str(p.relative_to(self.guard.workspace_dir)), "match_type": "content", "line_number": i, "snippet": line.strip()[:300]})
                        break
        return {"query": query, "matches": matches[:limit]}

    def write_file(self, path: str, content: str, overwrite: bool = False, dry_run: bool = True, confirm: bool = False) -> dict:
        p = self.guard.validate(path, for_write=True)
        warning = scan_prompt_injection(content)
        if warning["has_risk"]:
            raise PermissionError(f"Prompt injection risk blocked: {warning['warnings']}")
        plan = write_operation_plan(str(p.relative_to(self.guard.workspace_dir)), content, overwrite, dry_run, confirm)
        if dry_run:
            return {"plan": plan, "executed": False}
        if not confirm:
            raise PermissionError("confirm=true required")
        if p.exists() and not overwrite:
            raise FileExistsError(f"File exists and overwrite=false: {p}")
        backup = None
        if p.exists():
            backup = p.with_suffix(p.suffix + ".bak")
            backup.write_text(p.read_text(encoding="utf-8", errors="ignore"), encoding="utf-8")
        p.write_text(content, encoding="utf-8")
        event = {"operation": "write_file", "path": str(p), "backup": str(backup) if backup else None, "bytes": len(content.encode("utf-8"))}
        self.audit_log.append(event)
        return {"plan": plan, "executed": True, "rollback": event}

