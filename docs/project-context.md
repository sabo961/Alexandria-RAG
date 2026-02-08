---
project_name: 'Alexandria'
user_name: 'Sabo'
date: '2026-01-30'
sections_completed: ['technology_stack', 'python_rules', 'streamlit_rules', 'testing_rules', 'code_quality', 'workflow_rules', 'critical_rules']
status: 'complete'
rule_count: 45
optimized_for_llm: true
---

# Project Context for AI Agents

_This file contains critical rules and patterns that AI agents must follow when implementing code in this project. Focus on unobvious details that agents might otherwise miss._

---

## Technology Stack & Versions

### Core Technologies
- **Python 3.14** - Primary language
- **Streamlit >=1.29.0** - Web GUI framework (binds to 0.0.0.0:8501)
- **Qdrant >=1.7.1** - Vector database client (connects to 192.168.0.151:6333)
- **sentence-transformers >=2.3.1** - Embedding model library
- **PyTorch >=2.0.0** - Required by sentence-transformers

### Key Dependencies
- **EbookLib 0.18** - EPUB parsing (exact version)
- **PyMuPDF >=1.24.0** - PDF parsing
- **BeautifulSoup 4.12.2** - HTML parsing for EPUB content
- **lxml 4.9.3** - XML parser for BeautifulSoup
- **tqdm 4.66.1** - Progress bars (DISABLED globally via `TQDM_DISABLE=1`)
- **mcp >=1.0.0** - Model Context Protocol SDK for Claude Code integration
- **pytest 7.4.3** - Testing framework
- **pytest-playwright >=0.4.0** - Browser/UI testing
- **black 23.12.1** - Code formatter
- **flake8 7.0.0** - Linter

### MCP Server (Claude Code Integration)
- **Script**: `scripts/mcp_server.py` - FastMCP server with 5 read-only tools
- **Config**: `.mcp.json` - MCP server configuration for Claude Code
- **Tools**: `alexandria_query`, `alexandria_search`, `alexandria_book`, `alexandria_stats`, `alexandria_domains`
- **Docs**: `docs/reference/mcp-server.md`
- **Transport**: stdio (standard for Claude Code)

### Development Tools (Optional but Useful)
- **Datasette** - Web UI for exploring Calibre SQLite database
  ```bash
  datasette "G:/My Drive/alexandria/metadata.db" --port 8002
  # Open http://localhost:8002 - browse tables, run SQL, export data
  # JSON API: curl "http://localhost:8002/metadata/books.json?_limit=10"
  ```
- **Playwright codegen** - Record browser actions, generate test code
  ```bash
  playwright codegen http://localhost:8501
  ```

### Critical Version Constraints
- **Embedding models**: Multi-model registry (see `config.py:EMBEDDING_MODELS`)
  - `minilm`: all-MiniLM-L6-v2 (384-dim) - legacy, lightweight
  - `bge-large`: BAAI/bge-large-en-v1.5 (1024-dim) - default, GPU-accelerated
  - Model locked per collection - changing requires re-ingestion
- **Qdrant distance metric**: COSINE - hardcoded across ingestion and query scripts
- **tqdm**: Must be disabled globally (`os.environ['TQDM_DISABLE'] = '1'`) to prevent `[Errno 22]` stderr issues in Streamlit

## Critical Implementation Rules

### Python Language-Specific Rules

**Import Conventions:**
- Import order: stdlib → third-party → local modules (PEP 8)
- Use `from pathlib import Path` for all file operations
- Type hints: `from typing import List, Dict, Optional, Tuple`
- Dataclasses: `from dataclasses import dataclass` for structured data (e.g., CalibreBook, QueryResult)

**Logging Pattern (MANDATORY):**
```python
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
```
- NO `print()` statements - use `logger.info/error/warning/debug()`
- Emoji in output: ✅ (success), ❌ (error), ⚠️ (warning), 📚 (info)
- f-strings for log messages: `logger.info(f"✅ Loaded {count} books")`

