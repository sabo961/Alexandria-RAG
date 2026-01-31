# Alexandria - Temenos Academy Library

> *"Η Βιβλιοθήκη της Αλεξάνδρειας ήταν η μεγαλύτερη βιβλιοθήκη του αρχαίου κόσμου"*
>
> The Library of Alexandria was the largest library of the ancient world.

Semantic RAG library that connects 9000 multidisciplinary books (technical, psychology, philosophy, history) for knowledge synthesis across domains.

**Status:** Phase 1 - Production Ready ✅

---

## Quick Start

### MCP Server (Primary - via Claude Code)

Configure `.mcp.json`:
```json
{
  "mcpServers": {
    "alexandria": {
      "command": "uv",
      "args": ["run", "--directory", "C:/path/to/Alexandria", "python", "scripts/mcp_server.py"],
      "env": {
        "QDRANT_HOST": "192.168.0.151",
        "CALIBRE_LIBRARY_PATH": "G:\\My Drive\\alexandria"
      }
    }
  }
}
```

**Usage:**
```
User: What does Silverston say about shipment patterns?
Claude: [calls alexandria_query("shipment pattern", context_mode="contextual")]

User: Ingest all Nietzsche books
Claude: [calls alexandria_batch_ingest(author="Nietzsche", limit=10)]
```

### CLI (Secondary)
```bash
cd scripts
# Check what's been ingested
python collection_manifest.py show alexandria

# Query books
python rag_query.py "your question here" --limit 5 --context-mode contextual
```

**📖 For detailed guides:** See [docs/user-docs/how-to/common-workflows.md](docs/user-docs/how-to/common-workflows.md)

---

## Vision

**Short-term:** RAG system for semantic search across 9,000 books with citation-backed answers

**Long-term:** Multi-disciplinary knowledge synthesis engine that:
- Connects technical patterns with historical precedents
- Maps psychological principles to UX design decisions
- Validates architectural choices through philosophical frameworks
- Discovers cross-domain insights (e.g., "manufacturing execution patterns in 18th-century textile mills")

---

## Key Features

### 🤖 MCP Server (Primary Interface)
- Direct integration with Claude Code via Model Context Protocol
- Query tools: `alexandria_query`, `alexandria_search`, `alexandria_book`, `alexandria_stats`
- Ingest tools: `alexandria_ingest`, `alexandria_batch_ingest`, `alexandria_ingest_file`
- Context modes: precise, contextual, comprehensive

### 🔧 Python CLI
- Batch ingestion with automatic resume on failure
- Collection-specific manifest tracking with CSV export
- Experiment tools for A/B testing chunking strategies

### 📚 Calibre Integration
- Direct SQLite access to Calibre metadata
- Rich metadata extraction (author, series, tags, languages)
- Support for EPUB, PDF, TXT, MD formats

### 🧠 Universal Semantic Chunking
- Splits by semantic similarity, not word count
- Configurable threshold, min/max chunk sizes
- Hierarchical chunking (parent=chapter, child=semantic)
- See [technical spec](docs/architecture/technical/UNIVERSAL_SEMANTIC_CHUNKING.md)

---

## Technology Stack

- **Interface:** MCP Server (Model Context Protocol via FastMCP)
- **Vector DB:** Qdrant (192.168.0.151:6333)
- **Embeddings:** sentence-transformers (all-MiniLM-L6-v2, 384-dim)
- **LLM:** OpenRouter API (optional, for RAG answers)
- **Testing:** pytest (unit tests + integration tests)
- **DB Explorer:** Datasette (web UI for Calibre SQLite exploration)
- **Python:** 3.14+

**For complete technology details:** See [docs/project-context.md](docs/project-context.md)

---

## Testing

```bash
# Run all tests
pytest tests/

# Run unit tests only
pytest tests/ --ignore=tests/ui/

# Run UI tests (Playwright - headless)
pytest tests/ui/ -v

# Run UI tests with visible browser
pytest tests/ui/ -v --headed

# Slow motion for demos
pytest tests/ui/ -v --headed --slowmo=500

# First-time setup: install browsers
playwright install
```

