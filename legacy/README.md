# 🧬 MemoryOS — Personal Second Brain

An agentic AI system that ingests everything you consume, builds a living knowledge graph, and lets you query your own memory conversationally.

## Architecture

```
memoryos/
├── backend/
│   ├── api/          # FastAPI routes
│   ├── core/         # Config, DB connections
│   ├── ingestion/    # PDF, URL, text, voice parsers
│   ├── agents/       # LangChain agentic workflows
│   └── models/       # Pydantic schemas
├── frontend/         # React dashboard
├── docker-compose.yml
└── requirements.txt
```

## Tech Stack

| Layer | Tech |
|-------|------|
| Frontend | React, Recharts, D3 (knowledge graph) |
| Backend | FastAPI, Python 3.11 |
| LLM | OpenAI GPT-4o / local Ollama |
| Embeddings | HuggingFace sentence-transformers |
| Vector DB | ChromaDB |
| Agent Framework | LangChain + LlamaIndex |
| Containerization | Docker + docker-compose |

## Setup

```bash
# 1. Clone and install
pip install -r requirements.txt

# 2. Set environment variables
cp .env.example .env
# Add your OPENAI_API_KEY

# 3. Run with Docker
docker-compose up

# 4. Open dashboard
http://localhost:3000
```

## Features (Week-by-Week)

- **Week 1**: Ingestion pipeline — PDF, URL, text → ChromaDB
- **Week 2**: RAG agent + conversational query
- **Week 3**: Knowledge graph + React dashboard
- **Week 4**: Voice memos, polish, deploy
