$ErrorActionPreference = "Stop"
python -m compileall src tests
python -m pytest -q
python -m src.cli doctor-config
python -m src.cli doctor-mcp
python -m src.cli doctor-rag
python -m src.cli smoke-test
