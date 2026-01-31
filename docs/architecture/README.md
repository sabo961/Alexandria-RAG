# Alexandria RAG System - Architecture Documentation

**Generated:** 2026-01-30
**Project:** Alexandria - Temenos Academy Library
**Type:** Retrieval-Augmented Generation (RAG) System
**Status:** Production

> **Navigation:** This is **Reference** documentation (technical specs, diagrams).
> For the "why" behind decisions, see [Architecture Principles](../explanation/architecture-principles.md).

---

## Executive Summary

Alexandria is a **RAG (Retrieval-Augmented Generation) system** for semantic search across 9,000+ books in the Temenos Academy library. It provides:

- **Semantic book search** using vector embeddings and cosine similarity
- **LLM-powered answer generation** from book content
- **Calibre library integration** for rich book metadata
- **Multi-format support** (EPUB, PDF, TXT, MD, HTML)
- **Hierarchical chunking** with parent (chapter) and child (semantic) chunks
- **MCP Server integration** for Claude Code

**Key Innovations:**
- **Hierarchical Chunking** - Two-level structure for better context retrieval
- **Universal Semantic Chunking (ADR 0007)** - Preserves semantic coherence by splitting text at topic boundaries detected via sentence embedding similarity

---

## Quick Reference

### System Context (C4 Level 1)

```
[Claude Code / MCP Clients]
         ↓ (stdio)
   [MCP Server - scripts/mcp_server.py]
         ↓
   [Scripts Package - Business Logic]
         ↓ ↑
    ┌────┴────┬──────────────┐
    ↓         ↓              ↓
[Qdrant]  [OpenRouter]  [Calibre DB]
```

**External Systems:**
- **Qdrant (192.168.0.151:6333)** - Vector database storing 384-dim embeddings
- **OpenRouter API** - LLM inference (optional, for RAG answers)
- **Calibre Library** - Book metadata and file storage

### Performance at a Glance

| Operation | Latency | Details |
|-----------|---------|---------|
| **Book Ingestion** | ~11-13 sec | Text extraction (5s) + Chunking (3-5s) + Embedding (2s) + Upload (1s) |
| **Semantic Search** | <100ms | Qdrant vector search |
| **RAG Query (with LLM)** | 2.5-5.5 sec | Search (0.4s) + LLM inference (2-5s) |
| **Current Scale** | 150 books, 23K chunks | Main collection |
| **Target Scale** | 9,000 books, 1.35M chunks | ~2GB vectors, easily handled by Qdrant |

---

## Technology Stack

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| **Language** | Python | 3.14+ | Primary implementation language |
| **Interface** | FastMCP | ≥2.0.0 | MCP Server (Model Context Protocol) |
| **Vector Database** | Qdrant | ≥1.7.1 | Semantic search (external: 192.168.0.151:6333) |
| **Embeddings** | sentence-transformers | ≥2.3.1 | all-MiniLM-L6-v2 (384-dim vectors) |
| **ML Framework** | PyTorch | ≥2.0.0 | Required by sentence-transformers |
| **Semantic Analysis** | NumPy, scikit-learn | ≥1.24.0, ≥1.3.0 | Cosine similarity for chunking |
| **EPUB Parsing** | EbookLib | 0.18 | EPUB book ingestion |
| **PDF Parsing** | PyMuPDF | ≥1.24.0 | PDF book ingestion |
| **HTML Parsing** | BeautifulSoup4, lxml | 4.12.2, 4.9.3 | EPUB content extraction |
| **HTTP Client** | requests | ≥2.31.0 | OpenRouter API calls (optional) |
| **Testing** | pytest, pytest-cov | 7.4.3, 4.1.0 | Test framework |
| **Code Quality** | black, flake8 | 23.12.1, 7.0.0 | Formatting & linting |

---

## Architecture Pattern

### RAG System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Alexandria RAG System                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Claude Code / MCP Clients                                      │
│         ↓ (stdio)                                               │
│  ┌──────────────────┐     ┌─────────────────┐                  │
│  │   MCP Server     │────▶│  Scripts        │                  │
│  │  (mcp_server.py) │     │  Package        │                  │
│  │   10+ Tools      │     │  (Business      │                  │
│  └──────────────────┘     │   Logic)        │                  │
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

