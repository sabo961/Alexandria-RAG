# ADR-0009: HTTP API Wrapper for Non-MCP Consumers

## Status
**Proposed** (2026-01-31)

Implementation pending - currently in TODO.md as "Read-only public query API (FastAPI)" (P3 - BACKLOG)

## Date
2026-01-31

## Context

ADR-0008 defines Alexandria as a multi-consumer knowledge service with three integration tiers:
1. **MCP (stdio)** - Primary interface for Claude Code
2. **HTTP (REST)** - For web apps, remote agents, microservices
3. **Python library** - For local scripts (internal use)

**Current State:**
- ✅ MCP interface fully implemented (`scripts/mcp_server.py`)
- ✅ Python library usable (`scripts/` package)
- ❌ HTTP interface does not exist

**Problem:**
Web applications and remote systems cannot use stdio-based MCP. Specific use cases:
- **CWA (Calibre Web Automated)** fork wanting semantic search
- **Remote AI agents** running on different machines
- **Web dashboards** for Alexandria monitoring/querying
- **Microservices** needing knowledge retrieval

**Constraint:** FastMCP supports both stdio and HTTP transports, but current implementation only configures stdio.

## Decision

**Build a lightweight FastAPI wrapper that exposes Alexandria's core operations via REST endpoints, reusing MCP tool logic.**

### Architecture Pattern: Thin HTTP Layer

```
┌─────────────────────────────────────────────┐
│  Consumer Applications                      │
│  (CWA, Web Apps, Remote Agents)            │
└────────────┬────────────────────────────────┘
             │ HTTP/JSON
             ▼
┌─────────────────────────────────────────────┐
│  FastAPI HTTP Server (Port 8000)           │
│  - GET  /api/v1/query                      │
│  - POST /api/v1/query                      │
│  - GET  /api/v1/search                     │
│  - GET  /api/v1/books/{id}                 │
│  - GET  /api/v1/stats                      │
│  - GET  /api/v1/health                     │
└────────────┬────────────────────────────────┘
             │ Function calls
             ▼
┌─────────────────────────────────────────────┐
│  Scripts Package (Business Logic)          │
│  - perform_rag_query()                     │
│  - CalibreDB.get_book_by_id()              │
│  - get_collection_stats()                  │
└─────────────────────────────────────────────┘
```

**Key Principle:** HTTP layer is **thin** - it only handles HTTP protocol, validation, and serialization. All business logic remains in `scripts/`.

### API Design

**Base URL:** `http://{host}:{port}/api/v1`

**Endpoints (Read-Only):**

#### 1. Query Endpoint (Semantic Search)
```http
POST /api/v1/query
Content-Type: application/json

{
  "query": "What does Silverston say about shipment patterns?",
  "collection": "alexandria",
  "limit": 5,
  "context_mode": "contextual",
  "threshold": 0.5,
  "generate_answer": false
}

Response: 200 OK
{
  "results": [
    {
      "text": "Chunk text content...",
      "book_title": "The Data Model Resource Book",
      "author": "Len Silverston",
      "score": 0.87,
      "parent_context": "..." // if context_mode != "precise"
    }
  ],
  "count": 5,
  "query_time_ms": 120
}
```

#### 2. Search Endpoint (Metadata Search)
```http
GET /api/v1/search?author=Silverston&collection=alexandria&limit=10

Response: 200 OK
{
  "books": [
    {
      "id": 7970,
      "title": "The Data Model Resource Book",
      "author": "Len Silverston",
      "tags": ["data-modeling", "patterns"],
      "language": "eng"
    }
  ],
  "count": 1
}
```

#### 3. Book Details Endpoint
```http
GET /api/v1/books/7970?collection=alexandria

Response: 200 OK
{
  "id": 7970,
  "title": "The Data Model Resource Book",
  "author": "Len Silverston",
  "publisher": "Wiley",
  "tags": ["data-modeling", "patterns"],
  "series": "The Data Model Resource Book",
  "language": "eng",
  "ingested": true,
  "chunk_count": 342
}
```

#### 4. Collection Stats Endpoint
```http
GET /api/v1/stats?collection=alexandria

Response: 200 OK
{
  "collection": "alexandria",
  "total_books": 150,
  "total_chunks": 23847,
  "unique_authors": 87,
  "languages": ["eng", "hrv", "fra"],
  "last_updated": "2026-01-30T15:42:00Z"
}
```

#### 5. Health Check Endpoint
```http
GET /api/v1/health

Response: 200 OK
{
  "status": "healthy",
  "services": {
    "qdrant": {"status": "up", "host": "192.168.0.151:6333"},
    "calibre": {"status": "up", "books": 9247},
    "openrouter": {"status": "optional", "configured": true}
  },
  "version": "1.0.0"
}
```

### Versioning Strategy

**URL-Based Versioning:** `/api/v1/...`, `/api/v2/...`

**Rules:**
- **v1 (current):** Read-only endpoints (query, search, stats)
- **v2 (future):** Add write operations (ingest) if needed
- **Breaking changes:** Require new version (v2, v3, etc.)
- **Non-breaking changes:** Add optional parameters to existing endpoints

**Stability Guarantee:**
- v1 API will not break once released
- New fields can be added to responses (consumers should ignore unknown fields)
- Deprecated endpoints get 6-month notice before removal

### Authentication & Security

**Phase 1 (MVP): No Authentication**
- Deployed on trusted local network (192.168.0.151)
- Firewall blocks external access
- Suitable for: Local web apps, CWA integration

**Phase 2 (Optional): API Key Authentication**
```http
POST /api/v1/query
Authorization: Bearer alex_sk_abc123...
```

