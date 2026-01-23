# Alexandria TODO List

**Purpose:** Current work items and sprint tasks for active development.
For stable reference documentation (paths, defaults, conventions), see [AGENTS.md](AGENTS.md).

**Last Updated:** 2026-01-23 (Late Evening)
**Last Sprint:** Philosophical Chunking Integration (✅ COMPLETED 2026-01-23)

---

## 🔴 HIGH PRIORITY - Next Sprint

### 1. Manual Chunking Parameters vs Automatic Optimization (Design Decision)

**Status:** ⏸️ ON HOLD - Awaiting real-world usage experience

**Current Implementation:**
- ✅ Automatic optimization via `calculate_optimal_chunk_params()` (lines 265-282 in `alexandria_app.py`)
- ✅ Domain-specific defaults from `DOMAIN_CHUNK_SIZES` in `ingest_books.py`
- ✅ No manual parameter widgets in GUI (automatic-only approach)

**Original Issue (now moot):**
- Domain switching with manual parameters would not reset to new domain defaults
- This bug no longer exists because manual parameters were removed

**Open Questions:**
- Should we add manual override controls back?
- Is automatic optimization sufficient for all use cases?
- Do advanced users need fine-tuning capability?

**Design Options:**

**Option A: Keep Current (Automatic Only)**
- ✅ Simpler UX, fewer decisions for users
- ✅ Consistent, predictable results
- ❌ No control for edge cases
- ❌ Can't experiment with different strategies

**Option B: Add Manual Override (Advanced Settings)**
- ✅ Power users can fine-tune
- ✅ Experimentation possible
- ❌ More complex UX
- ❌ Need to solve parameter reset bug if implemented

**Decision Criteria (pending real usage):**
- How often does automatic optimization produce suboptimal results?
- Do users request manual controls?
- Are there specific book types where auto fails?
- Do we need A/B testing capability in GUI?

**Next Steps:**
- [ ] Use system with automatic optimization for 2-4 weeks
- [ ] Track cases where manual control would help
- [ ] Collect feedback on chunk quality
- [ ] Make informed decision based on actual usage patterns

**If implementing manual controls later:**
- [ ] Use widget callbacks with `on_change` parameter
- [ ] Force remount with unique keys: `key=f"max_tokens_{domain}"`
- [ ] Add "Reset to Defaults" button
- [ ] Store user overrides separately from domain defaults

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

### Philosophical Chunking Integration (SPRINT)
**Completed:** 2026-01-23 (Late Evening)
**Duration:** <2 hours
**Lines of Code:** ~30 LOC modified
**Sprint Goals:** Integrate argument-based pre-chunking into ingestion pipeline, test with philosophical texts

#### Deliverables:

**1. Integration into Ingestion Pipeline**
- ✅ **Added imports** to `scripts/ingest_books.py`
  - Imported `argument_prechunk` and `should_use_argument_chunking` from `philosophical_chunking.py`
- ✅ **Modified `create_chunks_from_sections()` function** (lines 377-447)
  - Added domain check: `use_argument_chunking = should_use_argument_chunking(domain)`
  - For both merge_sections paths (PDFs and EPUBs):
    - Pre-chunk text into argument blocks if domain requires it
    - Apply token-based chunking to each pre-chunked block
  - Logging: "📚 Using argument-based pre-chunking for domain: philosophy"
- ✅ **Automatic activation** via `domains.json`
  - Philosophy domain has `use_argument_chunking: true`
  - Technical, psychology, history, literature remain `false`

**2. Testing & Validation**
- ✅ **Test book:** "Sun and Steel" by Yukio Mishima
- ✅ **Collection:** alexandria_test
- ✅ **Domain:** philosophy (triggers argument chunking)
- ✅ **Results:**
  - Created 39 chunks (vs 39 without argument chunking, but better quality)
  - Average chunk size: 600-800 tokens (optimal for philosophical arguments)
  - Log confirmed: "Using argument-based pre-chunking for domain: philosophy"

**3. Retrieval Validation**
- ✅ **Query:** "Find passage where Mishima criticizes language and words versus physical action and the body"
- ✅ **Expected behavior:** Retrieve chunk containing BOTH sides of conceptual opposition
- ✅ **Result:** SUCCESS
  - Top chunk score: 0.44
  - Chunk contains WORDS side: ✅ (words, language, writing, wordless)
  - Chunk contains BODY side: ✅ (body, flesh, physical)
  - Opposition preserved: ✅
  - Full argument context maintained in single chunk

**4. Author-Specific Opposition Detection**
- ✅ **Mishima patterns active:**
  - words/language ↔ body/muscle/action
  - intellect/mind ↔ strength/physical/flesh
  - ideal/beauty ↔ death/violence
  - civilization ↔ nature/primitive
