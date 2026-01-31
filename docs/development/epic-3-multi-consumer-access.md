---
epic: 3
title: "Multi-Consumer Access & Integration"
status: in_progress
priority: P1
estimated_stories: 3
---

# Epic 3: Multi-Consumer Access & Integration

Provide multiple access patterns for different client types (Claude Code, web apps, Python scripts).

**User Outcome:** Users and developers can access Alexandria via MCP server (Claude Code), HTTP API (web/mobile), or Python library (scripts).

**FRs Covered:** FR-005 (multi-consumer service), NFR-004 (maintainability)

**ADR References:** ADR-0008 (Multi-Consumer Service Model), ADR-0003 (GUI as Thin Layer), ADR-0009 (HTTP API Wrapper)

**Current State:**
- ✅ **Tier 1 (MCP):** stdio protocol for Claude Code - PRIMARY
  - Implemented: `scripts/mcp_server.py` (FastMCP)
  - Tools: alexandria_query, alexandria_search, alexandria_book, alexandria_stats, alexandria_ingest, alexandria_test_chunking
  - Configuration via environment variables
- ✅ **Tier 3 (Python lib):** Direct import from scripts/ - INTERNAL
  - All business logic in `scripts/` package
  - Usage: `from scripts.rag_query import perform_rag_query`
- ❌ **Tier 2 (HTTP):** FastAPI REST API - SECONDARY (NOT IMPLEMENTED)
  - No HTTP endpoints
  - No Swagger/OpenAPI docs
  - No API authentication
  - No rate limiting

**Target State:**
- Tier 1 (MCP): Fully functional ✅
- Tier 2 (HTTP): FastAPI REST wrapper with authentication, rate limiting, Swagger docs
- Tier 3 (Python lib): Fully functional ✅
- All tiers share business logic in scripts/ (no duplication)
- API clients available (Python SDK, JavaScript examples, curl)

---

## Stories

### Story 3.1: HTTP REST API with FastAPI

**Status:** ⏳ PENDING

As a **web/mobile developer**,
I want **a RESTful HTTP API to access Alexandria**,
So that **I can integrate Alexandria into web apps, mobile apps, or external services**.

**Acceptance Criteria:**

**Given** the FastAPI server is running
**When** I send `POST /api/v1/query` with JSON payload:
```json
{
  "query": "What is Nietzsche's view on suffering?",
  "collection": "alexandria",
  "top_k": 5,
  "context_mode": "contextual",
  "response_pattern": "synthesis"
}
```
**Then** I receive a 200 response with RAG results:
```json
{
  "answer": "...",
  "sources": [...],
  "metadata": {...}
}
```
**And** the response time is < 6 seconds (< 100ms search + ~5.5s LLM)

**Given** I send invalid request (missing required fields)
**When** the API validates input
**Then** I receive a 422 response with clear error message:
```json
{
  "detail": [
    {
      "loc": ["body", "query"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**Given** I want to explore API capabilities
**When** I navigate to `http://localhost:8000/docs`
**Then** I see Swagger UI with all endpoints documented
**And** I can test endpoints directly from the browser
**And** example requests/responses are provided

**Technical Tasks:**

- [ ] Create `scripts/api_server.py` using FastAPI:
  ```python
  from fastapi import FastAPI, HTTPException
  from fastapi.middleware.cors import CORSMiddleware
  from pydantic import BaseModel, Field
  from typing import Optional, List

  app = FastAPI(
      title="Alexandria RAG API",
      description="RESTful API for semantic book search",
      version="1.0.0"
  )

  # CORS configuration for web clients
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["*"],  # Phase 1: Allow all; Phase 2+: Restrict to domains
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  ```
- [ ] Define Pydantic request/response models:
  ```python
  class QueryRequest(BaseModel):
      query: str = Field(..., description="Search query")
      collection: str = Field("alexandria", description="Collection name")
      top_k: int = Field(5, ge=1, le=20, description="Number of results")
      context_mode: str = Field("contextual", description="precise|contextual|comprehensive")
      response_pattern: str = Field("free", description="Response pattern")

  class QueryResponse(BaseModel):
      answer: Optional[str]
      sources: List[dict]
      metadata: dict
  ```
- [ ] Implement API endpoints (wrap scripts/ business logic):
  - `POST /api/v1/query` - Semantic search with RAG
  - `GET /api/v1/search` - Metadata search (title, author)
  - `GET /api/v1/book/{book_id}` - Get book details
  - `GET /api/v1/stats` - Collection statistics
  - `POST /api/v1/ingest` - Ingest book (authenticated)
  - `GET /api/v1/health` - Health check (Qdrant, OpenRouter API)
