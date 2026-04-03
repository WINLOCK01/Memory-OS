---
name: ingest-pipeline
description: >
  USE THIS SKILL whenever the user asks to add a new file type, data source, ingestion method,
  parser, or document loader to MemoryOS. Also trigger when they mention PDF, URL, text, voice,
  CSV, DOCX, Markdown, or any new format they want to ingest. If the user says "add support for X"
  where X is a data format, THIS is the skill to follow.
---

# Ingest Pipeline Skill — Adding New Ingestion Sources to MemoryOS

## Overview

MemoryOS ingests documents through a pipeline: **Parse → Chunk → Embed → Store**.
All parsers live in `backend/ingestion/parsers.py`, endpoints in `backend/api/main.py`,
and storage goes through `backend/core/vector_store.py`.

---

## Step-by-Step: Adding a New Ingestion Source

### 1. Create the Parser Function

Open `backend/ingestion/parsers.py` and add a new parser function.

Every parser MUST return a `list[str]` of text chunks ready for embedding.

```python
# backend/ingestion/parsers.py

import csv
from io import StringIO
from datetime import datetime

def parse_csv(file_content: bytes, filename: str) -> list[dict]:
    """Parse CSV file into chunks with metadata."""
    text = file_content.decode("utf-8")
    reader = csv.DictReader(StringIO(text))
    
    chunks = []
    for i, row in enumerate(reader):
        # Convert each row to a readable text block
        row_text = " | ".join(f"{k}: {v}" for k, v in row.items())
        chunks.append({
            "text": row_text,
            "metadata": {
                "source_type": "csv",
                "source": filename,
                "ingested_at": datetime.utcnow().isoformat(),
                "chunk_index": i,
            }
        })
    return chunks
```

### 2. Add Chunking (if needed)

For large documents, use the shared chunker. Standard chunk size is **500 characters** with **50 character overlap**:

```python
def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks
```

### 3. Register the FastAPI Endpoint

Open `backend/api/main.py` and add an upload endpoint:

```python
# backend/api/main.py

from fastapi import UploadFile, File, HTTPException
from backend.ingestion.parsers import parse_csv
from backend.core.vector_store import vector_store

@app.post("/ingest/csv")
async def ingest_csv(file: UploadFile = File(...)):
    """Ingest a CSV file into MemoryOS."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a .csv")
    
    content = await file.read()
    try:
        chunks = parse_csv(content, file.filename)
        vector_store.add_chunks(
            texts=[c["text"] for c in chunks],
            metadatas=[c["metadata"] for c in chunks],
        )
        return {
            "status": "success",
            "chunks_stored": len(chunks),
            "source": file.filename,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")
```

### 4. Add the Pydantic Response Model

In `backend/models/schemas.py`:

```python
from pydantic import BaseModel

class IngestResponse(BaseModel):
    status: str
    chunks_stored: int
    source: str
```

### 5. Store Chunks in ChromaDB

The `vector_store.add_chunks()` method handles embedding + storage. It:
1. Generates embeddings using `all-MiniLM-L6-v2`
2. Creates unique IDs: `f"{source_type}_{source}_{chunk_index}"`
3. Upserts into the ChromaDB collection

---

## Metadata Schema (MANDATORY)

Every chunk stored MUST have this metadata:

```python
{
    "source_type": "pdf" | "url" | "note" | "voice" | "csv" | "<new_type>",
    "source": "<filename or URL>",
    "ingested_at": "<ISO 8601 datetime>",
    "chunk_index": <int>,  # 0-indexed position within the source
}
```

**Do not omit any field.** The RAG agent and query filters depend on all four.

---

## Existing Parsers Reference

| Format | Function | Endpoint |
|--------|----------|----------|
| PDF | `parse_pdf()` | `POST /ingest/pdf` |
| URL | `parse_url()` | `POST /ingest/url` |
| Text/Note | `parse_note()` | `POST /ingest/note` |

---

## Error Handling Checklist

- [ ] Validate file extension / content type before parsing
- [ ] Catch and re-raise parsing errors as `HTTPException(500)`
- [ ] Log the number of chunks created for debugging
- [ ] Handle empty files gracefully (return 400, not 500)
- [ ] Handle encoding issues (try UTF-8, fall back to latin-1)

---

## Testing New Parsers

```python
# tests/test_parsers.py
import pytest
from backend.ingestion.parsers import parse_csv

def test_parse_csv_basic():
    content = b"name,age\nAlice,30\nBob,25"
    chunks = parse_csv(content, "test.csv")
    assert len(chunks) == 2
    assert chunks[0]["metadata"]["source_type"] == "csv"
    assert chunks[0]["metadata"]["chunk_index"] == 0
    assert "Alice" in chunks[0]["text"]
```

---

## Common Pitfalls

1. **Forgetting metadata fields** — the query system will break silently
2. **Not chunking large documents** — ChromaDB has embedding size limits
3. **Hardcoding file paths** — always use `UploadFile` or URL strings
4. **Missing CORS** — new endpoints inherit CORS from `main.py`, but verify
