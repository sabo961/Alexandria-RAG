# Alexandria - Project Overview

**Project Name:** Alexandria - Temenos Academy Library
**Type:** RAG (Retrieval-Augmented Generation) System
**Status:** Production
**Updated:** 2026-01-30

---

## What is Alexandria?

Alexandria is a **semantic search and knowledge retrieval system** for the Temenos Academy library of 9,000+ books. It uses vector embeddings and RAG (Retrieval-Augmented Generation) to enable:

- **Semantic book search** - Find relevant passages by meaning, not just keywords
- **LLM-powered answers** - Generate answers from book content using Claude/GPT-4
- **Multi-format support** - EPUB, PDF, TXT, MD, HTML
- **Calibre integration** - Browse and ingest books directly from Calibre library
- **Hierarchical chunking** - Parent (chapter) + child (semantic) chunks for better context

---

## Quick Facts

| Aspect | Details |
|--------|---------|
| **Primary Language** | Python 3.14+ |
| **Architecture** | MCP-first RAG System |
| **Primary Interface** | MCP Server (Claude Code integration) |
| **Vector Database** | Qdrant (external: 192.168.0.151:6333) |
| **Embedding Model** | all-MiniLM-L6-v2 (384-dimensional) |
| **Books Supported** | EPUB, PDF, TXT, MD, HTML |
| **Total Books** | ~9,000 (Temenos Academy Library) |
| **Repository Type** | Monolith (single cohesive codebase) |
| **Entry Point** | `scripts/mcp_server.py` (MCP Server) |

---

## Key Features

### 1. Semantic Search with Hierarchical Context
- Vector similarity search using Qdrant
- Three context modes: `precise`, `contextual`, `comprehensive`
- Parent chunks provide chapter context
- Child chunks provide precise semantic matches

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
- Configurable parameters: threshold, min_chunk_size, max_chunk_size

### 5. MCP Server Integration
- Full integration with Claude Code via Model Context Protocol
- Query tools: `alexandria_query`, `alexandria_search`, `alexandria_book`, `alexandria_stats`
- Ingest tools: `alexandria_ingest`, `alexandria_batch_ingest`, `alexandria_ingest_file`
- Progress tracking with visual indicators

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                  Alexandria RAG System                        │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  Claude Code / MCP Clients                                   │
│         ↓ (stdio)                                            │
│  MCP Server (scripts/mcp_server.py)                          │
│         ↓                                                     │
│  Scripts Package (Business Logic)                            │
│         ↓                                                     │
│  Qdrant Vector DB (External: 192.168.0.151:6333)            │
│                                                               │
│  External Systems:                                            │
│    - Calibre Library (G:\My Drive\alexandria)                │
│    - OpenRouter API (LLM calls - optional)                   │
└──────────────────────────────────────────────────────────────┘
```

**Architectural Principle:** MCP-first design
- MCP server is the primary interface
- All business logic in `scripts/` package
- Scripts reusable from CLI and MCP

---

## Technology Stack Summary

| Layer | Technologies |
|-------|--------------|
| **Interface** | MCP Server (FastMCP) |
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
├── scripts/                       # 🔹 Business logic package
│   ├── mcp_server.py              # 🔹 MCP server entry point
│   ├── calibre_db.py              # Calibre interface
│   ├── ingest_books.py            # Ingestion pipeline
│   ├── rag_query.py               # Query engine
│   ├── chapter_detection.py       # Hierarchical chunking
│   ├── universal_chunking.py      # Semantic chunking
│   └── [other modules]
├── docs/                          # 📚 Documentation
├── logs/                          # Runtime artifacts
├── _bmad-output/                  # BMad framework outputs
│   └── project-context.md         # 🔹 AI agent rules
└── .mcp.json                      # MCP server configuration
```

---

## Getting Started

### MCP Server Configuration

Add to your `.mcp.json`:

```json
{
  "mcpServers": {
    "alexandria": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/Alexandria", "python", "scripts/mcp_server.py"],
      "env": {
        "QDRANT_HOST": "192.168.0.151",
        "QDRANT_PORT": "6333",
        "CALIBRE_LIBRARY_PATH": "G:\\My Drive\\alexandria"
      }
    }
  }
}
```

### Usage via Claude Code

**Query Books:**
```
User: What does Silverston say about the shipment pattern?
Claude: [calls alexandria_query("shipment pattern", context_mode="contextual")]
```