- [ ] Add error handling and logging:
  ```python
  @app.exception_handler(Exception)
  async def global_exception_handler(request, exc):
      logger.error(f"Unhandled error: {exc}", exc_info=True)
      return JSONResponse(
          status_code=500,
          content={"detail": "Internal server error"}
      )
  ```
- [ ] Add startup event for connection checks:
  ```python
  @app.on_event("startup")
  async def startup_event():
      # Check Qdrant connection
      is_connected, error = check_qdrant_connection(QDRANT_HOST, QDRANT_PORT)
      if not is_connected:
          logger.error(f"Qdrant connection failed: {error}")
      else:
          logger.info("✅ Qdrant connection successful")
  ```
- [ ] Add ASGI server configuration (uvicorn):
  ```bash
  uvicorn scripts.api_server:app --host 0.0.0.0 --port 8000 --reload
  ```
- [ ] Create startup script: `scripts/start_api_server.sh`:
  ```bash
  #!/bin/bash
  # Load environment
  source .env
  # Start API server
  uvicorn scripts.api_server:app --host 0.0.0.0 --port 8000
  ```

**Files Modified:**
- `scripts/api_server.py` (new FastAPI server)
- `scripts/start_api_server.sh` (new startup script)
- `requirements.txt` (add fastapi, uvicorn, pydantic)

**Definition of Done:**
- FastAPI server running and accessible at http://localhost:8000
- All endpoints implemented and functional
- Swagger UI available at http://localhost:8000/docs
- CORS configured for web clients
- Error handling and logging working
- All tests pass

---

### Story 3.2: API Authentication & Rate Limiting

**Status:** ⏳ PENDING

As a **system administrator**,
I want **API key authentication and rate limiting**,
So that **only authorized users can access the API and abuse is prevented**.

**Acceptance Criteria:**

**Given** I have a valid API key
**When** I send request with header `X-API-Key: abc123...`
**Then** the request is authenticated and processed normally

**Given** I send request without API key (or invalid key)
**When** authentication is checked
**Then** I receive 401 Unauthorized response:
```json
{
  "detail": "Invalid or missing API key"
}
```

**Given** I send 100 requests in 1 minute (exceeding rate limit)
**When** rate limit is enforced
**Then** request 101 is rejected with 429 Too Many Requests:
```json
{
  "detail": "Rate limit exceeded: 100 requests per minute"
}
```
**And** response includes `Retry-After` header with seconds to wait

**Given** I am a PRO-tier user (Phase 2+)
**When** my API key is validated
**Then** I have higher rate limits (1000 requests/minute vs 100)
**And** I can access all collections (including private)

**Technical Tasks:**

- [ ] Create API key management module: `scripts/api_auth.py`:
  ```python
  import secrets
  import hashlib
  from typing import Optional
  from fastapi import Security, HTTPException, status
  from fastapi.security import APIKeyHeader

  API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

  # Phase 1: Simple in-memory API keys (Phase 2+: SQLite database)
  API_KEYS = {
      hashlib.sha256("dev-key-123".encode()).hexdigest(): {
          "user": "developer",
          "tier": "free",
          "rate_limit": 100  # requests per minute
      },
      hashlib.sha256("admin-key-456".encode()).hexdigest(): {
          "user": "admin",
          "tier": "pro",
          "rate_limit": 1000
      }
  }

  def validate_api_key(api_key: str = Security(API_KEY_HEADER)) -> dict:
      """Validate API key and return user info."""
      if not api_key:
          raise HTTPException(
              status_code=status.HTTP_401_UNAUTHORIZED,
              detail="Missing API key"
          )

      key_hash = hashlib.sha256(api_key.encode()).hexdigest()
      user_info = API_KEYS.get(key_hash)

      if not user_info:
          raise HTTPException(
              status_code=status.HTTP_401_UNAUTHORIZED,
              detail="Invalid API key"
          )

      return user_info
  ```
- [ ] Add rate limiting with slowapi:
  ```python
  from slowapi import Limiter, _rate_limit_exceeded_handler
  from slowapi.util import get_remote_address
  from slowapi.errors import RateLimitExceeded

  limiter = Limiter(key_func=get_remote_address)
  app.state.limiter = limiter
  app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

  @app.post("/api/v1/query")
  @limiter.limit("100/minute")  # Default rate limit
  async def query_endpoint(
      request: QueryRequest,
      user: dict = Depends(validate_api_key)
  ):
      # Apply user-specific rate limit (if PRO tier)
      # ...
  ```
