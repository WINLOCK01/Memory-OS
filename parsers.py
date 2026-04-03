import re
import requests
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
from typing import List, Dict, Tuple
from datetime import datetime
from backend.core.config import settings
import io


def chunk_text(text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
    """Split text into overlapping chunks."""
    chunk_size = chunk_size or settings.max_chunk_size
    overlap = overlap or settings.chunk_overlap
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap
    return [c for c in chunks if len(c.strip()) > 50]


def parse_pdf(file_bytes: bytes, filename: str) -> Tuple[List[str], List[Dict]]:
    """Extract text from PDF and return chunks + metadata."""
    reader = PdfReader(io.BytesIO(file_bytes))
    full_text = ""
    for page in reader.pages:
        full_text += page.extract_text() + "\n"

    full_text = re.sub(r'\s+', ' ', full_text).strip()
    chunks = chunk_text(full_text)
    metadata = [{
        "source_type": "pdf",
        "source": filename,
        "ingested_at": datetime.utcnow().isoformat(),
        "chunk_index": i
    } for i, _ in enumerate(chunks)]
    return chunks, metadata


def parse_url(url: str) -> Tuple[List[str], List[Dict]]:
    """Scrape and parse a webpage."""
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(response.text, "html.parser")

    # Remove nav, footer, scripts
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    title = soup.title.string if soup.title else url
    paragraphs = soup.find_all(["p", "h1", "h2", "h3", "article"])
    text = " ".join(p.get_text(separator=" ") for p in paragraphs)
    text = re.sub(r'\s+', ' ', text).strip()

    chunks = chunk_text(text)
    metadata = [{
        "source_type": "url",
        "source": url,
        "title": title,
        "ingested_at": datetime.utcnow().isoformat(),
        "chunk_index": i
    } for i, _ in enumerate(chunks)]
    return chunks, metadata


def parse_text(content: str, title: str = "Note") -> Tuple[List[str], List[Dict]]:
    """Parse raw text / notes."""
    chunks = chunk_text(content)
    metadata = [{
        "source_type": "note",
        "source": title,
        "ingested_at": datetime.utcnow().isoformat(),
        "chunk_index": i
    } for i, _ in enumerate(chunks)]
    return chunks, metadata
