from __future__ import annotations

import subprocess
import sys
import json


def test_cli_help_smoke() -> None:
    res = subprocess.run([sys.executable, "-m", "src.cli", "--help"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "ingest" in res.stdout


def test_doctor_llm_smoke() -> None:
    res = subprocess.run([sys.executable, "-m", "src.cli", "doctor-llm"], capture_output=True, text=True)
    assert res.returncode == 0
    payload = json.loads(res.stdout)
    assert payload["success"] is True
    assert payload["llm_backend"] == "mock"


def test_doctor_config_smoke() -> None:
    res = subprocess.run([sys.executable, "-m", "src.cli", "doctor-config"], capture_output=True, text=True)
    assert res.returncode == 0
    payload = json.loads(res.stdout)
    assert payload["success"] is True
    assert payload["workspace_dir"]
