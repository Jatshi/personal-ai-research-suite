from src.config.config_loader import load_config
from src.reading.article_extractor import import_reading_path
from src.reading.reading_tools import reading_search


def test_reading_import_and_search():
    config = load_config()
    import_reading_path(config, "./examples/sample_reading", "reading_test")
    results = reading_search(config, "Agent safety", "reading_test")
    assert results

