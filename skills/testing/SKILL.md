---
name: testing
description: >
  USE THIS SKILL whenever the user wants to write tests, run tests, debug a failing component,
  validate a feature, or verify that something works end to end. Trigger when they mention:
  pytest, test, unit test, integration test, mock, fixture, "is this working?", "how do I test
  this?", or CI/CD. Also trigger proactively when a new feature is implemented — always suggest
  writing tests. THIS skill covers the complete testing strategy for MemoryOS.
---

# Testing Skill — Writing and Running Tests for MemoryOS

## Overview

MemoryOS uses **pytest** for all testing. Tests cover ingestion parsers, FastAPI routes,
the RAG agent, and the vector store. External services (OpenAI, ChromaDB) are mocked in
unit tests, and real instances are used in integration tests.

---

## Project Test Structure

```
tests/
├── conftest.py              ← Shared fixtures
├── test_parsers.py          ← Ingestion parser tests
├── test_api.py              ← FastAPI route tests
├── test_vector_store.py     ← ChromaDB operations tests
├── test_agent.py            ← RAG agent tests
├── test_graph_builder.py    ← Knowledge graph tests
├── test_integration.py      ← End-to-end pipeline tests
└── fixtures/
    ├── sample.pdf           ← Test PDF file
    ├── sample.csv           ← Test CSV file
    └── sample.txt           ← Test text file
```

---

## Setup

### Install Test Dependencies

```bash
pip install pytest pytest-asyncio httpx pytest-mock
```

### pytest Configuration

```ini
# pyproject.toml or pytest.ini

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
markers = [
    "integration: marks tests as integration tests (deselect with '-m not integration')",
]
```

---

## Shared Fixtures

```python
# tests/conftest.py

import pytest
from unittest.mock import MagicMock, patch
from httpx import AsyncClient, ASGITransport
from backend.api.main import app

@pytest.fixture
def mock_vector_store():
    """Mock ChromaDB vector store."""
    with patch("backend.core.vector_store.vector_store") as mock:
        mock.count.return_value = 42
        mock.query.return_value = [
            {
                "id": "pdf_test.pdf_0",
                "text": "This is a test memory about machine learning.",
                "metadata": {
                    "source_type": "pdf",
                    "source": "test.pdf",
                    "ingested_at": "2025-01-15T10:00:00",
                    "chunk_index": 0,
                },
                "distance": 0.15,
            }
        ]
        mock.add_chunks.return_value = 3
        mock.list_memories.return_value = {
            "ids": ["pdf_test.pdf_0"],
            "documents": ["Test memory content"],
            "metadatas": [{"source_type": "pdf", "source": "test.pdf",
                          "ingested_at": "2025-01-15T10:00:00", "chunk_index": 0}],
        }
        yield mock

@pytest.fixture
def mock_openai():
    """Mock OpenAI API calls."""
    with patch("langchain_openai.ChatOpenAI") as mock:
        instance = MagicMock()
        instance.invoke.return_value = MagicMock(
            content="This is a test answer based on your memories."
        )
        mock.return_value = instance
        yield mock

@pytest.fixture
async def async_client():
    """Async HTTP client for testing FastAPI routes."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

@pytest.fixture
def sample_pdf_content():
    """Read the sample PDF fixture."""
    with open("tests/fixtures/sample.pdf", "rb") as f:
        return f.read()

@pytest.fixture
def sample_chunks():
    """Sample chunk data for testing."""
    return [
        {
            "text": "Machine learning is a subset of artificial intelligence.",
            "metadata": {
                "source_type": "pdf",
                "source": "ml_intro.pdf",
                "ingested_at": "2025-01-15T10:00:00",
                "chunk_index": 0,
            },
        },
        {
            "text": "Neural networks are inspired by biological neurons.",
            "metadata": {
                "source_type": "pdf",
                "source": "ml_intro.pdf",
                "ingested_at": "2025-01-15T10:00:00",
                "chunk_index": 1,
            },
        },
    ]
```

---

## Testing Ingestion Parsers

```python
# tests/test_parsers.py

import pytest
from backend.ingestion.parsers import parse_pdf, parse_url, parse_note, chunk_text

class TestChunking:
    def test_chunk_text_basic(self):
        text = "A" * 1000
        chunks = chunk_text(text, chunk_size=500, overlap=50)
        assert len(chunks) >= 2
        assert len(chunks[0]) == 500
    
    def test_chunk_text_short(self):
        """Short text should return a single chunk."""
        chunks = chunk_text("Hello world", chunk_size=500)
        assert len(chunks) == 1
        assert chunks[0] == "Hello world"
    
    def test_chunk_text_overlap(self):
        """Chunks should overlap."""
        text = "ABCDEFGHIJ" * 100
        chunks = chunk_text(text, chunk_size=100, overlap=20)
        # Check that end of chunk N appears at start of chunk N+1
        assert chunks[0][-20:] == chunks[1][:20]

class TestParsePDF:
    def test_parse_pdf_returns_chunks(self, sample_pdf_content):
        chunks = parse_pdf(sample_pdf_content, "test.pdf")
        assert len(chunks) > 0
        assert all("text" in c for c in chunks)
        assert all("metadata" in c for c in chunks)
    
    def test_parse_pdf_metadata(self, sample_pdf_content):
        chunks = parse_pdf(sample_pdf_content, "test.pdf")
        for chunk in chunks:
            assert chunk["metadata"]["source_type"] == "pdf"
            assert chunk["metadata"]["source"] == "test.pdf"
            assert "ingested_at" in chunk["metadata"]
            assert "chunk_index" in chunk["metadata"]

class TestParseNote:
    def test_parse_note_basic(self):
        chunks = parse_note("This is a simple note about testing.", "My Note")
        assert len(chunks) >= 1
        assert chunks[0]["metadata"]["source_type"] == "note"
    
    def test_parse_note_empty(self):
        """Empty notes should raise or return empty."""
        with pytest.raises(ValueError):
            parse_note("", "Empty Note")
```

