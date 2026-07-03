$ErrorActionPreference = "Stop"
python -m compileall src app tests
python -m pytest -q
python -m src.cli doctor-config
python -m src.cli doctor-llm