**Ingest Books:**
```
User: Ingest all Nietzsche books
Claude: [calls alexandria_batch_ingest(author="Nietzsche", limit=10)]
```

---

## Key Innovations

### Hierarchical Chunking (2026-01-30)

**Problem:** Flat chunks lose chapter context, making it hard to understand where content fits.

**Solution:** Two-level chunking:
- **Parent chunks**: One per chapter, contains full chapter text
- **Child chunks**: Semantic chunks within chapter, linked via `parent_id`

**Context Modes:**
| Mode | Returns | Use Case |
|------|---------|----------|
| `precise` | Child chunks only | Fast, exact citations |
| `contextual` | Children + parent context | Understanding context |
| `comprehensive` | Children + parent + siblings | Deep analysis |

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

---

## Data Flow

### Ingestion Pipeline

```
Book File → extract_text() → detect_chapters() →
UniversalChunker (per chapter) → generate_embeddings() →
upload_hierarchical_to_qdrant() → CollectionManifest.add_book()
```

### Query Pipeline

```
User Query → search_qdrant(chunk_level="child") →
fetch_parent_chunks() → [optional: generate_answer()] → RAGResult
```

---

## External Dependencies

| System | Location | Purpose |
|--------|----------|---------|
| **Qdrant Server** | 192.168.0.151:6333 | Vector database (MUST be accessible) |
| **Calibre Library** | G:\My Drive\alexandria | Book metadata source |
| **OpenRouter API** | Cloud service | LLM calls (optional) |

---

## Development Status

### Implemented ✅
- Semantic search with Qdrant
- Hierarchical chunking (parent/child)
- Context modes (precise/contextual/comprehensive)
- MCP server with 10+ tools
- LLM-powered RAG answers
- EPUB, PDF, TXT, MD, HTML parsing
- Universal semantic chunking
- Calibre library integration
- Batch ingestion
- Configurable chunking parameters

### Planned 🚧
- Re-ingest option (bypass manifest)
- Ingest versioning
- Chunk fingerprinting
- Query modes (fact/cite/explore/synthesize)

---

## Performance Characteristics

| Operation | Performance |
|-----------|-------------|
| EPUB ingestion | ~2-5 seconds per book |
| PDF ingestion | ~5-15 seconds per book |
| Vector search | <100ms |
| Contextual search | <250ms |
| LLM answer generation | 2-10 seconds |

---

## Documentation Index

### For Users
- **[MCP Server Reference](../reference/mcp-server.md)** - Complete tool documentation
- **[Common Workflows](../how-to-guides/common-workflows.md)** - Command cheat sheet

### For Developers
- **[Architecture](./architecture.md)** - System architecture
- **[Data Models & API](../reference/api/data-models.md)** - Module APIs
- **[Source Tree](../reference/api/source-tree.md)** - Codebase structure
- **[Project Context](../../_bmad-output/project-context.md)** - AI agent rules

### Architecture Details
- **[Architecture](./architecture.md)** - Complete system architecture
- **[ADRs](../reference/architecture/decisions/README.md)** - Architecture Decision Records
- **[Technical Specs](../reference/architecture/technical/)** - Detailed technical docs

---

## Key Architectural Decisions

| ADR | Decision | Status |
|-----|----------|--------|
| [0001](../reference/architecture/decisions/0001-use-qdrant-vector-db.md) | Use Qdrant Vector DB | ✅ Accepted |
| [0003](../reference/architecture/decisions/0003-gui-as-thin-layer.md) | GUI as Thin Layer | ⚠️ Superseded (GUI abandoned) |
| [0004](../reference/architecture/decisions/0004-collection-specific-manifests.md) | Collection-Specific Manifests | ✅ Accepted |
| [0006](../reference/architecture/decisions/0006-separate-systems-architecture.md) | Local Qdrant with Separate Collections | ✅ Accepted |
| [0007](../reference/architecture/decisions/0007-universal-semantic-chunking.md) | Universal Semantic Chunking | ✅ Accepted |

---

## Anti-Goals

- ❌ **GUI Development** - Abandoned in favor of MCP-first approach
- ❌ **Multiple ingestion pipelines** - Single universal pipeline
- ❌ **Framework-heavy RAG** - No LangChain, keep simple

---

**Last Updated:** 2026-01-30
**Document Version:** 2.0 (MCP-first)
