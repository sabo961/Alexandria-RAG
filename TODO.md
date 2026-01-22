# Alexandria TODO List

**Purpose:** Current work items and sprint tasks for active development.
For stable reference documentation (paths, defaults, conventions), see [AGENTS.md](AGENTS.md).

**Last Updated:** 2026-01-22 (Evening)
**Last Sprint:** Calibre Integration + GUI Enhancements (✅ COMPLETED 2026-01-22)

---

## 🔴 HIGH PRIORITY - Next Sprint

### 1. Integrate Philosophical Chunking

**Status:** Module exists (`philosophical_chunking.py`), needs integration into ingestion pipeline

**Files to modify:**
- [ ] `scripts/ingest_books.py`
  - [ ] Import: `from philosophical_chunking import argument_prechunk, should_use_argument_chunking`
  - [ ] In `create_chunks_from_sections()`:
    - [ ] Check domain flag: `if should_use_argument_chunking(domain):`
    - [ ] Pre-chunk: `text_blocks = argument_prechunk(section['text'], author=author)`
    - [ ] Else: `text_blocks = [section['text']]`
    - [ ] Loop through blocks and apply token chunking

**Test plan:**
- [ ] Re-ingest "Sun and Steel" with `domain=philosophy`
- [ ] Query: "Find passage where Mishima criticizes language vs physical action"
- [ ] Verify: Conceptual opposition preserved (words↔body in same chunk)

---

### 2. Domain Switching Parameter Reset (Bug Fix)

**Issue:** When switching domains in GUI, chunking parameters don't reset to new defaults

**Location:** `alexandria_app.py:248-258`

**Current behavior:**
- User modifies parameters in "technical" domain
- User switches to "psychology" domain
- Parameters stay at user-modified values (not psychology defaults)

**Attempted fix:** `del st.session_state[key]` + `st.rerun()` doesn't work

**Alternative approaches:**
- [ ] Use widget callbacks with `on_change` parameter
- [ ] Force remount with unique keys based on domain: `key=f"max_tokens_{domain}"`
- [ ] Separate user modifications from domain defaults in session state
- [ ] Add explicit "Reset to Defaults" button per domain change

**Test case:**
1. Switch technical→psychology→technical
2. Verify parameters reset each time
3. User modifications should only persist within same domain

---

## 🟡 MEDIUM PRIORITY - After Philosophical Chunking

### 3. Real-Time Progress Tracking

**Goal:** Show live progress during batch ingestion

**Implementation:**
- [ ] Monitor: `scripts/batch_ingest_progress_{collection}.json`
- [ ] Display: Progress bar, current book, chunks processed, ETA
- [ ] Update method: Streamlit auto-refresh (st.experimental_rerun) or polling
- [ ] UI: Stream subprocess stdout to GUI (real-time logs)

---

### 4. Resume Functionality in GUI

**Goal:** Resume interrupted batch ingestion from GUI

**Location:** `alexandria_app.py:412-414` (Ingestion tab)

**Features:**
- [ ] Check if progress file exists: `batch_ingest_progress_{collection}.json`
- [ ] Display:
  - [ ] Previously processed books (✅)
  - [ ] Failed books (❌)
  - [ ] Restart point (⏸️)
- [ ] Button: "Resume from Last Position"
- [ ] Pass `--resume` flag to `batch_ingest.py` subprocess

---

## 🟢 LOW PRIORITY - Nice to Have (Backlog)

### 5. Advanced Query Features (Tab 3)

**Goal:** Enhance query interface beyond basic search

**Features:**
- [ ] Multi-query mode (ask multiple questions in sequence)
- [ ] Query history (session-based, dropdown to re-run)
- [ ] Export results to markdown/PDF
- [ ] Highlight matching text in results
- [ ] Pagination for large result sets (> 10 chunks)
- [ ] "Similar passages" button (find more like this chunk)

---

### 6. Collection Management

**Goal:** Admin operations for Qdrant collections

**Features:**
- [ ] Copy collection (duplicate for testing)
- [ ] Merge collections (combine two collections)
- [ ] Delete collection (with confirmation prompt)
- [ ] Collection diff (compare two manifests)
- [ ] Backup/restore collection (export all points to JSON)

**Integration:**
- [ ] Add "⚙️ Admin" tab in GUI
- [ ] Use `qdrant_utils.py` functions
- [ ] Safety prompts for destructive operations

---

## 🔵 BACKLOG - Future Ideas

