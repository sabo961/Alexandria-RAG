# Alexandria RAG System - Architecture Documentation

**Generated:** 2026-01-26
**Project:** Alexandria - Temenos Academy Library
**Type:** Retrieval-Augmented Generation (RAG) System
**Status:** Production

---

## Executive Summary

Alexandria is a **RAG (Retrieval-Augmented Generation) system** for semantic search across 9,000+ books in the Temenos Academy library. It provides:

- **Semantic book search** using vector embeddings and cosine similarity
- **LLM-powered answer generation** from book content
- **Calibre library integration** for rich book metadata
- **Multi-format support** (EPUB, PDF with planned MOBI support)
- **Universal semantic chunking** that adapts to content structure

**Key Innovation:** Universal Semantic Chunking (ADR 0007) that preserves semantic coherence by splitting text at topic boundaries detected via sentence embedding similarity, replacing previous domain-specific and keyword-based approaches.

---

## Technology Stack

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| **Language** | Python | 3.14+ | Primary implementation language |
| **Web Framework** | Streamlit | ≥1.29.0 | GUI application (binds to 0.0.0.0:8501) |
| **Vector Database** | Qdrant | ≥1.7.1 | Semantic search (external: 192.168.0.151:6333) |
| **Embeddings** | sentence-transformers | ≥2.3.1 | all-MiniLM-L6-v2 (384-dim vectors) |
| **ML Framework** | PyTorch | ≥2.0.0 | Required by sentence-transformers |
| **Semantic Analysis** | NumPy, scikit-learn | ≥1.24.0, ≥1.3.0 | Cosine similarity for chunking |
| **EPUB Parsing** | EbookLib | 0.18 | EPUB book ingestion |
| **PDF Parsing** | PyMuPDF | ≥1.24.0 | PDF book ingestion |
| **HTML Parsing** | BeautifulSoup4, lxml | 4.12.2, 4.9.3 | EPUB content extraction |
| **HTTP Client** | requests | ≥2.31.0 | OpenRouter API calls (optional) |
| **Testing** | pytest, pytest-cov | 7.4.3, 4.1.0 | Test framework (planned) |
| **Code Quality** | black, flake8 | 23.12.1, 7.0.0 | Formatting & linting (planned) |

---

## Architecture Pattern

