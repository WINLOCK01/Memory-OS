import chromadb
from chromadb.utils import embedding_functions
from backend.core.config import settings


class VectorStore:
    """Singleton ChromaDB vector store for MemoryOS."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_store()
        return cls._instance

    def _init_store(self):
        self.client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir
        )
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=settings.embedding_model
        )
        self.collection = self.client.get_or_create_collection(
            name="memoryos",
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(self, texts: list[str], metadatas: list[dict]) -> int:
        """Add text chunks with metadata to the store."""
        ids = [
            f"{m['source_type']}_{m['source']}_{m['chunk_index']}"
            for m in metadatas
        ]
        self.collection.upsert(
            documents=texts,
            metadatas=metadatas,
            ids=ids,
        )
        return len(texts)

    def query(self, query_text: str, n_results: int = 5, where: dict = None) -> list[dict]:
        """Semantic search with optional metadata filters."""
        kwargs = {
            "query_texts": [query_text],
            "n_results": n_results,
        }
        if where:
            kwargs["where"] = where
        results = self.collection.query(**kwargs)
        return self._format_results(results)

    def search(self, query_text: str, n_results: int = 6, filters: dict = None) -> list[dict]:
        """Alias for query() — used by memory_agent.py."""
        results = self.query(query_text, n_results=n_results, where=filters)
        # memory_agent expects 'content' key instead of 'text'
        for r in results:
            r["content"] = r.get("text", "")
        return results

    def _format_results(self, results) -> list[dict]:
        """Convert ChromaDB results to a clean list of dicts."""
        formatted = []
        if not results["ids"] or not results["ids"][0]:
            return formatted
        for i in range(len(results["ids"][0])):
            formatted.append({
                "id": results["ids"][0][i],
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i] if results.get("distances") else None,
            })
        return formatted

    def list_memories(self, limit: int = 100, source_type: str = None) -> dict:
        """List stored memories with optional filtering."""
        kwargs = {"limit": limit}
        if source_type:
            kwargs["where"] = {"source_type": source_type}
        return self.collection.get(**kwargs)

    def get_all_metadata(self) -> list[dict]:
        """Return metadata for all stored chunks."""
        results = self.collection.get()
        return results.get("metadatas", [])

    def delete_memory(self, memory_id: str):
        """Delete a specific memory by ID."""
        self.collection.delete(ids=[memory_id])

    def delete_by_source(self, source: str):
        """Delete all chunks from a specific source."""
        self.collection.delete(where={"source": source})

    def count(self) -> int:
        """Return total number of stored chunks."""
        return self.collection.count()


# Module-level singleton
vector_store = VectorStore()