## 🔵 BACKLOG - Future Ideas

### 7. Calibre Metadata Enhancement

**Goal:** Store more Calibre metadata in Qdrant payloads

**Additional fields:**
- [ ] Series name + index (e.g., "Sea of Fertility #2")
- [ ] Tags (philosophy, existentialism, japanese-literature)
- [ ] Rating (1-5 stars from Calibre)
- [ ] Publisher
- [ ] ISBN
- [ ] Publication date

**Use case:**
- Filter queries by series: "Show all books in Sea of Fertility series"
- Filter by tags: "Find philosophy books with existentialism tag"
- Sort by rating in results

---

### 8. Multi-Format Preference

**Goal:** When multiple formats available, prefer specific format

**Example:**
- Book has: EPUB, PDF, MOBI
- User preference: EPUB > PDF > MOBI
- Ingestion automatically picks EPUB

**Implementation:**
- [ ] Add `format_preference` setting in GUI
- [ ] Filter files by preference before ingestion
- [ ] Warn if preferred format not available

---

### 9. Duplicate Detection

**Goal:** Avoid ingesting same book twice (different formats/editions)

**Detection strategies:**
- [ ] Exact title + author match
- [ ] Fuzzy title matching (Levenshtein distance)
- [ ] ISBN lookup (if available)
- [ ] Content hash (first 1000 chars of text)

**UI:**
- [ ] Show warning: "Similar book already ingested"
- [ ] Option to ingest anyway (different edition)
- [ ] Option to replace existing

---

### 10. MOBI Support

**Goal:** Support Kindle MOBI format

**Implementation:**
- [ ] Use `mobi` library or `Calibre ebook-convert`
- [ ] Convert MOBI → EPUB in-memory
- [ ] Process as EPUB

**Blocked by:**
- Testing MOBI files
- Calibre CLI dependency

---

## ✅ COMPLETED RECENTLY

### Calibre Integration + GUI Enhancements (SPRINT)
**Completed:** 2026-01-22 (Evening)
**Duration:** 1 day
**Lines of Code:** ~800 LOC (calibre_db.py + GUI tabs + manifest updates)
**Sprint Goals:** Direct Calibre DB integration, two new GUI tabs, manifest enhancements

#### Deliverables:

**1. Calibre Database Module (`scripts/calibre_db.py`)**
- ✅ Created 515-line SQLite interface to Calibre `metadata.db`
- ✅ `CalibreBook` dataclass with full metadata (language, tags, series, ISBN, rating)
- ✅ `CalibreDB.get_all_books()` - queries 9,000+ books in <2 seconds
- ✅ `CalibreDB.search_books()` - filters by author, title, language, tags, series, format
- ✅ `CalibreDB.match_file_to_book()` - fuzzy matching for language lookup
- ✅ `CalibreDB.get_stats()` - library statistics (books, authors, formats, languages)
- ✅ CLI interface for testing queries
- ✅ Fixed SQL `GROUP_CONCAT` DISTINCT syntax error

**2. GUI Tab 0: 📚 Calibre Library Browser**
- ✅ Loads 9,000+ books from Calibre database
- ✅ Filters: Author search, Title search, Language (multiselect), Format (EPUB/PDF/MOBI)
- ✅ Sort options: Title (A-Z), Author (A-Z), Date Added (newest/oldest)
- ✅ Quick stats: Total books, Authors, Languages, Formats
- ✅ DataFrame display with format icons (📕 EPUB, 📄 PDF, 📱 MOBI)
- ✅ Result count: "Showing X of Y books"
- ✅ Session state caching for performance

**3. GUI Tab 1: 📖 Ingested Books Viewer**
- ✅ Collection selector (alexandria, alexandria_test, etc.)
- ✅ Loads from `{collection}_manifest.json` files
- ✅ Filters: Author, Title, Language, Domain, Format
- ✅ Sort options: Ingested date, Title, Author, Chunks, Size
- ✅ Quick stats: Books, Chunks, Total Size, Formats count
- ✅ DataFrame with icons (📕 📄 📝) and language codes
- ✅ CSV export button (downloads manifest)
- ✅ Fixed path resolution for GUI context

**4. GUI Tab 4: 📊 Statistics Enhancements**
- ✅ Updated to load from `{collection}_manifest.json` format
- ✅ Shows all collections with expandable sections
- ✅ Displays first 10 books with icons and language codes
- ✅ Language display: 🏳️ emoji for unknown, ISO codes for known (ENG, JPN, HRV)
- ✅ Fixed manifest file loading logic