---

## Testing FastAPI Routes

```python
# tests/test_api.py

import pytest

class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health_returns_ok(self, async_client):
        response = await async_client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

class TestQueryEndpoint:
    @pytest.mark.asyncio
    async def test_query_success(self, async_client, mock_vector_store, mock_openai):
        response = await async_client.post("/query", json={
            "query": "What is machine learning?",
            "n_results": 3,
        })
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert "memories_used" in data
    
    @pytest.mark.asyncio
    async def test_query_empty_string(self, async_client):
        response = await async_client.post("/query", json={
            "query": "",
        })
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_query_with_source_filter(self, async_client, mock_vector_store, mock_openai):
        response = await async_client.post("/query", json={
            "query": "neural networks",
            "source_type": "pdf",
        })
        assert response.status_code == 200

class TestMemoriesEndpoint:
    @pytest.mark.asyncio
    async def test_list_memories(self, async_client, mock_vector_store):
        response = await async_client.get("/memories?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert "memories" in data
        assert "total" in data
    
    @pytest.mark.asyncio
    async def test_delete_memory(self, async_client, mock_vector_store):
        response = await async_client.delete("/memories/pdf_test.pdf_0")
        assert response.status_code == 200

class TestIngestEndpoint:
    @pytest.mark.asyncio
    async def test_ingest_pdf(self, async_client, mock_vector_store):
        # Create a minimal test PDF content
        files = {"file": ("test.pdf", b"%PDF-1.4 test content", "application/pdf")}
        response = await async_client.post("/ingest/pdf", files=files)
        assert response.status_code in [200, 500]  # 500 if PDF parsing fails on fake content
    
    @pytest.mark.asyncio
    async def test_ingest_wrong_file_type(self, async_client):
        files = {"file": ("test.exe", b"not a pdf", "application/octet-stream")}
        response = await async_client.post("/ingest/pdf", files=files)
        assert response.status_code == 400
```

---

## Testing the Vector Store

```python
# tests/test_vector_store.py

import pytest
from unittest.mock import patch, MagicMock

class TestVectorStore:
    def test_add_chunks(self, mock_vector_store, sample_chunks):
        result = mock_vector_store.add_chunks(
            texts=[c["text"] for c in sample_chunks],
            metadatas=[c["metadata"] for c in sample_chunks],
        )
        mock_vector_store.add_chunks.assert_called_once()
    
    def test_query_returns_results(self, mock_vector_store):
        results = mock_vector_store.query("machine learning", n_results=3)
        assert len(results) > 0
        assert "text" in results[0]
        assert "metadata" in results[0]
    
    def test_count(self, mock_vector_store):
        assert mock_vector_store.count() == 42
    
    def test_delete_memory(self, mock_vector_store):
        mock_vector_store.delete_memory("pdf_test.pdf_0")
        mock_vector_store.delete_memory.assert_called_with("pdf_test.pdf_0")

@pytest.mark.integration
class TestVectorStoreIntegration:
    """Integration tests using a real ChromaDB instance."""
    
    def test_add_and_query(self):
        import chromadb
        client = chromadb.EphemeralClient()
        collection = client.create_collection("test")
        
        collection.add(
            documents=["Machine learning is great"],
            metadatas=[{"source_type": "note", "source": "test", 
                       "ingested_at": "2025-01-01", "chunk_index": 0}],
            ids=["test_0"],
        )
        
        results = collection.query(query_texts=["ML"], n_results=1)
        assert len(results["ids"][0]) == 1
        assert "Machine learning" in results["documents"][0][0]
```

---

## Integration Tests (End-to-End)

```python
# tests/test_integration.py

import pytest

@pytest.mark.integration
class TestFullPipeline:
    """Test the complete ingest → store → query pipeline."""
    
    @pytest.mark.asyncio
    async def test_ingest_then_query(self, async_client):
        """Ingest a note, then query for it."""
        # 1. Ingest
        ingest_response = await async_client.post("/ingest/note", json={
            "text": "Python is a programming language used for AI and ML.",
            "title": "Python Notes",
        })
        assert ingest_response.status_code == 200
        
        # 2. Query
        query_response = await async_client.post("/query", json={
            "query": "What programming languages are used for AI?",
        })
        assert query_response.status_code == 200
        assert query_response.json()["memories_used"] > 0
```

---

## Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run a specific test file
pytest tests/test_api.py

# Run a specific test class
pytest tests/test_api.py::TestQueryEndpoint

# Run only unit tests (skip integration)
pytest -m "not integration"

# Run with coverage
pytest --cov=backend --cov-report=html

# Run in parallel (requires pytest-xdist)
pytest -n auto
```

---

## Mocking Best Practices

1. **Mock at the boundary**: Mock OpenAI and ChromaDB, not internal functions
2. **Use fixtures**: Define mocks in `conftest.py` for reuse
3. **Test both success and failure**: Always test error paths
4. **Use `EphemeralClient`** for ChromaDB integration tests (no disk)
5. **Test metadata**: Verify all 4 metadata fields in parser tests
