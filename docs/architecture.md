# System Architecture

## Overview

WenxinLens is a modular, production-grade AI platform for identifying Chinese ancient architecture and generating rich cultural explanations. It combines computer vision, retrieval-augmented generation (RAG), large language models, and a knowledge graph into a unified multi-agent pipeline.

```
┌──────────────────────────────────────────────────────────────┐
│                        User Clients                          │
│            Web Browser  ·  Mobile  ·  3rd-party API          │
└────────────────────────────┬─────────────────────────────────┘
                             │ HTTPS
┌────────────────────────────▼─────────────────────────────────┐
│                     Nginx Reverse Proxy                       │
│            SSL termination · rate-limit · routing             │
└──────────────┬─────────────────────────────┬─────────────────┘
               │ /api/*                       │ /*
┌──────────────▼───────────┐  ┌──────────────▼───────────────┐
│   FastAPI Backend        │  │   Next.js 14 Frontend        │
│  (Python 3.11, uvicorn)  │  │   (React 18, App Router)      │
│                          │  │                              │
│  Middleware:             │  │  Pages:                      │
│  · JWT / API-Key auth    │  │  / · /recognize · /chat      │
│  · Rate limiter (Redis)  │  │  /tour · /knowledge          │
│  · Request logger        │  │                              │
│                          │  │  Components:                 │
│  Routes:                 │  │  Navbar · RecognitionCard    │
│  /recognition            │  │  ChatPanel · TourMap         │
│  /chat                   │  └──────────────────────────────┘
│  /voice                  │
│  /tour                   │
│  /knowledge              │
│  /health                 │
└──────────────┬───────────┘
               │
┌──────────────▼──────────────────────────────────────────────┐
│               LangGraph Orchestrator Agent                    │
│                                                              │
│   ┌──────────┐  ┌───────────┐  ┌─────────────┐             │
│   │Recognition│→│ Retrieval │→│ Explanation  │             │
│   │  Agent   │  │  Agent    │  │   Agent     │             │
│   └──────────┘  └───────────┘  └─────────────┘             │
│          ↕               ↕              ↕                   │
│   ┌─────────────────────────────────────────┐               │
│   │          Interaction Agent              │               │
│   │   (stateful chat, Redis history)        │               │
│   └─────────────────────────────────────────┘               │
└──────────────┬──────────────────────────────────────────────┘
               │
       ┌───────┼──────────────────────┐
       │       │                      │
┌──────▼────┐ ┌▼─────────────┐ ┌─────▼──────────────┐
│  Vision   │ │  RAG Pipeline│ │ LLM Services        │
│ Module    │ │              │ │                     │
│           │ │ Vector Store │ │ OpenAI GPT-4o       │
│ CLIP      │ │ (Milvus)     │ │ Qwen 2.5-72b        │
│ ViT-L-14  │ │              │ │ Ollama (local)      │
│           │ │ Doc Processor│ │                     │
│ YOLOv8    │ │ BGE-Large     │ │ Translation (NLLB)  │
│ detector  │ │ embeddings   │ │ TTS (Azure/ElevenLabs│
└───────────┘ └──────┬───────┘ └─────────────────────┘
                     │
              ┌──────▼────────────┐
              │  Knowledge Graph  │
              │   Neo4j 5.17      │
              │                   │
              │  Dynasty → Style  │
              │  Building → Event │
              │  Person           │
              └───────────────────┘
```

---

## Component Details

### 1 · Computer Vision Pipeline

1. Image is received via `POST /recognition/analyze`
2. `ImagePreprocessor` resizes with padding to 640×640
3. **CLIP ViT-L-14** computes image embedding and compares against 8 class prompt averages (cosine similarity)
4. **YOLOv8** runs element detection (20 architectural classes: column, bracket, roof-ridge, etc.)
5. Structural feature probabilities are derived from CLIP sub-prompts
6. Results flow into `AgentState` for downstream agents

### 2 · RAG Pipeline

