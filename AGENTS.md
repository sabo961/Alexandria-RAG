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

### When to Use What
- **Production ingestion:** `batch_ingest.py` (logs automatically)
- **Check what's ingested:** `collection_manifest.py show <collection>`
- **Query books (CLI):** `python rag_query.py "your question" --limit 5`
- **Query books (Python):** `from rag_query import perform_rag_query`
- **Query books (GUI):** Streamlit Query tab (calls `rag_query.py` logic)
- **Admin tasks:** `qdrant_utils.py` (stats, search, copy, delete)
- **Testing:** `experiment_chunking.py`

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

### Collection-Specific Logging (NEW - 2026-01-21)
Each collection now has **separate log files**:

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

### Check What's Ingested
```bash
# Quick view
python collection_manifest.py show alexandria

# List all collections
python collection_manifest.py list

# Export manifest
python collection_manifest.py export alexandria --output ../logs/backup.json
```

### What Gets Logged
- File path (absolute)
- Book title, author, domain
- Number of chunks created
- File size (MB)
- Ingestion timestamp

---

## Current Status

### Check Status Commands
```bash
# What's been ingested?
python collection_manifest.py list
python collection_manifest.py show <collection>

# What's pending ingestion?
ls ../ingest/  # Books waiting to be processed

# What's been completed?
ls ../ingested/  # Successfully ingested books (moved from ingest/)
```

### Status Files (Collection-Specific)
- **Manifest JSON:** `logs/{collection_name}_manifest.json` - What's in Qdrant
- **Manifest CSV:** `logs/{collection_name}_manifest.csv` - Human-readable format
- **Progress JSON:** `scripts/batch_ingest_progress_{collection_name}.json` - Batch ingestion tracker

**Legacy files (backward compatibility):**
- `logs/collection_manifest.json` - Old global manifest (deprecated)
- `scripts/batch_ingest_progress.json` - Old global progress (deprecated)

---

## VS Code Configuration

### Debug Configurations
Available in `.vscode/launch.json`:
- Debug: Ingest Single Book
- Debug: Batch Ingest
- Debug: RAG Query
- Debug: Experiment Chunking
- Debug: Qdrant Utils (Stats/Search)

### Usage
Press **F5** → Select configuration → Start debugging

### Terminal Default
Default working directory: `scripts/`

---

## Common Commands

### Most Used
```bash
# Check what's ingested
python collection_manifest.py show alexandria

# Query books
python rag_query.py "your question" --limit 5

# Ingest new books (production)
python batch_ingest.py --directory ../ingest --domain technical --collection alexandria --resume

# Check collection stats
python qdrant_utils.py stats alexandria
```

### Troubleshooting
```bash
# Test Qdrant connection
python qdrant_utils.py list

# Reinstall dependencies
pip install -r ../requirements.txt

# Verify Python version
python --version  # Should be 3.14
```

---

## Documentation Structure

```
Alexandria/
├── README.md                           # Main project overview
├── AGENTS.md                           # This file (AI agent config)
├── SETUP_COMPLETE.md                   # Original setup notes
├── docs/
│   ├── guides/
│   │   ├── QUICK_REFERENCE.md          # Command cheat sheet
│   │   ├── LOGGING_GUIDE.md            # Tracking system guide
│   │   ├── OPEN_WEBUI_CONFIG.md        # Open WebUI integration
│   │   └── PROFESSIONAL_SETUP_COMPLETE.md  # Complete production guide
│   ├── alexandria-qdrant-project-proposal.md
│   └── missing-classics-analysis.md
├── logs/
│   ├── README.md                       # Logging documentation
│   └── collection_manifest.json        # Master manifest (auto-generated)
└── scripts/
    └── README.md                       # Script usage documentation
```

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

## Known Issues & Limitations

### CRITICAL - Blocks Production

**NONE** - All blocking issues resolved! ✅

### ANNOYING - UX Issues

