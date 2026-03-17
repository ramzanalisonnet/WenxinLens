# API Reference

Base URL: `http://localhost:8000/api/v1`

All endpoints return JSON unless noted. Authenticated endpoints require either:
- `Authorization: Bearer <JWT>` header, or
- `X-API-Key: <key>` header (set `API_KEY` in `.env`)

---

## Authentication

### `POST /auth/token`
Exchange credentials for a JWT.

**Body**
```json
{ "username": "...", "password": "..." }
```

**Response**
```json
{ "access_token": "eyJ...", "token_type": "bearer" }
```

---

## Recognition

### `POST /recognition/analyze`
Upload an image for architectural analysis.

**Request**: `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | binary | ✓ | JPEG/PNG image (max 10 MB) |
| `language` | string | — | `en` (default) or `zh` |
| `detail_level` | string | — | `tourist` / `standard` (default) / `academic` |

**Response**
```json
{
  "result_id": "uuid",
  "building_name_en": "Temple of Heaven",
  "building_name_zh": "天坛",
  "dynasty": "Ming",
  "confidence_score": 0.92,
  "structural_features": ["circular plan", "blue glazed tiles", "triple eaves"],
  "explanation": "...",
  "cultural_significance": "...",
  "follow_up_questions": ["...", "..."],
  "processing_time_ms": 1240
}
```

### `GET /recognition/styles`
List all recognisable architectural styles.

---

## Chat

### `POST /chat/session`
Create a new conversation session.

**Body**
```json
{
  "language": "en",
  "building_context": "<result_id>"   // optional
}
```

**Response**
```json
{ "session_id": "uuid", "created_at": "..." }
```

### `POST /chat/message`
Send a message and receive a response (or SSE stream).

**Body**
```json
{
  "session_id": "uuid",
  "message": "What dynasty built this?",
  "language": "en",
  "stream": false
}
```

**Response** (non-stream)
```json
{ "response": "...", "session_id": "...", "message_id": "..." }
```

**Response** (stream, `stream: true`) — `text/event-stream`
```
data: {"delta": "The "}
data: {"delta": "Temple..."}
data: [DONE]
```

### `GET /chat/session/{session_id}`
Retrieve session history.

### `DELETE /chat/session/{session_id}`
Delete a session.

---

## Voice

### `POST /voice/synthesize`
Convert text to audio.

**Body**
```json
{
  "text": "Welcome to the Forbidden City.",
  "language": "en",
  "voice_id": "zh-CN-XiaoxiaoNeural"
}
```

**Response**: `audio/mpeg` binary (MP3).

### `GET /voice/voices`
List available TTS voices.

---

## Tour

### `GET /tour/nearby`
Get nearby heritage sites based on GPS.

**Query params**: `lat`, `lon`, `radius_km` (default 50), `dynasty` (optional filter)

**Response**
```json
{
  "sites": [
    {
      "id": "...", "name_en": "...", "name_zh": "...",
      "latitude": 39.88, "longitude": 116.39,
      "dynasty": "Ming", "distance_km": 2.3
    }
  ]
}
```

### `GET /tour/site/{site_id}`
Get detailed information for a single site.

### `GET /tour/route`
Plan a multi-stop tour route.

**Query params**: `site_ids` (comma-separated), `optimize` (bool, default true)

---

## Knowledge Graph

### `GET /knowledge/building/{name}`
Look up a building in the knowledge graph.

**Response**
```json
{
  "name_en": "...", "name_zh": "...",
  "dynasty": "...", "style": "...",
  "description": "...",
  "related": [...]
}
```

### `GET /knowledge/search`
Full-text + graph search across all buildings.

**Query params**: `q` (search query), `limit` (default 10)

### `GET /knowledge/dynasty/{dynasty}`
Get all buildings attributed to a dynasty.

### `GET /knowledge/graph/relations`
Return a subgraph suitable for visualisation.

**Query params**: `building` (focus node), `depth` (default 2)

### `GET /knowledge/dynasties`
List all dynasties in the knowledge graph.

---

## Health

### `GET /health`
```json
{
  "status": "ok",
  "version": "1.0.0",
  "services": {
    "vision": "ok",
    "vector_store": "ok",
    "neo4j": "ok",
    "redis": "ok"
  }
}
```
