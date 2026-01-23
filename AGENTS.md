# Alexandria Agent Configuration & Defaults

**Purpose:** Central configuration file for AI agents working on this project.
This ensures consistent settings across sessions and prevents re-discovery of project setup.

---

## Project Overview

**Name:** Alexandria RAG System ("𝔸𝕝𝕖𝕩𝕒𝕟𝕕𝕣𝕚𝕒 𝕠𝕗 𝕋𝕖𝕞𝕖𝕟𝕠𝕤")
**Type:** Retrieval-Augmented Generation (RAG) system for book library
**Status:** Phase 1 - GUI Development + CLI Production-ready
**Primary Use:** Streamlit GUI + Python CLI workflow through VS Code
**Library Size:** ~9,000 books (EPUB: 3,844, PDF: 5,291, others: <200)

---

## Key Locations

### Paths
```
Root: c:\Users\goran\source\repos\Temenos\Akademija\Alexandria
Scripts: c:\Users\goran\source\repos\Temenos\Akademija\Alexandria\scripts
Ingest: c:\Users\goran\source\repos\Temenos\Akademija\Alexandria\ingest
Logs: c:\Users\goran\source\repos\Temenos\Akademija\Alexandria\logs
```

### External Services
```
Qdrant Server: 192.168.0.151:6333
Open WebUI: https://ai.jedai.space (not currently integrated)
```

### Python Environment
```
Version: Python 3.14
Virtual Env: Not used (system Python)
Dependencies: requirements.txt
```

---

## Default Values & Configuration

### Qdrant Configuration
```python
QDRANT_HOST = "192.168.0.151"
QDRANT_PORT = 6333
DEFAULT_COLLECTION = "alexandria"
TEST_COLLECTION = "alexandria_test"
```

### Embedding Model
```python
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
VECTOR_DIMENSIONS = 384
DISTANCE_METRIC = "Cosine"
```

### Chunking Strategies (Domain-Specific)
```python
DOMAIN_CHUNK_SIZES = {
    'technical': {
        'min': 1500,
        'max': 2000,
        'overlap': 200
    },
    'psychology': {
        'min': 1000,
        'max': 1500,
        'overlap': 150
    },
    'philosophy': {
        'min': 1200,
        'max': 1800,
        'overlap': 180,
        'use_argument_chunking': True  # Pre-chunk based on conceptual oppositions
    },
    'history': {
        'min': 1500,
        'max': 2000,
        'overlap': 200
    }
}
```

### RAG Query Parameters
```python
DEFAULT_FETCH_MULTIPLIER = 3  # Fetch limit × N results from Qdrant
                              # Higher = better quality, slower retrieval
                              # Educational use: 5-10
                              # Production agents: 2-3
                              # Min fetch always: 20
```

### File Formats Supported
```python
SUPPORTED_FORMATS = ['epub', 'pdf', 'txt', 'md']
# Note: MOBI not yet implemented (convert to EPUB with Calibre)
```

---

## Architecture Documentation

Alexandria uses **C4 model** for architecture documentation:

- **[Architecture Overview](docs/architecture/README.md)** - C4 diagrams, ADRs, technical specs
- **[System Context](docs/architecture/c4/01-context.md)** - Alexandria in ecosystem
- **[Containers](docs/architecture/c4/02-container.md)** - Major components (GUI, Scripts, DBs)
- **[Components](docs/architecture/c4/03-component.md)** - Internal Scripts Package structure
- **[ADRs](docs/architecture/decisions/README.md)** - Architecture Decision Records
- **[Feature Stories](docs/stories/README.md)** - Feature-focused docs mapped to C4 components

**View diagrams interactively:** Run `scripts/start-structurizr.bat` → Open http://localhost:8081

---

## Architecture Principle

**CRITICAL:** All business logic lives in `scripts/` - GUI is just a thin presentation layer.

