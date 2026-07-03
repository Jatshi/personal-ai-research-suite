from src.reporting.weekly_report import generate_weekly_report


def test_weekly_report_markdown():
    text = generate_weekly_report([{"done": True, "text": "完成 RAG"}], [])
    assert "# 周报" in text
    assert "完成 RAG" in text

