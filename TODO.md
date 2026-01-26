# Alexandria TODO List

**Purpose:** Lightweight backlog of ideas for active development.

For completed work, see [CHANGELOG.md](CHANGELOG.md).
For stable reference documentation, see [AGENTS.md](AGENTS.md) and [_bmad-output/project-context.md](_bmad-output/project-context.md).

**Last Updated:** 2026-01-26

---

## 🔴 HIGH PRIORITY

### Stability & Determinism (P0)

- [ ] **Ingest Versioning** - Add `ingest_version`, `chunking_strategy`, `embedding_model` to Qdrant payload for safe re-ingestion and comparison
- [ ] **Chunk Fingerprint** - Add `chunk_fingerprint = sha1(book_id + section + order + text)` for diff and selective re-index
- [ ] **Retrieval Explain Mode** - Add `--explain` flag to show score, distance, chunk_id, book for debugging
- [ ] **Manual Chunking Parameters vs Automatic Optimization** - Design decision: Keep automatic-only or add manual override controls? (⏸️ ON HOLD - awaiting real-world usage feedback)

---

## 🟡 MEDIUM PRIORITY

### Knowledge Quality & Control (P1)

- [ ] **Query Modes** - Single endpoint with multiple modes: `fact`, `cite`, `explore`, `synthesize` for predictable behavior
- [ ] **Domain-Aware Retrieval Weights** - Domain weight multiplier (philosophy > fiction) for better recall
- [ ] **Retrieval Self-Test Suite** - Canonical questions per domain with snapshot of expected sources for regression protection
- [x] **Real-Time Progress Tracking** - Show live progress during batch ingestion in GUI
- [ ] **Resume Functionality in GUI** - Resume interrupted batch ingestion from GUI

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

- ❌ Multiple ingestion pipelines - Keep single universal pipeline
- ❌ Logic in GUI - All business logic stays in `scripts/`
- ❌ Shared Qdrant ownership - Single source of truth
- ❌ Framework-heavy RAG - Avoid LangChain/similar (keep simple)

---

## Mental Compass

> If an improvement doesn't fit in `scripts/` without changing clients — it's probably not a good idea.

---

**Last Updated:** 2026-01-25
**Status:** Lightweight backlog for BMad workflow integration
**For completed work:** See [CHANGELOG.md](CHANGELOG.md)