### Why?
- **AI agents** need to call functions directly (not via GUI)
- **CLI tools** need same logic as GUI
- **Single source of truth** for all operations
- **Easy testing** without GUI overhead

### Rules
1. ✅ **GUI (`alexandria_app.py`)** - Calls functions from `scripts/`, displays results
2. ✅ **Scripts (`scripts/*.py`)** - Contains all logic, usable by GUI/CLI/agents
3. ❌ **Never** - Implement logic directly in GUI

## Production Scripts

### Primary Tools (Use These)
```bash
# INGESTION
batch_ingest.py          # Production book ingestion (auto-logs to manifest)
ingest_books.py          # Core ingestion functions (imported by batch & GUI)
philosophical_chunking.py # Argument-based chunking for philosophical texts
                         # - Detects conceptual oppositions (words↔body, mind↔flesh)
                         # - Preserves complete arguments in chunks
                         # - Author-specific patterns (Mishima, Nietzsche, Cioran)
                         # - Activated via domains.json flag: use_argument_chunking

# QUERY
rag_query.py             # Unified RAG query engine (CLI + module interface)
                         # - Semantic search via Qdrant
                         # - Similarity threshold filtering
                         # - Configurable fetch_multiplier (controls quality vs speed)
                         # - Optional LLM reranking
                         # - OpenRouter answer generation
                         # Used by: CLI, GUI, AI agents

# MANAGEMENT
collection_manifest.py   # Track what's been ingested per collection
qdrant_utils.py          # Collection admin (stats, search, copy, delete)
```

### Configuration Files
```bash
domains.json             # Domain list (technical, psychology, philosophy, history, literature)
                         # - Loaded by GUI dropdowns
                         # - Used for filtering in rag_query.py
                         # - Contains use_argument_chunking flag per domain
```

### Development Tools
```bash
experiment_chunking.py   # A/B testing chunk strategies
generate_book_inventory.py  # Calibre library scanning
count_file_types.py      # File format statistics
```

### GUI Integration
**File:** `alexandria_app.py`

**What it does:**
- Loads domains from `scripts/domains.json`
- Calls `ingest_books.py` functions for ingestion
- Calls `perform_rag_query()` from `rag_query.py` for queries
- Calls `collection_manifest.py` for statistics
- Uses `generate_embeddings()` from `ingest_books.py`

**What it does NOT do:**
- ❌ Implement ingestion logic
- ❌ Implement RAG query logic
- ❌ Manage Qdrant connections
- ❌ Define domain lists

---

## Logging & Tracking

### Collection-Specific Logging
Each collection has **separate log files**:

**Manifest files:**
- `logs/alexandria_manifest.json` - Alexandria collection manifest
- `logs/alexandria_test_manifest.json` - Test collection manifest
- `logs/{collection_name}_manifest.json` - Per-collection pattern

**Progress files:**
- `scripts/batch_ingest_progress_alexandria.json` - Alexandria progress
- `scripts/batch_ingest_progress_{collection_name}.json` - Per-collection pattern

**Auto-reset behavior:**
- When collection is deleted from Qdrant, manifest is automatically reset to empty
- Progress file is deleted to prevent stale resume attempts
- Verified on every `batch_ingest.py` run via `verify_collection_exists()`

### Automatic Logging
`batch_ingest.py` automatically logs to collection-specific files:
- **Manifest:** `logs/{collection_name}_manifest.json` (master record)
- **Progress:** `scripts/batch_ingest_progress_{collection_name}.json` (resume support)
- **CSV Export:** `logs/{collection_name}_manifest.csv` (human-readable)

**For detailed usage and commands, see [logs/README.md](logs/README.md)**

---

## VS Code Configuration

- Debug configurations available in `.vscode/launch.json` (press F5 to select)
- Terminal default directory: `scripts/`
- For detailed VS Code workflow, see [scripts/README.md](scripts/README.md)

---

## Design Decisions & Rationale