1. **Ingestion** (`document_processor.py`): PDF/HTML/TXT → chunks (512 tokens, 64 overlap) with language detection
2. **Embedding**: `BAAI/bge-large-zh-v1.5` (1024-dim) via `sentence-transformers`
3. **Storage**: Milvus collection `wenxinlens_knowledge` with HNSW index (M=16, efConstruction=256, COSINE metric)
4. **Retrieval**: Top-k vector search merged with Neo4j graph context for a unified ranked list
5. **Injection**: Formatted context string appended to LLM prompt

### 3 · LLM Service

Provider selection is automatic based on which API key is present:

```
OPENAI_API_KEY set?   → OpenAI GPT-4o (primary)
DASHSCOPE_API_KEY set? → Qwen2.5-72b via DashScope (secondary)
Neither set            → Ollama local (llama3.2)
```

Streaming is supported through `llm_service.stream()` which yields tokens as an async generator and is surfaced via SSE on the `/chat/message` endpoint.

### 4 · Knowledge Graph

Neo4j graph schema:

```
(:Dynasty {name, period, description})
  -[:PRODUCED_STYLE]→ (:Style {name, characteristics})
  
(:Building {name_en, name_zh, location, area, description})
  -[:BUILT_IN]→        (:Dynasty)
  -[:ARCHITECTURAL_STYLE]→ (:Style)
  -[:SYMBOLISES]→      (:Symbolism {concept, meaning})
  -[:ASSOCIATED_WITH]→ (:Person {name, role, period})
  -[:LOCATED_IN]→      (:Location {city, province})
  -[:PART_OF_EVENT]→   (:HistoricalEvent {name, year})
```

### 5 · Multi-Agent Orchestration (LangGraph)

The `OrchestratorAgent` constructs a `StateGraph` with nodes:

| Node | Function | Output |
|------|----------|--------|
| `recognition` | CLIP classification | `building_name_en/zh`, `confidence_score`, `structural_features` |
| `retrieval` | Milvus + Neo4j search | `retrieved_chunks`, `formatted_context` |
| `explanation` | LLM generation | `explanation`, `cultural_significance`, `follow_up_questions` |

Sequential fallback is available when LangGraph is not installed.

### 6 · Frontend Architecture

Next.js 14 **App Router** with the following structure:

```
src/app/
  layout.tsx         ← Root layout (Navbar removed here; in each page)
  page.tsx           ← Home / landing
  recognize/page.tsx ← Image upload + result + chat
  chat/page.tsx      ← Dedicated chat interface
  tour/page.tsx      ← Map + nearby sites
  knowledge/page.tsx ← Graph browser

src/components/
  Navbar.tsx         ← Sticky top nav (client component)
  RecognitionCard.tsx← Result display card
  ChatPanel.tsx      ← Inline chat (session managed internally)
  TourMap.tsx        ← Leaflet map (dynamic import, ssr:false)

src/services/
  api.ts             ← Axios client with JWT interceptors

src/types/index.ts   ← All shared TypeScript types
```

State management: **Zustand** for cross-page state, **React Query** for server state / caching.

---

## Data Flow — Image Recognition Request

```
Browser → POST /api/v1/recognition/analyze (multipart)
  → AuthMiddleware validates JWT
  → RateLimiter checks Redis
  → RecognitionRouter receives file
  → OrchestratorAgent.analyze(image_bytes, language, detail_level)
      → RecognitionAgent → VisionService._predict_sync()
          → CLIP image embed + cosine sim
          → YOLOv8 element detection
      → RetrievalAgent → RetrievalService.search(building_name)
          → Milvus top-5 chunks
          → Neo4j building context
      → ExplanationAgent → LLMService.generate(prompt + context)
          → Streaming or batch response
  → RecognitionResult JSON → browser
```

---

## Security Considerations

- All user-supplied images are validated for MIME type and size before processing
- JWT tokens expire after `JWT_EXPIRE_HOURS` (default 24 h); refresh is the client's responsibility
- Rate limiting at both Nginx (30 req/s per IP) and FastAPI (60 req/min + 500 req/hr per key) layers
- No user credentials are logged — only anonymised request metadata
- Neo4j queries use parameterised Cypher to prevent injection
- Milvus operations use the official SDK; no raw string interpolation in queries
- TLS termination at Nginx; all backend services communicate on a private Docker network