- [ ] Protect endpoints with authentication:
  ```python
  # Public endpoints (no auth):
  - GET /api/v1/health
  - GET /docs

  # Authenticated endpoints:
  - POST /api/v1/query  (requires API key)
  - POST /api/v1/ingest  (requires API key + admin role)
  ```
- [ ] Create API key generation script: `scripts/generate_api_key.py`:
  ```bash
  python scripts/generate_api_key.py --user sabo --tier free
  # Output:
  # API Key: alex_abc123def456...
  # Hash: sha256:abc123...
  # Rate Limit: 100 requests/minute
  # Add to API_KEYS dictionary in api_auth.py
  ```
- [ ] Add API key storage (Phase 1: in-memory dict; Phase 2+: SQLite):
  ```python
  # Future: Store in SQLite (Epic 6: Multi-Tenancy)
  # CREATE TABLE api_keys (
  #     key_hash TEXT PRIMARY KEY,
  #     user_id TEXT,
  #     tier TEXT,
  #     rate_limit INTEGER,
  #     created_at TIMESTAMP,
  #     last_used TIMESTAMP
  # );
  ```
- [ ] Add usage tracking (Phase 2+):
  - Log API calls to SQLite audit.db (Epic 7)
  - Track: timestamp, user, endpoint, latency, status code
  - Generate usage reports

**Files Modified:**
- `scripts/api_auth.py` (new authentication module)
- `scripts/api_server.py` (add authentication to endpoints)
- `scripts/generate_api_key.py` (new key generation script)
- `requirements.txt` (add slowapi for rate limiting)

**Definition of Done:**
- API key authentication working
- Rate limiting enforced (100 req/min default)
- 401 responses for invalid/missing keys
- 429 responses for rate limit exceeded
- API key generation script working
- Documentation updated with auth instructions

---

### Story 3.3: API Documentation & Client SDKs

**Status:** ⏳ PENDING

As a **third-party developer**,
I want **comprehensive API documentation and client SDKs**,
So that **I can integrate Alexandria into my applications quickly**.

**Acceptance Criteria:**

**Given** I visit the API documentation at `/docs`
**When** I view the Swagger UI
**Then** I see:
  - All endpoints documented with descriptions
  - Request/response schemas with examples
  - Authentication requirements clearly marked
  - Try-it-out functionality for testing

**Given** I want to integrate Alexandria into a Python app
**When** I use the Python SDK
**Then** I can query Alexandria with simple code:
```python
from alexandria_client import AlexandriaClient

client = AlexandriaClient(api_key="alex_abc123...", base_url="http://localhost:8000")
results = client.query("What is Nietzsche's view on suffering?", top_k=5)
print(results.answer)
for source in results.sources:
    print(f"- {source['book_title']}: {source['text'][:100]}...")
```

**Given** I want to integrate Alexandria into a JavaScript app
**When** I use the provided fetch examples
**Then** I can query the API:
```javascript
const response = await fetch('http://localhost:8000/api/v1/query', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': 'alex_abc123...'
  },
  body: JSON.stringify({
    query: "What is Nietzsche's view on suffering?",
    top_k: 5
  })
});
const data = await response.json();
console.log(data.answer);
```

**Technical Tasks:**

- [ ] Enhance Swagger/OpenAPI documentation in `api_server.py`:
  ```python
  @app.post(
      "/api/v1/query",
      summary="Semantic search with RAG answer",
      description="Perform semantic search across book collection and optionally generate an answer using LLM.",
      response_model=QueryResponse,
      responses={
          200: {"description": "Successful query with results"},
          401: {"description": "Invalid or missing API key"},
          422: {"description": "Validation error"},
          500: {"description": "Internal server error"}
      },
      tags=["Query"]
  )
  async def query_endpoint(...):
      """
      Semantic search with optional RAG answer generation.

      - **query**: Natural language search query (required)
      - **collection**: Qdrant collection name (default: "alexandria")
      - **top_k**: Number of results to return (1-20, default: 5)
      - **context_mode**: Context retrieval mode (precise, contextual, comprehensive)
      - **response_pattern**: LLM response pattern (free, direct, synthesis, critical)

      Example request:
      ```json
      {
        "query": "What is Nietzsche's view on suffering?",
        "top_k": 5,
        "context_mode": "contextual",
        "response_pattern": "synthesis"
      }
      ```
      """
      pass
  ```
