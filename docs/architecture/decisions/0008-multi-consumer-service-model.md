# ADR-0008: Alexandria as Multi-Consumer Knowledge Service

## Status
**Accepted** (2026-01-31)

## Date
2026-01-31

## Context

Alexandria was initially built as a personal RAG tool with a Streamlit GUI. Over time, the architecture evolved to support multiple access patterns:

- **MCP Server** for Claude Code integration (ADR-0003)
- **CLI tools** for batch operations and scripting
- **Streamlit GUI** for visual exploration (now secondary)
- **Multiple Qdrant collections** for different use cases (ADR-0006)

**Current Reality:**
- AI agents in other projects need interdisciplinary knowledge from Alexandria
- CWA (Calibre Web Automated) could benefit from semantic search integration
- Future consumers (web apps, other AI systems) may want to query the knowledge base

**Problem:**
- Architecture documentation focuses on MCP/CLI/GUI, not on Alexandria **as a service**
- No formal definition of what Alexandria provides to external consumers
- No guidance on how new consumers should integrate
- No versioning strategy for the service contract

**Key Insight:** Alexandria is not just a "RAG app" - it's **knowledge infrastructure** that multiple consumers can build on, similar to how context7 provides codebase knowledge to AI agents.

## Decision

**Formalize Alexandria as a Multi-Consumer Knowledge Service with clearly defined service boundaries, consumer patterns, and extension points.**

### Core Service Definition

Alexandria is a **knowledge retrieval service** that provides:

1. **Semantic Search** - Vector similarity search over book content
2. **Contextual Retrieval** - Hierarchical chunk retrieval (parent/child, siblings)
3. **Metadata Search** - Calibre-based filtering (author, title, tags, series)
4. **Ingestion Pipeline** - Book processing with configurable chunking strategies
5. **Collection Management** - Isolated namespaces for different use cases

### Consumer Types

**Primary Consumer (Tier 1): MCP Clients**
- **Examples:** Claude Code, other MCP-compatible AI assistants
- **Interface:** stdio protocol via FastMCP
- **Tools:** 11+ MCP tools (query, search, ingest, stats)
- **Priority:** Highest - MCP is the primary interface (ADR-0003)

**Secondary Consumers (Tier 2): HTTP Clients**
- **Examples:** Web apps (CWA), remote AI agents, microservices
- **Interface:** REST API (FastAPI wrapper, see ADR-0009)
- **Endpoints:** Subset of MCP tools exposed via HTTP
- **Priority:** Medium - supports integration scenarios MCP can't serve

**Tertiary Consumers (Tier 3): Python Library**
- **Examples:** Python scripts, Jupyter notebooks, local AI agents
- **Interface:** Direct import from `scripts/` package
- **API:** Python functions (`perform_rag_query()`, `ingest_book()`, etc.)
- **Priority:** Low - internal use, no stability guarantees

### Service Contract Guarantees

**What Alexandria PROMISES to consumers:**

1. **Semantic Search Stability**
   - Embedding model: `all-MiniLM-L6-v2` (384-dim) - immutable without migration
   - Distance metric: COSINE - immutable without collection recreation
   - Query interface: `query_text`, `limit`, `threshold`, `context_mode`

2. **Qdrant Payload Structure**
   - Core fields guaranteed: `text`, `book_title`, `author`, `section_name`, `language`
   - Hierarchical fields: `chunk_level`, `parent_id`, `sequence_index` (if hierarchical)
   - Metadata: Additional fields may be added (backward compatible)

3. **Collection Isolation** (ADR-0006)
   - Collections are independent namespaces
   - No cross-collection queries
   - Consumer-specific collections supported

4. **Graceful Degradation**
   - Search works without LLM (OpenRouter API optional)
   - Ingestion works without Calibre (local file mode)
   - Core functionality never depends on optional features

**What Alexandria DOES NOT guarantee:**