### RAG System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Alexandria RAG System                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐         ┌─────────────────┐                  │
│  │   Streamlit  │────────▶│  Scripts        │                  │
│  │   GUI        │         │  Package        │                  │
│  │  (Thin Layer)│         │  (Business      │                  │
│  └──────────────┘         │   Logic)        │                  │
│                           └─────────────────┘                  │
│                                  │                              │
│                                  ▼                              │
│                           ┌─────────────────┐                  │
│                           │  Qdrant Vector  │                  │
│                           │  Database       │                  │
│                           │ 192.168.0.151   │                  │
│                           └─────────────────┘                  │
│                                                                  │
│  External Systems:                                              │
│  ┌──────────────┐         ┌─────────────────┐                 │
│  │   Calibre    │         │   OpenRouter    │                 │
│  │   Library    │         │   API (LLM)     │                 │
│  └──────────────┘         └─────────────────┘                 │
└─────────────────────────────────────────────────────────────────┘
```

### Architectural Principles (ADR 0003)

**Thin GUI Layer Pattern:**
- GUI (`alexandria_app.py`) only handles presentation
- All business logic lives in `scripts/` package
- GUI calls scripts, displays results
- **Anti-pattern:** Duplicating logic in GUI

**Benefits:**
- ✅ Testability (scripts can be unit tested)
- ✅ Reusability (scripts usable from CLI and GUI)
- ✅ Maintainability (single source of truth for logic)

---

## System Components

### 1. GUI Layer (Streamlit)

**File:** `alexandria_app.py`
**Purpose:** User interface for all Alexandria features
**Binding:** `0.0.0.0:8501` (network accessible)

**Tabs:**
- **📖 Qdrant collections** - View ingested books, browse collections
- **📚 Calibre** - Browse Calibre library, select books for ingestion
- **🔍 Query** - Semantic search with optional LLM answer generation
- **⚙️ Admin** - Manage collections, settings, diagnostics

**Architecture:**
- Uses Streamlit fragments for tab isolation
- Session state management via `AppState` dataclass
- Caching with `@st.cache_data` for static data
- Directly imports and calls scripts package modules

---

### 2. Business Logic Layer (Scripts Package)

**Directory:** `scripts/`
**Pattern:** Flat module structure (no subdirectories)

**Core Modules:**

| Module | Purpose | Main API |
|--------|---------|----------|
| `calibre_db.py` | Calibre SQLite interface | `CalibreDB.get_all_books()` |
| `collection_manifest.py` | Ingestion tracking | `CollectionManifest.add_book()` |
| `ingest_books.py` | Book ingestion pipeline | `ingest_book()` |
| `rag_query.py` | Semantic search & RAG | `perform_rag_query()` |
| `qdrant_utils.py` | Qdrant operations | `list_collections()` |
| `universal_chunking.py` | Semantic chunking | `UniversalChunker.chunk()` |

**Helper Modules:**
- `batch_ingest.py` - Batch ingestion helper
- `generate_book_inventory.py` - Calibre inventory generator
- `experiment_chunking.py` - Chunking experiments
- `check_authors.py`, `fix_manifest_authors.py` - Data validation/repair

---

### 3. Data Architecture

#### Qdrant Vector Database (External)

**Location:** 192.168.0.151:6333
**Distance Metric:** COSINE (hardcoded, cannot change)
**Embedding Model:** all-MiniLM-L6-v2 (384-dimensional)

**Collections:**
- `alexandria` - Main production collection (~9,000 books)
- `alexandria_test` - Test collection for experiments
- Custom collections per domain/experiment

**Payload Structure:**
```json
{
  "title": "Book Title",
  "author": "Author Name",
  "file_path": "G:\\path\\to\\book.epub",
  "section_index": 42,
  "chunk_order": 12,
  "domain": "philosophy",
  "language": "eng",
  "text": "Chunk text content...",
  "metadata": {...}
}
```

#### Collection Manifests

**Purpose:** Track which books are ingested into which collections
**Format:** JSON
**Location:** `logs/collection_manifest_{collection_name}.json`

**Structure:**
```json
{
  "collections": {
    "alexandria": {
      "collection_name": "alexandria",
      "created": "2026-01-20T10:30:00Z",
      "last_updated": "2026-01-26T15:45:00Z",
      "total_books": 42,
      "total_chunks": 3847,
      "books": [...]
    }
  }
}
```

**CSV Export:** `logs/alexandria_manifest.csv` (human-readable)

#### Calibre Library (External)

**Location:** `G:\My Drive\alexandria`
**Database:** `metadata.db` (SQLite)
**Purpose:** Book metadata (author, title, tags, series, ISBN, etc.)

---

## Data Flow

### Ingestion Pipeline

```
┌─────────────────┐
│  Book File      │
│  (.epub/.pdf)   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│  extract_text()         │
│  - Parse EPUB/PDF       │
│  - Extract text         │
│  - Extract metadata     │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  UniversalChunker       │
│  - Split into sentences │
│  - Embed sentences      │
│  - Detect topic shifts  │
│  - Create chunks        │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  generate_embeddings()  │
│  - all-MiniLM-L6-v2     │
│  - 384-dim vectors      │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  upload_to_qdrant()     │
│  - Store vectors + meta │
│  - COSINE distance      │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  CollectionManifest     │
│  - Track ingestion      │
│  - Update manifest JSON │
│  - Export CSV           │
└─────────────────────────┘
```

### Query Pipeline

```
┌─────────────────┐
│  User Query     │
│  "What does..." │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│  search_qdrant()        │
│  - Embed query          │
│  - Semantic search      │
│  - Return top-k chunks  │
└────────┬────────────────┘
         │
         ▼ (optional)
┌─────────────────────────┐
│  rerank_with_llm()      │
│  - LLM relevance scoring│
│  - Reorder results      │
└────────┬────────────────┘
         │
         ▼ (optional)