- [ ] Create Python SDK: `clients/python/alexandria_client/`:
  ```python
  # clients/python/alexandria_client/__init__.py
  from typing import Optional, List
  import requests

  class AlexandriaClient:
      def __init__(self, api_key: str, base_url: str = "http://localhost:8000"):
          self.api_key = api_key
          self.base_url = base_url.rstrip('/')
          self.headers = {
              "X-API-Key": api_key,
              "Content-Type": "application/json"
          }

      def query(
          self,
          query: str,
          collection: str = "alexandria",
          top_k: int = 5,
          context_mode: str = "contextual",
          response_pattern: str = "free"
      ) -> dict:
          """Perform semantic search with RAG answer."""
          response = requests.post(
              f"{self.base_url}/api/v1/query",
              headers=self.headers,
              json={
                  "query": query,
                  "collection": collection,
                  "top_k": top_k,
                  "context_mode": context_mode,
                  "response_pattern": response_pattern
              }
          )
          response.raise_for_status()
          return response.json()

      def search(self, title: str = None, author: str = None) -> List[dict]:
          """Search books by metadata."""
          params = {}
          if title:
              params["title"] = title
          if author:
              params["author"] = author
          response = requests.get(
              f"{self.base_url}/api/v1/search",
              headers=self.headers,
              params=params
          )
          response.raise_for_status()
          return response.json()
  ```
- [ ] Create JavaScript examples: `clients/javascript/examples.js`:
  ```javascript
  // Using fetch API
  async function queryAlexandria(query) {
      const response = await fetch('http://localhost:8000/api/v1/query', {
          method: 'POST',
          headers: {
              'Content-Type': 'application/json',
              'X-API-Key': 'your-api-key-here'
          },
          body: JSON.stringify({
              query: query,
              top_k: 5,
              context_mode: 'contextual'
          })
      });

      if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
  }

  // Usage
  queryAlexandria("What is Nietzsche's view on suffering?")
      .then(data => console.log(data))
      .catch(error => console.error('Error:', error));
  ```
- [ ] Create curl examples: `docs/api/curl-examples.md`:
  ```bash
  # Query endpoint
  curl -X POST "http://localhost:8000/api/v1/query" \
    -H "X-API-Key: alex_abc123..." \
    -H "Content-Type: application/json" \
    -d '{
      "query": "What is Nietzsche'"'"'s view on suffering?",
      "top_k": 5
    }'

  # Search endpoint
  curl -X GET "http://localhost:8000/api/v1/search?author=Nietzsche" \
    -H "X-API-Key: alex_abc123..."

  # Health check (no auth required)
  curl -X GET "http://localhost:8000/api/v1/health"
  ```
- [ ] Create API deployment guide: `docs/deployment/api-server.md`:
  - Deployment options: Docker, systemd service, manual
  - Environment configuration
  - Reverse proxy setup (nginx, caddy)
  - SSL/TLS configuration
  - Monitoring and logging
- [ ] Package Python SDK: `clients/python/setup.py`:
  ```python
  setup(
      name="alexandria-client",
      version="1.0.0",
      description="Python client for Alexandria RAG API",
      packages=["alexandria_client"],
      install_requires=["requests>=2.28.0"]
  )
  ```

**Files Modified:**
- `scripts/api_server.py` (enhance Swagger docs)
- `clients/python/alexandria_client/__init__.py` (new Python SDK)
- `clients/python/setup.py` (new SDK packaging)
- `clients/javascript/examples.js` (new JS examples)
- `docs/api/curl-examples.md` (new curl examples)
- `docs/deployment/api-server.md` (new deployment guide)

**Definition of Done:**
- Swagger UI fully documented with examples
- Python SDK created and installable via pip
- JavaScript examples working
- curl examples documented
- API deployment guide complete
- All client examples tested and working

---

## Epic Summary

**Total Stories:** 3
**Status:** 🔄 IN PROGRESS (MCP server and Python lib done; HTTP API pending)

**Completed Features:**
- ✅ Tier 1 (MCP): stdio protocol for Claude Code - `scripts/mcp_server.py`
- ✅ Tier 3 (Python lib): Direct import from scripts/ package

**Pending Features:**
- ⏳ Tier 2 (HTTP): FastAPI REST API wrapper
- ⏳ API authentication & rate limiting
- ⏳ Swagger/OpenAPI documentation
- ⏳ Client SDKs (Python, JavaScript)
- ⏳ API deployment guide

**Dependencies:**
- None (standalone epic)

**Risks:**
- Rate limiting may impact legitimate high-volume users (mitigation: tiered limits)
- API key management in-memory is not persistent (mitigation: Phase 2+ SQLite storage)
- CORS configuration may be too permissive in Phase 1 (mitigation: restrict domains in Phase 2+)

**Success Metrics:**
- HTTP API responds to requests in < 6 seconds
- API authentication blocks unauthorized access (0% false positives)
- Swagger UI provides complete API documentation
- Python SDK installable and functional
- JavaScript examples work in browser and Node.js
