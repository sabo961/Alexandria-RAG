# Alexandria Changelog

**Purpose:** Archive of completed work for reference and project history.

For active work items, see [TODO.md](TODO.md).

---

## 2026-01-23 (Late Evening)

### Qdrant Health Check on Startup
**Duration:** <30 minutes
**Lines of Code:** ~40 LOC added
**Goal:** Production readiness - verify Qdrant availability on GUI startup

**Deliverables:**
- ✅ Created `check_qdrant_health(host, port, timeout=5)` function
- ✅ Sidebar status indicator (green: connected, red: error with message)
- ✅ Main page warning banner if Qdrant offline
- ✅ Session state tracking: `st.session_state.qdrant_healthy`

**Files Modified:**
- `alexandria_app.py` (lines 352-382, 387-393, 409-417)

**Impact:**
- Users immediately see if Qdrant is unreachable
- No cryptic ConnectionError messages during operations
- Critical for NAS deployment (network reliability)

---

### Philosophical Chunking Integration
**Duration:** <2 hours
**Lines of Code:** ~30 LOC modified
**Goal:** Integrate argument-based pre-chunking into ingestion pipeline

**Deliverables:**
- ✅ Integrated `argument_prechunk` into `scripts/ingest_books.py`
- ✅ Automatic activation via `domains.json` (philosophy domain)
- ✅ Modified `create_chunks_from_sections()` to pre-chunk philosophical texts
- ✅ Tested with "Sun and Steel" by Yukio Mishima (39 chunks, 600-800 tokens each)
- ✅ Verified retrieval preserves conceptual oppositions in single chunk

**Files Modified:**
- `scripts/ingest_books.py` (lines 32-33, 377-447)

**Test Results:**
- Ingestion: ✅ 39 chunks with argument-based pre-chunking
- Retrieval: ✅ Conceptual oppositions preserved (words ↔ body)
- Quality: ✅ Complete philosophical arguments maintained
- Performance: ✅ No slowdown (<3 seconds for full ingestion)

---

### GUI Polish + Manifest Bug Fix
**Duration:** <1 day
**Lines of Code:** ~50 LOC modified
**Goal:** Fix manifest tracking bug, clean up GUI redundancies

**Deliverables:**
- ✅ **Critical Bug Fix:** `CollectionManifest()` now uses `collection_name` parameter (was saving to global manifest)
- ✅ Removed Statistics tab (duplicate of Ingested Books)
- ✅ Removed Quick Stats sidebar panel (required restart to update)
- ✅ Moved OpenRouter configuration to sidebar
- ✅ Added Temperature control slider (0.0-2.0, default 0.7)

**Files Modified:**
- `alexandria_app.py` (lines 686, 398, 367-465, 1370-1425)
- `scripts/rag_query.py` (added `temperature` parameter)

**Bugs Fixed:**
- ❌→✅ Calibre ingestion showed success but didn't update manifest
- ❌→✅ Query tab cluttered with configuration

---

## 2026-01-22 (Evening)

### Calibre Integration + GUI Enhancements
**Duration:** 1 day
**Lines of Code:** ~800 LOC
**Goal:** Direct Calibre DB integration, new GUI tabs, manifest enhancements

**Deliverables:**

**1. Calibre Database Module (`scripts/calibre_db.py`)**
- ✅ Created 515-line SQLite interface to Calibre `metadata.db`
- ✅ `CalibreBook` dataclass with full metadata (language, tags, series, ISBN, rating)
- ✅ `CalibreDB.get_all_books()` - queries 9,000+ books in <2 seconds
- ✅ `CalibreDB.search_books()` - filters by author, title, language, tags, series, format
- ✅ CLI interface for testing queries

**2. GUI Tab 0: 📚 Calibre Library Browser**
- ✅ Loads 9,000+ books from Calibre database
- ✅ Filters: Author, Title, Language, Format
- ✅ Sort options: Title, Author, Date Added
- ✅ DataFrame with format icons (📕 EPUB, 📄 PDF, 📱 MOBI)

**3. GUI Tab 1: 📖 Ingested Books Viewer**
- ✅ Collection selector
- ✅ Filters: Author, Title, Language, Domain, Format
- ✅ Sort options: Ingested date, Title, Author, Chunks, Size
- ✅ CSV export button

**4. Manifest Enhancements**
- ✅ Added `file_type` field (auto-detects EPUB/PDF/TXT/MD)
- ✅ Added `language` field (Calibre DB lookup with fallback)
- ✅ Backfilled existing `alexandria_manifest.json`