1. **Domain Switching Bug (Streamlit)**
   - Location: `alexandria_app.py:248-258`
   - Issue: Session state parameters don't reset when changing domain dropdown
   - Expected: technical (1500-2000-200) → psychology (1000-1500-150)
   - Actual: Values persist at user-modified settings
   - `st.rerun()` doesn't force widget value reset

### NOT URGENT

2. **MOBI Support**
   - Not yet implemented
   - Workaround: Convert to EPUB using Calibre

3. **Open WebUI Integration**
   - Configuration documented but not actively used
   - Focus is on Python CLI + Streamlit GUI

4. **Image Handling**
   - Currently ignored (text-only extraction)
   - Future: OCR or multimodal embeddings (CLIP)

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
1. Read `collection_manifest.py show <collection>`
2. Check `SETUP_COMPLETE.md` for historical context
3. Check `batch_ingest_progress.json` for recent activity

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

## Project Phases

### Phase 1: Proof of Concept (Current)
- ✅ Basic ingestion pipeline: EPUB/HTML/MD, DOCX, PDF (born-digital)
- ✅ Domain-specific chunking
- ✅ Qdrant upload with embeddings
- ✅ RAG query tool
- ✅ Batch processing with resume
- ✅ Manifest tracking system
- ⏳ Test with 10 representative books

### Phase 2: Optimization (Next)
- Compare chunking strategies (A/B testing)
- Manual retrieval quality evaluation
- Optimize based on experiments
- Scale to 50-100 books

### Phase 3: Production (Future)
- Full library ingestion (9,383 books)
- Performance optimization
- Citation formatting
- Advanced features (concept graph, timeline search)

---

---

## Streamlit GUI (NEW - 2026-01-21)

### Overview
Professional web-based control panel for Alexandria RAG system.

