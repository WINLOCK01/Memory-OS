import pytest
from backend.ingestion.parsers import chunk_text, parse_text

def test_chunk_text():
    text = "word " * 600
    chunks = chunk_text(text, chunk_size=512, overlap=64)
    assert len(chunks) > 1
    assert len(chunks[0].split()) <= 512

def test_parse_text():
    content = "This is a test note for MemoryOS. " * 50
    chunks, metadata = parse_text(content, title="Testing Note")
    assert len(chunks) >= 1
    assert metadata[0]["source_type"] == "note"
    assert "timestamp" in metadata[0]