┌─────────────────────────┐
│  generate_answer()      │
│  - RAG context          │
│  - LLM answer gen       │
│  - Cite sources         │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  RAGResult              │
│  - Search results       │
│  - Optional LLM answer  │
└─────────────────────────┘
```

---

## Key Algorithms

### Universal Semantic Chunking (ADR 0007)

**Purpose:** Split text into semantically coherent chunks without fixed token windows.

**Algorithm:**
1. **Sentence Splitting:** Split text into individual sentences
2. **Sentence Embeddings:** Encode each sentence using all-MiniLM-L6-v2
3. **Similarity Calculation:** Cosine similarity between consecutive sentences
4. **Boundary Detection:** Low similarity (< threshold) = topic shift = chunk boundary
5. **Size Constraints:** Enforce MIN 200 tokens, MAX 1200 tokens per chunk

**Domain-Specific Thresholds:**
- **Philosophy:** 0.45 (preserve complex arguments)
- **Other domains:** 0.55 (standard splitting)

**Benefits:**
- ✅ Preserves semantic coherence (no mid-topic splits)
- ✅ Adapts to content structure automatically
- ✅ Language-agnostic (works with any language supported by embedding model)

**Supersedes:**
- ADR 0002: Domain-Specific Chunking (fixed token windows)
- ADR 0005: Philosophical Argument Chunking (keyword-based)

---

## Source Tree Structure

```
alexandria/
├── 📱 alexandria_app.py              # 🔹 ENTRY POINT - Streamlit GUI
├── 📄 requirements.txt                # Python dependencies
├── 📋 README.md                       # Project landing page
│
├── 📦 scripts/                        # 🔹 BUSINESS LOGIC
│   ├── calibre_db.py                  # Calibre interface
│   ├── collection_manifest.py         # Manifest tracking
│   ├── ingest_books.py                # 🔹 Ingestion pipeline
│   ├── rag_query.py                   # 🔹 Query engine
│   ├── qdrant_utils.py                # Qdrant operations
│   ├── universal_chunking.py          # Semantic chunking
│   └── [12 other modules]
│
├── 📂 docs/                           # Documentation
│   ├── architecture/                  # Architecture docs (ADRs, C4)
│   ├── guides/                        # User/dev guides
│   ├── research/                      # Research documents
│   ├── proposals/                     # External contributions
│   ├── architecture.md                # This file
│   ├── data-models-alexandria.md      # API reference
│   ├── source-tree-analysis.md        # Codebase structure
│   └── development-guide-alexandria.md # Dev setup guide
│
├── 📂 logs/                           # Runtime artifacts
│   ├── collection_manifest_*.json     # Ingestion tracking
│   └── alexandria_manifest.csv        # CSV export
│
├── 📂 ingest/ → ingested/             # File workflow
│
├── 📂 _bmad-output/                   # BMad outputs
│   └── project-context.md             # 🔹 AI agent rules (45 rules)
│
└── 📂 .streamlit/                     # Streamlit config
    ├── config.toml                    # UI settings
    └── secrets.toml                   # 🔐 API keys (gitignored)
```

---

## Development Workflow

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Configure API keys (optional)
# Edit .streamlit/secrets.toml

# Run GUI
streamlit run alexandria_app.py
```

### Ingestion Workflow

```
1. Place books in ingest/ folder
2. Launch GUI → Calibre/Ingestion Tab
3. Select files, choose domain & collection
4. Click "Start Ingestion"
5. Books auto-move to ingested/ on success
6. Manifest updated in logs/
```

### Query Workflow

```
1. Launch GUI → Query Tab
2. Enter search query
3. Select collection
4. Optional: Enable LLM answer generation
5. View results (chunks + optional answer)
```

---

## Testing Strategy

**Current Status:** Tests recommended but not yet implemented

**Planned Approach:**
- **Unit tests:** Test scripts/ modules in isolation
- **Integration tests:** End-to-end ingestion and query workflows
- **Fixture data:** Sample EPUB/PDF files in `tests/fixtures/`
- **Mocking:** Mock Qdrant client, OpenRouter API, file system

**Test Structure:**
```
tests/
├── test_ingest_books.py
├── test_rag_query.py
├── test_collection_manifest.py
├── test_calibre_db.py
└── fixtures/
    ├── sample.epub
    └── sample.pdf
```

**Run tests:** `pytest tests/` (when implemented)

---

## Deployment Architecture

**Current:** Local development environment

**Components:**
- **Alexandria Application:** Runs on developer machine (Streamlit GUI)
- **Qdrant Server:** External server at 192.168.0.151:6333
- **Calibre Library:** External storage at G:\My Drive\alexandria
- **OpenRouter API:** Cloud service (optional)

**No containerization** (Docker, Kubernetes) currently implemented.

**Future considerations:**
- Docker container for Streamlit GUI
- Environment-based configuration (dev/prod)
- CI/CD pipeline for automated testing

---

## Security Considerations

### Secrets Management

- **API Keys:** Stored in `.streamlit/secrets.toml` (gitignored)
- **Qdrant:** No authentication (trusted network)
- **Calibre DB:** Read-only SQLite access

### Data Privacy

- **Book Content:** Stored in Qdrant (external server)
- **User Queries:** Optionally sent to OpenRouter API for LLM answers
- **No user authentication:** Single-user application

### Network Security