**File Handling with Pathlib:**
- `.suffix.lower()` for file extension
- `.stem` for filename without extension
- `.exists()` for existence check
- `.mkdir(parents=True, exist_ok=True)` for directory creation
- Windows long paths: Use `normalize_file_path()` from ingest_books.py (handles `\\?\` prefix for paths > 248 chars)

**Docstring Format:**
```python
def function(arg: str) -> Dict:
    """
    Short one-line description.

    Args:
        arg: Description of argument

    Returns:
        Description of return value
    """
```

**Code Style:**
- f-strings preferred: `f"text {var}"` not `.format()` or `%`
- Context managers: Always use `with open()` for file operations
- Shebang: `#!/usr/bin/env python3` on executable scripts

### Streamlit Framework Rules

**Caching Strategy:**
- **Pure functions**: `@st.cache_data` for file reads, JSON parsing, static data
  ```python
  @st.cache_data
  def load_domains() -> Dict:
      """Cached - reads domains.json only once"""
  ```
- **TTL for dynamic data**: `@st.cache_data(ttl=30)` for health checks, API calls
- **Cache invalidation**: Call `.clear()` after updates: `load_gui_settings.clear()`

**Fragment Isolation:**
- **Tab isolation**: Wrap tab logic in `@st.fragment` to prevent full app reruns
  ```python
  @st.fragment
  def render_query_tab():
      """Query tab - interactions don't rerun entire app"""
  ```
- **Fragment placement**: Define functions BEFORE usage (no forward references)
- **Used in**: Query tab, Calibre filters, Ingested Books filters

**Session State Management:**
- **Centralized state**: Use `AppState` dataclass + `get_app_state()` pattern
  ```python
  app_state = get_app_state()
  app_state.calibre_selected_books = set()
  ```
- **Direct access when needed**: `st.session_state["key"]` for non-AppState values

**GUI Architecture (ADR 0003 - CRITICAL):**
- **Thin presentation layer**: GUI ONLY collects input, calls scripts, displays results
- **NO business logic in GUI**: All logic lives in `scripts/` package
- **Pattern**:
  ```python
  # ❌ BAD: Logic in GUI
  embeddings = model.encode(query)  # 100+ lines of logic

  # ✅ GOOD: GUI calls scripts
  from rag_query import perform_rag_query
  result = perform_rag_query(query, collection, limit)
  ```

**Streamlit Quirks:**
- **No sys.stderr**: Causes `[Errno 22]` errors - use `logging` instead
- **Rerun behavior**: Every interaction reruns entire script (use fragments to isolate)

### Testing Rules

**Directory Structure:**
```
Alexandria/
├── scripts/          # Business logic (testable)
├── tests/            # Test files
│   ├── conftest.py   # Root pytest config (path setup for scripts/)
│   ├── test_*.py     # Unit tests (mirror scripts/ structure)
│   └── ui/           # Playwright browser tests
│       ├── conftest.py          # Playwright fixtures (server, browser)
│       └── test_app_startup.py  # Smoke tests for Streamlit GUI
└── alexandria_app.py # GUI (thin layer, tested via Playwright)
```

**File Naming:**
- Test files: `test_<module_name>.py` (e.g., `test_ingest_books.py` for `scripts/ingest_books.py`)
- Test functions: `test_<function_name>_<scenario>` (e.g., `test_extract_text_epub_valid`)

**Testing Focus:**
- **Priority**: Test `scripts/` modules (business logic)
- **UI testing**: Playwright for Streamlit GUI (smoke tests, navigation)
- **External dependencies**: Mock Qdrant, OpenRouter API, file system

**Pytest Configuration:**
- Run all tests: `pytest tests/`
- Run unit tests only: `pytest tests/ --ignore=tests/ui/`
- Run UI tests only: `pytest tests/ui/`
- Coverage: `pytest --cov=scripts tests/`
- Framework: pytest 7.4.3 + pytest-playwright 0.4.0+

**Playwright UI Testing (IMPORTANT):**
```bash
# Install browsers (one-time setup after pip install)
playwright install

# Run UI tests (headless - default)
pytest tests/ui/ -v

# Run with visible browser (debugging)
pytest tests/ui/ -v --headed

# Run with slow motion (demos, watching)
pytest tests/ui/ -v --headed --slowmo=500

# Record video of tests
pytest tests/ui/ --video=on

# Generate test code by recording actions
playwright codegen http://localhost:8501
```

**Playwright Fixtures (tests/ui/conftest.py):**
- `streamlit_server` - Auto-starts Streamlit on port 8501, stops after tests
- `app_page` - Pre-navigated page with Streamlit app loaded
- Server detection: Reuses existing server if already running (dev workflow)

**Mock Pattern for External Services:**
```python
# Mock Qdrant client
from unittest.mock import MagicMock
qdrant_client = MagicMock()

# Mock file system for ingestion tests
from pathlib import Path
test_file = Path("tests/fixtures/sample.epub")
```

**Test Categories:**
- **Unit tests**: Individual functions (e.g., `extract_text()`, `chunk()`)
- **Integration tests**: End-to-end workflows (e.g., ingest EPUB → Qdrant upload)
- **UI smoke tests**: App loads, tabs visible, navigation works (Playwright)
- **Fixture data**: Store sample books in `tests/fixtures/` (small EPUB/PDF for testing)

### Code Quality & Style Rules

**Linting & Formatting:**
- **Black 23.12.1**: Code formatter (default settings, 88 char line length)
- **Flake8 7.0.0**: Linter (default settings)
- **No custom config**: Use Black/Flake8 defaults (no `.flake8` or `pyproject.toml` overrides)

**Naming Conventions:**
- **Classes**: PascalCase (`CalibreBook`, `CollectionManifest`, `UniversalChunker`)
- **Functions**: snake_case (`extract_text`, `perform_rag_query`, `generate_embeddings`)
- **Variables**: snake_case (`book_title`, `embedding_model`, `collection_name`)
- **Constants**: UPPER_SNAKE_CASE (`DOMAIN_CHUNK_SIZES`)

**File Organization:**
- **Flat structure**: All modules in `scripts/` (no subdirectories)
- **File categories**:
  - Production: `ingest_books.py`, `rag_query.py`, `calibre_db.py`, `collection_manifest.py`, `qdrant_utils.py`, `universal_chunking.py`
  - Utilities: `check_*.py`, `fix_*.py`, `count_*.py`
  - Experiments: `experiment_*.py`

**Comment Style:**
- Inline comments: Capitalize first letter, explain "what" code does
- Example: `# Extract text based on file format`
- Keep comments short and focused

**Black Formatting Defaults:**
- Line length: 88 characters
- Double quotes for strings
- Trailing commas in multi-line structures

### Development Workflow Rules

**Git Commit Format (Conventional Commits - MANDATORY):**
```
type(scope): subject

Examples:
✅ feat(calibre): add direct ingestion from library
✅ fix(ui): resolve post-ingestion UI refresh
✅ docs(adr): add GUI architecture decision
✅ debug(ingest): add author tracking through pipeline
```

**Commit Types:**
- `feat` - New feature for user
- `fix` - Bug fix for user
- `docs` - Documentation only (ADRs, README)
- `debug` - Debugging/diagnostic changes
- `refactor` - Code restructuring (no behavior change)
- `perf` - Performance improvement
- `test` - Test changes
- `chore` - Maintenance tasks
- `revert` - Revert previous commit

**Commit Scopes (Optional but Recommended):**
- `calibre` - Calibre integration
- `ui` / `ux` - User interface
- `manifest` - Collection manifest tracking
- `architecture` - Architecture documentation
- `ingest` - Ingestion pipeline
- `diagnostics` - Diagnostic/debug features

**Subject Rules:**
- Imperative mood: "add" not "added"
- Don't capitalize first letter
- No period (.) at end
- Keep under 50 characters

**Branching Strategy:**
- **Main branch**: `master` - stable, production-ready code
- **Small fixes**: Direct commits to master (typos, small bug fixes, documentation)
- **Large refactors**: Create feature branch, then merge to master
  - Branch naming: `refactor/<description>` (e.g., `refactor/streamlit-optimization`)
  - Branch naming: `feat/<description>` (e.g., `feat/mobi-support`)
- **Optional PR process**: Use pull requests for code review on large changes (recommended but not enforced)

**Files to NEVER Commit (.gitignore):**
- **Secrets**: `.streamlit/secrets.toml`, API keys
- **Runtime files**: `batch_ingest_progress.json`, logs
- **Large files**: `ingest/`, `ingested/` directories (books)
- **Generated outputs**: Architecture diagrams, Structurizr cache

**Deployment Configuration:**
- **Streamlit GUI**: Runs on `0.0.0.0:8501` (accessible from network)
- **Qdrant server**: External at `192.168.0.151:6333` (not in repo)
- **Calibre library**: External at `G:\My Drive\alexandria` (not in repo)

### Critical Don't-Miss Rules

**Anti-Patterns to NEVER Do:**

1. **NEVER duplicate business logic in GUI (ADR 0003 violation)**
   - ❌ BAD: Implementing RAG query logic in `alexandria_app.py`
   - ✅ GOOD: Call `perform_rag_query()` from `scripts/rag_query.py`
   - **Why**: Creates divergence, maintenance burden, breaks CLI/API consistency

2. **Embedding model is LOCKED per collection**
   - Multi-model registry: `minilm` (384-dim), `bge-large` (1024-dim)
   - Changing model for existing collection = full re-ingestion required
   - Query MUST use same model as collection's ingestion model
   - Different collections CAN use different models (A/B testing)

3. **NEVER change Qdrant distance metric (hardcoded COSINE)**
   - Distance metric is COSINE across all ingestion and query scripts
   - Changing to EUCLIDEAN or DOT would break existing collections
   - **Fix**: Would require collection recreation

4. **NEVER use `print()` or `sys.stderr` in scripts**
   - ❌ `print("message")` or `sys.stderr.write("error")`
   - ✅ `logger.info("message")` or `logger.error("error")`
   - **Why**: Streamlit causes `[Errno 22]` on stderr access

**Missing Critical Functionality (LOST AFTER REFACTOR):**

5. **Interactive chunking parameter testing GUI - LOST CODE**
   - **Previously existed**: Interactive GUI interface for testing chunking parameters
   - **What it did**: Real-time chunking with different threshold/min/max values, side-by-side comparison, visual feedback
   - **Current state**: ✅ CLI tool exists (`experiment_chunking.py`), ❌ Interactive GUI version: CODE NOT SAVED
   - **Impact**: Lost valuable tool for tuning chunking quality
   - **Action needed**: Recreate interactive chunking experiment interface in Streamlit

**Configuration Issues (NEEDS REFACTORING):**

6. **Universal Semantic Chunking - hardcoded parameters (SHOULD BE CONFIGURABLE)**
   - **Currently hardcoded in code:**
     - Philosophy: `threshold=0.45`, Others: `threshold=0.55`
     - `min_chunk_size=200`, `max_chunk_size=1200`
   - **SHOULD BE**: Exposed in Config/Settings sidebar + Interactive Experiment Tab
   - **Impact**: Can't experiment with chunking parameters without code changes

7. **Calibre library path - REGRESSION after Haiku refactor**
   - **Before**: Configurable through Settings sidebar
   - **After refactor**: Hardcoded `CALIBRE_LIBRARY_PATH = "G:\\My Drive\\alexandria"`
   - **Status**: GUI functionality was overwritten during refactor
   - **Fix needed**: Restore Settings sidebar input for Calibre library path

8. **tqdm progress bars disabled globally (WORKAROUND - needs review)**
   - `os.environ['TQDM_DISABLE'] = '1'` in `ingest_books.py`
   - Reason: "stderr issues in Streamlit"
   - **Note**: May be obsolete workaround, needs architect review

**Immutable System Constraints:**

9. **Qdrant server location: `192.168.0.151:6333`**
   - External server, NOT localhost
   - Collection data persists on server, not in repo
   - **SHOULD BE**: Configurable through Settings sidebar (host + port)

10. **Windows long path handling (>248 characters)**
    - ALWAYS use `normalize_file_path()` before file operations
    - Adds `\\?\` prefix for paths > 248 chars on Windows
    - **Failure mode**: `FileNotFoundError` on deeply nested Calibre paths

**Data Integrity:**

11. **Collection-specific manifests track ingestion**
    - Each collection has its own manifest: `logs/collection_manifest_{name}.json`
    - Manifest MUST be updated after successful ingestion
    - **Don't**: Manually edit manifests or skip manifest updates

12. **Author metadata requires careful handling**
    - Calibre stores authors as `Author1 & Author2 & Author3`
    - Must handle multi-author books correctly during ingestion
    - **Don't**: Split on `&` without understanding Calibre format

**Critical Files (DO NOT DELETE):**

13. **requirements.txt is OFFICIAL Python dependency file**
    - File MUST be named `requirements.txt` (NOT .md)
    - Used by: `pip install -r requirements.txt`
    - Expected by: PyCharm, Docker, GitHub Actions, all Python tooling
    - **Don't**: Rename to .md, delete, or move to docs/
    - **Location:** Project root (same directory as README.md)

---

## Usage Guidelines

**For AI Agents:**

- Read this file before implementing any code
- Follow ALL rules exactly as documented
- When in doubt, prefer the more restrictive option
- Update this file if new patterns emerge

**For Humans:**

- Keep this file lean and focused on agent needs
- Update when technology stack changes
- Review quarterly for outdated rules
- Remove rules that become obvious over time

---

## Epic & Story Management

**Purpose:** Clarify Alexandria's implementation roadmap structure and workflow.

### How Implementation Planning Works

**docs/development/epics.md (Strategic Planning):**
- Epic definitions with user outcomes and requirements mapping
- 8 epics covering entire system vision (Phase 1-4)
- Maps functional/non-functional requirements to epics
- Think: "WHAT are we building and WHY?"

**docs/development/epic-*.md (Tactical Execution):**
- One file per epic with detailed implementation stories
- Each story: User story + Acceptance criteria + Technical tasks
- Tasks marked ✅ DONE or ⏳ PENDING (living documentation)
- Think: "HOW do we build this specific epic?"

**docs/development/ideas/ (Brainstorming):**
- Unfiltered future visions and concepts
- Briefs for features not yet in epics (Phase 3-4+)
- Examples: Librarians, Makers, Temporal Knowledge Layer
- Think: "What MIGHT we build someday?"

**CHANGELOG.md (Completed Work Archive):**
- Historical record of completed sprints/features
- Extracted from epic stories when work is done
- Format: Date, Story name, Deliverables, Files modified
- Think: "What have we ALREADY built?"

### BMad Agent Workflow

When a BMad agent starts work:

1. **Read epics.md** to understand overall vision and requirements
2. **Open relevant epic-*.md** for current work (e.g., epic-0-model-migration.md)
3. **Find next ⏳ PENDING story** in sequence
4. **Implement story** following acceptance criteria and technical tasks
5. **Mark tasks ✅ DONE** as they complete
6. **Update story status** when complete
7. **Move to CHANGELOG.md** when epic or major story completes

### Guidelines for Humans

**When adding new ideas:**
- Create brief in `docs/development/ideas/` for exploration
- If accepted, integrate into existing epic or create new epic
- Don't bypass epic structure - always plan before execution

**When working on existing epics:**
- Update story status (⏳ PENDING → 🔄 IN PROGRESS → ✅ DONE)
- Mark technical tasks as complete with checkboxes
- Stories are living documentation - keep them current

**Structure principles:**
- epics.md = Strategic (WHAT and WHY)
- epic-*.md = Tactical (HOW - detailed stories)
- ideas/ = Exploration (MAYBE - future concepts)
- CHANGELOG.md = Historical (DONE - completed work)

---

**Last Updated:** 2026-01-30
