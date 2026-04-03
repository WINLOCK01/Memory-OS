---
name: docker-deploy
description: >
  USE THIS SKILL whenever the user mentions Docker, docker-compose, deployment, container,
  environment variables, .env, volumes, production, hosting, Railway, Render, DigitalOcean,
  or "how to run the app." Also trigger when they say "it works locally but not in Docker"
  or have any container/deployment issues. THIS skill covers building, running, and deploying.
---

# Docker & Deployment Skill — Building, Running, and Deploying MemoryOS

## Overview

MemoryOS is containerized with Docker and orchestrated via `docker-compose.yml`.
The setup includes the FastAPI backend, React frontend, and persistent ChromaDB storage.

---

## File Structure

```
memoryos/
├── Dockerfile                ← Multi-stage build for backend
├── docker-compose.yml        ← Orchestrates all services
├── .env                      ← Environment variables
├── .dockerignore             ← Files to exclude from build
├── data/                     ← Persistent storage (mounted volume)
│   └── chroma/              ← ChromaDB persistence directory
└── frontend/
    └── Dockerfile            ← Frontend build (if separate)
```

---

## Dockerfile (Backend)

```dockerfile
# Dockerfile

FROM python:3.11-slim AS base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory for ChromaDB
RUN mkdir -p /app/data/chroma

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## docker-compose.yml

```yaml
# docker-compose.yml

version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./data:/app/data          # Persist ChromaDB data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:8000
    depends_on:
      - backend
    restart: unless-stopped
```

---

## Environment Variables

### `.env` File

```env
# OpenAI
OPENAI_API_KEY=sk-your-key-here

# ChromaDB
CHROMA_PERSIST_DIR=/app/data/chroma

# Embedding Model
EMBEDDING_MODEL=all-MiniLM-L6-v2

# API Settings
API_HOST=0.0.0.0
API_PORT=8000

# Frontend URL (for CORS)
FRONTEND_URL=http://localhost:3000
```

### Accessing in Code

```python
# backend/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    CHROMA_PERSIST_DIR: str = "./data/chroma"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:3000"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

---

## Common Commands

### Building and Running

```bash
# Build and start all services
docker-compose up --build

# Run in detached mode
docker-compose up -d --build

# Stop all services
docker-compose down

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Rebuild a specific service
docker-compose up --build backend
```

### Managing Data

```bash
# Persist data — the volume mount handles this automatically
# Data lives in ./data/chroma on the host

# Reset ChromaDB (delete all memories)
rm -rf ./data/chroma/*
docker-compose restart backend

# Backup data
cp -r ./data/chroma ./backups/chroma-$(date +%Y%m%d)
```

### Debugging

```bash
# Shell into the running container
docker-compose exec backend bash

# Check if ChromaDB is accessible
docker-compose exec backend python -c "import chromadb; c = chromadb.PersistentClient('/app/data/chroma'); print(c.list_collections())"

# Check environment variables
docker-compose exec backend env | grep -E "(OPENAI|CHROMA)"
```

---

## Adding a New Service

To add a new service (e.g., Redis for caching):

```yaml
# docker-compose.yml

services:
  # ... existing services ...
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    restart: unless-stopped

volumes:
  redis-data:
```

Then update the backend to connect:

```python
# backend/core/config.py
class Settings(BaseSettings):
    # ... existing ...
    REDIS_URL: str = "redis://redis:6379"
```

---

## Deploying to Cloud

### Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up

# Set environment variables
railway variables set OPENAI_API_KEY=sk-...
railway variables set CHROMA_PERSIST_DIR=/app/data/chroma
```

### Render

1. Create a new Web Service on render.com
2. Connect your GitHub repo
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables in the Render dashboard
6. Add a persistent disk mounted at `/app/data`

### DigitalOcean (Docker Droplet)

```bash
# SSH into your droplet
ssh root@your-droplet-ip

# Clone your repo
git clone https://github.com/yourusername/memoryos.git
cd memoryos

# Create .env file
cp .env.example .env
nano .env  # Add your API keys

# Build and run
docker-compose up -d --build

# Set up Nginx reverse proxy (optional)
apt install nginx
```

---

## .dockerignore

```
.git
.env
__pycache__
*.pyc
.pytest_cache
node_modules
data/
*.egg-info
.vscode
.idea
```

---

## Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| `OPENAI_API_KEY not set` | `.env` not loaded | Check `env_file` in docker-compose |
| ChromaDB data lost on restart | Missing volume mount | Add `volumes: ./data:/app/data` |
| CORS errors | Frontend URL not in allowed origins | Update CORS in `main.py` |
| Port already in use | Another service on 8000 | Change port mapping: `"8001:8000"` |
| Build fails on `sentence-transformers` | Missing system deps | Add `build-essential` to Dockerfile |
