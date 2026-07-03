from __future__ import annotations

import subprocess
import sys


def test_cli_help_smoke() -> None:
    result = subprocess.run([sys.executable, "-m", "src.cli", "--help"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "scan-files" in result.stdout

