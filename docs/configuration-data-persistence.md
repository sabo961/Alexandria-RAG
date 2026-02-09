# Configuration & Data Persistence

**Generated:** 2026-02-09
**System:** Alexandria RAG System
**Focus:** Configuration management, environment variables, SQLite persistence, and logging

---

## Overview

Alexandria uses a **hybrid persistence strategy**:
1. **Environment variables** → Runtime configuration (.env file)
2. **SQLite database** → Ingestion tracking and manifest (shared NAS)
3. **Qdrant vector DB** → Primary data store (embeddings + payloads)
4. **File system** → Calibre library structure (books on NAS)

---

## Configuration Files

### 1. .env File

**Location:** Project root (`Alexandria/.env`)
**Purpose:** Environment-specific configuration (gitignored for security)
**Loader:** `scripts/config.py`

**Structure:**
```bash
# Qdrant Vector Database
QDRANT_HOST=192.168.0.151
QDRANT_PORT=6333
QDRANT_COLLECTION=alexandria

# Calibre Library (NAS path - use forward slashes on Windows)
CALIBRE_LIBRARY_PATH=//Sinovac/docker/calibre/alexandria
CALIBRE_WEB_URL=https://alexandria.jedai.space

# CWA Auto-Ingest Folder (NAS path)
CWA_INGEST_PATH=//Sinovac/docker/autocalibreweb/ingest

# Local File Ingestion (default browse directory)
LOCAL_INGEST_PATH=C:\Users\Sabo\Downloads

# Embedding Model Configuration
# Available: minilm (384-dim), bge-large (1024-dim), bge-m3 (1024-dim, multilingual)
DEFAULT_EMBEDDING_MODEL=bge-m3
EMBEDDING_DEVICE=auto  # auto, cuda, cpu

# OpenRouter API (optional - only needed for CLI --answer testing)
# OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

### 2. config.py

**Location:** `scripts/config.py`
**Purpose:** Central configuration loader with fallback defaults

**Key Features:**
- Loads .env file automatically
- Provides fallback defaults for all settings
- Validates required configuration
- Exposes helper functions (`get_qdrant_url()`, `print_config()`)

**Configuration Priority:**
1. Environment variables (highest)
2. .env file values
3. Generic fallback defaults (lowest)

**Example Usage:**
```python
from config import QDRANT_HOST, QDRANT_PORT, CALIBRE_LIBRARY_PATH

# Use in code
client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
```

**Validation:**
- Warns if critical paths missing (CALIBRE_LIBRARY_PATH, CWA_INGEST_PATH)
- Checks for .env file existence
- Silenced during --help invocations

---

## Embedding Model Registry

**Location:** `scripts/config.py` → `EMBEDDING_MODELS` dict

**Purpose:** Multi-model support for embeddings

**Structure:**
```python
EMBEDDING_MODELS = {
    "minilm": {
        "name": "all-MiniLM-L6-v2",
        "dim": 384
    },
    "bge-large": {
        "name": "BAAI/bge-large-en-v1.5",
        "dim": 1024
    },
    "bge-m3": {
        "name": "BAAI/bge-m3",
        "dim": 1024  # Multilingual (100+ languages)
    }
}
```

**Usage:**
```python
from config import EMBEDDING_MODELS, DEFAULT_EMBEDDING_MODEL

model_config = EMBEDDING_MODELS[DEFAULT_EMBEDDING_MODEL]
model_name = model_config["name"]  # "BAAI/bge-m3"
dimension = model_config["dim"]    # 1024
```

**Current Default:** `bge-m3` (multilingual, 1024-dim)

---

## SQLite Database (alexandria.db)

### Location & Strategy

**Path:** `\\Sinovac\docker\calibre\alexandria\.qdrant\alexandria.db` (NAS)
**Fallback:** `logs/alexandria.db` (local if NAS not available)
**Configuration:** `ALEXANDRIA_DB` environment variable

**Purpose:** Shared tracking database for multi-machine ingestion coordination

**Why SQLite on NAS:**
- ✅ Shared visibility across Windows + BUCO machines
- ✅ Simple schema (no server required)
- ✅ Persistent tracking even if Qdrant is reset
- ⚠️ Known issue: Concurrent write conflicts (see Migration Plan below)

### Schema: books Table

**Purpose:** Track ingested books per collection (manifest)

**DDL:**
```sql
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    collection TEXT NOT NULL,
    book_title TEXT NOT NULL,
    author TEXT DEFAULT 'Unknown',
    language TEXT DEFAULT 'unknown',
    source TEXT DEFAULT 'unknown',         -- calibre, gutenberg, archive
    source_id TEXT DEFAULT '',             -- External ID (e.g., Calibre book_id)
    file_path TEXT DEFAULT '',
    file_name TEXT DEFAULT '',
    file_type TEXT DEFAULT '',             -- EPUB, PDF, TXT, etc.
    chunks_count INTEGER DEFAULT 0,
    file_size_mb REAL DEFAULT 0.0,
    ingested_at TEXT NOT NULL             -- ISO 8601 timestamp
);

