---
name: memory-query
description: >
  USE THIS SKILL whenever the user wants to improve querying, add filters, do time-based
  retrieval, summarize topics, add query history, or build suggested questions. Trigger when
  they mention: filter, date range, "memories from last week", topic summary, query suggestions,
  "find memories about X", search refinement, or smart search. If the user wants better
  search capabilities, THIS skill applies.
---

# Memory Query Skill — Advanced Querying and Filtering in MemoryOS

## Overview

Memory querying goes beyond basic semantic search. This skill covers adding filter parameters
to the `/query` endpoint, ChromaDB `where` clauses, time-based retrieval, topic summarization,
query history, and AI-powered query suggestions.

---

## Step-by-Step: Adding Filters to the Query Endpoint

### 1. Extend the Query Request Model

```python
# backend/models/schemas.py

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    n_results: int = Field(default=5, ge=1, le=50)
    source_type: Optional[str] = Field(
        default=None,
        description="Filter by source type: pdf, url, note, voice"
    )
    date_from: Optional[str] = Field(
        default=None,
        description="ISO date string — only return memories after this date"
    )
    date_to: Optional[str] = Field(
        default=None,
        description="ISO date string — only return memories before this date"
    )
    source: Optional[str] = Field(
        default=None,
        description="Filter by specific source filename or URL"
    )
```

### 2. Build ChromaDB Where Clauses

```python
# backend/core/query_builder.py

def build_where_clause(
    source_type: str = None,
    date_from: str = None,
    date_to: str = None,
    source: str = None,
) -> dict | None:
    """Build a ChromaDB where clause from filter parameters."""
    conditions = []
    
    if source_type:
        conditions.append({"source_type": source_type})
    
    if source:
        conditions.append({"source": source})
    
    if date_from:
        conditions.append({"ingested_at": {"$gte": date_from}})
    
    if date_to:
        conditions.append({"ingested_at": {"$lte": date_to}})
    
    if not conditions:
        return None
    elif len(conditions) == 1:
        return conditions[0]
    else:
        return {"$and": conditions}
```

### 3. Update the Query Route

```python
# backend/api/main.py

from backend.core.query_builder import build_where_clause

@app.post("/query")
async def query_memories(request: QueryRequest):
    """Query memories with optional filters."""
    where = build_where_clause(
        source_type=request.source_type,
        date_from=request.date_from,
        date_to=request.date_to,
        source=request.source,
    )
    
    results = vector_store.query(
        query_text=request.query,
        n_results=request.n_results,
        where=where,
    )
    
    # Pass to RAG agent for answer generation
    answer = generate_answer(request.query, results)
    
    return {
        "answer": answer,
        "sources": [r["metadata"]["source"] for r in results],
        "memories_used": len(results),
        "filters_applied": {
            "source_type": request.source_type,
            "date_from": request.date_from,
            "date_to": request.date_to,
        },
    }
```

---

## Time-Based Retrieval

### Recent Memories

```python
from datetime import datetime, timedelta

def get_recent_memories(hours: int = 24, n_results: int = 10):
    """Get memories ingested in the last N hours."""
    cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
    
    return vector_store.query(
        query_text="",  # Empty query = return all matching filter
        n_results=n_results,
        where={"ingested_at": {"$gte": cutoff}},
    )

@app.get("/memories/recent")
async def recent_memories(hours: int = 24):
    """Get recently ingested memories."""
    memories = get_recent_memories(hours=hours)
    return {"memories": memories, "time_window_hours": hours}
```

### Memories by Date Range

```python
@app.get("/memories/by-date")
async def memories_by_date(
    date_from: str,  # ISO format: 2025-01-01
    date_to: str,    # ISO format: 2025-01-31
    limit: int = 50,
):
    """Get memories within a date range."""
    where = {
        "$and": [
            {"ingested_at": {"$gte": date_from}},
            {"ingested_at": {"$lte": date_to}},
        ]
    }
    return vector_store.list_memories_with_filter(where=where, limit=limit)
```

---

## Topic Summarization

