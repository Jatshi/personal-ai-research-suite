import json
import subprocess
import sys

from fastapi.testclient import TestClient

from src.api.fastapi_app import app


def test_cli_delete_doc_defaults_to_dry_run():
    result = subprocess.run(
        [sys.executable, "-m", "src.cli", "delete-doc", "--doc-id", "missing-doc"],
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["success"] is True
    assert payload["executed"] is False
    assert payload["requires_confirmation"] is True


def test_api_delete_doc_defaults_to_dry_run():
    client = TestClient(app)
    res = client.post("/kb/delete", json={"doc_id": "missing-doc"})
    assert res.status_code == 200
    payload = res.json()
    assert payload["success"] is True
    assert payload["executed"] is False
    assert payload["requires_confirmation"] is True
