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
        'overlap': 180
    },
    'history': {
        'min': 1500,
        'max': 2000,
        'overlap': 200
    }
}
```

### File Formats Supported
```python
SUPPORTED_FORMATS = ['epub', 'pdf', 'txt', 'md']
# Note: MOBI not yet implemented (convert to EPUB with Calibre)
```

---

## Production Scripts

### Primary Tools (Use These)
```bash
batch_ingest.py          # Production ingestion (auto-logs to manifest)
rag_query.py             # Query tool (LLM-ready markdown output)
collection_manifest.py   # Track what's been ingested
qdrant_utils.py          # Collection management
```

### Development Tools
```bash
ingest_books.py          # Single book ingestion (testing only)
experiment_chunking.py   # A/B testing chunk strategies
```

### When to Use What
- **Production ingestion:** `batch_ingest.py` (logs automatically)
- **Check what's ingested:** `collection_manifest.py show <collection>`
- **Query books:** `rag_query.py "your question" --limit 5`
- **Admin tasks:** `qdrant_utils.py` (stats, search, copy, delete)
- **Testing:** `ingest_books.py` or `experiment_chunking.py`

---

## Logging & Tracking

### Automatic Logging
`batch_ingest.py` automatically logs to:
- **Manifest:** `logs/collection_manifest.json` (master record)
- **Progress:** `scripts/batch_ingest_progress.json` (resume support)

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

### Status Files
- **Manifest:** `logs/collection_manifest.json` - What's in Qdrant
- **Manifest CSV:** `logs/collection_manifest.csv` - Human-readable format
- **Progress:** `scripts/batch_ingest_progress.json` - Batch ingestion tracker

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

1. **batch_ingest.py Import Errors**
   - `generate_embeddings` function missing from `ingest_books.py`
   - Blocks actual ingestion execution
   - Priority: Fix before any ingestion

2. **GUI Ingestion Not Implemented**
   - `alexandria_app.py:384-410` - Start Ingestion button is placeholder
   - Shows parameters but doesn't execute
   - Need: subprocess call to batch_ingest.py

### ANNOYING - UX Issues

3. **Domain Switching Bug (Streamlit)**
   - Location: `alexandria_app.py:248-258`
   - Issue: Session state parameters don't reset when changing domain dropdown
   - Expected: technical (1500-2000-200) → psychology (1000-1500-150)
   - Actual: Values persist at user-modified settings
   - `st.rerun()` doesn't force widget value reset

### NOT URGENT

4. **MOBI Support**
   - Not yet implemented
   - Workaround: Convert to EPUB using Calibre

5. **Open WebUI Integration**
   - Configuration documented but not actively used
   - Focus is on Python CLI + Streamlit GUI

6. **PDF Ingestion Quality**
   - Not yet tested (Silverston Vol 1 & 2 are PDFs)
   - May need tuning compared to EPUB

7. **Image Handling**
   - Currently ignored (text-only extraction)
   - Future: OCR or multimodal embeddings (CLIP)

---

## Agent Instructions

### When Starting a Session
1. Check this file first (AGENTS.md) for defaults
2. Verify working directory: `Alexandria/scripts`
3. Check current status: `python collection_manifest.py list`

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
- ✅ Basic ingestion pipeline (EPUB, PDF, TXT)
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
  - technical / psychology / philosophy / history
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

#### ⏸️ Tab 3: Query (Not Implemented)
- Placeholder for semantic search interface

#### ⏸️ Tab 4: Statistics (Partial)
- Shows manifest data if available
- Collection overview: books, chunks, size
- TODO: Real-time Qdrant stats

### GUI Architecture

**Styling:**
- Purple gradient theme (`#667eea` → `#764ba2`)
- Greek title with fancy Unicode: "𝔸𝕝𝕖𝕩𝕒𝕟𝕕𝕣𝕚𝕒 𝕠𝕗 𝕋𝕖𝕞𝕖𝕟𝕠𝕤"
- Professional layout with columns and expanders
- Icons for file types (📕 EPUB, 📄 PDF, 📝 TXT/MD)

**Session State Management:**
- `selected_books` - checkbox states
- `last_domain` - track domain changes
- `min_tokens`, `max_tokens`, `overlap_tokens` - chunking params
- `embedding_model`, `batch_size` - ingestion config

**Known Bug:**
- Domain switching doesn't reset widget values (see Known Issues #3)

---

## TODO List (Priority Order)

### 🔴 HIGH PRIORITY - Blockers for Production

1. **Fix batch_ingest.py import errors**
   - File: `scripts/batch_ingest.py`
   - Issue: `from ingest_books import generate_embeddings` fails
   - Action: Check `ingest_books.py`, implement missing function or fix import path

2. **Implement actual ingestion in GUI**
   - File: `alexandria_app.py:384-410`
   - Current: Shows parameters only (placeholder)
   - Action: Add subprocess call to `batch_ingest.py` with:
     - Selected book paths from `st.session_state.selected_books`
     - All ingestion parameters (domain, collection, tokens, model, batch_size)
     - Real-time output streaming to GUI

3. **Test full ingestion workflow**
   - Action: End-to-end test with 2-3 sample books
   - Verify: EPUB parsing → chunking → embedding → Qdrant upload
   - Check: Collection creation, metadata, vector storage, manifest update

### 🟡 MEDIUM PRIORITY - UX Improvements

4. **Fix domain switching parameter reset**
   - File: `alexandria_app.py:248-258`
   - Current: `del st.session_state[key]` + `st.rerun()` doesn't work
   - Alternative approaches:
     - Use widget callbacks with `on_change`
     - Force remount with unique keys based on domain
     - Separate user modifications from domain defaults
   - Test: Switch technical→psychology→technical, verify reset each time

5. **Add real-time progress tracking**
   - Monitor: `scripts/batch_ingest_progress.json`
   - Display: Progress bar, current book, chunks processed, ETA
   - Update method: Streamlit auto-refresh or polling
   - UI: Show live log output from subprocess

6. **Implement Resume functionality**
   - File: `alexandria_app.py:412-414`
   - Use: `batch_ingest.py --resume` flag
   - Display: Previously processed books, failed books, restart point
   - Button: Resume from last position

### 🟢 LOW PRIORITY - Nice to Have

7. **Query interface (Tab 3)**
   - File: `alexandria_app.py:452-475`
   - Implement: Text input → embedding → Qdrant search → display results
   - UI Components:
     - Query text area
     - Domain filter dropdown
     - Result limit slider (1-20)
     - Results: book title, author, relevant chunk, similarity score
     - Pagination for multiple results

8. **Test embedding model lock**
   - Verify: Dropdown disabled when `points_count > 0`
   - Test case: Ingest 1 book, reload GUI, check if lock appears
   - Edge case: Empty collection should show unlocked dropdown

---

**Last Updated:** 2026-01-21 22:00
**Next Review:** After fixing batch_ingest.py imports
**Next Milestone:** First successful GUI-initiated ingestion
