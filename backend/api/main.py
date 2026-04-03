from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from backend.models.schemas import (
    IngestURLRequest, IngestTextRequest,
    QueryRequest, QueryResponse, IngestResponse
)
from backend.ingestion.parsers import parse_pdf, parse_url, parse_text, parse_voice
from backend.core.vector_store import vector_store
from collections import Counter
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("memoryos.api")

app = FastAPI(
    title="MemoryOS API",
    description="Personal Second Brain — RAG-powered memory system",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Lazy imports for Week 2/3 modules ──────────────────────────────────────

_memory_agent = None
_build_knowledge_graph = None


def _get_memory_agent():
    global _memory_agent
    if _memory_agent is None:
        try:
            from backend.agents.memory_agent import memory_agent
            _memory_agent = memory_agent
        except ImportError as e:
            raise HTTPException(
                503, f"RAG agent not available — install Week 2 deps first: {e}"
            )
    return _memory_agent


def _get_graph_builder():
    global _build_knowledge_graph
    if _build_knowledge_graph is None:
        try:
            from backend.agents.graph_builder import build_knowledge_graph
            _build_knowledge_graph = build_knowledge_graph
        except ImportError as e:
            raise HTTPException(
                503, f"Graph builder not available — install Week 3 deps first: {e}"
            )
    return _build_knowledge_graph


# ─── Ingestion Routes ────────────────────────────────────────────────────────

@app.post("/ingest/pdf", response_model=IngestResponse)
async def ingest_pdf(file: UploadFile = File(...), memory_block: str = Form("Default")):
    """Upload and ingest a PDF file into memory."""
    logger.info("Ingesting PDF file: %s into memory_block: %s", file.filename, memory_block)
    if not file.filename.endswith(".pdf"):
        raise HTTPException(400, "Only PDF files supported")
    content = await file.read()
    chunks, metadata = parse_pdf(content, file.filename)
    if not chunks:
        raise HTTPException(422, "No extractable text found in PDF. The file may be scanned/image-only or password-protected.")
    for m in metadata:
        m["memory_block"] = memory_block
    vector_store.add_chunks(chunks, metadata)
    return IngestResponse(
        message="PDF ingested successfully",
        chunks_stored=len(chunks),
        source=file.filename
    )


@app.post("/ingest/url", response_model=IngestResponse)
async def ingest_url(req: IngestURLRequest):
    """Scrape and ingest a webpage URL."""
    logger.info("Ingesting URL: %s into memory_block: %s", req.url, req.memory_block)
    try:
        chunks, metadata = parse_url(req.url)
        if not chunks:
            raise HTTPException(422, "No text content found at that URL. The page may require JavaScript or be behind a login.")
        for m in metadata:
            m["memory_block"] = req.memory_block
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
    logger.info("Ingesting Text Note: %s into memory_block: %s", req.title, req.memory_block)
    chunks, metadata = parse_text(req.content, req.title)
    if not chunks:
        raise HTTPException(422, "Note content is too short to store. Please provide more text.")
    for m in metadata:
        m["memory_block"] = req.memory_block
    vector_store.add_chunks(chunks, metadata)
    return IngestResponse(
        message="Note ingested successfully",
        chunks_stored=len(chunks),
        source=req.title
    )

@app.post("/ingest/voice", response_model=IngestResponse)
async def ingest_voice(file: UploadFile = File(...), memory_block: str = Form("Default")):
    """Upload and ingest an audio file using Whisper."""
    logger.info("Ingesting Voice Memo: %s into memory_block: %s", file.filename, memory_block)
    allowed = [".mp3", ".wav", ".m4a", ".webm"]
    if not any(file.filename.lower().endswith(ext) for ext in allowed):
        raise HTTPException(400, f"Allowed audio formats: {', '.join(allowed)}")
    
    content = await file.read()
    chunks, metadata = parse_voice(content, file.filename)
    if not chunks:
        raise HTTPException(422, "No speech was detected in the audio file. Ensure the file contains clear spoken audio.")
    for m in metadata:
        m["memory_block"] = memory_block
    vector_store.add_chunks(chunks, metadata)
    return IngestResponse(
        message="Voice memo ingested successfully",
        chunks_stored=len(chunks),
        source=file.filename
    )


# ─── Query Routes (Week 2) ──────────────────────────────────────────────────

@app.post("/query", response_model=QueryResponse)
async def query_memory(req: QueryRequest):
    """Ask a question and get an answer from your memories."""
    logger.info("Query received: '%s', Model: %s, Block Filter: %s", req.question, req.model, req.memory_block)
    agent = _get_memory_agent()
    
    filters = []
    if req.source_type:
        filters.append({"source_type": req.source_type})
    if req.start_timestamp:
        filters.append({"timestamp": {"$gte": req.start_timestamp}})
    if req.end_timestamp:
        filters.append({"timestamp": {"$lte": req.end_timestamp}})
    if req.memory_block:
        filters.append({"memory_block": req.memory_block})
        
    final_filter = None
    if len(filters) == 1:
        final_filter = filters[0]
    elif len(filters) > 1:
        final_filter = {"$and": filters}

    try:
        result = agent.query(req.question, model=req.model, filters=final_filter)
        return QueryResponse(
            answer=result["answer"],
            sources=result["sources"],
            memories_used=result["memories_used"]
        )
    except Exception as e:
        logger.error("Query execution failed: %s", str(e), exc_info=True)
        raise HTTPException(500, detail=f"Query execution failed: {str(e)}")

@app.get("/summarize/{topic}")
async def summarize_topic(topic: str):
    """Generate a comprehensive summary of a topic from memory."""
    agent = _get_memory_agent()
    summary = agent.summarize_topic(topic)
    return {"topic": topic, "summary": summary}


@app.get("/graph")
async def get_knowledge_graph():
    """Get the knowledge graph for visualization."""
    builder = _get_graph_builder()
    return builder()

@app.get("/memory_blocks")
async def get_memory_blocks():
    """Get unique active memory block names."""
    metadata = vector_store.get_all_metadata()
    blocks = list(set(m.get("memory_block", "Default") for m in metadata if m.get("memory_block") or "Default"))
    return {"memory_blocks": sorted(blocks)}


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