**For complete testing documentation:** See [docs/project-context.md](docs/project-context.md#testing-rules)

---

## Calibre Database Explorer (Datasette)

Explore the Calibre library metadata through a web interface:

```bash
# Start Datasette on Calibre database
datasette "G:/My Drive/alexandria/metadata.db" --port 8002

# Open http://localhost:8002 in browser
```

Features:
- Browse all tables (books, authors, tags, publishers, series...)
- SQL editor for custom queries
- Faceted search and filtering
- Export to CSV/JSON
- Automatic REST API for every table

```bash
# Example: JSON API access
curl "http://localhost:8002/metadata/books.json?_limit=10"
```

---

## Documentation Map

### 🚀 For New Users
- **[Quick Start](#quick-start)** - Get running in 5 minutes (above)
- **[Common Workflows](docs/user-docs/how-to/common-workflows.md)** - Command cheat sheet
- **[Track Ingestion Guide](docs/user-docs/how-to/track-ingestion.md)** - Track ingested books
- **[Professional Setup Guide](docs/user-docs/tutorials/professional-setup.md)** - Complete production guide

### 🤖 For AI Agents
- **[AGENTS.md](AGENTS.md)** - Navigation hub (start here)
- **[docs/project-context.md](docs/project-context.md)** - Critical rules & patterns (implementation bible)

### 🔒 Security
- **[SECURITY.md](docs/development/security/SECURITY.md)** - XSS prevention, HTML sanitization, safe coding guidelines
- **[Unsafe HTML Audit](docs/development/security/unsafe_html_audit.md)** - Complete audit of unsafe_allow_html usage

### 👨‍💻 For Contributors
- **[TODO.md](TODO.md)** - Prioritized backlog (P0-P3)
- **[CHANGELOG.md](CHANGELOG.md)** - Completed work archive

### 🛠️ Developer Tools
- **[PowerShell Setup](docs/user-docs/tutorials/powershell-setup.md)** - Git/dotnet/npm/docker aliases + enhanced prompt
- **[Git Workflow](docs/user-docs/how-to/git-workflow.md)** - Branching strategy & Auto-Claude integration

### 🏗️ For Architecture
- **[Architecture Overview](docs/architecture/README.md)** - Complete system architecture
- **[System Context](docs/architecture/c4/01-context.md)** - C4 Level 1
- **[Containers](docs/architecture/c4/02-container.md)** - C4 Level 2
- **[Components](docs/architecture/c4/03-component.md)** - C4 Level 3
- **[ADRs](docs/architecture/decisions/README.md)** - Architecture Decision Records
- **[MCP Server Reference](docs/architecture/mcp-server.md)** - Complete MCP tool documentation

### 🔬 Research
- **[Project Proposal](docs/development/research/alexandria-qdrant-project-proposal.md)** - Original vision
- **[Philosophical Chunking](docs/development/research/argument_based_chunking_for_philosophical_texts_alexandria_rag.md)** - Argument-based approach

---

## 📚 Documentation Structure

| Section | Purpose |
|---------|---------|
| **[docs/index.md](docs/index.md)** | Documentation hub - Start here |
| **[docs/architecture/](docs/architecture/)** | C4 diagrams, ADRs, technical specs |
| **[docs/user-docs/](docs/user-docs/)** | Tutorials, how-to guides, explanations |
| **[docs/development/ideas/](docs/development/ideas/)** | Future visions (not yet in TODO) |
| **[docs/development/backlog/](docs/development/backlog/)** | Detailed docs for active TODO items |
| **[docs/development/research/](docs/development/research/)** | Research papers and analysis |

**Key documents:**
- **[MCP Server Reference](docs/architecture/mcp-server.md)** - Complete tool documentation
- **[Architecture Overview](docs/architecture/README.md)** - System design
- **[Common Workflows](docs/user-docs/how-to/common-workflows.md)** - Quick reference

**For AI agents:**
- **[Project Context](docs/project-context.md)** - Implementation rules
- **[AGENTS.md](AGENTS.md)** - Navigation hub

---

## Configuration

**MCP Server:**
- Configure in `.mcp.json`
- Entry point: `scripts/mcp_server.py`

**Qdrant Server:**
- Host: 192.168.0.151
- Port: 6333
- Status: ✅ Running

**Python Environment:**
- Version: Python 3.14+
- Dependencies: requirements.txt
- Package manager: uv (recommended)

**OpenRouter API (optional):**
- Set `OPENROUTER_API_KEY` environment variable

**For complete configuration details:** See [docs/project-context.md](docs/project-context.md)

---

## Recent Highlights

**Latest completed work:** See [CHANGELOG.md](CHANGELOG.md)

**Recent features (2026-01-30):**
- ✅ MCP-first architecture (simplified GUI for browsing)
- ✅ Hierarchical chunking (parent/child chunks)
- ✅ Context modes (precise, contextual, comprehensive)
- ✅ Batch ingestion via MCP
- ✅ Response patterns for RAG discipline (direct, synthesis, critical...)
- ✅ Configurable chunking parameters

**Active work:** See [TODO.md](TODO.md)

---

## Support

**Project Owner:** Sabo (BMad team)
**Location:** `c:\Users\goran\source\repos\Temenos\Akademija\Alexandria`
**Qdrant Server:** 192.168.0.151:6333

**For AI Agents:** Start with [AGENTS.md](AGENTS.md), then read [docs/project-context.md](docs/project-context.md)

---

**Last Updated:** 2026-01-30
**Phase:** 2 - MCP-First
**Status:** ✅ MCP Server + Python CLI + Calibre Integration + Hierarchical RAG
