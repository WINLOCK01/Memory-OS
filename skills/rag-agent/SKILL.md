---
name: rag-agent
description: >
  USE THIS SKILL whenever the user wants to modify, improve, or extend the LangChain RAG agent
  in MemoryOS. Trigger when they mention: answer quality, retrieval, system prompt, chain,
  reasoning, agent tools, memory retrieval strategy, streaming, structured output, LangChain,
  or "make the agent smarter/better." If the user talks about how MemoryOS answers questions,
  THIS skill applies.
---

# RAG Agent Skill — Extending the MemoryOS LangChain Agent

## Overview

The RAG agent lives in `backend/agents/memory_agent.py`. It uses LangChain's `ChatOpenAI` (gpt-4o)
with a retrieval chain that queries ChromaDB for relevant memories, then generates an answer
with source citations.

---

## Architecture

```
User Query
    │
    ▼
┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
│ /query API   │ ──► │ memory_agent.py  │ ──► │ vector_store │
│ (FastAPI)    │     │ (LangChain RAG)  │     │ (ChromaDB)   │
└──────────────┘     └──────────────────┘     └──────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │ gpt-4o LLM   │
                     │ (ChatOpenAI)  │
                     └──────────────┘
```

---

## Step-by-Step: Modifying the RAG Agent

### 1. Changing the System Prompt

The system prompt defines the agent's personality and behavior. Edit it in `memory_agent.py`:

```python
# backend/agents/memory_agent.py

SYSTEM_PROMPT = """You are MemoryOS, a personal knowledge assistant.
You have access to the user's stored memories including PDFs, web pages, and notes.

When answering:
1. ALWAYS cite which source(s) you used
2. If you don't find relevant memories, say so honestly
3. Synthesize information across multiple sources when possible
4. Use the user's own language and terminology when available

Context from memory:
{context}

Chat history:
{chat_history}
"""
```

### 2. Changing Retrieval Parameters

Modify how many results are fetched and how they're filtered:

```python
from backend.core.vector_store import vector_store

def retrieve_memories(query: str, n_results: int = 5, source_type: str = None):
    """Retrieve relevant memories from ChromaDB."""
    where_filter = None
    if source_type:
        where_filter = {"source_type": source_type}
    
    results = vector_store.query(
        query_text=query,
        n_results=n_results,
        where=where_filter,
    )
    return results
```

**Tuning tips:**
- `n_results=3` for precise, focused answers
- `n_results=10` for comprehensive answers across many sources
- Add `where` filters to scope retrieval (e.g., only PDFs, only recent)

### 3. Building the LangChain Chain

```python
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser

def build_rag_chain():
    """Build the RAG chain with retrieval and generation."""
    llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
    
    prompt = ChatPromptTemplate.from_template(SYSTEM_PROMPT)
    
    chain = (
        {
            "context": lambda x: retrieve_memories(x["query"]),
            "chat_history": lambda x: x.get("chat_history", ""),
            "query": lambda x: x["query"],
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    return chain
```

### 4. Adding New Tools to the Agent

To make the agent capable of actions beyond retrieval:

```python
from langchain.agents import tool

@tool
def search_by_date(date_str: str) -> str:
    """Search memories ingested on a specific date."""
    results = vector_store.query(
        query_text="",
        where={"ingested_at": {"$gte": date_str}},
        n_results=10,
    )
    return format_results(results)

@tool
def summarize_topic(topic: str) -> str:
    """Summarize all memories related to a topic."""
    results = vector_store.query(query_text=topic, n_results=20)
    # Use LLM to summarize the retrieved chunks
    summary_prompt = f"Summarize these memories about '{topic}':\n{results}"
    return llm.invoke(summary_prompt).content
```

### 5. Streaming Responses

For real-time streaming to the frontend:

```python
from langchain.callbacks import StreamingStdOutCallbackHandler

async def stream_query(query: str):
    """Stream the RAG response token by token."""
    llm = ChatOpenAI(
        model="gpt-4o",
        streaming=True,
        callbacks=[StreamingStdOutCallbackHandler()],
    )
    
    chain = build_rag_chain_with_llm(llm)
    
    async for chunk in chain.astream({"query": query}):
        yield chunk
```

### 6. Returning Structured Output

The agent should return answer + sources + memories:

```python
from pydantic import BaseModel

class AgentResponse(BaseModel):
    answer: str
    sources: list[str]
    memories_used: int
    confidence: float

def query_with_sources(query: str) -> AgentResponse:
    """Query the agent and return structured output."""
    memories = retrieve_memories(query)
    
    # Build context from memories
    context = "\n---\n".join([m["text"] for m in memories])
    sources = list(set([m["metadata"]["source"] for m in memories]))
    
    # Get LLM answer
    answer = rag_chain.invoke({"query": query, "context": context})
    
    return AgentResponse(
        answer=answer,
        sources=sources,
        memories_used=len(memories),
        confidence=calculate_confidence(memories),
    )
```

---

## Key Files

| File | Purpose |
|------|---------|
| `backend/agents/memory_agent.py` | RAG agent logic, chains, tools |
| `backend/core/vector_store.py` | ChromaDB retrieval interface |
| `backend/api/main.py` | `/query` endpoint |
| `backend/models/schemas.py` | `QueryRequest`, `QueryResponse` models |

---

## Error Handling

- **No results found**: Return a friendly message, don't hallucinate
- **LLM timeout**: Wrap in try/except, return partial results if available
- **Token limit exceeded**: Truncate context to fit within gpt-4o's window
- **Rate limiting**: Implement exponential backoff on OpenAI calls

---

## Common Improvements

1. **Re-ranking**: After retrieval, re-rank results using a cross-encoder
2. **Hybrid search**: Combine semantic search with keyword (BM25) search
3. **Query expansion**: Use LLM to generate alternative queries
4. **Memory-aware chat**: Maintain conversation history for multi-turn
5. **Confidence scoring**: Use embedding distance as a confidence proxy
