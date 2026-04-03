from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from backend.models.schemas import (
    IngestURLRequest, IngestTextRequest,
    QueryRequest, QueryResponse, IngestResponse
)
from backend.ingestion.parsers import parse_pdf, parse_url, parse_text
from backend.core.vector_store import vector_store
from backend.agents.memory_agent import memory_agent
from backend.agents.graph_builder import build_knowledge_graph
from collections import Counter

app = FastAPI(
    title="MemoryOS API",
    description="Personal Second Brain — RAG-powered memory system",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Ingestion Routes ────────────────────────────────────────────────────────

@app.post("/ingest/pdf", response_model=IngestResponse)
async def ingest_pdf(file: UploadFile = File(...)):
    """Upload and ingest a PDF file into memory."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(400, "Only PDF files supported")
    content = await file.read()
    chunks, metadata = parse_pdf(content, file.filename)
    vector_store.add_chunks(chunks, metadata)
    return IngestResponse(
        message="PDF ingested successfully",
        chunks_stored=len(chunks),
        source=file.filename
    )


@app.post("/ingest/url", response_model=IngestResponse)
async def ingest_url(req: IngestURLRequest):
    """Scrape and ingest a webpage URL."""
    try:
        chunks, metadata = parse_url(req.url)
    except Exception as e:
        raise HTTPException(400, f"Failed to scrape URL: {str(e)}")
    vector_store.add_chunks(chunks, metadata)
    return IngestResponse(
        message="URL ingested successfully",
        chunks_stored=len(chunks),
        source=req.url
    )


@app.post("/ingest/text", response_model=IngestResponse)
async def ingest_text(req: IngestTextRequest):
    """Ingest a plain text note."""
    chunks, metadata = parse_text(req.content, req.title)
    vector_store.add_chunks(chunks, metadata)
    return IngestResponse(
        message="Note ingested successfully",
        chunks_stored=len(chunks),
        source=req.title
    )


# ─── Query Routes ────────────────────────────────────────────────────────────

@app.post("/query", response_model=QueryResponse)
async def query_memory(req: QueryRequest):
    """Ask a question and get an answer from your memories."""
    filters = {"source_type": req.source_type} if req.source_type else None
    result = memory_agent.query(req.question, filters=filters)
    return QueryResponse(
        answer=result["answer"],
        sources=result["sources"],
        memories_used=result["memories_used"]
    )


@app.get("/graph")
async def get_knowledge_graph():
    """Get the knowledge graph for visualization."""
    return build_knowledge_graph()


# ─── Stats Routes ────────────────────────────────────────────────────────────

@app.get("/stats")
async def get_stats():
    """Get memory statistics."""
    metadata = vector_store.get_all_metadata()
    type_counts = Counter(m.get("source_type", "unknown") for m in metadata)
    return {
        "total_chunks": vector_store.count(),
        "total_sources": len(set(m.get("source", "") for m in metadata)),
        "by_type": dict(type_counts)
    }


@app.get("/health")
async def health():
    return {"status": "ok", "memories": vector_store.count()}
