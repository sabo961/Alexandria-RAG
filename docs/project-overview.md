# Alexandria - Project Overview

**Project Name:** Alexandria - Temenos Academy Library
**Type:** RAG (Retrieval-Augmented Generation) System
**Status:** Production
**Generated:** 2026-01-26

---

## What is Alexandria?

Alexandria is a **semantic search and knowledge retrieval system** for the Temenos Academy library of 9,000+ books. It uses vector embeddings and RAG (Retrieval-Augmented Generation) to enable:

- **Semantic book search** - Find relevant passages by meaning, not just keywords
- **LLM-powered answers** - Generate answers from book content using Claude/GPT-4
- **Multi-format support** - EPUB, PDF (with planned MOBI support)
- **Calibre integration** - Browse and ingest books directly from Calibre library

---

## Quick Facts

| Aspect | Details |
|--------|---------|
| **Primary Language** | Python 3.14+ |
| **Architecture** | RAG System (Monolith) |
| **GUI Framework** | Streamlit ≥1.29.0 |
| **Vector Database** | Qdrant (external: 192.168.0.151:6333) |
| **Embedding Model** | all-MiniLM-L6-v2 (384-dimensional) |
| **Books Supported** | EPUB, PDF |
| **Total Books** | ~9,000 (Temenos Academy Library) |
| **Repository Type** | Monolith (single cohesive codebase) |
| **Entry Point** | `alexandria_app.py` (Streamlit GUI) |

---

## Key Features

### 1. Semantic Search
- Vector similarity search using Qdrant
- COSINE distance metric
- Returns top-k most relevant chunks from book collection

### 2. RAG Answer Generation
- Optional LLM-powered answer generation
- Cites sources from book collection
- Supports Claude 3.5 Sonnet, GPT-4, and other models

### 3. Calibre Library Integration
- Direct access to Calibre metadata.db (SQLite)
- Browse by author, title, language, tags, series
- Rich metadata (ISBN, publisher, ratings, etc.)
- Direct ingestion from Calibre library to Qdrant

### 4. Universal Semantic Chunking (Innovation)
- Splits text at semantic boundaries (not fixed token windows)
- Uses sentence embeddings + cosine similarity
- Preserves philosophical arguments and coherent sections
- Adapts to content structure automatically

### 5. Collection Management
- Multiple Qdrant collections supported
- Per-collection ingestion tracking (manifests)
- Copy, delete, and manage collections via GUI

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────┐
│                  Alexandria RAG System                │
├──────────────────────────────────────────────────────┤
│                                                       │
│  Streamlit GUI (Thin Layer)                          │
│         ↓                                             │
│  Scripts Package (Business Logic)                    │
│         ↓                                             │
│  Qdrant Vector DB (External: 192.168.0.151:6333)    │
│                                                       │
│  External Systems:                                    │
│    - Calibre Library (G:\My Drive\alexandria)        │
│    - OpenRouter API (LLM calls - optional)           │
└──────────────────────────────────────────────────────┘
```

**Architectural Principle:** Thin GUI layer (ADR 0003)
- GUI only handles presentation
- All business logic in `scripts/` package
- Scripts reusable from CLI and GUI

---

## Technology Stack Summary

| Layer | Technologies |
|-------|--------------|
| **GUI** | Streamlit, Pandas, Dataclasses |
| **Business Logic** | Python (scripts/ package) |
| **Embeddings** | sentence-transformers, PyTorch, NumPy, scikit-learn |
| **Vector DB** | Qdrant client |
| **Book Parsing** | EbookLib (EPUB), PyMuPDF (PDF), BeautifulSoup4 (HTML) |
| **LLM Integration** | requests (OpenRouter API) |
| **Development** | pytest, black, flake8 |

---

## Repository Structure

```
alexandria/
├── alexandria_app.py              # 🔹 GUI entry point
├── scripts/                       # 🔹 Business logic package
│   ├── calibre_db.py              # Calibre interface
│   ├── ingest_books.py            # Ingestion pipeline
│   ├── rag_query.py               # Query engine
│   ├── qdrant_utils.py            # Qdrant operations
│   ├── universal_chunking.py      # Semantic chunking
│   └── [12 other modules]
├── docs/                          # 📚 Documentation
├── logs/                          # Runtime artifacts
├── ingest/ → ingested/            # File workflow
├── _bmad-output/                  # BMad framework outputs
│   └── project-context.md         # 🔹 AI agent rules (45 rules)
└── .streamlit/                    # Configuration
```

---

## Getting Started

### Installation

```bash
# Clone repository
git clone <repository-url> alexandria
cd alexandria

# Install dependencies
pip install -r requirements.txt

# Configure API keys (optional)
# Edit .streamlit/secrets.toml

