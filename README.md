# Alexandria - Temenos Academy Library

> *"Η Βιβλιοθήκη της Αλεξάνδρειας ήταν η μεγαλύτερη βιβλιοθήκη του αρχαίου κόσμου"*
>
> The Library of Alexandria was the largest library of the ancient world.

Semantička RAG knjižnica koja povezuje 9000 multidisciplinarnih knjiga (tehnika, psihologija, filozofija, povijest) za sintezu znanja preko domena.

**Status:** Phase 1 - Production Ready ✅

---

## Quick Start

### GUI (Recommended)
```bash
streamlit run alexandria_app.py
# Open browser to http://localhost:8501
# Browse Calibre library, ingest books, query collection
```

### CLI (Advanced)
```bash
cd scripts
# Check what's been ingested
python collection_manifest.py show alexandria

# Query books
python rag_query.py "your question here" --limit 5

# Batch ingest
python batch_ingest.py --directory ../ingest --domain technical
```

**📖 For detailed guides:** See [docs/guides/QUICK_REFERENCE.md](docs/guides/QUICK_REFERENCE.md)

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

### 🖥️ Streamlit GUI
- Calibre library browser with filters and pagination
- Direct ingestion from Calibre (no file copying)
- RAG-powered Q&A with OpenRouter LLM integration
- Advanced query settings (similarity, temperature, reranking)

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
- Domain-specific thresholds (philosophy vs technical)
- Author-specific patterns (Mishima, Nietzsche, Cioran)
- See [technical spec](docs/architecture/technical/UNIVERSAL_SEMANTIC_CHUNKING.md)

---

## Technology Stack

- **GUI:** Streamlit (web interface, binds to 0.0.0.0:8501)
- **Vector DB:** Qdrant (192.168.0.151:6333)
- **Embeddings:** sentence-transformers (all-MiniLM-L6-v2, 384-dim)
- **LLM:** OpenRouter API (configurable models)
- **Python:** 3.14+

**For complete technology details:** See [_bmad-output/project-context.md](_bmad-output/project-context.md)

---

## Documentation Map

### 🚀 For New Users
- **[Quick Start](#quick-start)** - Get running in 5 minutes (above)
- **[QUICK_REFERENCE.md](docs/guides/QUICK_REFERENCE.md)** - Command cheat sheet
- **[LOGGING_GUIDE.md](docs/guides/LOGGING_GUIDE.md)** - Track ingested books
- **[PROFESSIONAL_SETUP_COMPLETE.md](docs/guides/PROFESSIONAL_SETUP_COMPLETE.md)** - Complete production guide

### 🤖 For AI Agents
- **[AGENTS.md](AGENTS.md)** - Navigation hub (start here)
- **[_bmad-output/project-context.md](_bmad-output/project-context.md)** - Critical rules & patterns (implementation bible)

### 🔒 Security
- **[SECURITY.md](docs/SECURITY.md)** - XSS prevention, HTML sanitization, safe coding guidelines
- **[Unsafe HTML Audit](docs/unsafe_html_audit.md)** - Complete audit of unsafe_allow_html usage

### 👨‍💻 For Contributors
- **[TODO.md](TODO.md)** - Prioritized backlog (P0-P3)
- **[CHANGELOG.md](CHANGELOG.md)** - Completed work archive

### 🏗️ For Architecture
- **[Architecture Overview](docs/architecture/README.md)** - C4 diagrams + ADRs
- **[System Context](docs/architecture/c4/01-context.md)** - C4 Level 1
- **[Containers](docs/architecture/c4/02-container.md)** - C4 Level 2
- **[Components](docs/architecture/c4/03-component.md)** - C4 Level 3
- **[ADRs](docs/architecture/decisions/README.md)** - Architecture Decision Records
- **[Structurizr Workspace](docs/architecture/workspace.dsl)** - Interactive diagrams (run `scripts/start-structurizr.bat`)

### 🔬 Research
- **[Project Proposal](docs/research/alexandria-qdrant-project-proposal.md)** - Original vision
- **[Philosophical Chunking](docs/research/argument_based_chunking_for_philosophical_texts_alexandria_rag.md)** - Argument-based approach
- **[Hierarchical Chunking](docs/backlog/Hierarchical Chunking for Alexandria RAG.md)** - Research proposal

---

## 📚 Generated Documentation (AI-Ready)

**Generated:** 2026-01-26 by `document-project` workflow (exhaustive scan)
**Total:** 7 files, 9,614 words (~38 pages), 89 KB

| Document | Size | Purpose |
|----------|------|---------|
| **[docs/index.md](docs/index.md)** | 13 KB | 🔹 **Master documentation index** - Start here for navigation |
| **[docs/architecture.md](docs/architecture.md)** | 21 KB | Complete system architecture (data flow, algorithms, constraints) |
| **[docs/project-overview.md](docs/project-overview.md)** | 12 KB | Executive summary & quick reference |
| **[docs/data-models-alexandria.md](docs/data-models-alexandria.md)** | 14 KB | API reference for all scripts/ modules |
| **[docs/source-tree-analysis.md](docs/source-tree-analysis.md)** | 15 KB | Annotated codebase structure with entry points |
| **[docs/development-guide-alexandria.md](docs/development-guide-alexandria.md)** | 12 KB | Setup, workflow, CLI usage, debugging |
| **[docs/project-scan-report.json](docs/project-scan-report.json)** | 2.4 KB | Workflow state & scan metadata |

**Primary entry point:** [docs/index.md](docs/index.md) - Master index with links to all documentation

**Why useful:**
- ✅ AI agents get complete codebase context (API reference, architecture, data models)
- ✅ New developers can onboard without Q&A sessions
- ✅ BMad PRD workflow can reference detailed architecture
- ✅ Future you (6 months from now) remembers how everything works

---

## Configuration

**Qdrant Server:**
- Host: 192.168.0.151
- Port: 6333
- Status: ✅ Running

**Python Environment:**
- Version: Python 3.14+
- Dependencies: requirements.txt
- Virtual Env: Not used (system Python)

**OpenRouter API:**
- Configure in `.streamlit/secrets.toml` (gitignored)
- Or set `OPENROUTER_API_KEY` environment variable

**For complete configuration details:** See [_bmad-output/project-context.md](_bmad-output/project-context.md)

---

## Recent Highlights

**Latest completed work:** See [CHANGELOG.md](CHANGELOG.md)

**Recent features (2026-01-23):**
- ✅ Qdrant health check on startup
- ✅ Philosophical argument-based chunking
- ✅ GUI polish + manifest bug fixes
- ✅ Calibre integration enhancements

**Active work:** See [TODO.md](TODO.md)

---

## Support

**Project Owner:** Sabo (BMad team)
**Location:** `c:\Users\goran\source\repos\Temenos\Akademija\Alexandria`
**Qdrant Server:** 192.168.0.151:6333

**For AI Agents:** Start with [AGENTS.md](AGENTS.md), then read [_bmad-output/project-context.md](_bmad-output/project-context.md)

---

**Last Updated:** 2026-01-25
**Phase:** 1 - Production Ready
**Status:** ✅ Streamlit GUI + Python CLI + Calibre Integration + RAG Query System
