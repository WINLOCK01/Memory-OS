---
name: vector-store
description: >
  USE THIS SKILL whenever the user mentions ChromaDB, FAISS, embeddings, vector search, similarity
  search, memory storage, memory not found, empty results, dimension mismatch, persistence,
  or wants to manage/list/delete stored memories. Also trigger if they want to change the
  embedding model or switch vector databases. If something is wrong with memory retrieval,
  START HERE.
---

# Vector Store Skill — Working with ChromaDB in MemoryOS

## Overview

The vector store is the heart of MemoryOS. It lives in `backend/core/vector_store.py` and
provides a singleton ChromaDB client that all other modules use. The default embedding model
is `all-MiniLM-L6-v2` via sentence-transformers, using cosine similarity.

---

## Core Vector Store Class

```python
# backend/core/vector_store.py

import chromadb
from chromadb.utils import embedding_functions
from backend.core.config import settings

class VectorStore:
    """Singleton ChromaDB vector store for MemoryOS."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_store()
        return cls._instance
    
    def _init_store(self):
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR  # default: ./data/chroma
        )
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        self.collection = self.client.get_or_create_collection(
            name="memoryos",
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )
    
    def add_chunks(self, texts: list[str], metadatas: list[dict]):
        """Add text chunks with metadata to the store."""
        ids = [
            f"{m['source_type']}_{m['source']}_{m['chunk_index']}"
            for m in metadatas
        ]
        self.collection.upsert(
            documents=texts,
            metadatas=metadatas,
            ids=ids,
        )
        return len(texts)
    
    def query(self, query_text: str, n_results: int = 5, where: dict = None):
        """Semantic search with optional metadata filters."""
        kwargs = {
            "query_texts": [query_text],
            "n_results": n_results,
        }
        if where:
            kwargs["where"] = where
        
        results = self.collection.query(**kwargs)
        return self._format_results(results)
    
    def _format_results(self, results):
        """Convert ChromaDB results to a clean list of dicts."""
        formatted = []
        for i in range(len(results["ids"][0])):
            formatted.append({
                "id": results["ids"][0][i],
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i] if results.get("distances") else None,
            })
        return formatted
    
    def list_memories(self, limit: int = 100, source_type: str = None):
        """List stored memories with optional filtering."""
        kwargs = {"limit": limit}
        if source_type:
            kwargs["where"] = {"source_type": source_type}
        return self.collection.get(**kwargs)
    
    def delete_memory(self, memory_id: str):
        """Delete a specific memory by ID."""
        self.collection.delete(ids=[memory_id])
    
    def delete_by_source(self, source: str):
        """Delete all chunks from a specific source."""
        self.collection.delete(where={"source": source})
    
    def count(self) -> int:
        """Return total number of stored chunks."""
        return self.collection.count()


# Module-level singleton
vector_store = VectorStore()
```

---

## Common Operations

### Adding Chunks

```python
from backend.core.vector_store import vector_store

vector_store.add_chunks(
    texts=["chunk 1 text", "chunk 2 text"],
    metadatas=[
        {"source_type": "pdf", "source": "paper.pdf", "ingested_at": "2025-01-15T10:00:00", "chunk_index": 0},
        {"source_type": "pdf", "source": "paper.pdf", "ingested_at": "2025-01-15T10:00:00", "chunk_index": 1},
    ],
)
```

### Semantic Search with Filters

```python
# Basic search
results = vector_store.query("machine learning techniques", n_results=5)

# Search only PDFs
results = vector_store.query(
    "machine learning",
    n_results=5,
    where={"source_type": "pdf"},
)

# Search with compound filters
results = vector_store.query(
    "neural networks",
    where={
        "$and": [
            {"source_type": "pdf"},
            {"ingested_at": {"$gte": "2025-01-01"}},
        ]
    },
)
```

### Listing and Deleting

```python
# List all memories
all_memories = vector_store.list_memories(limit=50)

# List only URL-sourced memories
url_memories = vector_store.list_memories(source_type="url")

# Delete a specific memory
vector_store.delete_memory("pdf_paper.pdf_0")

# Delete all chunks from a source
vector_store.delete_by_source("paper.pdf")

# Get total count
total = vector_store.count()
```

---

## Changing the Embedding Model

To switch from `all-MiniLM-L6-v2` to another model:

```python
# In vector_store.py, change the embedding function:

# Option 1: Larger sentence-transformers model
self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-mpnet-base-v2"  # 768 dims, better quality
)

# Option 2: OpenAI embeddings
self.embedding_fn = embedding_functions.OpenAIEmbeddingFunction(
    api_key=settings.OPENAI_API_KEY,
    model_name="text-embedding-3-small",
)
```

> **⚠️ WARNING**: Changing the embedding model requires re-ingesting ALL data.
> Old embeddings are incompatible with new models (different dimensions).
> Delete the collection first: `self.client.delete_collection("memoryos")`

---

## Switching to FAISS

If you need to switch from ChromaDB to FAISS:

```python
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

class FAISSVectorStore:
    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.dimension = 384  # MiniLM output dimension
        self.index = faiss.IndexFlatIP(self.dimension)  # cosine via normalized vectors
        self.documents = []
        self.metadatas = []
    
    def add_chunks(self, texts, metadatas):
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        self.index.add(np.array(embeddings, dtype="float32"))
        self.documents.extend(texts)
        self.metadatas.extend(metadatas)
    
    def query(self, query_text, n_results=5):
        query_emb = self.model.encode([query_text], normalize_embeddings=True)
        distances, indices = self.index.search(np.array(query_emb, dtype="float32"), n_results)
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.documents):
                results.append({
                    "text": self.documents[idx],
                    "metadata": self.metadatas[idx],
                    "distance": float(distances[0][i]),
                })
        return results
```

---

## Debugging Common Issues

### Empty Results
```python
# Check if collection has data
print(f"Total chunks: {vector_store.count()}")

# Check if query is too specific
results = vector_store.query("test", n_results=1)
print(results)

# Check collection metadata
print(vector_store.collection.metadata)
```

### Dimension Mismatch
- Happens when embedding model was changed without re-ingesting
- Fix: delete collection and re-ingest all data

### Persistence Issues
- Verify `CHROMA_PERSIST_DIR` in `.env` points to a writable directory
- Ensure the directory exists: `mkdir -p data/chroma`
- Check Docker volume mounts if running in container

### Duplicate Entries
- The `upsert` method prevents true duplicates (same ID)
- If seeing duplicates, check that IDs are generated consistently
- IDs follow format: `{source_type}_{source}_{chunk_index}`

---

## Configuration

In `.env`:
```
CHROMA_PERSIST_DIR=./data/chroma
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

In `backend/core/config.py`:
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    CHROMA_PERSIST_DIR: str = "./data/chroma"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    
    class Config:
        env_file = ".env"
```