CREATE INDEX IF NOT EXISTS idx_books_collection ON books(collection);
CREATE INDEX IF NOT EXISTS idx_books_title ON books(collection, book_title);
```

**Sample Row:**
```
id: 1
collection: alexandria
book_title: "Thinking, Fast and Slow"
author: "Daniel Kahneman"
language: "eng"
source: "calibre"
source_id: "42"
file_path: "G:/My Drive/alexandria/Daniel Kahneman/Thinking, Fast and Slow (42)/Thinking, Fast and Slow - Daniel Kahneman.epub"
file_name: "Thinking, Fast and Slow - Daniel Kahneman.epub"
file_type: "EPUB"
chunks_count: 202
file_size_mb: 1.5
ingested_at: "2026-02-08T15:30:00"
```

### CollectionManifest API

**Module:** `scripts/collection_manifest.py`

**Class:** `CollectionManifest`

**Methods:**
```python
# Add book to manifest (called after successful ingestion)
manifest.add_book(
    collection_name="alexandria",
    book_path="/path/to/book.epub",
    book_title="Thinking, Fast and Slow",
    author="Daniel Kahneman",
    chunks_count=202,
    file_size_mb=1.5,
    file_type="EPUB",
    language="eng",
    source="calibre",
    source_id="42"
)

# Get all books for a collection
books = manifest.get_books("alexandria")

# Get summary statistics
summary = manifest.get_summary("alexandria")
# Returns: {"book_count": 150, "total_chunks": 30400, "total_size_mb": 225.5}

# Sync manifest with actual Qdrant collection (repair)
manifest.sync_with_qdrant("alexandria")

# List all collections
manifest.list_collections()

# Remove book from manifest
manifest.remove_book("alexandria", "Book Title")
```

**CLI Usage:**
```bash
# List all collections
python collection_manifest.py list

# Show specific collection
python collection_manifest.py show alexandria

# Sync manifest with Qdrant (repair discrepancies)
python collection_manifest.py sync alexandria

# Remove book from manifest
python collection_manifest.py remove alexandria --book "Book Title"
```

### Duplicate Prevention

**Strategy:** Check before adding to manifest

**Lookup Order:**
1. If `source` + `source_id` provided → Check by source identity
2. Otherwise → Check by `book_title` exact match

**Code:**
```python
# Check if already ingested
existing = conn.execute(
    'SELECT id FROM books WHERE collection=? AND source=? AND source_id=?',
    (collection_name, source, str(source_id))
).fetchone()

if existing:
    # Skip ingestion (book already tracked)
    return
```

---

## Multi-Machine Coordination

### Current Setup

**Machines:**
- **Windows** (development machine) → Reads/writes `\\Sinovac\...\alexandria.db`
- **BUCO** (GPU server) → Reads/writes same DB via SMB mount

**Coordination Strategy:**
1. Check manifest before ingestion
2. If book exists → Skip (already ingested)
3. If new → Ingest and add to manifest atomically

**Known Issue:** Concurrent writes can cause SQLite lock timeouts (WAL mode + network file locking = unreliable)

### Proposed Migration: Qdrant-Based Event Logging

**Document:** `docs/development/ideas/qdrant-event-logging.md`

**Summary:** Replace SQLite with Qdrant collection for event logging

**Benefits:**
- ✅ Multi-user safe (Qdrant handles concurrent writes natively)
- ✅ Global visibility (query from any machine without NAS mount)
- ✅ No corruption risk (no network file locking issues)
- ✅ Unified storage (embeddings + events in same system)

**Implementation Plan:**
- Create `alexandria_events` Qdrant collection (vector-less, payload-only)
- Log events: `ingest_start`, `ingest_complete`, `ingest_error`
- Migrate from SQLite calls to Qdrant logger API

**Status:** Proposed (not yet implemented as of 2026-02-09)

---

## Configuration Validation

### Startup Checks

**Location:** `scripts/config.py` (lines 114-128)

**Checks:**
```python
_MISSING = []
if not QDRANT_HOST or QDRANT_HOST == 'localhost':
    pass  # localhost is valid for local dev
if not CALIBRE_LIBRARY_PATH:
    _MISSING.append('CALIBRE_LIBRARY_PATH')
