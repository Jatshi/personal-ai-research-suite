from __future__ import annotations

import json
import re
from pathlib import Path

from src.tools.document_tools import read_document


def check_thesis_structure(path: str) -> dict:
    text = read_document(path)["text"]
    headings = re.findall(r"^(#{1,3})\s*([0-9]+(?:\.[0-9]+)*)?\s*(.+)$", text, flags=re.M)
    issues = []
    seen = set()
    prev_top = 0
    for marks, number, title in headings:
        if not number:
            continue
        if number in seen:
            issues.append(_todo("章节编号", "medium", title, f"重复章节编号 {number}", "检查并重排章节编号"))
        seen.add(number)
        if len(marks) == 1:
            top = int(number.split(".")[0])
            if prev_top and top != prev_top + 1:
                issues.append(_todo("章节编号", "high", title, f"一级标题跳号：{prev_top} -> {top}", "补齐或修正章节编号"))
            prev_top = top
    required = ["摘要", "Abstract", "绪论", "相关", "方法", "实验", "结果", "讨论", "总结", "参考文献", "致谢"]
    missing = [name for name in required if name.lower() not in text.lower()]
    for name in missing:
        issues.append(_todo("缺失章节", "low", name, f"可能缺少章节：{name}", "确认论文结构是否需要该部分"))
    return {"headings": headings, "issues": issues, "missing_sections": missing}


def check_figure_table_references(path: str) -> dict:
    text = read_document(path)["text"]
    fig_defs = _numbers(r"图\s*([0-9]+(?:\.[0-9]+)*)", text)
    table_defs = _numbers(r"表\s*([0-9]+(?:\.[0-9]+)*)", text)
    eq_defs = _numbers(r"[（(]\s*([0-9]+(?:\.[0-9]+)*)\s*[)）]", text)
    issues = []
    for label, nums in [("图", fig_defs), ("表", table_defs), ("公式", eq_defs)]:
        duplicates = sorted(n for n in set(nums) if nums.count(n) > 1)
        for n in duplicates:
            issues.append(_todo(f"{label}编号", "medium", n, f"{label}{n} 可能重复", "检查定义与引用是否混淆"))
        issues.extend(_sequence_issues(label, nums))
    return {"figures": fig_defs, "tables": table_defs, "equations": eq_defs, "issues": issues}


def check_bibliography_references(path: str) -> dict:
    text = read_document(path)["text"]
    citations = [int(x) for x in re.findall(r"(?:参考文献|文献)?\s*\[(\d+)\]", text)]
    bib = [int(x) for x in re.findall(r"^\[(\d+)\]\s+", text, flags=re.M)]
    issues = []
    for c in sorted(set(citations)):
        if c not in bib:
            issues.append(_todo("参考文献", "high", f"[{c}]", f"文中引用 [{c}] 未出现在参考文献列表", "补充或修正文献条目"))
    for b in sorted(set(bib)):
        if b not in citations:
            issues.append(_todo("参考文献", "low", f"[{b}]", f"参考文献 [{b}] 可能未被正文引用", "确认是否保留"))
    return {"citations": citations, "bibliography": bib, "issues": issues}


def generate_todo_list(*reports: dict) -> list[dict]:
    todos: list[dict] = []
    for report in reports:
        todos.extend(report.get("issues", []))
    return todos


def run_thesis_check(path: str, output_dir: str | Path) -> dict:
    structure = check_thesis_structure(path)
    figures = check_figure_table_references(path)
    bibliography = check_bibliography_references(path)
    todos = generate_todo_list(structure, figures, bibliography)
    report = {"path": path, "structure": structure, "figures_tables_equations": figures, "bibliography": bibliography, "todos": todos}
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "thesis_check_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "thesis_check_report.md").write_text(thesis_report_markdown(report), encoding="utf-8")
    return report


def thesis_report_markdown(report: dict) -> str:
    lines = ["# Thesis Finishing Check Report", "", f"Source: `{report['path']}`", ""]
    lines += ["## Chapter Structure", f"- Missing sections: {', '.join(report['structure']['missing_sections']) or 'None'}", ""]
    lines += [
        "## Figures / Tables / Equations",
        f"- Figures: {report['figures_tables_equations']['figures']}",
        f"- Tables: {report['figures_tables_equations']['tables']}",
        f"- Equations: {report['figures_tables_equations']['equations']}",
        "",
    ]
    lines += [
        "## Bibliography",
        f"- Citations: {report['bibliography']['citations']}",
        f"- Bibliography entries: {report['bibliography']['bibliography']}",
        "",
    ]
    lines.append("## Todo List")
    for i, todo in enumerate(report["todos"], start=1):
        lines.append(f"{i}. [{todo['severity']}] {todo['issue_type']} - {todo['description']} ({todo['location']})")
    return "\n".join(lines)


def _numbers(pattern: str, text: str) -> list[str]:
    return re.findall(pattern, text)


def _sequence_issues(label: str, nums: list[str]) -> list[dict]:
    ints = []
    for n in nums:
        try:
            ints.append(int(n.split(".")[-1]))
        except ValueError:
            pass
    issues = []
    uniq = sorted(set(ints))
    for a, b in zip(uniq, uniq[1:]):
        if b != a + 1:
            issues.append(_todo(f"{label}编号", "medium", f"{a}-{b}", f"{label}编号可能跳号：{a} -> {b}", "检查编号连续性"))
    return issues


def _todo(issue_type: str, severity: str, location: str, description: str, suggestion: str) -> dict:
    return {
        "issue_type": issue_type,
        "severity": severity,
        "location": location,
        "description": description,
        "suggestion": suggestion,
        "requires_human_confirmation": True,
    }
