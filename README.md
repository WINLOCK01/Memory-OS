# MemoryOS

> **A Personal Second Brain & RAG-Powered Memory System**

*MemoryOS is an advanced, multimodal Data Ingestion and Retrieval Augmented Generation (RAG) agent designed to act as your ultimate personal second brain. Engineered for enterprise-grade scalability, it supports dynamic LLM model switching, rich ingestion pipelines (PDFs, URLs, Text, Voice), and an interactive knowledge graph representation.*

---

## Key Features

- **Multimodal Data Ingestion**: Seamlessly process and store PDFs, Web Articles, Plain Text Notes, and Voice Memos (via Whisper).
- **Intelligent RAG Pipeline**: Context-aware querying powered by Langchain and LlamaIndex.
- **Dynamic Model Switching**: Swap seamlessly between models like `nvidia/nemotron-3-super-120b`, `gemini-2.0-flash`, `anthropic/claude-3.5-sonnet`, `meta-llama/llama-3.3-70b-instruct`, and OpenAI models.
- **Memory Block Categorization**: Group your data into semantic time-bound or context-bound memory blocks.
- **Interactive Knowledge Graph**: Visualize the relationships between different data chunks and sources natively within the UI.
- **Premium User Interface**: Built with an aesthetically rich, glassmorphism-inspired Streamlit frontend.

---

## System Architecture

The application is split into two primary layers to ensure optimal separation of concerns and high scalability:

1. **FastAPI Backend Services**: Handles data parsing (PyPDF2, BeautifulSoup, Whisper), embedding generation (Sentence-Transformers/OpenAI), vector storage (ChromaDB/FAISS), and graph orchestration (NetworkX).
2. **Streamlit Frontend**: Provides a reactive, modern UI with 4 main components: Dashboard, Data Ingestion, Chat/Querying, and Graph Visualization.

---

## Tech Stack

- **Backend Framework**: FastAPI, Uvicorn, Python 3.10+
- **Frontend App**: Streamlit, Streamlit-Agraph, React (Optional component in `MemoryOS.jsx`)
- **AI / LLM Core**: LangChain, LlamaIndex, OpenAI, Google GenAI
- **Embeddings & Vector Store**: Sentence-Transformers, ChromaDB, FAISS
- **Data Extractor Layer**: PyPDF2, BeautifulSoup4, Youtube Transcript API, OpenAI Whisper
- **Analytics & Graphs**: Pandas, NumPy, NetworkX

---

## Project Structure

```text
Memory-OS/
├── backend/
│   ├── agents/          # AI agents for query processing (memory_agent, graph_builder)
│   ├── api/             # API routes
│   ├── core/            # Core configuration & DB logic (vector_store)
│   ├── ingestion/       # Parsers for different modalities (PDFs, URLs, text, voice)
│   └── models/          # Pydantic schemas and domain data models
├── data/                # Vector DB and Graph persistent storage
├── skills/              # Agent skills and capabilities
├── tests/               # Unit and Integration tests
├── main.py              # FastAPI Application Entrypoint
├── streamlit_app.py     # Main Streamlit Frontend Application
├── MemoryOS.jsx         # React Frontend Component Sandbox
├── requirements.txt     # Python Dependencies
├── Dockerfile           # Docker Containerization Configuration
└── docker-compose.yml   # Multi-container orchestration logic
```

---

## Prerequisites

- **Python 3.9+** (3.10 or 3.11 recommended)
- **Node.js** (Only if utilizing the React frontend module)
- API Keys for necessary LLM Providers (OpenAI, Google GenAI, Anthropic, OpenRouter)

---

## Installation & Setup

### 1. Clone the repository
```bash
git clone https://github.com/your-org/memory-os.git
cd memory-os
```

### 2. Configure Environment Variables
Create a `.env` file based on the provided example template:
```bash
cp .env.example .env
```
Populate the respective values inside `.env`:
```env
OPENAI_API_KEY=your_openai_api_key
GOOGLE_API_KEY=your_google_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
OPENROUTER_API_KEY=your_openrouter_api_key
```

### 3. Setup Python Backend
Create a virtual environment and install backend dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Running the Application Locally
#### Start the FastAPI Backend
Initialize the backend APIs for ingestion and queries.
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
#### Start the Streamlit Frontend
Deploy the interactive frontend dashboard. In a separate terminal (with the venv activated):
```bash
streamlit run streamlit_app.py
```

### 5. Docker Deployment (Optional)
For highly consistent production or staging setups, utilize Docker Compose context:
```bash
docker-compose up --build -d
```

---

## API Reference

A fully documented API is exposed via Swagger UI. Accessible locally at `http://localhost:8000/docs` while the backend is running.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/ingest/pdf` | `POST` | Upload and ingest a PDF document. |
| `/ingest/url` | `POST` | Scrape and ingest a webpage content. |
| `/ingest/text` | `POST` | Ingest manually typed plain text notes. |
| `/ingest/voice` | `POST` | Transcribe and ingest voice audio payloads via Whisper. |
| `/query` | `POST` | Run RAG-backed query against stored memory chunks. |
| `/graph` | `GET`  | Fetch knowledge graph node networks. |
| `/stats` | `GET`  | Retrieve metrics of stored modalities and chunks. |
| `/health` | `GET` | Check engine health and count elements. |

---

## Contributing

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## License

This codebase is proprietary to the application developer. See the LICENSE file (if present) for granular distribution terms.

---
*Developed by the AI Engineering Team.*
