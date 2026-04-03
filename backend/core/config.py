from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """MemoryOS configuration — loaded from .env file."""

    # ChromaDB
    chroma_persist_dir: str = "./data/chroma"
    embedding_model: str = "all-MiniLM-L6-v2"

    # Chunking
    max_chunk_size: int = 512
    chunk_overlap: int = 64

    # LLM (Week 2)
    openai_api_key: str = ""
    google_api_key: str = ""
    openrouter_api_key: str = ""
    hf_token: str = ""
    llm_model: str = "nvidia/nemotron-3-super-120b-a12b:free"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()

# Push the API keys to os.environ for downstream libraries
import os
if settings.hf_token:
    os.environ["HF_TOKEN"] = settings.hf_token
if settings.google_api_key:
    os.environ["GOOGLE_API_KEY"] = settings.google_api_key
if settings.openrouter_api_key:
    os.environ["OPENROUTER_API_KEY"] = settings.openrouter_api_key
if settings.openai_api_key:
    os.environ["OPENAI_API_KEY"] = settings.openai_api_key