### Architecture Principles

#### 1. MCP-First Architecture (ADR 0003 - Superseded)

**Principle:** All business logic lives in `scripts/` package. MCP Server is the primary interface.

**Why?**
- Single source of truth (no duplication)
- Multiple interfaces (MCP, CLI)
- Easy testing (no UI overhead)
- Direct integration with Claude Code

**Implementation:**
- MCP Server (`scripts/mcp_server.py`) exposes tools
- All business logic lives in `scripts/` package
- MCP tools call scripts, return results
- **Anti-pattern:** Duplicating logic in interface layer

**Benefits:**
- ✅ Testability (scripts can be unit tested)
- ✅ Reusability (scripts usable from CLI and MCP)
- ✅ Maintainability (single source of truth for logic)
- ✅ AI Integration (direct Claude Code access)

**See:** [ADR 0003: GUI as Thin Layer](./decisions/0003-gui-as-thin-layer.md) (Superseded - MCP-first)

---

#### 2. Collection Isolation (ADR 0004)

**Principle:** Each collection has separate manifests, progress files, and can use different settings.

**Why?**
- Prevents cross-contamination between collections
- Allows experimentation (test different chunking strategies)
- Supports multiple use cases (personal library, research corpus, client project)

**Implementation:**
- `logs/{collection}_manifest.json` - Master manifest
- `logs/{collection}_manifest.csv` - Human-readable export
- `scripts/batch_ingest_progress_{collection}.json` - Resume tracker
- Separate Qdrant collections per domain/experiment

**Benefits:**
- ✅ Data integrity (no cross-contamination)
- ✅ Experimentation (A/B test chunking strategies)
- ✅ Flexibility (different settings per collection)

**See:** [ADR 0004: Collection-Specific Manifests](architecture/decisions/0004-collection-specific-manifests.md)

---

#### 3. Progressive Enhancement

**Principle:** Core functionality works with minimal dependencies. Advanced features are optional.

**Examples:**
- Ingestion works without Calibre DB (use folder ingestion)
- Query works without OpenRouter (search-only mode, no answer generation)
- GUI is optional (CLI works standalone)

**Why?**
- Easier onboarding (start simple, add features as needed)
- Resilience (system degrades gracefully)
- Flexibility (choose features based on use case)

**Benefits:**
- ✅ Lower barrier to entry
- ✅ Graceful degradation
- ✅ Modular feature adoption

---

## System Components

### 1. MCP Server Layer

**File:** `scripts/mcp_server.py`
**Purpose:** Primary interface for Claude Code and MCP clients
**Protocol:** Model Context Protocol (stdio)

**Query Tools:**
- `alexandria_query` - Semantic search with context modes
- `alexandria_search` - Search Calibre by metadata
- `alexandria_book` - Get book details by ID
- `alexandria_stats` - Collection statistics

**Ingest Tools:**
- `alexandria_ingest` - Ingest single book from Calibre
- `alexandria_batch_ingest` - Ingest multiple books
- `alexandria_ingest_file` - Ingest local file (no Calibre)
- `alexandria_ingest_preview` - Preview books for ingestion
- `alexandria_test_chunking` - Test chunking without upload

**Architecture:**
- Built with FastMCP library
- Exposes scripts as MCP tools
- Returns structured JSON responses
- Progress tracking for long operations

---

### 2. Business Logic Layer (Scripts Package)

**Directory:** `scripts/`
**Pattern:** Flat module structure (no subdirectories)

**Core Modules:**

