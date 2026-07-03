import json
import subprocess
import sys


def test_doctor_mcp_cli():
    result = subprocess.run([sys.executable, "-m", "src.cli", "doctor-mcp"], text=True, capture_output=True, timeout=30)
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["success"] is True
    assert payload["tool_count"] >= 3
    assert "search_documents" in payload["tools"]