```python
# backend/agents/memory_agent.py

from langchain_openai import ChatOpenAI

def summarize_topic(topic: str, n_results: int = 20) -> dict:
    """Retrieve and summarize all memories about a topic."""
    # 1. Retrieve relevant memories
    results = vector_store.query(query_text=topic, n_results=n_results)
    
    if not results:
        return {"summary": f"No memories found about '{topic}'.", "sources": []}
    
    # 2. Build context
    context = "\n---\n".join([
        f"[{r['metadata']['source']}]: {r['text']}"
        for r in results
    ])
    
    # 3. Generate summary with LLM
    llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
    prompt = f"""Summarize the following memories about "{topic}". 
Provide a concise, structured summary highlighting key points.

Memories:
{context}

Summary:"""
    
    summary = llm.invoke(prompt).content
    sources = list(set([r["metadata"]["source"] for r in results]))
    
    return {
        "topic": topic,
        "summary": summary,
        "sources": sources,
        "memories_analyzed": len(results),
    }

# Route
@app.get("/summarize/{topic}")
async def summarize(topic: str):
    return summarize_topic(topic)
```

---

## Query History

```python
# backend/core/query_history.py

from datetime import datetime
from collections import deque

class QueryHistory:
    """Track recent queries for suggestions and analytics."""
    
    def __init__(self, max_size: int = 100):
        self.history = deque(maxlen=max_size)
    
    def add(self, query: str, results_count: int):
        self.history.append({
            "query": query,
            "results_count": results_count,
            "timestamp": datetime.utcnow().isoformat(),
        })
    
    def get_recent(self, n: int = 10) -> list[dict]:
        return list(self.history)[-n:]
    
    def get_popular_queries(self, n: int = 5) -> list[str]:
        """Return most frequent queries."""
        from collections import Counter
        counter = Counter(item["query"] for item in self.history)
        return [q for q, _ in counter.most_common(n)]

query_history = QueryHistory()

# In main.py — add to query endpoint:
# query_history.add(request.query, len(results))

@app.get("/query/history")
async def get_query_history(limit: int = 10):
    return {"history": query_history.get_recent(limit)}
```

---

## Query Suggestions

```python
# backend/agents/memory_agent.py

def generate_suggestions(recent_queries: list[str], n: int = 5) -> list[str]:
    """Generate smart query suggestions based on history and stored memories."""
    llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
    
    # Get a sample of stored topics
    sample_memories = vector_store.list_memories(limit=20)
    topics = [m["source"] for m in sample_memories["metadatas"]] if sample_memories["metadatas"] else []
    
    prompt = f"""Based on these recent searches and available topics, suggest {n} new 
interesting questions the user might want to ask their memory system.

Recent searches: {recent_queries}
Available topics from stored memories: {topics}

Return only the questions, one per line."""
    
    response = llm.invoke(prompt).content
    suggestions = [line.strip() for line in response.strip().split("\n") if line.strip()]
    return suggestions[:n]

@app.get("/query/suggestions")
async def get_suggestions():
    recent = query_history.get_recent(5)
    recent_queries = [q["query"] for q in recent]
    suggestions = generate_suggestions(recent_queries)
    return {"suggestions": suggestions}
```

---

## ChromaDB Filter Reference

| Filter | Syntax | Example |
|--------|--------|---------|
| Equals | `{"field": "value"}` | `{"source_type": "pdf"}` |
| Not equals | `{"field": {"$ne": "value"}}` | `{"source_type": {"$ne": "note"}}` |
| Greater than | `{"field": {"$gt": "value"}}` | `{"ingested_at": {"$gt": "2025-01-01"}}` |
| Greater or equal | `{"field": {"$gte": "value"}}` | `{"chunk_index": {"$gte": 5}}` |
| Less than | `{"field": {"$lt": "value"}}` | `{"ingested_at": {"$lt": "2025-12-31"}}` |
| In list | `{"field": {"$in": [...]}}` | `{"source_type": {"$in": ["pdf", "url"]}}` |
| AND | `{"$and": [{...}, {...}]}` | See date range example above |
| OR | `{"$or": [{...}, {...}]}` | Filter by pdf OR url |

---

## Error Handling

- **No results for filter**: Return empty list with a helpful message, don't error
- **Invalid date format**: Validate ISO format before passing to ChromaDB
- **Too broad query**: Warn if n_results is very high (> 50)
- **Empty query with no filters**: Return most recent memories as default behavior
