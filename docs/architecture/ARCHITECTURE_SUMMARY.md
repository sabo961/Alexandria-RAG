# Alexandria RAG System - Architecture Summary

**One-page reference for the complete Alexandria architecture**

---

## System Overview

**Alexandria** is a RAG (Retrieval-Augmented Generation) system that enables semantic search and knowledge synthesis across a multi-disciplinary library of ~9,000 books. It uses vector embeddings for semantic search, intelligent chunking for context preservation, and LLM integration for natural language answers.

**Key Capabilities:**
- 📚 Browse and search Calibre library (9,000+ books)
- 🔍 Semantic search across all ingested books
- 🤖 LLM-powered answer generation with source citations
- 📊 Multi-domain support (technical, psychology, philosophy, history, literature)
- 🎯 Universal semantic chunking (topic-aware text splitting)

---

## C4 Architecture Layers

### Level 1: System Context

```
[Developer/Researcher]
         ↓
   [Alexandria RAG System]
         ↓ ↑
    ┌────┴────┬──────────────┐
    ↓         ↓              ↓
[Qdrant]  [OpenRouter]  [Calibre DB]
```

**External Systems:**
- **Qdrant (192.168.0.151:6333)** - Vector database storing 384-dim embeddings
- **OpenRouter API** - LLM inference (GPT-4, Claude, Llama, etc.)
- **Calibre Library** - Book metadata and file storage

**See:** [docs/architecture/c4/01-context.md](c4/01-context.md)

---

### Level 2: Containers

```
Alexandria RAG System
├── Streamlit GUI (Web Browser)
├── Scripts Package (Python Modules)
├── File System (Book Storage + Logs)
└── Calibre Database (SQLite)
```

**Container Details:**

**1. Streamlit GUI** - Web interface (Python 3.14, Streamlit)
   - Browse Calibre library with filters
   - Trigger book ingestion with domain assignment
   - Execute RAG queries with parameter controls
   - Display collection statistics and manifests

**2. Scripts Package** - Core business logic (Python modules)
   - `ingest_books.py` - Book ingestion and chunking
   - `universal_chunking.py` - Semantic text splitting
   - `rag_query.py` - RAG query engine
   - `collection_manifest.py` - Collection tracking
   - `calibre_db.py` - Calibre integration

**3. File System** - Local storage
   - `ingest/` - Books waiting to be processed
   - `ingested/` - Successfully processed books
   - `logs/` - Collection manifests (JSON/CSV)

**4. Calibre Database** - SQLite metadata store
   - Book metadata (title, author, series, tags)
   - File paths and formats
   - Read-only access

**See:** [docs/architecture/c4/02-container.md](c4/02-container.md)

---

### Level 3: Components (Scripts Package)

```
Scripts Package
├── Ingestion Engine (ingest_books.py)
├── Universal Semantic Chunker (universal_chunking.py)
├── RAG Query Engine (rag_query.py)
├── Collection Management (collection_manifest.py)
└── Calibre Integration (calibre_db.py)
```

**Component Responsibilities:**

**Ingestion Engine:**
- Extract text from EPUB/PDF/TXT files
- Coordinate chunking and embedding
- Upload to Qdrant with metadata
- Log to manifest system

**Universal Semantic Chunker:**
- Split text by semantic topic boundaries
- Use sentence embeddings + cosine similarity
- Enforce min/max chunk size constraints
- Domain-agnostic approach

**RAG Query Engine:**
- Embed user query
- Search Qdrant with filters
- Apply similarity threshold
- Optional LLM reranking
- Generate answers via OpenRouter

**Collection Management:**
- Track ingested books per collection
- Export manifests to JSON/CSV
- Auto-reset on collection deletion
- Resume interrupted batch ingestion

**Calibre Integration:**
- Direct SQLite access to metadata.db
- Browse library with filters
- Provide file paths for ingestion
- Library statistics

**See:** [docs/architecture/c4/03-component.md](c4/03-component.md)

---

## Data Flows

### Ingestion Flow

```
1. User selects book in GUI
2. GUI → Ingestion Engine (file path + domain)
3. Ingestion Engine → Text Extractor (EPUB/PDF/TXT)
4. Text Extractor → Universal Semantic Chunker (raw text)
5. Chunker → Embedder (sentence embeddings for similarity)
6. Chunker splits at semantic boundaries (threshold-based)
7. Embedder → Qdrant Uploader (chunk embeddings)
8. Uploader → Qdrant (batch upsert with metadata)
9. Uploader → Collection Management (log to manifest)
```

**Key Insight:** Chunks are created by semantic similarity, not word count. This preserves conceptual integrity.

---

### Query Flow

