from __future__ import annotations

from pathlib import Path


AI_PROJECT_DIRS = {
    "personal-academic-rag-workspace",
    "personal-agent-workspace",
    "personal-ai-workspace",
    "local-mcp-toolkit",
    "integration_demo",
}

SKIP_DIR_MARKERS = {
    "__pycache__",
    ".pytest_cache",
    ".git",
    ".venv",
    "node_modules",
    "data",
    "miktex_data",
    "miktex_logs",
    "miktex_logs2",
    ".miktex",
}


def should_skip_path(path: Path, root: Path) -> bool:
    try:
        parts = set(path.resolve().relative_to(root.resolve()).parts)
    except ValueError:
        return True
    if parts & AI_PROJECT_DIRS:
        return True
    if parts & SKIP_DIR_MARKERS:
        return True
    name = path.name.lower()
    if name.endswith((".aux", ".log", ".bbl", ".blg", ".toc", ".out")):
        return True
    return False


def classify_file(path: Path, root: Path) -> dict[str, object]:
    rel = str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    low = rel.lower()
    name = path.name.lower()
    suffix = path.suffix.lower()
    tags: set[str] = set()
    collection = "personal"
    doc_type = "general"

    thesis_markers = ("latex模板", "博士", "thesis", "dissertation", "chapters", "main.pdf")
    if any(marker in rel or marker in low or marker in name for marker in thesis_markers):
        collection = "thesis"
        doc_type = "thesis"
        tags.update({"博士论文", "thesis"})

    paper_markers = ("reference", "文献", "paper", "journal", "conference", "manuscript", "supplementary")
    if any(marker in rel or marker in low for marker in paper_markers) or suffix == ".pdf":
        if collection != "thesis":
            collection = "academic"
            doc_type = "paper"
        tags.update({"paper", "literature"})

    if "meeting" in low or "会议" in rel:
        collection = "meetings"
        doc_type = "meeting"
        tags.add("meeting")

    if "resume" in low or "简历" in rel or "cv" in low:
        collection = "resume"
        doc_type = "resume"
        tags.add("resume")

    if "project" in low or "项目" in rel or "sound_target_detection_app" in rel:
        collection = "projects"
        doc_type = "project"
        tags.add("project")

    if ".workbuddy" in rel:
        collection = "notes"
        doc_type = "note"
        tags.add("workbuddy")

    if "figures" in low or "figure" in name or "fig." in name:
        tags.add("figure")
        if doc_type == "paper":
            doc_type = "figure_pdf"

    if suffix in {".md", ".txt"}:
        tags.add("text")
    if suffix == ".docx":
        tags.add("word")
    if suffix == ".pptx":
        tags.add("slides")
        collection = "slides"
        doc_type = "slides"

    return {"collection": collection, "doc_type": doc_type, "tags": sorted(tags), "relative_path": rel}