- ❌ Internal implementation details (chunking algorithm may evolve)
- ❌ Python function signatures (scripts/ package is internal)
- ❌ Qdrant server availability (consumer's deployment responsibility)
- ❌ LLM answer generation quality (depends on external OpenRouter API)

### Integration Patterns

**Pattern 1: MCP Integration (Recommended)**
```yaml
# .mcp.json
{
  "mcpServers": {
    "alexandria": {
      "command": "python",
      "args": ["c:/path/to/scripts/mcp_server.py"],
      "env": {
        "QDRANT_HOST": "192.168.0.151",
        "QDRANT_PORT": "6333"
      }
    }
  }
}
```

**Pattern 2: HTTP Integration (For Web Apps)**
```python
# Consumer code (e.g., CWA fork)
import requests

response = requests.post("http://192.168.0.151:8000/api/v1/query", json={
    "query": "What does Silverston say about shipment?",
    "collection": "alexandria",
    "limit": 5,
    "context_mode": "contextual"
})
results = response.json()
```

**Pattern 3: Python Library (Internal Use Only)**
```python
# Local Python script
from scripts.rag_query import perform_rag_query

result = perform_rag_query(
    query="your question",
    collection="ai_agents",
    limit=10
)
```

### Extension Points

Consumers can customize behavior via:

1. **Chunking Parameters** (MCP tools, HTTP API)
   - `threshold`: Semantic similarity threshold (0.0-1.0)
   - `min_chunk_size`, `max_chunk_size`: Size constraints

2. **Context Modes** (Query interface)
   - `precise`: Child chunks only (fastest)
   - `contextual`: Child + parent context
   - `comprehensive`: Child + parent + siblings

3. **Response Patterns** (MCP only, future HTTP)
   - Templated prompts: `tldr`, `synthesis`, `critical`, etc.

4. **Custom Collections** (All consumers)
   - Create dedicated collections per project/domain
   - Isolation prevents cross-contamination

## Consequences

### Positive

- ✅ **Clear service boundaries** - Consumers know what to depend on
- ✅ **Multiple integration paths** - MCP, HTTP, Python library
- ✅ **Explicit stability contract** - Breaking changes are visible
- ✅ **Future-proof** - New consumers can integrate without changing core
- ✅ **Collection isolation** - Consumers don't interfere with each other
- ✅ **Graceful degradation** - Optional features don't block core functionality

### Negative

- ⚠️ **Increased maintenance burden** - Service contract must be honored
- ⚠️ **Breaking changes become costly** - Consumers may depend on stable API
- ⚠️ **Testing complexity** - Must validate multiple consumer patterns
- ⚠️ **Documentation overhead** - Service contract needs ongoing updates

### Neutral

- 🔄 **MCP remains primary** - HTTP is additive, not replacement
- 🔄 **Python library is internal** - No public API guarantees for scripts/
- 🔄 **Deployment flexibility** - Single-machine or distributed (NAS, Docker)

## Implementation

### Component
- **Service Layer** - Entire Alexandria system (MCP Server + Scripts Package)
- **Consumer Integrations** - External systems calling Alexandria

### Files
**Core Service:**
- `scripts/mcp_server.py` - MCP interface (Tier 1 consumers)
- `scripts/rag_query.py` - Query engine (all consumers)
- `scripts/ingest_books.py` - Ingestion pipeline (all consumers)
- `scripts/qdrant_utils.py` - Collection management

**Future HTTP API (ADR-0009):**
- `scripts/http_api.py` - FastAPI wrapper (Tier 2 consumers)

**Documentation:**
- `docs/architecture/mcp-server.md` - MCP tool reference
- `docs/architecture/decisions/0008-multi-consumer-service-model.md` (this ADR)

### Story
Brownfield architecture documentation - formalizes existing patterns

## Alternatives Considered

### Alternative 1: Single-Consumer Architecture
**Rejected because:**
- Already serving multiple consumers (MCP, CLI, GUI)
- Future needs (CWA, AI agents) require multi-consumer model
- Would artificially constrain Alexandria's utility

### Alternative 2: Microservice with Only HTTP API
**Rejected because:**
- MCP is the primary interface (ADR-0003)
- HTTP adds deployment complexity
- Single-user desktop app doesn't need full microservice architecture
- Can add HTTP later (ADR-0009) without rebuilding core

### Alternative 3: Versioned Python Package (PyPI)
**Considered:** Publish Alexandria as pip-installable library
**Rejected because:**
- scripts/ package is internal implementation, not public API
- Packaging overhead not justified for single-user tool
- Can reconsider if multi-team adoption happens

## Related Decisions

- **ADR-0003: GUI as Thin Layer** - Established MCP-first, scripts/ as single source of truth
- **ADR-0006: Separate Collections Architecture** - Collection isolation enables multi-consumer model
- **ADR-0009: HTTP API Wrapper** - Implements Tier 2 consumer support
- **ADR-0001: Use Qdrant Vector DB** - Service depends on Qdrant availability

## References

- **C4 Diagrams:**
  - [System Context](../c4/01-context.md) - External systems view
  - [Container Diagram](../c4/02-container.md) - MCP Server architecture

- **Code:**
  - MCP Server: `scripts/mcp_server.py`
  - Query Engine: `scripts/rag_query.py`

- **External Patterns:**
  - **context7** - Codebase knowledge service for AI (inspiration)
  - **Model Context Protocol (MCP)** - Primary integration protocol

---

**Author:** Winston (Architect Agent) + Sabo
**Reviewers:** Sabo (Project Owner)
