# Alexandria - Temenos Academy Library

> *"Η Βιβλιοθήκη της Αλεξάνδρειας ήταν η μεγαλύτερη βιβλιοθήκη του αρχαίου κόσμου"*
>
> The Library of Alexandria was the largest library of the ancient world.

Semantička RAG knjižnica koja povezuje 9000 multidisciplinarnih knjiga (tehnika, psihologija, filozofija, povijest) za sintezu znanja preko domena.

**Status:** Phase 1 - Production Ready ✅ (Streamlit GUI + Python CLI + Calibre Integration)

---

## Quick Start

### GUI (Recommended)
```bash
# 1. Start Streamlit app
streamlit run alexandria_app.py

# 2. Open browser to http://localhost:8501
# 3. Browse Calibre library, ingest books, query collection
```

### CLI (Advanced)
```bash
# Navigate to scripts directory
cd scripts

# Check what's been ingested
python collection_manifest.py show alexandria

# Query books
python rag_query.py "your question here" --limit 5

# Batch ingest
python batch_ingest.py --directory ../ingest --domain technical --collection alexandria
```

**📖 For detailed guides, see [`docs/guides/`](docs/guides/)**

---

## Vizija

**Kratkoročno:** RAG sustav koji semantički pretražuje 9000 knjiga i vraća relevantne pasaže s citacijama

**Dugoročno:** Multidisciplinarni knowledge synthesis engine koji:
- Povezuje tehničke paterne s povijesnim precedentima
- Mapira psihološke principe u UX dizajn odluke
- Validira arhitekturalne izbore preko filozofskih okvira
- Otkriva cross-domain uvide (npr. "manufacturing execution patterns u 18th-century textile mills")

---

## Tehnologije

- **GUI:** Streamlit web interface (localhost:8501)
- **Vector DB:** Qdrant (192.168.0.151:6333)
- **Embedding Model:** Nomic AI embedding model (768-dim)
- **LLM:** OpenRouter API (configurable models, free & paid)
- **Calibre:** Direct integration with Calibre library database
- **Chunking:** Domain-specific automatic optimization (Technical: 1500-2000 tokens, Psychology: 1000-1500, Philosophy: 1200-1800, History: 1500-2000)
- **Workflow:** Streamlit GUI + Python CLI
- **Ingestion:** EPUB, PDF, TXT, MD support
- **Tracking:** Automatic collection-specific manifest logging

---

## Struktura Projekta

```
Alexandria/
├── README.md                           # This file
├── AGENTS.md                           # AI agent configuration & defaults
├── alexandria_app.py                   # 🌟 Streamlit GUI application
├── requirements.txt                    # Python dependencies
│
├── .streamlit/                         # Streamlit configuration
│   ├── config.toml                     # Server & theme config
│   └── secrets.toml                    # API keys (gitignored)
│
├── .vscode/                            # VS Code configuration
│   ├── launch.json                     # Debug configurations
│   └── settings.json                   # Python settings
│
├── .claude/                            # Claude Code configuration
│   └── config.json                     # Agent instructions
│
├── docs/                               # Documentation
│   ├── guides/                         # User guides
│   │   ├── QUICK_REFERENCE.md          # Command cheat sheet ⭐
│   │   ├── LOGGING_GUIDE.md            # Tracking system guide
│   │   ├── PROFESSIONAL_SETUP_COMPLETE.md  # Complete guide
│   │   └── OPEN_WEBUI_CONFIG.md        # Open WebUI integration
│   ├── alexandria-qdrant-project-proposal.md
│   └── missing-classics-analysis.md
│
├── scripts/                            # Python scripts
│   ├── ingest_books.py                 # Single book ingestion
│   ├── batch_ingest.py                 # Batch processing + auto-logging
│   ├── rag_query.py                    # Query tool (LLM-ready output)
│   ├── experiment_chunking.py          # A/B testing chunk strategies
│   ├── qdrant_utils.py                 # Collection management
│   ├── collection_manifest.py          # Track ingested books
│   ├── README.md                       # Script documentation
│   └── batch_ingest_progress.json      # Resume tracker (auto-generated)
│
├── logs/                               # Logs & manifests
│   ├── README.md                       # Logging documentation
│   └── collection_manifest.json        # Master manifest (auto-generated)
│
├── ingest/                             # Books waiting to be processed
│   ├── Silverston Vol 1.pdf
│   ├── Silverston Vol 2.pdf
│   └── Silverston Vol 3.epub
│
└── ingested/                           # Successfully processed books (moved here)
    └── README.md                       # Ingested folder documentation
```

