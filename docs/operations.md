# Operations and security notes

## Production configuration

Do not use the example credentials in production. The backend rejects production startup when the app secret, JWT secret, master API key, Redis password, or Neo4j password is missing, too short, reused, or an obvious development placeholder. Use distinct random values of at least 32 characters, set `APP_DEBUG=false`, restrict `CORS_ORIGINS` to the exact HTTPS origins that need access, and set a browser-reachable `NEXT_PUBLIC_API_URL`.

The compose file binds the backend, frontend, and database ports to host localhost. Nginx remains the public entry point on port 80; configure TLS at Nginx or an upstream ingress before public use.

## Liveness and readiness

- `GET /health` is a liveness probe. It tells a scheduler that the API process responds.
- `GET /ready` is a dependency-aware readiness probe. It returns HTTP 503 when fast startup is enabled or the vision/vector/graph dependencies are not initialized.

The application deliberately supports degraded behavior during development. A process being live does not mean all AI features are ready.

## Image and audio uploads

Recognition accepts JPEG, PNG, and WebP images only, with byte and pixel limits. HEIC is intentionally not advertised as supported because the current Pillow pipeline does not guarantee it can decode that format. Avatar speech uploads are also byte-limited. Provider exceptions are logged server-side; API responses avoid returning raw provider details.

## AI fallback behavior

When the vision model is unavailable, recognition returns an explicit unknown result rather than a fabricated high-confidence building identification. If YOLO weights are missing, the detector returns no detections instead of inferring structural classes from average image colours. These fallbacks are more honest but do not replace installation and validation of the trained model weights.

The FAISS fallback is in-memory and not persistent across process restarts. Use Milvus for durable vector retrieval in a deployed instance.

## Dependency upgrade priority

The frontend is still pinned to Next.js 14.1.0 and React 18.2.0 in the existing lockfile. That framework baseline predates later security releases. A separate coordinated framework migration is still required before public production deployment; it should upgrade Next.js, React, and incompatible UI libraries together, regenerate `frontend/package-lock.json`, then pass the checked-in type-check and production-build jobs. Do not treat the presence of Dependabot configuration alone as evidence that this migration has been completed.
