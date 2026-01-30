# ADR 0003: GUI as Thin Presentation Layer

## Status
**Superseded** - GUI development abandoned in favor of MCP-first approach (2026-01-30)

The core principle (all logic in `scripts/`) remains valid, but the interface is now MCP Server instead of Streamlit GUI.

See: [docs/reference/mcp-server.md](../../mcp-server.md)

## Date
2026-01-21

## Context

Alexandria needs to support multiple interfaces:
- **Streamlit GUI** for visual interaction
- **CLI tools** for scripting and automation
- **AI agents** for programmatic access
- **Future integrations** (Obsidian, API, etc.)

**Problem:** If business logic is implemented in the GUI, we face:
1. **Duplication:** CLI, agents, and future integrations would duplicate logic
2. **Maintenance burden:** Changes require updates in multiple places
3. **Testing difficulty:** Can't test business logic without GUI overhead
4. **Inconsistency:** Different interfaces might implement logic differently

**Example from history:** Query tab initially had 160+ lines of RAG logic duplicated from `rag_query.py`, leading to divergence and maintenance issues.

## Decision

**All business logic lives in `scripts/` package. GUI is a thin presentation layer.**

### GUI Responsibilities (ONLY)
- Collect user input via widgets
- Call functions from `scripts/` modules
- Display results in formatted UI
- Manage session state for interactivity

### Scripts Responsibilities (ALL LOGIC)
- Book ingestion and processing
- Domain-specific chunking
- Semantic search and RAG queries
- Collection management
- Calibre database integration
- All data transformations

### Example Structure
```python
# ❌ BAD: Logic in GUI
def query_books(query):
    embeddings = model.encode(query)
    results = qdrant.search(embeddings)
    answer = openrouter.generate(results)
    return answer

# ✅ GOOD: GUI calls scripts
from rag_query import perform_rag_query

result = perform_rag_query(query, collection="alexandria", limit=5)
st.write(result.answer)
```

## Consequences

### Positive
- **Single source of truth:** One implementation for all operations
- **Easy testing:** Unit tests without GUI overhead
- **AI agent support:** Agents call functions directly
- **CLI support:** Same logic as GUI
- **Reduced duplication:** Query tab refactoring eliminated 160+ LOC
- **Consistency:** All interfaces use same logic
- **Maintainability:** Changes in one place propagate everywhere

### Negative
- **Extra indirection:** GUI → scripts → external services (adds one hop)
- **Learning curve:** GUI developers must understand scripts package structure
- **Import management:** Need to manage dependencies between GUI and scripts

### Neutral
- **Architecture enforced by convention:** No technical barrier to violating this pattern (requires discipline)

## Implementation

### Component
- **GUI Container** (`alexandria_app.py`)
- **Scripts Package** (all modules in `scripts/`)

### Files
**GUI:**
- `alexandria_app.py` - Streamlit application

**Scripts (imported by GUI):**
- `scripts/ingest_books.py` - Ingestion functions
- `scripts/rag_query.py` - Query functions
- `scripts/collection_manifest.py` - Manifest functions
- `scripts/calibre_db.py` - Calibre functions
- `scripts/qdrant_utils.py` - Qdrant operations

### Story
[04-GUI.md](../../../explanation/stories/04-GUI.md)

### Example Refactoring
**Before (duplicated logic in GUI):**
```python
# alexandria_app.py (lines 894-948)
embeddings = generate_embeddings([query])
results = qdrant_client.search(
    collection_name=collection,
    query_vector=embeddings[0],
    limit=limit * 3
)
# ... 100+ more lines of filtering, reranking, answer generation
```

**After (calls scripts):**
```python
# alexandria_app.py (lines 894-948)
from rag_query import perform_rag_query

result = perform_rag_query(
    query=query,
    collection=collection,
    limit=limit,
    fetch_multiplier=fetch_multiplier,
    similarity_threshold=threshold
)
st.write(result.answer)
```

**Savings:** 160 lines eliminated, single source of truth established.

## Alternatives Considered

### Alternative 1: Business Logic in GUI
**Rejected because:**
- Duplicates logic across CLI and GUI
- Can't test without GUI
- AI agents can't reuse logic
- Maintenance burden increases with each interface

### Alternative 2: GUI as API Client
**Considered:** GUI calls REST API, scripts are API server
**Rejected because:**
- Overkill for single-user desktop application
- Adds deployment complexity
- Requires network layer (latency, error handling)
- Can revisit if multi-user deployment needed

### Alternative 3: Shared Library + GUI
**Considered:** Extract logic to separate library package
**Rejected because:**
- Current `scripts/` package already serves this purpose
- No need for separate packaging (single repository)
- Would add build/distribution complexity

## Related Decisions
- [ADR 0001: Use Qdrant Vector DB](0001-use-qdrant-vector-db.md) - Scripts interact with Qdrant
- [ADR 0002: Domain-Specific Chunking](0002-domain-specific-chunking.md) - Chunking logic in scripts

## References
- **C4 Container Diagram:** [02-container.md](../c4/02-container.md)
- **AGENTS.md:** Lines 104-117 (Architecture Principle section)
- **Code example:** Query tab refactoring (2026-01-22)

---

**Author:** Claude Code + User
**Reviewers:** User (Sabo)