---

## Current Status

### System Status
- **GUI:** ✅ Fully functional Streamlit interface
- **Calibre Integration:** ✅ Direct ingestion from library
- **Vector DB:** ✅ Qdrant running on 192.168.0.151:6333
- **RAG Query:** ✅ OpenRouter LLM integration
- **Manifest Tracking:** ✅ Collection-specific logging

### Supported Content
- Technical books (Data Modeling, Software Engineering, Architecture)
- Literature (Fiction, Essays, Poetry)
- Philosophy & Psychology
- History & Social Sciences

### Available Tools
| Tool | Purpose | Status |
|------|---------|--------|
| `alexandria_app.py` | **Streamlit GUI** (browse, ingest, query) | ✅ Ready |
| `batch_ingest.py` | Production ingestion + auto-logging | ✅ Ready |
| `rag_query.py` | Query tool (LLM-ready markdown) | ✅ Ready |
| `collection_manifest.py` | Track what's been ingested | ✅ Ready |
| `qdrant_utils.py` | Collection management | ✅ Ready |
| `experiment_chunking.py` | A/B testing | ✅ Ready |
| `ingest_books.py` | Single book (dev/testing) | ✅ Ready |

### Test Results
- ✅ EPUB ingestion: 20 chapters → 153 chunks (~1450 tokens/chunk)
- ✅ PDF ingestion: 525 pages → 525 chunks (~200 tokens/chunk)
- ✅ Chunking quality: Validated for both formats
- ✅ Semantic search: 0.38-0.65 relevance scores (both formats)
- 📊 Comparison: See [docs/PDF_vs_EPUB_COMPARISON.md](docs/PDF_vs_EPUB_COMPARISON.md)

---

## Documentation

### 🚀 Start Here
- **[AGENTS.md](AGENTS.md)** - AI agent config & defaults (read this first!)
- **[QUICK_REFERENCE.md](docs/guides/QUICK_REFERENCE.md)** - Command cheat sheet
- **[TODO.md](TODO.md)** - Current tasks and roadmap

### 🏗️ Architecture (C4 Model)
- **[Architecture Overview](docs/architecture/README.md)** - C4 diagrams + ADRs
- **[System Context](docs/architecture/c4/01-context.md)** - Alexandria in ecosystem
- **[Containers](docs/architecture/c4/02-container.md)** - Major components
- **[Components](docs/architecture/c4/03-component.md)** - Internal structure
- **[ADRs](docs/architecture/decisions/README.md)** - Architecture decisions
- **Interactive Diagrams:** Run `scripts/start-structurizr.bat`

### 📖 Feature Stories
- **[Stories Index](docs/stories/README.md)** - Feature-focused documentation
- Maps to C4 components (Ingestion, Chunking, Query, GUI, etc.)

### 📚 User Guides
- **[LOGGING_GUIDE.md](docs/guides/LOGGING_GUIDE.md)** - Track what's been ingested
- **[PROFESSIONAL_SETUP_COMPLETE.md](docs/guides/PROFESSIONAL_SETUP_COMPLETE.md)** - Complete production guide
- **[OPEN_WEBUI_CONFIG.md](docs/guides/OPEN_WEBUI_CONFIG.md)** - Open WebUI integration (optional)

### 🔧 Technical Docs
- **[scripts/README.md](scripts/README.md)** - Script usage documentation
- **[logs/README.md](logs/README.md)** - Logging system details
- **[Qdrant Payload Structure](docs/architecture/technical/QDRANT_PAYLOAD_STRUCTURE.md)** - Vector DB schema
- **[PDF vs EPUB Comparison](docs/architecture/technical/PDF_vs_EPUB_COMPARISON.md)** - Format analysis

### 🔬 Research
- **[Project Proposal](docs/research/alexandria-qdrant-project-proposal.md)** - Original proposal
- **[Missing Classics Analysis](docs/research/missing-classics-analysis.md)** - Gap analysis
- **[Philosophical Chunking Research](docs/research/argument_based_chunking_for_philosophical_texts_alexandria_rag.md)** - Argument-based chunking

---

## Key Features