### Why Domain-Specific Chunking?
Different content types need different chunk sizes:
- **Technical:** Larger chunks (1500-2000) for complete context (diagrams, code, multi-paragraph explanations)
- **Psychology:** Medium chunks (1000-1500) for self-contained concepts
- **Philosophy:** Medium-large (1200-1800) for argument structures (setup → claim → justification)
- **History:** Larger chunks (1500-2000) for case studies with full context

### Why Python CLI vs Web UI?
- **Control:** Direct access to Qdrant, no middleware
- **Debugging:** Easier to debug with VS Code
- **Reproducibility:** Scripts are version-controlled
- **Flexibility:** Easy to customize and extend
- **Performance:** No web overhead

### Why Manifest System?
- **Audit trail:** Know exactly what's been ingested
- **Avoid duplicates:** Check before re-ingesting
- **Resume support:** Track batch ingestion progress
- **Quick lookup:** No need to query Qdrant for metadata

---

## Agent Instructions

### CRITICAL: Language & Token Efficiency
**ALWAYS communicate in ENGLISH** when working with this user.
- English responses use ~30% fewer tokens than Croatian
- User preference: English for technical work
- Exception: Only use Croatian if explicitly requested by user

### When Starting a Session
1. Check this file first (AGENTS.md) for defaults
2. Verify working directory: `Alexandria/scripts`
3. Check current status: `python collection_manifest.py list`
4. **Speak English** - more token-efficient

### When Adding New Features
1. Update this file with new defaults/conventions
2. Update relevant guide in `docs/guides/`
3. Update `scripts/README.md` if adding new scripts

### When User Asks "What's Been Done?"
1. Check [TODO.md](TODO.md) for recently completed work
2. Check `collection_manifest.py show <collection>` for ingestion status
3. Check [README.md](README.md) for current system status

### When User Asks "How Do I...?"
1. Check `docs/guides/QUICK_REFERENCE.md` first
2. Check relevant guide in `docs/guides/`
3. Check `scripts/README.md` for script details

---

## Commit Message Convention

Follow Conventional Commits format (defined in CLAUDE.md):

```
type(scope): subject

Types: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert
Scopes: adr, xpo, db, security, ui (or context-appropriate scope)

Examples:
feat(ingest): add manifest auto-logging to batch_ingest.py
docs(guides): reorganize documentation into docs/guides/
fix(qdrant): update deprecated search API to query_points
```

---

## Streamlit GUI

**Launch:** `streamlit run alexandria_app.py` (runs on http://localhost:8501)

**Main Features:**
- **Calibre Library Browser** - Browse and filter entire Calibre library with direct ingestion
- **Ingestion Interface** - Domain selection, automatic chunking optimization, collection management
- **Query Interface** - RAG-powered Q&A with OpenRouter LLM integration
- **Collection Management** - View ingested books with filtering, sorting, and CSV export

**Architecture:**
- GUI is a thin presentation layer (calls functions from `scripts/`)
- All business logic lives in Python modules
- Session state management for interactive features
- Purple gradient theme with professional layout

**For detailed GUI features, see [README.md](README.md#key-features)**

---

## Current Work & TODO

For current sprint tasks, priorities, and work items, see **[TODO.md](TODO.md)**.

AGENTS.md contains stable reference documentation (paths, defaults, conventions).
TODO.md contains dynamic workflow (current tasks, blockers, backlog).

---

## Documentation Reference

**For detailed information:**
- **Common commands and workflows:** [scripts/README.md](scripts/README.md)
- **Logging and manifest system:** [logs/README.md](logs/README.md)
- **Quick reference guide:** [docs/guides/QUICK_REFERENCE.md](docs/guides/QUICK_REFERENCE.md)
- **Current tasks and issues:** [TODO.md](TODO.md)
- **Project overview and features:** [README.md](README.md)

---

**Last Updated:** 2026-01-23
