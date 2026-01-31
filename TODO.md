# Alexandria TODO List

**Purpose:** Lightweight backlog of ideas for active development.

For completed work, see [CHANGELOG.md](CHANGELOG.md).
For stable reference documentation, see [AGENTS.md](AGENTS.md) and [docs/project-context.md](docs/project-context.md).

**Last Updated:** 2026-01-30

---

## 🔴 HIGH PRIORITY

### Hierarchical Chunking (P0) - PHASE 0+1 COMPLETE

**Goal:** Two-level chunking (parent=chapter, child=semantic) for better context retrieval.

**Phase 0: Basic Hierarchy** (Est. 2 days) - ✅ IMPLEMENTATION COMPLETE
- [x] **Implementation Plan** - Completed and archived
- [x] **Chapter Detection Module** - Created `scripts/chapter_detection.py` (EPUB NCX/NAV, PDF outline, fallback)
- [x] **Data Model Extension** - Parent/child payloads with `chunk_level`, `parent_id`, `sequence_index`
- [x] **Hierarchical Ingestion** - `ingest_book(hierarchical=True)` creates parent+child structure
- [x] **Contextual Retrieval** - `perform_rag_query(context_mode="contextual")` fetches parent context
- [x] **Test with 5 books** - Nietzsche, Kahneman, Silverston, Mishima, Taleb (3476 points: 198 parents, 3278 children)

**Phase 1: MCP Integration** (Est. 1 day) - ✅ COMPLETE
- [x] **Context Mode in MCP** - `alexandria_query(context_mode="precise|contextual|comprehensive")`
- [x] **Hierarchical Ingest Flag** - `alexandria_ingest(hierarchical=True|False)` and `alexandria_ingest_file`
- [x] **Parent Context in Response** - Returns `parent_chunks` and `hierarchy_stats` when context_mode != "precise"

**Phase 2+:** Evaluation, Comprehensive Mode (siblings), Full Re-ingestion

**Reference:** See `scripts/chapter_detection.py` and `scripts/ingest_books.py` for implementation details.

---

### MCP Server Enhancement (P0) - STRATEGIC FOCUS

**Decision:** GUI development abandoned. MCP server is the primary interface for Alexandria.

- [x] **Local file ingestion** - `alexandria_ingest_file` and `alexandria_test_chunking_file` (implemented 2026-01-30)
- [x] **Progress tracking (basic)** - Step-by-step progress with visual bar in response (implemented 2026-01-30)
- [x] **Configurable chunking parameters** - `threshold`, `min_chunk_size`, `max_chunk_size` in both ingest tools
- [x] **Batch ingest tool** - `alexandria_batch_ingest(book_ids=[...])` or `(author="...", limit=10)`
- [ ] **Re-ingest option** - Allow re-ingest with different parameters (bypass manifest check)
- [x] **Context mode support** - `alexandria_query(context_mode="precise|contextual|comprehensive")`
- [x] **Response patterns** - `alexandria_query(response_pattern="free|direct|synthesis|critical|...")`

---

### Stability & Determinism (P1)

- [ ] **Ingest Versioning** - Add `ingest_version`, `chunking_strategy`, `embedding_model` to Qdrant payload for safe re-ingestion and comparison
- [ ] **Chunk Fingerprint** - Add `chunk_fingerprint = sha1(book_id + section + order + text)` for diff and selective re-index
- [ ] **Retrieval Explain Mode** - Add `--explain` flag to show score, distance, chunk_id, book for debugging
- [ ] **Manual Chunking Parameters vs Automatic Optimization** - Design decision: Keep automatic-only or add manual override controls? (⏸️ ON HOLD - awaiting real-world usage feedback)
- [ ] **Multiple API Keys (not only OpenRouter)** - multiple AI API keys!!
---

## 🟡 MEDIUM PRIORITY

### Knowledge Quality & Control (P1)

- [x] **Response Patterns** - Implemented via `prompts/patterns.json` with RAG-discipline templates (direct, synthesis, critical, etc.)
- [ ] **Retrieval Self-Test Suite** - Canonical questions with snapshot of expected sources for regression protection
- [ ] **Source Attribution Metrics** - Measure how well answers cite retrieved sources vs. hallucinate

---

## 🟢 LOW PRIORITY

### Operational Ergonomics (P2)

- [ ] **Ingest Diff Tool** - Script to compare two ingestion versions (chunk count, size, coverage)
- [ ] **Soft Delete + Re-Ingest Flow** - Flag `active=false` in payload instead of physical deletion
- [ ] **Performance Telemetry** - Log times for embedding, upload, search, LLM answer generation
- [ ] **Advanced Query Features** - Multi-query mode, query history, export results, pagination for large results
- [ ] **Collection Management** - Copy/merge collections, collection diff, backup/restore

---

## 🔵 BACKLOG

### Strategic, Low-Risk Additions (P3)

- [ ] **Pluggable Embedding Backends** - Adapter pattern for multiple embedding models
- [ ] **Read-Only Public Query API** - Minimal FastAPI wrapper without ingestion capabilities
- [ ] **NAS Deployment** - Deploy Alexandria as Docker container on NAS for 24/7 multi-device access
- [ ] **Calibre Metadata Enhancement** - Store tags, rating, publisher, ISBN, publication date in Qdrant payloads
- [ ] **Multi-Format Preference** - Auto-select preferred format when multiple available (EPUB > PDF > MOBI)
- [ ] **Duplicate Detection** - Avoid ingesting same book twice (fuzzy title, ISBN, content hash)
- [ ] **MOBI Support** - Convert MOBI → EPUB for ingestion

---

## Anti-Goals (Consciously NOT Doing)

- ❌ **Complex GUI** - Simplified to single-page dashboard (`alexandria_app.py`). MCP + Claude Code is primary interface.
- ❌ **Domain tagging** - Content determines topic, not pre-assigned labels. Removed domain concept entirely.
- ❌ **Multiple ingestion pipelines** - Keep single universal pipeline
- ❌ Shared Qdrant ownership - Single source of truth
- ❌ Framework-heavy RAG - Avoid LangChain/similar (keep simple)

---

## Mental Compass

> MCP server is the primary interface. If a feature can't be exposed via MCP tools, reconsider its value.

---

**Last Updated:** 2026-01-30
**Status:** Lightweight backlog for BMad workflow integration
**For completed work:** See [CHANGELOG.md](CHANGELOG.md)
