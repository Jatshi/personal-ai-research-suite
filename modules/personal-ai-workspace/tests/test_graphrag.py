from __future__ import annotations

from src.config.config_loader import load_config
from src.graphrag.graph_index import NetworkXGraphIndex
from src.graphrag.graph_retriever import GraphRAGRetriever
from src.storage.sqlite_store import SQLiteStore


def test_networkx_graph_index_and_retrieval(tmp_path):
    config = load_config()
    config["app"]["data_dir"] = str(tmp_path / "data")
    store = SQLiteStore(config)
    store.add_chunks(
        [
            {"chunk_id": "c1", "doc_id": "d1", "collection": "research", "file_name": "paper.md", "section_title": "", "page_number": None, "paragraph_number": 1, "text": "GraphRAG connects retrieval concepts through evidence relationships.", "embedding": [], "metadata": {}},
            {"chunk_id": "c2", "doc_id": "d2", "collection": "research", "file_name": "notes.md", "section_title": "", "page_number": None, "paragraph_number": 1, "text": "GraphRAG improves multi hop retrieval for research evidence.", "embedding": [], "metadata": {}},
        ]
    )
    report = NetworkXGraphIndex(store).build(store.get_chunks("research"), "research")
    results = GraphRAGRetriever(store).search("GraphRAG evidence", "research", 5)
    assert report["node_count"] > 0
    assert results and results[0]["chunk_id"] in {"c1", "c2"}
