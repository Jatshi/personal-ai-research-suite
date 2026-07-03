import json
import subprocess
import sys


def test_doctor_rag_cli():
    result = subprocess.run([sys.executable, "-m", "src.cli", "doctor-rag"], text=True, capture_output=True, timeout=30)
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["success"] is True
    assert payload["search_ok"] is True
    assert payload["ask_ok"] is True
    assert payload["result_count"] >= 1