**Launch:** `streamlit run alexandria_app.py` (runs on http://localhost:8501)

### Features Implemented

#### ✅ Tab 1: Library Management
- Book inventory generation (`generate_book_inventory.py`)
- File type analysis (`count_file_types.py`)
- Search books by author/title
- Results: 9,174 books in 40,636 files

#### ✅ Tab 2: Ingestion (Partial)
- **Book Selection:**
  - Shows books in `ingest/` folder
  - Individual checkboxes per book
  - Bulk controls: Select All, Deselect All, EPUB Only
  - File info: format icon, name, size in MB

- **Domain Selection:**
  - technical / psychology / philosophy / history / literature
  - Auto-loads domain-specific chunking defaults

- **Advanced Settings Expander:**
  - Min Tokens (500-3000, step 100)
  - Max Tokens (500-3000, step 100)
  - Overlap (0-500, step 50)
  - Embedding Model dropdown (all-MiniLM-L6-v2, all-mpnet-base-v2, multi-qa-MiniLM-L6-cos-v1)
  - Batch Upload Size (10-500, step 10)
  - Reset to Defaults button
  - Real-time parameter display (📊 info box)

- **Embedding Model Lock:**
  - Checks if collection has data (`points_count > 0`)
  - If YES: dropdown disabled with 🔒 icon + warning message
  - If NO: dropdown enabled with warning about lock after first ingestion
  - Prevents model change after data exists (different vector dimensions)

- **Start Ingestion Button:**
  - Validates: at least 1 book selected
  - Displays: all ingestion parameters
  - Shows: command to run manually (placeholder)
  - TODO: Implement actual subprocess call

#### ⏸️ Tab 3: Query (Implemented)
- TODO: enter details

#### ⏸️ Tab 4: Statistics (Partial)
- Shows manifest data if available
- Collection overview: books, chunks, size
- TODO: Real-time Qdrant stats

### GUI Architecture

**Styling:**
- Purple gradient theme (`#667eea` → `#764ba2`)
- Greek title with fancy Unicode: "𝔸𝕝𝕖𝕩𝕒𝕟𝕕𝕣𝕚𝕒 𝕠𝕗 𝕋𝕖𝕞𝕖𝕟𝕠𝕤"
- Professional layout with columns and expanders
- Icons for file types (📕 EPUB, ? HTML, 📝 MD, 📄 PDF, ? DOCX)

**Session State Management:**
- `selected_books` - checkbox states
- `last_domain` - track domain changes
- `min_tokens`, `max_tokens`, `overlap_tokens` - chunking params
- `embedding_model`, `batch_size` - ingestion config

**Known Bug:**
- Domain switching doesn't reset widget values (see Known Issues #3)

---

## Current Work & TODO

For current sprint tasks, priorities, and work items, see **[TODO.md](TODO.md)**.

AGENTS.md contains stable reference documentation (paths, defaults, conventions).
TODO.md contains dynamic workflow (current tasks, blockers, backlog).

---

## Recent Changes (2026-01-22 02:15)

### ✅ Query Tab Refactoring (2026-01-22)
- **COMPLETED**: Eliminated 160+ lines of duplicated RAG logic in GUI
- Query tab now calls `perform_rag_query()` from `rag_query.py` (lines 894-948)
- Added missing `RAGResult` attributes: `initial_count`, `error`, `sources` property
- GUI properly displays search info, filters, and error handling
- Single source of truth for RAG logic (usable by CLI, GUI, and AI agents)

### ✅ Configurable Fetch Multiplier (2026-01-22)
- Added `fetch_multiplier` parameter to `search_qdrant()` and `perform_rag_query()`
- Default: 3 (good balance of quality vs speed)
- CLI: `--fetch-multiplier` argument (1-10)
- GUI: Number input in Advanced Settings (1-10)
- Educational use: Can increase to 5-10 for better quality
- Production agents: Can decrease to 2 for faster responses
- Controls how many extra results to fetch for filtering/reranking

### ✅ Philosophical Chunking Module (2026-01-22)
- **CREATED**: `scripts/philosophical_chunking.py`
- Implements argument-based chunking for philosophical texts
- Preserves complete conceptual oppositions (both poles + authorial stance)
- Author-specific opposition pairs:
  - Mishima: words↔body, intellect↔muscle, ideal↔death, civilization↔nature
  - Nietzsche: slave↔master, morality↔transvaluation, reason↔life
  - Cioran: hope↔despair, life↔death
  - Default: mind↔body, ideal↔real, theory↔practice
- Activated via `use_argument_chunking` flag in `domains.json`
- Philosophy domain: `use_argument_chunking: true`
- CLI testing interface: `python philosophical_chunking.py <file> --author <name>`
- **PENDING**: Integration into `ingest_books.py`

### ✅ Language Preference
- **ENGLISH ONLY** for all AI interactions (saves ~30% tokens)
- Added to Agent Instructions section

### ✅ Collection-Specific Logging
- Each collection now has separate manifest: `logs/{collection_name}_manifest.json`
- Each collection has separate progress: `batch_ingest_progress_{collection_name}.json`
- Auto-reset behavior: manifest cleared when collection deleted from Qdrant
- Implemented via `verify_collection_exists()` in `CollectionManifest`

### ✅ Ingestion System Fixes
- Fixed chunking logic (PDFs merge pages: 98 chunks vs 525)
- Added UUID point IDs (prevents conflicts)
- Added `generate_embeddings()` and `get_token_count()` helpers
- GUI ingestion now fully functional

### ✅ GUI Improvements (2026-01-22)
- Removed debug caption section for cleaner interface
- Added compact vertical spacing CSS (0.25rem margins, 1.4 line-height)
- Combined success message with file movement into single colored block
- Proper Markdown line breaks (`  \n`) for multi-line messages within success blocks
- Query tab Advanced Settings: similarity threshold, fetch_multiplier, reranking controls

### ✅ Documentation Restructure (2026-01-22)
- **SPLIT**: Extracted TODO section from AGENTS.md into separate [TODO.md](TODO.md) file
- AGENTS.md = stable reference (paths, defaults, conventions, architecture)
- TODO.md = dynamic workflow (current sprint, priorities, backlog)
- Clearer separation of concerns for AI agents and developers

---

**Last Updated:** 2026-01-22
**For Current Tasks:** See [TODO.md](TODO.md)