### 🖥️ Streamlit GUI
- **Calibre Library Browser** - Browse and filter your entire Calibre library with pagination
- **Direct Ingestion** - Select books from Calibre and ingest directly (no file copying needed)
- **Query Interface** - RAG-powered Q&A with context from your books
- **Advanced Settings** - Control similarity threshold, fetch multiplier, LLM reranking, temperature
- **Collection Management** - View ingested books, stats, and manifest tracking
- **OpenRouter Integration** - Use any LLM model (free or paid) for answer generation

### 🔧 Python CLI
- **Batch Ingestion** - Process multiple books with automatic resume on failure
- **Manifest Tracking** - Collection-specific JSON manifests with CSV exports
- **Experiment Tools** - A/B test different chunking strategies
- **Direct Qdrant Access** - Low-level collection management and search

### 📚 Calibre Integration
- Direct SQLite database access to Calibre library
- Rich metadata extraction (title, author, series, tags, languages)
- Support for multiple formats (EPUB, PDF, MOBI, AZW3)
- No file duplication - ingest directly from Calibre library paths

---

## Common Tasks

### GUI Workflow (Recommended)

1. **Start the GUI:**
   ```bash
   streamlit run alexandria_app.py
   ```

2. **Browse Calibre Library:**
   - Go to "Calibre Library" tab
   - Use filters to find books (author, format, tags)
   - Browse with pagination (20/50/100/200 rows)

3. **Ingest Books:**
   - Select books from Calibre Library tab
   - Click "Start Ingestion"
   - Or use "Ingestion" tab for manual folder ingestion

4. **Query Collection:**
   - Go to "Query" tab
   - Configure OpenRouter API key in sidebar
   - Ask questions, get LLM-generated answers with sources

5. **View Statistics:**
   - "Ingested Books" tab shows all books with filters
   - View by collection, domain, format, language

### CLI Workflow (Advanced)

#### Check What's Been Ingested
```bash
cd scripts
python collection_manifest.py show alexandria
```

#### Query Books
```bash
python rag_query.py "What does Silverston say about shipments?" --limit 5
```

#### Batch Ingest
```bash
# Process multiple books
python batch_ingest.py --directory ../ingest --domain technical --collection alexandria

# Resume after failure
python batch_ingest.py --directory ../ingest --domain technical --resume
```

#### Test Retrieval Quality
```bash
python qdrant_utils.py search alexandria "your test query" --limit 5
```

#### Experiment with Chunking
```bash
python experiment_chunking.py \
  --file "../ingest/book.epub" \
  --strategies small,medium,large
```

---

## Configuration

### Qdrant Server
```
Host: 192.168.0.151
Port: 6333
Status: ✅ Running
```

### Python Environment
```
Version: Python 3.14
Dependencies: requirements.txt
Virtual Env: Not used (system Python)
```

### VS Code
```
Debug configs: .vscode/launch.json (6 configurations)
Terminal default: scripts/ directory
```

---

## Future Development

See [TODO.md](TODO.md) for current sprint tasks and backlog.

### High Priority
- Philosophical argument-based chunking integration
- Domain parameter reset bug fix
- Pagination arrow button styling

### Planned Features
- Real-time batch ingestion progress tracking
- Resume functionality in GUI
- Advanced query history and export
- Collection admin operations (copy, merge, delete)
- MOBI format support

### Long-term Vision
- Multi-domain knowledge synthesis
- Cross-reference system between books
- Obsidian vault integration
- Web articles and YouTube transcript ingestion

---

## Support

**Project Owner:** Sabo (BMad team)
**Location:** `c:\Users\goran\source\repos\Temenos\Akademija\Alexandria`
**Qdrant Server:** 192.168.0.151:6333

**For AI Agents:** Start with [AGENTS.md](AGENTS.md) for defaults and configuration.

---

## Recent Updates (2026-01-23)

- ✅ **Streamlit GUI** - Full-featured web interface with Calibre integration
- ✅ **Calibre Direct Ingestion** - No need to copy files, ingest directly from library
- ✅ **OpenRouter Integration** - RAG with LLM answer generation
- ✅ **Advanced Query Settings** - Temperature control, reranking, fetch multiplier
- ✅ **Collection Management** - Manifest tracking with CSV exports
- ✅ **Bug Fixes** - Manifest tracking now properly updates after ingestion

---

**Last Updated:** 2026-01-23
**Phase:** 1 - Production Ready
**Status:** ✅ Streamlit GUI + Python CLI + Calibre Integration + RAG Query System
