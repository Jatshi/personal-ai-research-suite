from __future__ import annotations

import subprocess
import sys


def test_cli_smoke_test_command() -> None:
    res = subprocess.run([sys.executable, "-m", "src.cli", "smoke-test"], capture_output=True, text=True)
    assert res.returncode == 0
    assert '"success": true' in res.stdout