```
1. User enters query in GUI
2. GUI → RAG Query Engine (query + parameters)
3. Query Engine → Embedder (embed query)
4. Query Engine → Qdrant (search with filters)
5. Qdrant → Query Engine (top K chunks)
6. Query Engine filters by similarity threshold
7. (Optional) Query Engine → OpenRouter (LLM reranking)
8. Query Engine → OpenRouter (generate answer with context)
9. OpenRouter → Query Engine (natural language answer)
10. Query Engine → GUI (answer + source citations)
```

**Key Insight:** Threshold filtering removes irrelevant results before LLM sees them, improving answer quality.

---

## Key Technologies

| Component | Technology | Purpose |
|-----------|-----------|---------|
| GUI | Streamlit | Web interface |
| Backend | Python 3.14 | All business logic |
| Vector DB | Qdrant | Semantic search (cosine distance) |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) | 384-dim vectors |
| LLM API | OpenRouter | Multi-model inference |
| Book Metadata | Calibre (SQLite) | Library management |
| Text Extraction | PyMuPDF, ebooklib | PDF/EPUB parsing |

---

## Universal Semantic Chunking

**Core Algorithm:**

```python
1. Split text into sentences (regex)
2. Embed all sentences (all-MiniLM-L6-v2)
3. For each sentence pair:
   - Calculate cosine similarity
   - If similarity < threshold AND buffer >= min_size:
     → Create chunk
   - Else:
     → Add to buffer
4. Enforce max_chunk_size safety cap
```

**Parameters:**
- **Threshold:** 0.55 (default), 0.45 (philosophy) - Lower = more splits
- **Min chunk size:** 200 words - Prevents atomic chunks
- **Max chunk size:** 1200 words - Safety cap for LLM context

**Benefits:**
- ✅ Semantic integrity (breaks at topic boundaries)
- ✅ Domain-agnostic (same logic for all content)
- ✅ Adaptive (automatically adjusts to content structure)
- ✅ Context preservation (minimum buffer ensures LLM has context)

**See:** [docs/architecture/technical/UNIVERSAL_SEMANTIC_CHUNKING.md](technical/UNIVERSAL_SEMANTIC_CHUNKING.md)

---

## Architecture Principles

### 1. Scripts-First Architecture

**Principle:** All business logic lives in `scripts/` package. GUI is a thin presentation layer.

**Why?**
- Single source of truth (no duplication)
- Multiple interfaces (GUI, CLI, AI agents)
- Easy testing (no GUI overhead)
- Clear separation of concerns

**See:** [ADR 0003: GUI as Thin Layer](decisions/0003-gui-as-thin-layer.md)

---

### 2. Collection Isolation

**Principle:** Each collection has separate manifests, progress files, and can use different settings.

**Why?**
- Prevents cross-contamination
- Allows experimentation (test different chunking strategies)
- Supports multiple use cases (personal library, research corpus, client project)

**Files:**
- `logs/{collection}_manifest.json` - Master manifest
- `logs/{collection}_manifest.csv` - Human-readable export
- `scripts/batch_ingest_progress_{collection}.json` - Resume tracker

**See:** [ADR 0004: Collection-Specific Manifests](decisions/0004-collection-specific-manifests.md)

---

### 3. Progressive Enhancement

**Principle:** Core functionality works with minimal dependencies. Advanced features are optional.

**Examples:**
- Ingestion works without Calibre DB (use folder ingestion)
- Query works without OpenRouter (search-only mode, no answer generation)
- GUI is optional (CLI works standalone)

**Why?**
- Easier onboarding (start simple, add features as needed)
- Resilience (system degrades gracefully)
- Flexibility (choose features based on use case)

---

## Deployment Architecture

### Current: Single-User Desktop

```
[User's PC]
├── Alexandria (Python scripts + Streamlit GUI)
├── Calibre Library (SQLite)
└── Docker Desktop
    └── Qdrant Container (localhost:6333)
```

**Access:** http://localhost:8501

---

### Future: NAS Deployment (Planned)

```
[NAS - 192.168.0.151]
├── Docker: Alexandria Container
│   ├── Port: 8501 (Streamlit)
│   └── Volumes: /books, /calibre, /logs
├── Docker: Qdrant Container
│   └── Port: 6333
├── Calibre Library (metadata.db)
└── Book Storage (EPUB/PDF files)
```

**Benefits:**
- 24/7 availability
- Multi-device access (phone, tablet, desktop)
- Centralized storage with RAID backup
- Low latency (Alexandria and Qdrant on same host)

**See:** [docs/architecture/c4/02-container.md](c4/02-container.md) - Deployment section

---

## Security

### Current Posture (Single-User)

- **Qdrant:** No authentication (local network only)
- **OpenRouter:** API key in `.streamlit/secrets.toml` (gitignored)
- **Calibre DB:** Read-only access
- **File System:** Local user permissions

