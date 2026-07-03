$ErrorActionPreference = "Stop"

python -m src.cli doctor-config
python -m src.cli doctor-llm
pytest -q