**Files Modified:**
- NEW: `scripts/calibre_db.py` (515 lines)
- NEW: `.streamlit/config.toml` (27 lines)
- MODIFIED: `alexandria_app.py` (added Tab 0, Tab 1, fixed Tab 4)
- MODIFIED: `scripts/collection_manifest.py` (path resolution, new fields)
- MODIFIED: `scripts/batch_ingest.py` (Calibre DB integration)

**Bugs Fixed:**
- ❌→✅ SQL error: "DISTINCT aggregates must have exactly one argument"
- ❌→✅ Ingested Books tab showing "Collection has no ingested books yet"

---

## 2026-01-21

### Query Tab Refactoring
- ✅ Eliminated 160+ lines of duplicated RAG logic in GUI
- ✅ Query tab now calls `perform_rag_query()` from `rag_query.py`
- ✅ Added missing `RAGResult` attributes
- ✅ Single source of truth for RAG logic

---

### Configurable Fetch Multiplier
- ✅ Added `fetch_multiplier` parameter (1-10, default 3)
- ✅ CLI argument: `--fetch-multiplier`
- ✅ GUI: Number input in Advanced Settings
- ✅ Controls quality vs speed trade-off

---

### Philosophical Chunking Module
- ✅ Created `scripts/philosophical_chunking.py`
- ✅ Argument-based chunking for philosophical texts
- ✅ Author-specific opposition pairs (Mishima, Nietzsche, Cioran)
- ✅ CLI testing interface
- ✅ **Integration:** Completed 2026-01-23 (see above)

---

### Collection-Specific Logging
- ✅ Separate manifest per collection: `logs/{collection_name}_manifest.json`
- ✅ Separate progress per collection: `batch_ingest_progress_{collection_name}.json`
- ✅ Auto-reset on collection deletion via `verify_collection_exists()`

---

## 2026-01-21

### Automatic File Management + CSV Export
**Duration:** 1 day
**Goal:** Production workflow improvements - automatic file organization and human-readable tracking

**Deliverables:**
- ✅ Automatic file movement: `ingest/` → `ingested/` after successful processing
- ✅ CSV manifest export for human-readable tracking (open in Excel/LibreOffice)
- ✅ Visual status checking: empty `ingest/` folder = all books processed
- ✅ Resume functionality: `--resume` flag skips already processed books
- ✅ Archive preservation: original files kept in `ingested/` folder

**Files Modified:**
- `scripts/batch_ingest.py` (auto-move functionality)
- `scripts/collection_manifest.py` (CSV export)
- `logs/collection_manifest.csv` (auto-generated)
- `ingested/README.md` (folder documentation)

**Impact:**
- No more "Was this book ingested?" confusion - check folders
- Easy audit via CSV (sort by date, domain, size)
- Avoid accidental re-processing

---

### Query Tab Refactoring
- ✅ Eliminated 160+ lines of duplicated RAG logic in GUI
- ✅ Query tab now calls `perform_rag_query()` from `rag_query.py`
- ✅ Added missing `RAGResult` attributes
- ✅ Single source of truth for RAG logic

---

### Configurable Fetch Multiplier
- ✅ Added `fetch_multiplier` parameter (1-10, default 3)
- ✅ CLI argument: `--fetch-multiplier`
- ✅ GUI: Number input in Advanced Settings
- ✅ Controls quality vs speed trade-off

---

### Philosophical Chunking Module
- ✅ Created `scripts/philosophical_chunking.py`
- ✅ Argument-based chunking for philosophical texts
- ✅ Author-specific opposition pairs (Mishima, Nietzsche, Cioran)
- ✅ CLI testing interface
- ✅ **Integration:** Completed 2026-01-23 (see above)

---

### Collection-Specific Logging
- ✅ Separate manifest per collection: `logs/{collection_name}_manifest.json`
- ✅ Separate progress per collection: `batch_ingest_progress_{collection_name}.json`
- ✅ Auto-reset on collection deletion via `verify_collection_exists()`

---

## 2026-01-22 (Early Morning)

### GUI Cleanup
- ✅ Removed debug caption section for cleaner interface
- ✅ Added compact vertical spacing CSS
- ✅ Combined success message with file movement into single colored block
- ✅ Proper Markdown line breaks for multi-line messages

---

**Archive Format:** Date, Story name, Delivered features, Files modified
**Last Updated:** 2026-01-25
**Status:** Completed work archive for BMad workflow integration