### Future Hardening (Multi-User)

- Qdrant authentication (API key or JWT)
- User authentication in GUI (Streamlit auth)
- Role-based access control (read-only vs admin)
- API rate limiting

---

## Performance Characteristics

### Ingestion Throughput

**Benchmark (typical book, ~500 pages):**
- Text extraction: ~5 seconds
- Semantic chunking: ~3-5 seconds
- Embedding generation: ~2 seconds
- Qdrant upload: ~1 second
- **Total:** ~11-13 seconds per book

**Bottleneck:** Semantic chunking (6x slower than fixed-window, but better quality)

---

### Query Latency

**Benchmark (typical query):**
- Query embedding: ~0.1 seconds
- Qdrant search: ~0.3 seconds
- LLM answer generation: ~2-5 seconds (depends on model)
- **Total:** ~2.5-5.5 seconds

**Bottleneck:** LLM inference (OpenRouter API network latency)

---

### Scalability

**Current Scale:**
- ~150 books ingested
- ~23,000 chunks in Qdrant
- ~9,000 books in Calibre library (not all ingested)

**Projected Scale (full library):**
- 9,000 books × ~150 chunks/book = ~1.35 million chunks
- 1.35M chunks × 384 dims × 4 bytes = ~2 GB vectors
- Qdrant easily handles this on commodity hardware

**Future Scale (if needed):**
- Qdrant supports billions of vectors
- Can add multiple Qdrant nodes (clustering)
- Can partition by domain (separate collections)

---

## Key Architecture Decisions (ADRs)

All architectural decisions are documented as ADRs. See [docs/architecture/decisions/README.md](decisions/README.md) for full index.

**Implemented Decisions:**

| ADR | Decision | Status | Impact |
|-----|----------|--------|--------|
| [0001](decisions/0001-use-qdrant-vector-db.md) | Use Qdrant Vector DB | ✅ Implemented | Fast semantic search (<100ms) |
| [0002](decisions/0002-domain-specific-chunking.md) | Domain-Specific Chunking | ⚠️ Superseded | Replaced by Universal Semantic |
| [0003](decisions/0003-gui-as-thin-layer.md) | GUI as Thin Presentation Layer | ✅ Implemented | Reduced 160 LOC duplication |
| [0004](decisions/0004-collection-specific-manifests.md) | Collection-Specific Manifests | ✅ Implemented | Prevents cross-contamination |
| [0005](decisions/0005-philosophical-argument-chunking.md) | Philosophical Argument Chunking | ⚠️ Superseded | Incorporated into Universal Semantic |
| [0006](decisions/0006-separate-systems-architecture.md) | Separate Systems Architecture | ✅ Implemented | Clear separation of concerns |

---

## Related Documentation

### Architecture Docs

- **[Architecture Overview](README.md)** - Navigation hub
- **[C4 Context](c4/01-context.md)** - System overview
- **[C4 Container](c4/02-container.md)** - Major components
- **[C4 Component](c4/03-component.md)** - Internal structure
- **[Structurizr Workspace](workspace.dsl)** - Interactive diagrams

### Technical Specs

- **[Universal Semantic Chunking](technical/UNIVERSAL_SEMANTIC_CHUNKING.md)** - Chunking deep-dive
- **[Qdrant Payload Structure](technical/QDRANT_PAYLOAD_STRUCTURE.md)** - Vector DB schema
- **[PDF vs EPUB Comparison](technical/PDF_vs_EPUB_COMPARISON.md)** - Format analysis

### User Guides

- **[Quick Reference](../guides/QUICK_REFERENCE.md)** - Command cheat sheet
- **[Logging Guide](../guides/LOGGING_GUIDE.md)** - Tracking system
- **[Professional Setup](../guides/PROFESSIONAL_SETUP_COMPLETE.md)** - Complete guide

---

## View Interactive Diagrams

### Structurizr Lite (Recommended)

```bash
# Start Structurizr Lite on port 8081
cd docs/architecture
docker run -it --rm -p 8081:8080 -v "%cd%:/usr/local/structurizr" structurizr/lite
```

Open: http://localhost:8081

**Views Available:**
- System Context - High-level ecosystem
- Containers - Major components
- Components - Internal structure
- Detailed Ingestion Flow - Book processing pipeline

---

## Contact & Contributions

**Project:** Alexandria of Temenos
**Status:** Phase 1 - Production Ready ✅
**License:** Internal Use (Temenos Academy)

**For questions or contributions:**
- See [docs/stories/](../stories/) for feature documentation
- See [docs/architecture/decisions/](decisions/) for ADRs
- See [TODO.md](../../TODO.md) for backlog

---

**Last Updated:** 2026-01-25
**Version:** 1.0 (Universal Semantic Chunking)