if not CWA_INGEST_PATH:
    _MISSING.append('CWA_INGEST_PATH')

if _MISSING:
    if not ENV_FILE.exists():
        print(f"[WARN] No .env file found: {ENV_FILE}")
        print(f"       Run: cp .env.example .env")
    else:
        print(f"[WARN] Missing config: {', '.join(_MISSING)}")
```

**Behavior:**
- Warnings printed to stderr (not exceptions)
- Silenced during `--help` invocations
- Allows partial configuration for development

### Runtime Checks

**Qdrant Connection:**
```python
from qdrant_utils import check_qdrant_connection

is_connected, error_msg = check_qdrant_connection(QDRANT_HOST, QDRANT_PORT)
if not is_connected:
    logger.error(f"Cannot connect to Qdrant: {error_msg}")
    sys.exit(1)
```

**Calibre Library:**
```python
from calibre_db import CalibreDB

try:
    db = CalibreDB(CALIBRE_LIBRARY_PATH)
    stats = db.get_stats()
except FileNotFoundError:
    logger.error(f"Calibre library not found: {CALIBRE_LIBRARY_PATH}")
    sys.exit(1)
```

---

## Logging Configuration

### Application Logging

**Standard Setup:**
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
```

**MCP Server Logging:**
```python
# scripts/mcp_server.py
logging.basicConfig(
    level=logging.WARNING,  # Minimized for MCP stdio
    format='%(asctime)s - %(levelname)s - %(message)s'
)
```

**Log Levels by Component:**
- **MCP Server:** WARNING (reduce stdio noise)
- **Ingestion Scripts:** INFO (progress tracking)
- **Query Scripts:** INFO (result display)
- **Batch Scripts:** INFO (batch progress)

### Progress Bars

**Library:** tqdm
**Configuration:** `TQDM_DISABLE=1` (globally disabled)
**Alternative:** Manual progress tracking via logging

**Example:**
```python
logger.info(f"Processing book {i+1}/{total}: {title}")
logger.info(f"  Extracting text... ({file_size:.1f} MB)")
logger.info(f"  Chunking... (threshold={threshold})")
logger.info(f"  Generating embeddings... ({model_id})")
logger.info(f"  Uploading {len(chunks)} chunks to Qdrant...")
logger.info(f"✓ Completed in {duration:.1f}s")
```

---

## File System Structure

### Calibre Library Layout

**Root:** `\\Sinovac\docker\calibre\alexandria\` (NAS)

**Structure:**
```
alexandria/
├── Author Name 1/
│   ├── Book Title 1 (42)/         # (42) = Calibre book_id
│   │   ├── Book Title 1.epub
│   │   ├── cover.jpg
│   │   └── metadata.opf
│   └── Book Title 2 (43)/
│       └── Book Title 2.pdf
├── Author Name 2/
│   └── ...
└── .qdrant/                       # Alexandria metadata
    └── alexandria.db              # Shared SQLite manifest
```

**Book Identification:**
- Folder name includes `(book_id)` → Unique identifier
- `source_id` in manifest = Calibre `book_id`
- File path constructed from author + title + book_id

### Project File Structure

**Configuration:**
```
Alexandria/
├── .env                          # Environment config (gitignored)
├── .env.example                  # Template for .env
├── scripts/
│   ├── config.py                 # Configuration loader
│   └── collection_manifest.py    # SQLite manifest manager
└── logs/
    ├── alexandria.db             # Fallback local manifest
    ├── *.log                     # Application logs (gitignored)
    └── README.md                 # Logs documentation
```

---

## Configuration Best Practices

### 1. Use .env for Secrets

**Do:**
```bash
# .env (gitignored)
OPENROUTER_API_KEY=sk-or-v1-abc123...
QDRANT_HOST=192.168.0.151
```

**Don't:**
```python
# Hardcoded in code (BAD!)
API_KEY = "sk-or-v1-abc123..."
```

### 2. Provide Fallback Defaults

**Example:**
```python
QDRANT_HOST = os.environ.get('QDRANT_HOST', 'localhost')
QDRANT_PORT = int(os.environ.get('QDRANT_PORT', '6333'))
```

### 3. Validate Critical Paths

**Example:**
```python
if not CALIBRE_LIBRARY_PATH:
    logger.warning("CALIBRE_LIBRARY_PATH not set in .env")
    logger.warning("Some features (Calibre ingestion) will not work")