**5. Manifest Enhancements**
- ✅ Added `file_type` field to `collection_manifest.py`
  - Auto-detects from file extension (EPUB, PDF, TXT, MD)
  - CSV export includes "File Type" column
- ✅ Added `language` field to manifest tracking
  - Integrates Calibre DB lookup during ingestion
  - Fallback to "unknown" if not found
  - CSV export includes "Language" column
- ✅ Backfilled existing `alexandria_manifest.json` with new fields
- ✅ Fixed relative path issues: `../logs/` → smart detection of logs directory

**6. Infrastructure Improvements**
- ✅ Created `.streamlit/config.toml` for network access (0.0.0.0:8501)
- ✅ Sidebar Quick Stats updated to new manifest format
- ✅ Added `MANIFEST_GLOB_PATTERN` constant to reduce duplication

#### Bugs Fixed:
- ❌→✅ SQL error: "DISTINCT aggregates must have exactly one argument"
- ❌→✅ Ingested Books tab showing "Collection has no ingested books yet" (path resolution)
- ❌→✅ Statistics tab using old `collection_manifest.json` path
- ❌→✅ Sidebar Quick Stats using deprecated manifest format
- ❌→✅ "UNKNOWN" language display → changed to 🏳️ emoji

#### Files Modified:
- NEW: `scripts/calibre_db.py` (515 lines)
- NEW: `.streamlit/config.toml` (27 lines)
- MODIFIED: `alexandria_app.py` (added Tab 0, Tab 1, fixed Tab 4, updated sidebar)
- MODIFIED: `scripts/collection_manifest.py` (path resolution fix, file_type/language fields)
- MODIFIED: `scripts/batch_ingest.py` (Calibre DB lookup integration)
- MODIFIED: `logs/alexandria_manifest.json` (backfilled 12 books with file_type/language)

---

### Query Tab Refactoring
**Completed:** 2026-01-21
- ✅ Eliminated 160+ lines of duplicated RAG logic in GUI
- ✅ Query tab now calls `perform_rag_query()` from `rag_query.py`
- ✅ Added missing `RAGResult` attributes
- ✅ Single source of truth for RAG logic

### Configurable Fetch Multiplier
**Completed:** 2026-01-21
- ✅ Added `fetch_multiplier` parameter (1-10, default 3)
- ✅ CLI argument: `--fetch-multiplier`
- ✅ GUI: Number input in Advanced Settings
- ✅ Controls quality vs speed trade-off

### Philosophical Chunking Module
**Completed:** 2026-01-21
- ✅ Created `scripts/philosophical_chunking.py`
- ✅ Argument-based chunking for philosophical texts
- ✅ Author-specific opposition pairs (Mishima, Nietzsche, Cioran)
- ✅ CLI testing interface
- ⏳ **Pending:** Integration into `ingest_books.py`

### Collection-Specific Logging
**Completed:** 2026-01-21
- ✅ Separate manifest per collection: `logs/{collection_name}_manifest.json`
- ✅ Separate progress per collection: `batch_ingest_progress_{collection_name}.json`
- ✅ Auto-reset on collection deletion via `verify_collection_exists()`

### GUI Cleanup
**Completed:** 2026-01-22 (early morning)
- ✅ Removed debug caption section for cleaner interface
- ✅ Added compact vertical spacing CSS
- ✅ Combined success message with file movement into single colored block
- ✅ Proper Markdown line breaks for multi-line messages

---

## Notes

**Workflow:**
1. Prioritize HIGH tasks first
2. Test incrementally (don't merge untested features)
3. Update this file as tasks are completed
4. Move completed items to COMPLETED RECENTLY section with date
5. Start new chat session for fresh context after major milestones

**Current Focus:**
- Philosophical chunking integration into ingestion pipeline
- Domain parameter reset bug fix
- Re-ingest books with proper language metadata from Calibre

**Testing strategy:**
- Test on `alexandria_test` collection first
- Keep `alexandria` collection stable
- Use small batches (5-10 books) for testing

---

**Last Updated:** 2026-01-22 (Evening)
**Last Sprint:** Calibre Integration (✅ COMPLETED)
**Next Sprint:** Philosophical Chunking Integration + Bug Fixes
**Next Milestone:** Re-ingest Mishima books with Calibre language metadata + philosophical chunking
