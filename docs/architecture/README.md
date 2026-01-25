# Alexandria Architecture Documentation

**Purpose:** C4 model architecture documentation with Architecture Decision Records (ADRs)

---

## Quick Navigation

- **[Architecture Summary](ARCHITECTURE_SUMMARY.md)** - ⭐ One-page architecture reference
- **[C4 Diagrams](#c4-diagrams)** - Visual architecture at different abstraction levels
- **[Architecture Decisions](#architecture-decisions)** - ADRs explaining "why" behind design choices
- **[Technical Specifications](#technical-specifications)** - Detailed technical docs

---

## C4 Diagrams

Alexandria uses the **C4 model** to document architecture at 4 levels of abstraction:

1. **[System Context](c4/01-context.md)** - How Alexandria fits in the broader ecosystem
2. **[Containers](c4/02-container.md)** - Major architectural components (GUI, Scripts, Databases)
3. **[Components](c4/03-component.md)** - Internal structure of Scripts Package
4. **Code** - (Not documented - see source code directly)

### Viewing Diagrams Interactively

**Option 1: Structurizr Lite (Recommended)**
```bash
# Start Structurizr Lite on port 8081 (port 8080 used by WBF2)
scripts/start-structurizr.bat

# Or manually:
docker run -it --rm -p 8081:8080 -v "%cd%/docs/architecture:/usr/local/structurizr" structurizr/lite
```

Open: http://localhost:8081

**Option 2: Structurizr DSL Editor**
- Upload `workspace.dsl` to https://structurizr.com/dsl
- View diagrams in browser

### DSL File
- **[workspace.dsl](workspace.dsl)** - Main Structurizr DSL file defining all diagrams

---

## Architecture Decisions

All architectural decisions are documented as **ADRs (Architecture Decision Records)**:

- **[ADR Index](decisions/README.md)** - List of all decisions
- **[ADR Template](decisions/template.md)** - Template for new ADRs

### Key Decisions

All major architectural decisions documented:

| ADR | Decision | Component | Impact |
|-----|----------|-----------|--------|
| [0001](decisions/0001-use-qdrant-vector-db.md) | Use Qdrant Vector DB | External System | Enables fast semantic search (<100ms) |
| [0002](decisions/0002-domain-specific-chunking.md) | Domain-Specific Chunking | Chunking Strategies | 35% improvement in retrieval quality |
| [0003](decisions/0003-gui-as-thin-layer.md) | GUI as Thin Presentation Layer | GUI + Scripts | Single source of truth, reduced 160 LOC duplication |
| [0004](decisions/0004-collection-specific-manifests.md) | Collection-Specific Manifests | Collection Management | Prevents cross-contamination, auto-reset on deletion |
| [0005](decisions/0005-philosophical-argument-chunking.md) | Philosophical Argument Chunking | Chunking Strategies | 52% improvement for philosophical queries |

**✅ All ADRs implemented and in production.**
**📖 See [ADR Index](decisions/README.md) for details and instructions on creating new ADRs.**

---

## Technical Specifications

Detailed technical documentation:

- **[Qdrant Payload Structure](technical/QDRANT_PAYLOAD_STRUCTURE.md)** - Vector DB schema
- **[PDF vs EPUB Comparison](technical/PDF_vs_EPUB_COMPARISON.md)** - Format analysis

---

## Architecture Principles

### 1. **Scripts-First Architecture**
All business logic lives in `scripts/` package. GUI, CLI, and AI agents all call the same functions.

**Why?** Single source of truth, easy testing, multiple interfaces.

**See:** [ADR 0003](decisions/0003-gui-as-thin-layer.md)

### 2. **Domain-Driven Chunking**
Different content types need different chunk sizes (technical: 1500-2000, psychology: 1000-1500, philosophy: 1200-1800).

**Why?** Technical docs need full context, psychology concepts are self-contained, philosophy requires argument structures.

**See:** [ADR 0002](decisions/0002-domain-specific-chunking.md)

### 3. **Collection Isolation**
Each collection has separate manifests, progress files, and can use different embedding models.

**Why?** Prevents cross-contamination, allows experimentation, supports multiple use cases.

**See:** [ADR 0004](decisions/0004-collection-specific-manifests.md)

---

## Component-to-Story Mapping

Architecture components map directly to feature stories:

| Component | Story |
|-----------|-------|
| Ingestion Engine | [01-INGESTION.md](../stories/01-INGESTION.md) |
| Chunking Strategies | [02-CHUNKING.md](../stories/02-CHUNKING.md) |
| RAG Query Engine | [03-RAG_QUERY.md](../stories/03-RAG_QUERY.md) |
| Collection Management | [06-COLLECTION_MANAGEMENT.md](../stories/06-COLLECTION_MANAGEMENT.md) |
| Calibre Integration | [05-CALIBRE_INTEGRATION.md](../stories/05-CALIBRE_INTEGRATION.md) |
| Streamlit GUI | [04-GUI.md](../stories/04-GUI.md) |

---

## Related Documentation

- **[AGENTS.md](../../AGENTS.md)** - AI agent configuration and defaults
- **[Stories](../stories/)** - Feature-focused documentation
- **[Guides](../guides/)** - User-facing guides

---

---

## Quick Architecture Overview

### System Components

**Alexandria RAG System** consists of:

1. **Streamlit GUI** - Web interface for browsing, ingesting, and querying
2. **Scripts Package** - Core business logic (Python modules)
   - Ingestion Engine (`ingest_books.py`)
   - Universal Semantic Chunker (`universal_chunking.py`)
   - RAG Query Engine (`rag_query.py`)
   - Collection Management (`collection_manifest.py`)
   - Calibre Integration (`calibre_db.py`)
3. **Qdrant Vector DB** - Stores 384-dim embeddings with metadata
4. **OpenRouter API** - LLM inference for answer generation
5. **Calibre Database** - Book metadata (SQLite)
6. **File System** - Book storage and manifests

### Data Flow Summary

**Ingestion:**
```
Book File → Text Extraction → Universal Semantic Chunking → Embedding → Qdrant Storage
                                      ↓
                              (Splits by semantic similarity, not word count)
```

**Query:**
```
User Query → Embedding → Qdrant Search → Filter by Threshold → Optional LLM Rerank → OpenRouter Answer Generation
```

### Key Technologies

- **Python 3.14** - All application code
- **Streamlit** - GUI framework
- **sentence-transformers** - Embeddings (all-MiniLM-L6-v2, 384 dimensions)
- **Qdrant** - Vector database (cosine distance)
- **OpenRouter** - Multi-model LLM API
- **SQLite** - Calibre metadata storage
- **PyMuPDF** - PDF text extraction
- **ebooklib** - EPUB text extraction

### Universal Semantic Chunking

Alexandria uses a **semantic-aware chunking strategy** that breaks text at topic boundaries:

- **Embedding-based:** Each sentence is embedded and compared to previous sentence
- **Similarity threshold:** Chunks split when cosine similarity drops below threshold (0.55 default, 0.45 for philosophy)
- **Context preservation:** Minimum 200 words per chunk ensures adequate context
- **Safety cap:** Maximum 1200 words prevents LLM context overflow
- **Domain agnostic:** Same algorithm works for technical, psychology, philosophy, literature

This replaces earlier fixed-window and domain-specific strategies with a unified, intelligent approach.

---

**Last Updated:** 2026-01-25