# Run GUI
streamlit run alexandria_app.py
```

**Access:** http://localhost:8501

### Usage

**Ingest Books:**
1. Place books in `ingest/` folder
2. GUI → Calibre/Ingestion Tab
3. Select files → Choose domain & collection → Start Ingestion

**Search Books:**
1. GUI → Query Tab
2. Enter query → Select collection
3. Optional: Enable LLM answer generation
4. View results

**Browse Calibre:**
1. GUI → Calibre Tab
2. Browse by filters (author, language, tags)
3. Select books for ingestion

---

## Key Innovations

### Universal Semantic Chunking (ADR 0007)

**Problem:** Fixed token windows split text mid-topic, destroying context.

**Solution:** Detect topic shifts using sentence embedding similarity:
1. Split text into sentences
2. Embed each sentence
3. Calculate cosine similarity between consecutive sentences
4. Split where similarity drops below threshold
5. Enforce min/max chunk sizes

**Benefits:**
- Preserves semantic coherence
- Adapts to content automatically
- Works with any domain/language

**Impact:** 52% improvement in philosophical query relevance (tested with Mishima)

---

## Data Flow

### Ingestion Pipeline

```
Book File → extract_text() → UniversalChunker → generate_embeddings() →
upload_to_qdrant() → CollectionManifest.add_book()
```

### Query Pipeline

```
User Query → search_qdrant() → [optional: rerank_with_llm()] →
[optional: generate_answer()] → RAGResult
```

---

## External Dependencies

| System | Location | Purpose |
|--------|----------|---------|
| **Qdrant Server** | 192.168.0.151:6333 | Vector database (MUST be accessible) |
| **Calibre Library** | G:\My Drive\alexandria | Book metadata source |
| **OpenRouter API** | Cloud service | LLM calls (optional) |

---

## Documentation Index

### For Users
- **[README.md](../README.md)** - Project landing page
- **[Quick Reference](guides/QUICK_REFERENCE.md)** - Command cheat sheet
- **[Setup Guide](guides/PROFESSIONAL_SETUP_COMPLETE.md)** - Professional setup

### For Developers
- **[Development Guide](development-guide-alexandria.md)** - Setup and workflow
- **[Architecture](architecture.md)** - System architecture
- **[Data Models & API](data-models-alexandria.md)** - Module APIs
- **[Source Tree](source-tree-analysis.md)** - Codebase structure
- **[Project Context](../_bmad-output/project-context.md)** - AI agent rules

### Architecture Details
- **[Architecture Summary](architecture/ARCHITECTURE_SUMMARY.md)** - High-level overview
- **[C4 Diagrams](architecture/c4/)** - Visual diagrams (Context, Container, Component)
- **[ADRs](architecture/decisions/README.md)** - Architecture Decision Records (7 ADRs)
- **[Technical Specs](architecture/technical/)** - Detailed technical docs

### Other
- **[CHANGELOG.md](../CHANGELOG.md)** - Completed work archive
- **[TODO.md](../TODO.md)** - Prioritized backlog
- **[Research](research/)** - Background research

---

## Key Architectural Decisions

| ADR | Decision | Status |
|-----|----------|--------|
| [0001](architecture/decisions/0001-use-qdrant-vector-db.md) | Use Qdrant Vector DB | ✅ Accepted |
| [0003](architecture/decisions/0003-gui-as-thin-layer.md) | GUI as Thin Presentation Layer | ✅ Accepted |
| [0004](architecture/decisions/0004-collection-specific-manifests.md) | Collection-Specific Manifests | ✅ Accepted |
| [0006](architecture/decisions/0006-separate-systems-architecture.md) | Local Qdrant with Separate Collections | ✅ Accepted |
| [0007](architecture/decisions/0007-universal-semantic-chunking.md) | Universal Semantic Chunking | ✅ Accepted |
| [0002](architecture/decisions/0002-domain-specific-chunking.md) | Domain-Specific Chunking | 🔄 Superseded by 0007 |
| [0005](architecture/decisions/0005-philosophical-argument-chunking.md) | Philosophical Argument Chunking | 🔄 Superseded by 0007 |

---

## Development Status

### Implemented ✅
- Semantic search with Qdrant
- LLM-powered RAG answers
- EPUB and PDF parsing
- Universal semantic chunking
- Calibre library integration
- Collection management GUI
- Ingestion tracking with manifests
- CLI scripts for all operations

### Planned 🚧
- Ingest versioning (track version in Qdrant payload)
- Chunk fingerprinting (sha1 for deduplication)
- Query modes (fact/cite/explore/synthesize)
- Calibre path configuration (restore GUI setting)
- Test coverage (pytest suite)

### Future Ideas 💡
- MOBI format support
- Multi-file drag-and-drop upload
- Dockerization
- CI/CD pipeline

---

## Performance Characteristics

| Operation | Performance |
|-----------|-------------|
| EPUB ingestion | ~2-5 seconds per book |
| PDF ingestion | ~5-15 seconds per book |
| Vector search | <100ms |
| LLM answer generation | 2-10 seconds |
| Collection size | ~9,000 books, ~800,000 chunks |

---

## Known Limitations

1. **Embedding model immutable** - Cannot change from all-MiniLM-L6-v2 without re-ingesting all books
2. **Distance metric hardcoded** - COSINE only, changing would break existing collections
3. **Calibre path hardcoded** - Currently `G:\My Drive\alexandria` (should be configurable)
4. **Chunking parameters hardcoded** - Threshold/min/max not exposed in GUI settings

**See:** [Architecture](architecture.md) for full list of constraints

---

## Getting Help

### Internal Resources
- Check documentation in `docs/`
- Review code comments and docstrings
- Consult CHANGELOG.md for recent changes
- Check TODO.md for known issues

### External Resources
- **Streamlit Docs:** https://docs.streamlit.io
- **Qdrant Docs:** https://qdrant.tech/documentation
- **sentence-transformers:** https://www.sbert.net

---

## License & Credits

**Project:** Alexandria - Temenos Academy Library
**Author:** User (Sabo) with Claude Code assistance
**Framework:** BMad Method (project management and workflows)
**Documentation:** Generated by document-project workflow (2026-01-26)

---

**Last Updated:** 2026-01-26
**Document Version:** 1.0