- **Streamlit GUI:** Binds to `0.0.0.0:8501` (network accessible)
- **Qdrant:** External server on trusted network (192.168.0.151)
- **Calibre Library:** Local/network file system access

---

## Performance Characteristics

### Ingestion Performance

- **EPUB:** ~2-5 seconds per book (depends on size)
- **PDF:** ~5-15 seconds per book (depends on size/complexity)
- **Bottleneck:** Embedding generation (CPU-bound)

**Optimization:**
- Batch ingestion for multiple books
- tqdm progress bars disabled globally (Streamlit compatibility)

### Query Performance

- **Vector Search:** <100ms (Qdrant)
- **LLM Answer:** 2-10 seconds (depends on model, network)
- **Reranking:** 1-3 seconds (LLM call)

**Optimization:**
- Qdrant handles vector search efficiently
- Caching not implemented (future enhancement)

---

## Known Limitations & Constraints

### Technical Constraints

1. **Embedding Model Immutable** (ADR critical)
   - Cannot change from all-MiniLM-L6-v2 without re-ingesting ALL books
   - Would require complete Qdrant collection recreation

2. **Distance Metric Hardcoded**
   - COSINE distance only
   - Changing to EUCLIDEAN/DOT would break existing collections

3. **Windows Long Paths**
   - Paths > 248 characters require `\\?\` prefix handling
   - Implemented in `normalize_file_path()` function

4. **tqdm Disabled Globally**
   - Progress bars cause `[Errno 22]` in Streamlit
   - Set via `TQDM_DISABLE=1` environment variable

### Configuration Issues (from project-context.md)

1. **Calibre Library Path Hardcoded** (REGRESSION)
   - Currently: `G:\My Drive\alexandria` hardcoded
   - Should be: GUI-configurable setting
   - Future: Restore Settings sidebar input

2. **Universal Chunking Parameters Hardcoded**
   - Currently: threshold, min_chunk_size, max_chunk_size in code
   - Should be: Exposed in Config/Settings sidebar
   - Impact: Can't experiment without code changes

### Missing Features (Lost After Refactor)

1. **Interactive Chunking GUI - LOST**
   - Previously existed: Real-time chunking parameter testing
   - Current state: CLI tool exists (`experiment_chunking.py`)
   - Action needed: Recreate interactive Streamlit version

---

## Future Enhancements

**See:** [TODO.md](../TODO.md) for full backlog

### HIGH PRIORITY
- Ingest Versioning (track ingestion version in Qdrant payload)
- Chunk Fingerprint (sha1 hash for deduplication)

### MEDIUM PRIORITY
- Query Modes (fact/cite/explore/synthesize)
- Calibre Path Configuration (restore GUI setting)

### LOW PRIORITY
- Multi-file Upload (GUI drag-and-drop)
- MOBI format support

---

## Related Documentation

### Architecture
- **[Architecture Summary](architecture/ARCHITECTURE_SUMMARY.md)** - High-level overview
- **[C4 Diagrams](architecture/c4/)** - Visual architecture (Context, Container, Component)
- **[ADRs](architecture/decisions/README.md)** - Architecture Decision Records (7 ADRs)
- **[Technical Specs](architecture/technical/)** - Detailed technical documentation

### Development
- **[Development Guide](development-guide-alexandria.md)** - Setup and workflow
- **[Source Tree](source-tree-analysis.md)** - Codebase structure
- **[Data Models & API](data-models-alexandria.md)** - Module APIs
- **[Project Context](../_bmad-output/project-context.md)** - AI agent rules (45 rules)

### Guides
- **[Quick Reference](guides/QUICK_REFERENCE.md)** - Command cheat sheet
- **[Logging Guide](guides/LOGGING_GUIDE.md)** - Logging patterns

### Research
- **[docs/research/](research/)** - Background research documents
- **[docs/backlog/](backlog/)** - Feature proposals

---

## Change Log

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-25 | 1.0 | Universal Semantic Chunking implemented (ADR 0007) |
| 2026-01-24 | 0.9 | Calibre direct ingestion added |
| 2026-01-23 | 0.8 | Collection-specific manifests (ADR 0004) |
| 2026-01-21 | 0.7 | GUI architecture refactor (ADR 0003) |
| 2026-01-20 | 0.6 | Domain-specific chunking (superseded by ADR 0007) |

**See:** [CHANGELOG.md](../CHANGELOG.md) for detailed change history

---

**Document Version:** 1.0
**Generated by:** document-project workflow (exhaustive scan)
**Last Updated:** 2026-01-26
**Reviewed by:** [Pending]
