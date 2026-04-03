from pydantic import BaseModel, Field
from typing import Optional, List


# ─── Ingestion Requests ─────────────────────────────────────────────────────

class IngestURLRequest(BaseModel):
    url: str = Field(..., description="URL of the webpage to ingest")
    memory_block: str = Field(default="Default", description="Memory Block name assigned by user")


class IngestTextRequest(BaseModel):
    content: str = Field(..., min_length=1, description="Text content to ingest")
    title: str = Field(default="Note", description="Title for the note")
    memory_block: str = Field(default="Default", description="Memory Block name assigned by user")


# ─── Ingestion Response ─────────────────────────────────────────────────────

class IngestResponse(BaseModel):
    message: str
    chunks_stored: int
    source: str


# ─── Query ───────────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    source_type: Optional[str] = None
    n_results: int = Field(default=6, ge=1, le=50)
    start_timestamp: Optional[float] = None
    end_timestamp: Optional[float] = None
    model: str = Field(default="nvidia/nemotron-3-super-120b-a12b:free", description="LLM model identifier")
    memory_block: Optional[str] = Field(default=None, description="Memory Block filter")


class QueryResponse(BaseModel):
    answer: str
    sources: List[str]
    memories_used: int


# ─── Stats ───────────────────────────────────────────────────────────────────

class StatsResponse(BaseModel):
    total_chunks: int
    total_sources: int
    by_type: dict


class HealthResponse(BaseModel):
    status: str
    memories: int
