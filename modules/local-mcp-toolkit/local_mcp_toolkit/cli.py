from __future__ import annotations

import sys
import importlib.util
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    cli_path = root / "src" / "cli.py"
    if not cli_path.exists():
        raise RuntimeError("Cannot find src/cli.py. Run this console script from an editable/source checkout.")
    sys.path.insert(0, str(root))
    spec = importlib.util.spec_from_file_location("local_mcp_toolkit_src_cli", cli_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load CLI module from {cli_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.main()


if __name__ == "__main__":
    main()