| Module | Purpose | Main API |
|--------|---------|----------|
| `mcp_server.py` | MCP Server entry point | `@mcp.tool()` decorators |
| `calibre_db.py` | Calibre SQLite interface | `CalibreDB.get_all_books()` |
| `collection_manifest.py` | Ingestion tracking | `CollectionManifest.add_book()` |
| `ingest_books.py` | Book ingestion pipeline | `ingest_book()` |
| `rag_query.py` | Semantic search & RAG | `perform_rag_query()` |
| `qdrant_utils.py` | Qdrant operations | `list_collections()` |
| `universal_chunking.py` | Semantic chunking | `UniversalChunker.chunk()` |
| `chapter_detection.py` | Chapter boundary detection | `detect_chapters()` |

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
├── 📄 requirements.txt                # Python dependencies
├── 📋 README.md                       # Project landing page
├── 📄 .mcp.json                       # 🔹 MCP Server configuration
│
├── 📦 scripts/                        # 🔹 BUSINESS LOGIC + MCP SERVER
│   ├── mcp_server.py                  # 🔹 ENTRY POINT - MCP Server
│   ├── calibre_db.py                  # Calibre interface
│   ├── collection_manifest.py         # Manifest tracking
│   ├── ingest_books.py                # 🔹 Ingestion pipeline
│   ├── rag_query.py                   # 🔹 Query engine
│   ├── chapter_detection.py           # Chapter boundary detection
│   ├── qdrant_utils.py                # Qdrant operations
│   ├── universal_chunking.py          # Semantic chunking
│   └── [other modules]
│
├── 📂 docs/                           # Documentation
│   ├── reference/architecture/        # Architecture docs (ADRs, C4)
│   ├── how-to-guides/                 # User guides
│   ├── tutorials/                     # Getting started
│   ├── explanation/                   # Conceptual docs
│   └── backlog/                       # Feature proposals
│
├── 📂 logs/                           # Runtime artifacts
│   ├── collection_manifest_*.json     # Ingestion tracking
│   └── alexandria_manifest.csv        # CSV export
│
├── 📂 _bmad-output/                   # BMad outputs
│   └── project-context.md             # 🔹 AI agent rules
│
└── 📂 tests/                          # Test suite
    ├── unit/                          # Unit tests
    └── integration/                   # Integration tests
```

---

## Development Workflow

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Configure MCP Server in .mcp.json
# Restart Claude Code to activate

# Run CLI scripts directly
cd scripts
python rag_query.py "your question" --context-mode contextual
```

### Ingestion Workflow (via Claude Code)

```
User: Ingest the Nietzsche book with ID 7970
Claude: [calls alexandria_ingest(book_id=7970)]

User: Ingest all philosophy books
Claude: [calls alexandria_batch_ingest(tag="philosophy", limit=10)]
```

### Query Workflow (via Claude Code)

```
User: What does Silverston say about shipment patterns?
Claude: [calls alexandria_query("shipment pattern", context_mode="contextual")]

User: Find books by Kahneman
Claude: [calls alexandria_search(author="Kahneman")]
```

### CLI Workflow (Secondary)

