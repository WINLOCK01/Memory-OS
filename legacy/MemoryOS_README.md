**🧬 MemoryOS**  ·  Personal Second Brain — Full Build README

**🧬 MemoryOS**

Personal Second Brain

Full 4-Week Build README  ·  by Devraj


# **Project Overview**
MemoryOS is an agentic AI system that ingests everything you consume — PDFs, web pages, notes, and voice memos — builds a living knowledge graph, and lets you query your own memory conversationally using a RAG-powered LLM agent.
## **Core Concept**
You produce and consume enormous amounts of knowledge every day. MemoryOS captures it all, semantically indexes it, and surfaces it when you need it — becoming a literal extension of your memory.
## **Tech Stack**

|**Layer**|**Technology**|**Purpose**|
| :- | :- | :- |
|Frontend|React + Recharts + D3|Dashboard, chat UI, knowledge graph|
|Backend|FastAPI + Python 3.11|REST API, ingestion orchestration|
|LLM|GPT-4o / Ollama|Conversational reasoning|
|Embeddings|sentence-transformers|Semantic vector encoding|
|Vector DB|ChromaDB + FAISS|Persistent memory storage|
|Agents|LangChain + LlamaIndex|Agentic RAG workflows|
|Graph|NetworkX|Knowledge graph construction|
|DevOps|Docker + docker-compose|Containerized deployment|

# **Architecture**
The system is built in three horizontal layers that work together as a pipeline:

- Ingestion Layer — parses raw inputs (PDF, URL, text, voice) into chunks and embeddings stored in ChromaDB
- Memory & Reasoning Layer — LangChain agents perform semantic retrieval and LLM synthesis with source citation
- Presentation Layer — React dashboard with chat interface, knowledge graph visualisation, and memory timeline

**Directory layout:** memoryos/backend/ (api/, core/, ingestion/, agents/, models/)  frontend/src/
# **4-Week Roadmap at a Glance**

|**Week**|**Theme**|**Key Deliverable**|**Color**|
| :- | :- | :- | :- |
|**Week 1**|Ingestion Pipeline|PDF + URL + text → ChromaDB|●|
|**Week 2**|RAG Agent + Chat UI|Conversational memory queries|●|
|**Week 3**|Knowledge Graph + Dashboard|React UI with D3 graph viz|●|
|**Week 4**|Voice, Polish & Deploy|Production-ready Docker app|●|



|**WEEK<br>1**|<p>**Ingestion Pipeline**</p><p>Days 1–7  ·  Foundation</p>|
| :-: | :- |

## **Goal**
Build the core data ingestion pipeline — the foundation of the entire system. By end of week 1 you should be able to drop any PDF, paste any URL, or type a note and have it semantically chunked, embedded, and stored in ChromaDB ready for retrieval.
### **Tasks**

|**#**|**Task**|**Details**|**Status**|
| :-: | :- | :- | :-: |
|**1**|**Project scaffold**|Create folder structure, requirements.txt, .env, docker-compose skeleton|✓ Done|
|**2**|**PDF parser**|PyPDF2 extraction → regex clean → chunk\_text() with sliding window overlap|✓ Done|
|**3**|**URL scraper**|BeautifulSoup scraper stripping nav/footer → paragraph extraction + title|✓ Done|
|**4**|**Text/note ingestion**|Raw text endpoint + chunking pipeline identical to PDF path|✓ Done|
|**5**|**ChromaDB vector store**|Persistent client + SentenceTransformer embeddings + cosine similarity search|✓ Done|
|**6**|**FastAPI endpoints**|POST /ingest/pdf, /ingest/url, /ingest/text with Pydantic schemas + CORS|✓ Done|
|**7**|**GET /stats + /health**|Memory count, source breakdown by type, health check endpoint|✓ Done|

### **Files Produced**
- backend/ingestion/parsers.py — PDF, URL, text parsers with chunking
- backend/core/vector\_store.py — ChromaDB wrapper with semantic search
- backend/core/config.py — Pydantic settings from .env
- backend/models/schemas.py — Pydantic request/response models
- backend/api/main.py — FastAPI app with ingestion + stats routes
- requirements.txt, .env.example, docker-compose.yml

### **How to Test Week 1**
uvicorn backend.api.main:app --reload

- Visit http://localhost:8000/docs — Swagger UI auto-generated
- POST /ingest/url with { "url": "https://arxiv.org/abs/1706.03762" }
- GET /stats — should show chunks stored and source breakdown


### **Key Design Decisions**
- Chunk size 512 words with 64-word overlap — balances context and retrieval precision
- all-MiniLM-L6-v2 embedding model — fast, good quality, runs locally without API cost
- ChromaDB with cosine similarity — persistent on disk, no separate DB process needed



