from src.chunking.chunker import chunk_text


def test_chunking_stable_chunk_id():
    doc = {"doc_id": "d1", "collection": "c", "file_name": "a.md"}
    chunks = chunk_text("# Title\n\nhello world", doc, 20, 0)
    assert chunks[0]["chunk_id"]
    assert chunks[0]["doc_id"] == "d1"