**Phase 3 (Future): OAuth2**
- Only if multi-user deployment becomes necessary

### Deployment Model

**Option 1: Standalone HTTP Server (Recommended for MVP)**
```bash
# Run FastAPI server on port 8000
cd scripts
uvicorn http_api:app --host 0.0.0.0 --port 8000
```

**Option 2: Docker Deployment (NAS)**
```dockerfile
FROM python:3.14
WORKDIR /app
COPY scripts/ ./scripts/
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN pip install fastapi uvicorn
EXPOSE 8000
CMD ["uvicorn", "scripts.http_api:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Option 3: Systemd Service (Linux)**
```ini
# /etc/systemd/system/alexandria-api.service
[Unit]
Description=Alexandria HTTP API
After=network.target

[Service]
Type=simple
User=alexandria
WorkingDirectory=/opt/alexandria
ExecStart=/usr/bin/uvicorn scripts.http_api:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

### CORS Configuration

**Development:**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8501"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"]
)
```

**Production (NAS):**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://192.168.0.151:*"],  # Only local network
    allow_methods=["GET", "POST"],
    allow_headers=["*"]
)
```

## Consequences

### Positive

- ✅ **Web app integration** - CWA, custom dashboards can query Alexandria
- ✅ **Remote access** - AI agents on different machines can connect
- ✅ **Standard protocol** - REST is universal (no MCP client needed)
- ✅ **Reuses logic** - Calls same scripts/ functions as MCP
- ✅ **Stateless** - No session management needed
- ✅ **Lightweight** - FastAPI is minimal overhead
- ✅ **Future-proof** - Can add auth, rate limiting, caching later

### Negative

- ⚠️ **Additional deployment** - Must run HTTP server alongside MCP
- ⚠️ **Network exposure** - HTTP is less secure than stdio
- ⚠️ **Versioning burden** - Must maintain API compatibility
- ⚠️ **Testing complexity** - Need HTTP integration tests
- ⚠️ **Monitoring needed** - Health checks, error tracking, logging

### Neutral

- 🔄 **MCP still primary** - HTTP is secondary interface (ADR-0008)
- 🔄 **Read-only initially** - Write operations (ingest) are future scope
- 🔄 **Optional feature** - Core Alexandria works without HTTP layer

## Implementation

### Component
- **HTTP API Server** - New FastAPI application in `scripts/http_api.py`

### Files

**New:**
- `scripts/http_api.py` - FastAPI application and routes
- `tests/test_http_api.py` - HTTP endpoint tests
- `docker/Dockerfile.api` - Docker container (optional)
- `docs/architecture/http-api.md` - API reference documentation

**Modified:**
- `requirements.txt` - Add `fastapi`, `uvicorn`, `pydantic`
- `docs/architecture/README.md` - Update deployment section
- `.env.example` - Add `HTTP_API_PORT`, `HTTP_API_HOST`

### Story
**TODO.md (P3 - BACKLOG):**
- "Read-only public query API (FastAPI)"

**New items to add:**
- HTTP API authentication (Phase 2)
- HTTP API monitoring/logging (Phase 2)
- Ingest endpoints (Phase 3)

## Alternatives Considered

### Alternative 1: MCP over HTTP (FastMCP Feature)
**Considered:** Use FastMCP's built-in HTTP transport
**Rejected because:**
- MCP protocol overhead for simple REST queries
- Harder for web apps to integrate (need MCP client library)
- Less standard than plain REST API

### Alternative 2: GraphQL API
**Considered:** Use GraphQL instead of REST
**Rejected because:**
- Overkill for simple query/search operations
- Higher learning curve for consumers
- More complex implementation (schema, resolvers)
- REST is simpler and sufficient

### Alternative 3: Embed HTTP Server in MCP Server
**Considered:** Single process serving both MCP and HTTP
**Rejected because:**
- Violates single responsibility principle
- MCP Server should focus on stdio protocol
- Separate processes allow independent scaling
- Easier to disable HTTP if not needed

### Alternative 4: gRPC API
**Considered:** Use gRPC for performance
**Rejected because:**
- Web browsers don't support gRPC natively (need gRPC-Web)
- REST is more accessible for web apps
- Performance difference negligible for knowledge queries
- Can add gRPC later if needed

## Related Decisions

- **ADR-0008: Multi-Consumer Service Model** - Defines HTTP as Tier 2 consumer interface
- **ADR-0003: GUI as Thin Layer** - Same principle: HTTP layer calls scripts/
- **ADR-0006: Separate Collections** - HTTP API respects collection isolation

## References

- **FastAPI Documentation:** https://fastapi.tiangolo.com/
- **MCP Server Reference:** [mcp-server.md](../mcp-server.md)
- **Implementation Guide:** [TODO.md](../../../TODO.md) (P3 - BACKLOG)

---

**Author:** Winston (Architect Agent) + Sabo
**Reviewers:** Sabo (Project Owner)
**Status:** Proposed - Awaiting implementation

---

## Implementation Checklist (When Ready)

- [ ] Create `scripts/http_api.py` with FastAPI app
- [ ] Implement read-only endpoints (query, search, stats, health)
- [ ] Add Pydantic models for request/response validation
- [ ] Write HTTP integration tests (`tests/test_http_api.py`)
- [ ] Update `requirements.txt` with FastAPI dependencies
- [ ] Document API in `docs/architecture/http-api.md`
- [ ] Add deployment instructions (Docker, systemd, uvicorn)
- [ ] Configure CORS for local network access
- [ ] Add health check endpoint for monitoring
- [ ] Update architecture README with HTTP deployment section