|**WEEK<br>2**|<p>**RAG Agent + Chat UI**</p><p>Days 8–14  ·  Intelligence</p>|
| :-: | :- |

## **Goal**
Wire the LangChain RAG agent to the vector store and build the conversational interface. Users should be able to type any question and receive a grounded answer with citations pointing back to their own ingested sources.
### **Tasks**

|**#**|**Task**|**Details**|**Status**|
| :-: | :- | :- | :-: |
|**1**|**LangChain RAG chain**|Retrieval chain: embed query → top-6 semantic search → format\_context() → LLM|→ Build|
|**2**|**System prompt**|Citation-aware prompt instructing model to reference source names explicitly|→ Build|
|**3**|**POST /query endpoint**|Accept question + optional source\_type filter, return answer + sources array|→ Build|
|**4**|**Chat UI component**|React chat bubbles with user/assistant roles, source tags, loading spinner|→ Build|
|**5**|**Source filtering**|Allow user to filter queries to only pdf | url | note sources|→ Build|
|**6**|**Topic summariser**|summarize\_topic() endpoint — retrieve top-10 chunks and produce synthesis|→ Build|
|**7**|**Error handling**|Graceful fallback when no memories match; token limit guard on context string|→ Build|

### **New Files**
- backend/agents/memory\_agent.py — LangChain RAG chain with MemoryAgent class
- frontend/src/components/QueryChat.jsx — Chat interface component
- backend/api/main.py — add POST /query and GET /summarize/{topic}

### **RAG Flow Diagram**
User question  →  embed(query)  →  chroma.search(top\_k=6)  →  format\_context()  →  GPT-4o  →  answer + sources
### **Environment Variables Needed**
- OPENAI\_API\_KEY — set in .env for GPT-4o access
- LLM\_MODEL=gpt-4o — or swap for ollama/mistral for fully local operation
- MAX\_CHUNK\_SIZE=512, CHUNK\_OVERLAP=64 — tune for your content type


### **Key Design Decisions**
- Temperature 0.3 — low enough for factual grounding, enough for natural language
- top\_k=6 retrieval — empirically good balance between context richness and token cost
- Source deduplication — set() on source field prevents duplicate citations in response



|**WEEK<br>3**|<p>**Knowledge Graph + Dashboard**</p><p>Days 15–21  ·  Visualisation</p>|
| :-: | :- |

## **Goal**
Build the full React dashboard — the face of MemoryOS. Five pages: Dashboard overview, Ingest panel, Query chat, Memories list, and Knowledge Graph. The graph must render all ingested sources as interactive nodes connected by semantic relationships.
### **Tasks**

|**#**|**Task**|**Details**|**Status**|
| :-: | :- | :- | :-: |
|**1**|**Knowledge graph builder**|NetworkX graph from ChromaDB metadata; nodes=sources, edges=type clusters|✓ Done|
|**2**|**GET /graph endpoint**|Serialise NetworkX graph to JSON {nodes, links, stats} for D3 rendering|✓ Done|
|**3**|**React app scaffold**|Shell layout: topbar + sidebar nav + main content area with routing state|✓ Done|
|**4**|**Dashboard page**|3-stat cards (chunks, sources, docs) + graph preview + recent memories list|✓ Done|
|**5**|**Ingest page**|Tab switcher: URL input / PDF drag-drop / note textarea with title field|✓ Done|
|**6**|**Query / chat page**|Full chat UI with message history, source tags, thinking animation|✓ Done|
|**7**|**Memories page**|Full list of all ingested sources with type badge, chunk count, date|✓ Done|
|**8**|**Graph page**|SVG force graph with colour-coded nodes by type (pdf/url/note)|✓ Done|

### **Week 3 Upgrade: D3 Force Graph**
Replace the static SVG with a D3 force-directed simulation for the Graph page. Install d3 and implement:

- d3.forceSimulation with forceLink, forceManyBody, forceCenter
- Node radius proportional to chunk count — bigger nodes = richer sources
- Hover tooltip showing source title, type, ingestion date, chunk count
- Click node to auto-populate the Query input with that source name
- Color legend: green=PDF, blue=URL, pink=note

### **Recharts Stats Dashboard**
- Bar chart — chunks per source (top 10)
- Pie chart — breakdown by source type
- Timeline — ingestion activity over last 30 days


### **Key Design Decisions**
- Dark terminal aesthetic (Syne + JetBrains Mono) — memorable, fits ML/AI persona
- Demo mode fallback — UI works without backend for recruiter demos
- Single JSX file — portable, easy to drop into any React project or share as artifact



|**WEEK<br>4**|<p>**Voice, Polish & Deploy**</p><p>Days 22–28  ·  Production</p>|
| :-: | :- |