```

### 4. Use Forward Slashes on Windows

**Why:** Python's `Path()` handles conversion, avoids backslash escaping

**Do:**
```bash
CALIBRE_LIBRARY_PATH=//Sinovac/docker/calibre/alexandria
```

**Don't:**
```bash
CALIBRE_LIBRARY_PATH=\\Sinovac\\docker\\calibre\\alexandria  # Escaping hell
```

---

## Debugging Configuration

### Print Current Configuration

**CLI:**
```bash
python scripts/config.py
```

**Output:**
```
Alexandria Configuration
========================================
ENV_FILE:             C:\...\Alexandria\.env (exists)
QDRANT_HOST:          192.168.0.151
QDRANT_PORT:          6333
QDRANT_COLLECTION:    alexandria
CALIBRE_LIBRARY_PATH: //Sinovac/docker/calibre/alexandria
CALIBRE_WEB_URL:      https://alexandria.jedai.space
CWA_INGEST_PATH:      //Sinovac/docker/autocalibreweb/ingest
LOCAL_INGEST_PATH:    C:\Users\Sabo\Downloads
EMBEDDING_MODELS:     ['minilm', 'bge-large', 'bge-m3']
DEFAULT_MODEL:        bge-m3
EMBEDDING_DEVICE:     auto
ALEXANDRIA_DB:        \\Sinovac\docker\calibre\alexandria\.qdrant\alexandria.db
INGEST_VERSION:       2.0
OPENROUTER_API_KEY:   ***xyz (last 4 chars)
========================================
```

### Check Manifest Database

**CLI:**
```bash
# List all collections in manifest
python scripts/collection_manifest.py list

# Show specific collection
python scripts/collection_manifest.py show alexandria

# Check database file directly
sqlite3 "\\Sinovac\docker\calibre\alexandria\.qdrant\alexandria.db" "SELECT COUNT(*) FROM books;"
```

### Test Qdrant Connection

**Python:**
```python
from qdrant_utils import check_qdrant_connection
from config import QDRANT_HOST, QDRANT_PORT

connected, error = check_qdrant_connection(QDRANT_HOST, QDRANT_PORT)
print(f"Connected: {connected}")
if not connected:
    print(f"Error: {error}")
```

---

## Environment Variables Reference

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| **QDRANT_HOST** | string | localhost | Qdrant server hostname/IP |
| **QDRANT_PORT** | int | 6333 | Qdrant server port |
| **QDRANT_COLLECTION** | string | alexandria | Default collection name |
| **CALIBRE_LIBRARY_PATH** | path | (required) | Path to Calibre library root |
| **CALIBRE_WEB_URL** | URL | (optional) | Calibre-Web instance URL |
| **CWA_INGEST_PATH** | path | (required) | Auto-ingest folder path |
| **LOCAL_INGEST_PATH** | path | ~/Downloads | Default local file browse path |
| **DEFAULT_EMBEDDING_MODEL** | string | bge-m3 | Model key (minilm, bge-large, bge-m3) |
| **EMBEDDING_DEVICE** | string | auto | Device (auto, cuda, cpu) |
| **ALEXANDRIA_DB** | path | (auto) | SQLite manifest database path |
| **OPENROUTER_API_KEY** | string | (optional) | OpenRouter API key for testing |

---

## Migration Notes

### From Old Configuration

**Pre-2026-01:** Configurations were hardcoded in scripts

**Migration Steps:**
1. Create `.env` file from `.env.example`
2. Set all required paths (CALIBRE_LIBRARY_PATH, CWA_INGEST_PATH)
3. Update scripts to use `from config import ...` instead of hardcoded values

### From SQLite to Qdrant Logging (Planned)

**Current:** SQLite manifest (`alexandria.db`)
**Future:** Qdrant events collection (`alexandria_events`)

**Migration Path:**
1. Implement `qdrant_logger.py` module
2. Update ingestion scripts to log to both (parallel mode)
3. Verify consistency
4. Switch to Qdrant-only logging
5. Archive SQLite database

**Reference:** `docs/development/ideas/qdrant-event-logging.md`

---

## Summary

**Configuration Stack:**
1. **.env** → Environment-specific settings (git ignored)
2. **config.py** → Central loader with fallback defaults
3. **EMBEDDING_MODELS** → Multi-model registry (minilm, bge-large, bge-m3)
4. **alexandria.db** → Shared SQLite manifest (NAS)
5. **Qdrant** → Primary vector storage

**Key Locations:**
- Config file: `Alexandria/.env`
- Config loader: `scripts/config.py`
- Manifest DB: `\\Sinovac\docker\calibre\alexandria\.qdrant\alexandria.db`
- Manifest API: `scripts/collection_manifest.py`

**Best Practices:**
- Use .env for all environment-specific config
- Validate critical paths at startup
- Use forward slashes for Windows paths
- Provide fallback defaults where sensible
- Log configuration on startup (debug mode)
