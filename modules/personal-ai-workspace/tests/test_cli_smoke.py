import subprocess
import sys


def test_cli_help():
    result = subprocess.run([sys.executable, "-m", "src.cli", "--help"], text=True, capture_output=True, timeout=30)
    assert result.returncode == 0
    assert "ingest" in result.stdout

