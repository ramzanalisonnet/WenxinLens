# WenxinLens — AI Cultural Interpretation System for Chinese Ancient Architecture

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![Next.js 14](https://img.shields.io/badge/Next.js-14+-black.svg)](https://nextjs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> Point your camera at a piece of Chinese history — WenxinLens tells its story.

WenxinLens is a production-grade, multi-agent AI platform that combines computer vision, large language models, retrieval-augmented generation (RAG), and a cultural knowledge graph to identify Chinese ancient architecture and deliver rich, multilingual cultural explanations.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      USER (Web / Mobile)                    │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTPS
┌──────────────────────────▼──────────────────────────────────┐
│             Next.js Frontend  (React 18 + Tailwind)         │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST / SSE
┌──────────────────────────▼──────────────────────────────────┐
│          FastAPI Backend  (async, JWT-auth, rate-limit)     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Orchestrator Agent (LangGraph)          │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐   │   │
│  │  │Recognition │Retrieval││ Explanation│ │Interact│   │   │
│  │  │  Agent   │ │  Agent   │ │  Agent   │ │ Agent  │   │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └────────┘   │   │
│  └──────────────────────────────────────────────────────┘   │
└──────┬────────────────┬─────────────┬───────────────────────┘
       │                │             │
┌──────▼──────┐  ┌──────▼──────┐  ┌───▼────────────┐
│  Vision     │  │RAG + Milvus │  │ Neo4j Knowledge│
│ (CLIP+YOLO) │  │  Vector DB  │  │     Graph      │
└─────────────┘  └─────────────┘  └────────────────┘
                        │
                  ┌─────▼──────┐
                  │  Redis     │
                  │  Cache +   │
                  │  Sessions  │
                  └────────────┘
```

---

## Repository Structure

```
wenxinlens/
├── backend/                # FastAPI application
│   ├── api/                # Route handlers
│   ├── services/           # Business logic services
│   ├── agents/             # LangGraph AI agents
│   ├── rag/                # RAG pipeline
│   ├── vision/             # Computer vision module
│   ├── knowledge_graph/    # Neo4j graph module
│   └── middleware/         # Auth, rate-limiting, logging
├── frontend/               # Next.js 14 application
│   └── src/
│       ├── app/            # App Router pages
│       ├── components/     # React components
│       ├── hooks/          # Custom React hooks
│       ├── services/       # API client
│       └── types/          # TypeScript types
├── agents/                 # Standalone agent definitions
├── rag/                    # RAG utilities
├── vision/                 # Vision pipeline
├── knowledge_graph/        # Graph database
├── datasets/               # Data collection & processing
├── training/               # Model training scripts
├── deployment/             # Docker, K8s, Nginx configs
└── docs/                   # Architecture & API docs
```

---

## Quick Start

### Prerequisites

- Docker & Docker Compose v2+
- Python 3.11+
- Node.js 20+
- NVIDIA GPU (optional, recommended for production)

### 1. Clone and configure

```bash
git clone https://github.com/yourorg/wenxinlens.git
cd wenxinlens
cp .env.example .env
# Edit .env with your API keys and secrets
```

### 2. Start all services

```bash
docker-compose up -d
```

### 3. Initialize the knowledge base

```bash
docker-compose exec backend python -m scripts.init_knowledge_base
```

### 4. Open the application

- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs
- Neo4j Browser: http://localhost:7474

---

## Core Features

| Feature | Technology |
|---|---|
| Architecture Recognition | YOLOv8 + CLIP + ViT |
| Cultural Explanation | Qwen2.5 / GPT-4 via LangGraph |
| Knowledge Retrieval | RAG + Milvus + BGE-Large |
| Knowledge Graph | Neo4j + Cypher |
| Interactive Chat | LangGraph Stateful Agents |
| Voice Narration | Azure TTS / Coqui TTS |
| Multilingual | NLLB-200 / LLM translation |
| Session Memory | Redis |
| Caching | Redis + in-process LRU |

---

## Development

```bash
# Backend
cd backend && pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd frontend && npm install
npm run dev
```

---

## License

MIT License — see [LICENSE](LICENSE) for details.
