# MemoryOS Skills — Walkthrough

## What Was Done
Created **9 Claude Code Skills** under `d:\Projects\files\skills\`, each with a `SKILL.md` containing YAML frontmatter with pushy descriptions, step-by-step instructions, code examples, and error handling guidance.

## Skills Summary

| # | Skill | Trigger Examples | Path |
|---|-------|-----------------|------|
| 1 | **ingest-pipeline** | "add CSV support", "new file type", "ingest DOCX" | [SKILL.md](file:///d:/Projects/files/skills/ingest-pipeline/SKILL.md) |
| 2 | **rag-agent** | "improve answers", "change retrieval", "add reasoning", "streaming" | [SKILL.md](file:///d:/Projects/files/skills/rag-agent/SKILL.md) |
| 3 | **vector-store** | "ChromaDB", "embeddings", "memory not found", "FAISS", "empty results" | [SKILL.md](file:///d:/Projects/files/skills/vector-store/SKILL.md) |
| 4 | **knowledge-graph** | "graph", "connections", "topic clusters", "centrality", "D3" | [SKILL.md](file:///d:/Projects/files/skills/knowledge-graph/SKILL.md) |
| 5 | **frontend-dashboard** | "UI", "new page", "dashboard", "visualization", "CSS", "React" | [SKILL.md](file:///d:/Projects/files/skills/frontend-dashboard/SKILL.md) |
| 6 | **fastapi-routes** | "API endpoint", "new route", "CORS", "Pydantic model", "HTTP error" | [SKILL.md](file:///d:/Projects/files/skills/fastapi-routes/SKILL.md) |
| 7 | **docker-deploy** | "Docker", "deploy", "docker-compose", "Railway", "Render", ".env" | [SKILL.md](file:///d:/Projects/files/skills/docker-deploy/SKILL.md) |
| 8 | **memory-query** | "filter", "date range", "topic summary", "suggestions", "smart search" | [SKILL.md](file:///d:/Projects/files/skills/memory-query/SKILL.md) |
| 9 | **testing** | "pytest", "write tests", "mock", "integration test", "is this working?" | [SKILL.md](file:///d:/Projects/files/skills/testing/SKILL.md) |

## Conventions Encoded

All skills reference the standard MemoryOS conventions:
- **Metadata schema**: `source_type`, `source`, `ingested_at`, `chunk_index`
- **Embedding model**: `all-MiniLM-L6-v2`
- **LLM**: `gpt-4o` via `ChatOpenAI`
- **Vector DB**: ChromaDB (persistent, cosine)
- **Backend**: FastAPI + Uvicorn
- **Frontend**: React with CSS variables (`--accent`, `--surface`, `--font-mono`)

## File Tree
```
skills/
├── ingest-pipeline/SKILL.md
├── rag-agent/SKILL.md
├── vector-store/SKILL.md
├── knowledge-graph/SKILL.md
├── frontend-dashboard/SKILL.md
├── fastapi-routes/SKILL.md
├── docker-deploy/SKILL.md
├── memory-query/SKILL.md
└── testing/SKILL.md
```