## **Goal**
Add voice memo ingestion using OpenAI Whisper, implement time-based memory filtering, polish the UI with animations and error states, write tests, and package everything as a production-ready Docker application.
### **Tasks**

|**#**|**Task**|**Details**|**Status**|
| :-: | :- | :- | :-: |
|**1**|**Whisper voice ingestion**|Upload .mp3/.wav → Whisper transcription → text pipeline → ChromaDB|→ Build|
|**2**|**POST /ingest/voice**|FastAPI endpoint accepting audio files, returns transcript + chunks stored|→ Build|
|**3**|**Time-based filtering**|Query filter by date range: { ingested\_after: '2025-03-01' } in ChromaDB where clause|→ Build|
|**4**|**Memory timeline view**|React calendar heatmap showing ingestion frequency by day (like GitHub contrib)|→ Build|
|**5**|**Dockerfile**|Multi-stage build: Python 3.11-slim + requirements install + uvicorn CMD|→ Build|
|**6**|**docker-compose prod**|backend + frontend + volume mounts + env injection for production deploy|→ Build|
|**7**|**Test suite**|pytest for parsers, vector store, agent; React Testing Library for components|→ Build|
|**8**|**README + demo GIF**|Record Loom walkthrough, add architecture diagram, update GitHub README|→ Build|

### **Voice Ingestion Pipeline**
Audio file  →  whisper.load\_audio()  →  model.transcribe()  →  parse\_text(transcript)  →  ChromaDB

- Model: whisper-base for fast local transcription (upgradeable to large-v3)
- Metadata tags include source\_type: voice and original filename for citation
- Accepts .mp3, .wav, .m4a, .webm via FastAPI UploadFile

### **Dockerfile (Backend)**
FROM python:3.11-slim  →  COPY requirements.txt  →  RUN pip install  →  COPY .  →  CMD uvicorn

- Multi-stage build keeps image under 1.2GB
- Chroma persist directory mounted as Docker volume — memories survive restarts
- Health check: GET /health returns {status: ok, memories: N}

### **Deployment Options**
- Local: docker-compose up — backend :8000, frontend :3000
- Cloud: Railway.app or Render.com free tier — push to GitHub, auto-deploy
- Self-hosted: Any VPS with Docker — nginx reverse proxy for custom domain


### **Final Polish Checklist**
- Mobile-responsive layout for the React dashboard
- Toast notifications for all async operations with error states
- Loading skeletons instead of blank states during API calls
- Keyboard shortcut: Enter to submit query, Escape to clear input
- Export memory: GET /export returns all chunks as JSON backup


# **Setup & Running Locally**
## **Prerequisites**
- Python 3.11+
- Node.js 20+
- Docker + Docker Compose
- OpenAI API key (or Ollama for local LLM)

## **Quick Start**
git clone https://github.com/devraj/memoryos && cd memoryos

cp .env.example .env   # add OPENAI\_API\_KEY

pip install -r requirements.txt

uvicorn backend.api.main:app --reload   # backend on :8000

cd frontend && npm install && npm start  # frontend on :3000
## **Docker (Recommended)**
docker-compose up --build

Both services start together. Chroma data is persisted in ./data/chroma.
## **API Reference**

|**Method**|**Endpoint**|**Description**|**Body**|
| :- | :- | :- | :- |
|POST|/ingest/pdf|Upload PDF file|multipart/form-data|
|POST|/ingest/url|Ingest webpage|{ url: string }|
|POST|/ingest/text|Save a note|{ content, title }|
|POST|/ingest/voice|Transcribe audio|multipart/form-data|
|POST|/query|Query memory|{ question, source\_type? }|
|GET|/graph|Knowledge graph JSON|—|
|GET|/stats|Memory statistics|—|
|GET|/health|Health check|—|

# **Why This Project Stands Out**
MemoryOS is not a tutorial project — it is a complete, original product that demonstrates every skill on the resume simultaneously:

- RAG + LangChain agents — production-grade retrieval-augmented generation
- Vector databases — ChromaDB + FAISS with real embedding pipelines
- NLP pipelines — chunking, tokenisation, semantic search, context formatting
- Data engineering — ETL parsers for PDF, HTML, audio with metadata management
- Backend engineering — FastAPI with async endpoints, Pydantic validation, CORS
- Frontend — React dashboard with D3 graph visualisation and Recharts analytics
- DevOps — Docker containerisation with multi-service docker-compose
- MLOps — configurable models, persistent vector store, modular agent design

Every component was built from scratch. No tutorial followed. No boilerplate cloned. This is the kind of system-level thinking that separates ML engineers who can deploy real AI products from those who can only run notebooks.


**GitHub:** github.com/devraj/memoryos    ·    **Contact:** devraj.099909@gmail.com
MemoryOS Build Guide  ·  Devraj  ·  Page 