- ✅ **Author auto-detection:** Works via `detect_author_style()` function
  - Checks author metadata: "Mishima, Yukio" → uses Mishima opposition pairs
  - Fallback: keyword detection in first 5000 chars

#### Files Modified:
- `scripts/ingest_books.py` (lines 32-33, 377-447)
  - Added philosophical_chunking imports
  - Integrated argument pre-chunking into `create_chunks_from_sections()`
  - Dual-path implementation (merged sections + individual sections)

#### Test Results:
- **Ingestion:** ✅ 39 chunks created with argument-based pre-chunking
- **Retrieval:** ✅ Conceptual oppositions preserved in same chunk
- **Quality:** ✅ Complete philosophical arguments maintained
- **Performance:** ✅ No significant slowdown (<3 seconds for full ingestion)

#### Next Steps:
- Test with other philosophical authors (Nietzsche, Cioran)
- Validate with longer philosophical works
- Consider enabling for literature domain (Mishima novels have philosophical themes)

---

### GUI Polish + Manifest Bug Fix (SPRINT)
**Completed:** 2026-01-23 (Evening)
**Duration:** <1 day
**Lines of Code:** ~50 LOC modified
**Sprint Goals:** Fix manifest tracking bug, clean up GUI redundancies, improve UX

#### Deliverables:

**1. Critical Bug Fix: Manifest Not Updating**
- ✅ **Root cause identified:** `CollectionManifest()` initialized without `collection_name` parameter
  - Was saving to global manifest instead of collection-specific file
  - Statistics tab expects `{collection}_manifest.json` format
  - Result: Books ingested to Qdrant but manifest not updating
- ✅ **Fix:** Changed `manifest = CollectionManifest()` → `manifest = CollectionManifest(collection_name=calibre_collection)`
- ✅ **Location:** `alexandria_app.py:686`
- ✅ **Verified:** Ingestion now properly updates `alexandria_manifest.json` with new books

**2. GUI Simplification**
- ✅ **Removed Statistics tab** - Was duplicate of "Ingested Books" tab (which has filters)
- ✅ **Removed Quick Stats sidebar panel** - Required restart to update, not useful
- ✅ **Moved OpenRouter Configuration to sidebar**
  - Previously in Query tab, taking up space
  - Now in sidebar with other configuration
  - Query tab is cleaner and focused

**3. Advanced Settings Enhancements**
- ✅ **Added Temperature control** in Query tab Advanced Settings
  - Slider: 0.0-2.0, default 0.7
  - Controls LLM creativity vs focus
  - Passed through to `generate_answer()` → OpenRouter API
- ✅ **UI improvement:** All query settings in collapsible expander (similarity, fetch multiplier, reranking, temperature)

**4. Tab Reorganization**
- ✅ **Before:** 5 tabs (Calibre Library, Ingested Books, Ingestion, Query, Statistics)
- ✅ **After:** 4 tabs (Statistics removed, Query cleaned up)
- ✅ **Result:** Cleaner interface, less duplication, better UX

#### Files Modified:
- `alexandria_app.py` (lines 686, 398, 367-465, 1370-1425)
  - Fixed manifest initialization with collection_name
  - Removed Statistics tab code (~60 lines)
  - Removed Quick Stats panel (~30 lines)
  - Moved OpenRouter config to sidebar
  - Added Temperature slider in Advanced Settings
- `scripts/rag_query.py`
  - Added `temperature` parameter to `perform_rag_query()`
  - Added `temperature` parameter to `generate_answer()`
  - Passed temperature to OpenRouter API call

#### Bugs Fixed:
- ❌→✅ **Critical:** Calibre direct ingestion showed success but didn't update manifest
- ❌→✅ Quick Stats panel not refreshing without restart
- ❌→✅ Query tab cluttered with configuration that belonged in sidebar

---

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
- ✅ **2026-01-23:** Integration into `ingest_books.py` COMPLETED (see sprint above)

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
- ✅ Manifest bug fix completed - ingestion now properly tracks books
- ✅ GUI cleanup completed - removed redundant tabs/panels
- ✅ Philosophical chunking integration completed - argument-based pre-chunking active for philosophy domain
- ⏸️ Manual vs automatic chunking - on hold pending real-world usage experience
- Next: Quality-focused testing with philosophical books (Nietzsche, Cioran)

**Testing strategy:**
- Test on `alexandria_test` collection first
- Keep `alexandria` collection stable
- Use small batches (5-10 books) for testing

---

**Last Updated:** 2026-01-23 (Late Evening)
**Last Sprint:** Philosophical Chunking Integration (✅ COMPLETED)
**Next Sprint:** Domain Parameter Reset Bug Fix
**Next Milestone:** Quality-focused ingestion with optimized chunking parameters (philosophy + literature domains)
