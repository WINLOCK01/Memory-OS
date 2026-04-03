---
name: fastapi-routes
description: >
  USE THIS SKILL whenever the user wants to add, modify, or debug a FastAPI route or endpoint.
  Trigger when they mention: API, endpoint, route, REST, request, response, CORS, Pydantic model,
  HTTP error, 404, 500, "expose X via API," or "connect frontend to backend." If the user needs
  to wire a new feature to the API layer, THIS skill applies.
---

# FastAPI Routes Skill — Adding New Endpoints to MemoryOS

## Overview

All API routes live in `backend/api/main.py`. The app uses FastAPI with Uvicorn, CORS middleware
for frontend access, and Pydantic models from `backend/models/schemas.py` for request/response
validation.

---

## Project Conventions

### Route Naming
- Use **lowercase with hyphens**: `/ingest/pdf`, `/query`, `/memories/list`
- Group by feature: `/ingest/*`, `/graph/*`, `/memories/*`
- Use HTTP verbs correctly: `GET` for reads, `POST` for creates, `DELETE` for deletes

### File Responsibilities
| File | Purpose |
|------|---------|
| `backend/api/main.py` | All route definitions |
| `backend/models/schemas.py` | Pydantic request/response models |
| `backend/core/config.py` | Settings (reads `.env`) |
| `backend/core/vector_store.py` | ChromaDB access |
| `backend/agents/memory_agent.py` | RAG agent |
| `backend/agents/graph_builder.py` | Knowledge graph |
| `backend/ingestion/parsers.py` | Document parsers |

---

## Step-by-Step: Adding a New Route

### 1. Define Pydantic Models

```python
# backend/models/schemas.py

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# Request model
class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    n_results: int = Field(default=5, ge=1, le=50)
    source_type: Optional[str] = None

# Response model
class QueryResponse(BaseModel):
    answer: str
    sources: list[str]
    memories_used: int
    query_time_ms: float

class MemoryItem(BaseModel):
    id: str
    text: str
    source: str
    source_type: str
    ingested_at: str

class MemoryListResponse(BaseModel):
    memories: list[MemoryItem]
    total: int

class IngestResponse(BaseModel):
    status: str
    chunks_stored: int
    source: str

class ErrorResponse(BaseModel):
    detail: str
```

### 2. Create the Route

```python
# backend/api/main.py

from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from backend.models.schemas import (
    QueryRequest, QueryResponse,
    MemoryListResponse, MemoryItem,
    IngestResponse,
)
from backend.core.vector_store import vector_store
from backend.agents.memory_agent import query_agent
import time

app = FastAPI(
    title="MemoryOS API",
    description="Personal second-brain API",
    version="1.0.0",
)

# CORS — allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/query", response_model=QueryResponse)
async def query_memories(request: QueryRequest):
    """Query the RAG agent with a natural language question."""
    start = time.time()
    try:
        result = query_agent(
            query=request.query,
            n_results=request.n_results,
            source_type=request.source_type,
        )
        elapsed = (time.time() - start) * 1000
        return QueryResponse(
            answer=result["answer"],
            sources=result["sources"],
            memories_used=result["memories_used"],
            query_time_ms=round(elapsed, 2),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

@app.get("/memories", response_model=MemoryListResponse)
async def list_memories(
    limit: int = Query(default=50, ge=1, le=500),
    source_type: str = Query(default=None),
):
    """List stored memories with optional filtering."""
    memories = vector_store.list_memories(limit=limit, source_type=source_type)
    items = [
        MemoryItem(
            id=memories["ids"][i],
            text=memories["documents"][i][:200],
            source=memories["metadatas"][i]["source"],
            source_type=memories["metadatas"][i]["source_type"],
            ingested_at=memories["metadatas"][i]["ingested_at"],
        )
        for i in range(len(memories["ids"]))
    ]
    return MemoryListResponse(memories=items, total=vector_store.count())

@app.delete("/memories/{memory_id}")
async def delete_memory(memory_id: str):
    """Delete a specific memory by ID."""
    try:
        vector_store.delete_memory(memory_id)
        return {"status": "deleted", "id": memory_id}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Memory not found: {str(e)}")

@app.get("/stats")
async def get_stats():
    """Get memory statistics."""
    total = vector_store.count()
    return {
        "total_memories": total,
        "status": "healthy",
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "memoryos"}
```

### 3. Wire to Modules

When adding a new feature route, follow this wiring pattern:

```python
# 1. Import the module
from backend.agents.graph_builder import KnowledgeGraphBuilder

# 2. Create the route that calls the module
@app.get("/graph")
async def get_graph(limit: int = 100):
    memories = vector_store.list_memories(limit=limit)
    builder = KnowledgeGraphBuilder()
    # ... build and return
    return builder.export_d3_json()
```

---

## CORS Configuration

The default CORS setup allows requests from common frontend dev servers:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",   # React dev server (CRA)
        "http://localhost:5173",   # Vite dev server
        "http://localhost:4173",   # Vite preview
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Adding a new origin**: Just append to the `allow_origins` list.
**Production**: Replace with your actual domain(s).

---

## Error Handling Pattern

```python
from fastapi import HTTPException

# 400 — Bad request (invalid input)
raise HTTPException(status_code=400, detail="Query cannot be empty")

# 404 — Not found
raise HTTPException(status_code=404, detail=f"Memory {memory_id} not found")

# 500 — Internal error (catch-all)
try:
    result = some_operation()
except Exception as e:
    raise HTTPException(status_code=500, detail=f"Operation failed: {str(e)}")
```

**Convention**: Always include a descriptive `detail` message.

---

## Running the API

```bash
# Development
uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## Testing Routes

```python
# tests/test_api.py
import pytest
from httpx import AsyncClient, ASGITransport
from backend.api.main import app

@pytest.mark.asyncio
async def test_health_check():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

@pytest.mark.asyncio
async def test_query_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/query", json={
            "query": "What is machine learning?",
            "n_results": 3,
        })
        assert response.status_code == 200
        assert "answer" in response.json()
```
