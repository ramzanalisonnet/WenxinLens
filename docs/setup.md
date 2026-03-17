# Development Setup Guide

## Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| Python | 3.11+ | Use `pyenv` or `conda` |
| Node.js | 20+ | Use `nvm` |
| Docker | 24+ | For infrastructure |
| Docker Compose | v2.20+ | Bundled with Docker Desktop |
| Git | 2.40+ | |

---

## 1 · Clone and configure

```bash
git clone https://github.com/yourorg/wenxinlens.git
cd wenxinlens
cp .env.example .env
# Edit .env and fill in your API keys
```

**Minimum required keys** for a working dev environment:

```dotenv
# One LLM provider (the first available is used automatically)
OPENAI_API_KEY=sk-...          # or
DASHSCOPE_API_KEY=...          # Alibaba Qwen

# Leave the infrastructure defaults as-is for Docker dev
```

---

## 2 · Start infrastructure services (Docker)

```bash
docker compose -f deployment/docker-compose.yml up -d etcd minio milvus redis neo4j
```

Wait for all services to be healthy (≈ 60 s):

```bash
docker compose -f deployment/docker-compose.yml ps
```

---

## 3 · Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Seed the vector store with curated knowledge
python -m rag.knowledge_base_init

# Start the API server
uvicorn main:app --reload --port 8000
```

Interactive API docs: http://localhost:8000/docs

---

## 4 · Frontend

```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:3000

---

## 5 · Dataset pipeline (optional)

```bash
# Collect Wikipedia text
python datasets/collect_wikipedia.py --out-dir datasets/raw/wikipedia

# Collect museum/Wikidata metadata
python datasets/collect_museum_data.py

# Prepare training data (requires images in datasets/raw/images/<ClassName>/)
python datasets/prepare_training_data.py
```

---

## 6 · Training (optional)

```bash
# Evaluate zero-shot CLIP performance
python training/evaluate_clip.py --split test

# Fine-tune YOLOv8 classifier
python training/train_yolo.py --task classify --epochs 50

# Fine-tune YOLOv8 detector
python training/train_yolo.py --task detect --model-base yolov8m.pt --epochs 100
```

---

## 7 · Production deployment

```bash
# Build and start all services
docker compose -f deployment/docker-compose.yml up --build -d

# Or build individual images
docker build -f deployment/Dockerfile.backend -t wenxinlens/backend:latest .
docker build -f deployment/Dockerfile.frontend -t wenxinlens/frontend:latest .
```

### Kubernetes

```bash
# Create secrets (replace values with real credentials)
kubectl create secret generic wenxinlens-secrets \
  --from-env-file=.env

# Apply manifests
kubectl apply -f deployment/kubernetes/manifests.yaml
```

---

## 8 · Environment variables reference

See [`.env.example`](../.env.example) for the full list with descriptions.

Key groups:

| Group | Variables |
|-------|-----------|
| LLM | `OPENAI_API_KEY`, `DASHSCOPE_API_KEY`, `OLLAMA_BASE_URL`, `LLM_MODEL` |
| Vision | `CLIP_MODEL_NAME`, `YOLO_MODEL_PATH` |
| Vector DB | `MILVUS_HOST`, `MILVUS_PORT`, `MILVUS_COLLECTION` |
| Graph DB | `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` |
| Cache | `REDIS_URL` |
| TTS | `TTS_PROVIDER`, `AZURE_TTS_KEY`, `AZURE_TTS_REGION`, `ELEVENLABS_API_KEY` |
| Auth | `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `API_KEY` |
| Monitoring | `SENTRY_DSN` |

---

## 9 · Troubleshooting

**Milvus connection refused** — ensure etcd and minio are healthy first; milvus depends on them.

**CUDA out of memory** — set `CLIP_MODEL_NAME=ViT-B-32` to use the smaller model.

**Neo4j authentication error** — the password in `NEO4J_AUTH` inside docker-compose must match `NEO4J_PASSWORD` in `.env`.

**`open_clip` import error** — install with `pip install open-clip-torch`. Torch must be installed first.

**Leaflet map tiles don't load** — requires internet access; the tile URL uses OpenStreetMap servers.