```bash
# Query with context mode
cd scripts
python rag_query.py "your question" --limit 5 --context-mode contextual

# Check manifest
python collection_manifest.py show alexandria

# Collection stats
python qdrant_utils.py stats alexandria
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

### Current: MCP Server + Claude Code

```
[User's PC]
├── Claude Code (MCP Client)
│   └── .mcp.json (configuration)
├── Alexandria MCP Server (scripts/mcp_server.py)
├── Calibre Library (SQLite - G:\My Drive\alexandria)
└── External Qdrant Server (192.168.0.151:6333)
```

**Components:**
- **MCP Server:** `scripts/mcp_server.py` (stdio protocol)
- **Qdrant Server:** External server at 192.168.0.151:6333
- **Calibre Library:** External storage at G:\My Drive\alexandria
- **OpenRouter API:** Cloud service (optional, for RAG answers)

**Access:** Via Claude Code terminal (MCP tools)

**No containerization** (Docker, Kubernetes) currently implemented.

---

### Future: MCP Server on NAS (Planned)

```
[NAS - 192.168.0.151]
├── Alexandria MCP Server
│   └── Accessible via SSH or remote MCP
├── Docker: Qdrant Container
│   └── Port: 6333
├── Calibre Library (metadata.db)
└── Book Storage (EPUB/PDF files)
```

**Benefits:**
- 24/7 availability
- Centralized storage with RAID backup
- Low latency (MCP Server and Qdrant on same host)
- Multi-machine access via remote MCP

**Implementation Steps:**
1. Deploy MCP server on NAS
2. Configure remote MCP access in Claude Code
3. Mount Calibre library as Docker volume
4. Configure environment variables for NAS paths

---

## Security Considerations

### Secrets Management

- **API Keys:** Stored in environment variables or `.env` file (gitignored)
- **Qdrant:** No authentication (trusted network)
- **Calibre DB:** Read-only SQLite access

### Data Privacy

- **Book Content:** Stored in Qdrant (external server)
- **User Queries:** Optionally sent to OpenRouter API for LLM answers
- **No user authentication:** Single-user application

### Network Security

- **MCP Server:** stdio protocol (local only, no network exposure)
- **Qdrant:** External server on trusted network (192.168.0.151)
- **Calibre Library:** Local/network file system access

---

## Performance Characteristics

### Ingestion Throughput

**Benchmark (typical book, ~500 pages):**
- Text extraction: ~5 seconds
- Semantic chunking: ~3-5 seconds
- Embedding generation: ~2 seconds
- Qdrant upload: ~1 second
- **Total:** ~11-13 seconds per book

**Format-Specific:**
- **EPUB:** ~2-5 seconds per book (cleaner extraction)
- **PDF:** ~5-15 seconds per book (OCR/complex layouts slower)

**Bottleneck:** Semantic chunking (6x slower than fixed-window, but better quality)

**Optimization:**
- Batch ingestion for multiple books
- tqdm progress bars disabled globally (Streamlit compatibility)
- No caching implemented (each book processed fresh)

---

### Query Latency

**Benchmark (typical query):**
- Query embedding: ~0.1 seconds
- Qdrant search: ~0.3 seconds
- LLM answer generation: ~2-5 seconds (depends on model)
- **Total:** ~2.5-5.5 seconds

**Breakdown:**
- **Vector Search Alone:** <100ms (Qdrant)
- **With Reranking:** +1-3 seconds (LLM call)
- **With Answer Generation:** +2-10 seconds (depends on model, network)

**Bottleneck:** LLM inference (OpenRouter API network latency)

**Optimization:**
- Qdrant handles vector search efficiently
- Caching not implemented (future enhancement)
- No connection pooling for OpenRouter API

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

### Configuration

1. **Calibre Library Path**
   - Configured via `CALIBRE_LIBRARY_PATH` environment variable
   - Default: `G:\My Drive\alexandria`

2. **Chunking Parameters**
   - Configurable via MCP tools: `threshold`, `min_chunk_size`, `max_chunk_size`
   - Default: 0.55, 200, 1200
   - CLI: `experiment_chunking.py` for testing

---

## Future Enhancements

**See:** [TODO.md](../../TODO.md) for full backlog

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
- **[C4 Diagrams](./c4/)** - Visual architecture (Context, Container, Component)
- **[ADRs](./decisions/README.md)** - Architecture Decision Records
- **[Technical Specs](./technical/)** - Detailed technical documentation

### MCP Server
- **[MCP Server Reference](./mcp-server.md)** - Complete tool documentation
- **[Common Workflows](../how-to/common-workflows.md)** - Usage examples

### Development
- **[Development Guide](../tutorials/getting-started.md)** - Setup and workflow
- **[Source Tree](../source-tree.md)** - Codebase structure
- **[Data Models](./technical/data-models.md)** - Data structure specifications
- **[Project Context](../project-context.md)** - AI agent rules (MANDATORY)

### Guides
- **[Common Workflows](../how-to/common-workflows.md)** - MCP tool reference
- **[Logging Guide](../how-to/track-ingestion.md)** - Logging patterns

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

**See:** [Structurizr Guide](../tutorials/structurizr-guide.md) for more details

---

## Change Log

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-30 | 2.0 | MCP-first architecture, GUI abandoned |
| 2026-01-30 | 1.5 | Hierarchical chunking, context modes |
| 2026-01-25 | 1.0 | Universal Semantic Chunking implemented (ADR 0007) |
| 2026-01-24 | 0.9 | Calibre direct ingestion added |
| 2026-01-23 | 0.8 | Collection-specific manifests (ADR 0004) |
| 2026-01-21 | 0.7 | GUI architecture refactor (ADR 0003) |
| 2026-01-20 | 0.6 | Domain-specific chunking (superseded by ADR 0007) |

**See:** [CHANGELOG.md](../../CHANGELOG.md) for detailed change history

---

**Document Version:** 2.0 (MCP-first)
**Last Updated:** 2026-01-30
