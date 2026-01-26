# Alexandria Development Guide

**Generated:** 2026-01-26
**Project:** Alexandria RAG System
**For:** Developers setting up and working with Alexandria codebase

---

## Prerequisites

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| **Python** | 3.14+ | Primary language |
| **pip** | Latest | Package management |
| **Git** | Latest | Version control |
| **Streamlit** | ≥1.29.0 | Web GUI framework |

### External Systems

| System | Access | Purpose |
|--------|--------|---------|
| **Qdrant Server** | 192.168.0.151:6333 | Vector database |
| **Calibre Library** | G:\My Drive\alexandria | Book metadata |
| **OpenRouter API** | API key required | LLM calls (optional) |

---

## Installation

### 1. Clone Repository

```bash
git clone <repository-url> alexandria
cd alexandria
```

### 2. Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Dependencies installed:**
- Streamlit (GUI framework)
- Qdrant client (vector DB)
- sentence-transformers (embeddings)
- PyTorch (ML framework)
- EbookLib, PyMuPDF (book parsing)
- BeautifulSoup4, lxml (HTML parsing)
- NumPy, scikit-learn (semantic analysis)
- pytest, black, flake8 (dev tools - optional)

### 4. Configure Streamlit Secrets

Create `.streamlit/secrets.toml` (gitignored):

```toml
# OpenRouter API (for LLM answer generation)
[openrouter]
api_key = "your-api-key-here"
```

**Note:** LLM features are optional. Query and ingestion work without API keys.

### 5. Verify Qdrant Connection

```bash
python scripts/qdrant_utils.py --list
```

**Expected output:**
```
Connected to Qdrant: 192.168.0.151:6333
Collections:
  - alexandria (42 books, 3847 chunks)
  - alexandria_test (5 books, 412 chunks)
```

**If connection fails:**
- Check network access to 192.168.0.151:6333
- Verify Qdrant server is running

---

## Environment Setup

### Directory Structure (First Run)

Alexandria auto-creates these directories:

```bash
mkdir -p ingest ingested logs
```

| Directory | Purpose |
|-----------|---------|
| `ingest/` | Place books here for ingestion |
| `ingested/` | Auto-moved after successful ingestion |
| `logs/` | Runtime logs and manifests |

### Optional: Calibre Library Path

**Default:** `G:\My Drive\alexandria`

To use a different path:
1. Edit `scripts/calibre_db.py` line 59 (currently hardcoded)
2. Or pass path to CalibreDB constructor

**Future:** GUI setting will be restored (see TODO.md)

---

## Running Alexandria

### GUI Application (Primary Interface)

```bash
streamlit run alexandria_app.py
```

**Binds to:** `0.0.0.0:8501` (accessible from network)

**Access:** http://localhost:8501

**GUI Tabs:**
- 📖 Qdrant collections - View ingested books
- 📚 Calibre - Browse Calibre library, ingest books
- 🔍 Query - Semantic search with optional LLM answers
- ⚙️ Admin - Manage collections, settings

---

## Development Workflow

### Code Style & Formatting

**Black** (code formatter):
```bash
black scripts/ alexandria_app.py
```

**Flake8** (linter):
```bash
flake8 scripts/ alexandria_app.py
```

**Settings:**
- Line length: 88 characters (Black default)
- No custom config files

### Logging Pattern (MANDATORY)

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Use emojis for visual clarity
logger.info(f"✅ Loaded {count} books")
logger.error(f"❌ Failed: {error}")
logger.warning(f"⚠️ Skipping {file}")
```

**Anti-patterns:**
- ❌ `print()` statements
- ❌ `sys.stderr.write()` (breaks Streamlit)

---

## Testing (Recommended - Not Yet Implemented)

### Setup Tests

```bash
# Create test directory
mkdir -p tests

# Run tests
pytest tests/

# With coverage
pytest --cov=scripts tests/
```

### Test Structure

```
tests/
├── test_ingest_books.py         # Ingestion pipeline tests
├── test_rag_query.py             # Query engine tests
├── test_collection_manifest.py   # Manifest tracking tests
├── test_calibre_db.py            # Calibre integration tests
└── fixtures/                     # Sample test data
    ├── sample.epub
    └── sample.pdf
```

### Mocking External Dependencies

```python
from unittest.mock import MagicMock

# Mock Qdrant client
qdrant_client = MagicMock()

# Mock file system
from pathlib import Path
test_file = Path("tests/fixtures/sample.epub")
```

---

## CLI Scripts Usage

All scripts in `scripts/` support CLI execution:

### Ingest Book

```bash
python scripts/ingest_books.py path/to/book.epub \
    --domain philosophy \
    --collection alexandria \
    --host 192.168.0.151 \
    --port 6333
```

**Arguments:**
- `filepath` - Path to .epub or .pdf file
- `--domain` - Domain (philosophy, psychology, history, etc.)
- `--collection` - Qdrant collection name
- `--host`, `--port` - Qdrant server (default: 192.168.0.151:6333)

### Query Collection

```bash
python scripts/rag_query.py "What does Mishima say about words vs body?" \
    --collection alexandria \
    --use-llm \
    --llm-model "anthropic/claude-3-5-sonnet-20241022" \
    --limit 5
```

**Arguments:**
- `query` - Search query
- `--collection` - Qdrant collection name
- `--use-llm` - Generate LLM answer
- `--llm-model` - LLM model to use
- `--limit` - Number of results (default: 5)

### Qdrant Management

```bash
# List collections
python scripts/qdrant_utils.py --list

# Collection stats
python scripts/qdrant_utils.py --stats alexandria

# Copy collection
python scripts/qdrant_utils.py --copy alexandria alexandria_backup

# Delete collection (with artifacts)
python scripts/qdrant_utils.py --delete alexandria --delete-artifacts
```

### Calibre Stats

```bash
python scripts/calibre_db.py
```

**Output:** Library statistics (total books, languages, tags, etc.)

---

## Common Development Tasks

### Add New Book Format Support

1. Edit `scripts/ingest_books.py`
2. Add format to `extract_text()` function
3. Implement parser (similar to EPUB/PDF handling)
4. Test with sample file

### Modify Chunking Strategy

1. Edit `scripts/universal_chunking.py`
2. Adjust thresholds or algorithm in `UniversalChunker`
3. Re-ingest books to test changes
4. Document in ADR if significant change

### Add New Domain

1. Edit domain-specific thresholds in `scripts/universal_chunking.py`
2. Update `project-context.md` if special handling needed
3. Test with sample books from that domain

### Create New Script Module

```python
#!/usr/bin/env python3
"""
Module description
"""

import logging
from pathlib import Path
from typing import List, Dict, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """CLI entry point"""
    logger.info("✅ Starting...")
    # ... logic ...


if __name__ == "__main__":
    main()
```

**Guidelines:**
- Place in `scripts/` package
- Follow logging pattern
- Add CLI entry point
- Document in module docstring

---

## Debugging

### Enable Debug Logging

```python
logging.basicConfig(level=logging.DEBUG, ...)
```

### Streamlit Debug Mode

```bash
streamlit run alexandria_app.py --logger.level=debug
```

### Check Qdrant Connection

```python
from qdrant_client import QdrantClient

client = QdrantClient(host="192.168.0.151", port=6333)
print(client.get_collections())
```

### Inspect Embeddings

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode(["test sentence"])
print(embeddings.shape)  # Should be (1, 384)
```

---

## Performance Optimization

### Batch Ingestion

For ingesting multiple books:

```python
# Use batch_ingest.py
python scripts/batch_ingest.py \
    --input-dir ingest/ \
    --domain philosophy \
    --collection alexandria
```

### Disable Progress Bars (Streamlit)

Already configured via environment variable:
```python
os.environ['TQDM_DISABLE'] = '1'
```

**Reason:** tqdm stderr causes `[Errno 22]` in Streamlit

---

## Git Workflow

### Commit Message Convention (Conventional Commits)

```
type(scope): subject

Examples:
✅ feat(calibre): add direct ingestion from library
✅ fix(ui): resolve post-ingestion UI refresh
✅ docs(adr): add GUI architecture decision
✅ debug(ingest): add author tracking through pipeline
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation only
- `debug` - Debugging/diagnostic changes
- `refactor` - Code restructuring (no behavior change)
- `perf` - Performance improvement
- `test` - Test changes
- `chore` - Maintenance tasks

**Scopes:**
- `calibre`, `ui`, `manifest`, `ingest`, `diagnostics`, etc.

### Branching Strategy

- **Main branch:** `master`
- **Small fixes:** Direct commits to master
- **Large refactors:** Feature branch → merge to master

### What NOT to Commit

See `.gitignore`:
- `.streamlit/secrets.toml` (API keys)
- `ingest/`, `ingested/` (large book files)
- `logs/*.json`, `logs/*.csv` (runtime artifacts)
- `__pycache__/` (bytecode cache)

---

## Troubleshooting

### "FileNotFoundError: Calibre database not found"

**Cause:** Calibre library path incorrect

**Fix:**
```python
# Check path
from pathlib import Path
calibre_path = Path("G:\\My Drive\\alexandria\\metadata.db")
print(calibre_path.exists())
```

### "Connection refused: Qdrant"

**Cause:** Qdrant server not accessible

**Fix:**
1. Verify server is running: `ping 192.168.0.151`
2. Check port: `telnet 192.168.0.151 6333`
3. Update host/port in scripts if needed

### "[Errno 22] Invalid argument" (Streamlit)

**Cause:** Writing to `sys.stderr` in Streamlit

**Fix:** Use `logging` instead of `print()` or stderr

### "Windows long path error"

**Cause:** Path > 248 characters

**Fix:** Use `normalize_file_path()` from `ingest_books.py`:
```python
from scripts.ingest_books import normalize_file_path
path_for_open, display_path, _, _ = normalize_file_path(filepath)
```

---

## Additional Resources

### Documentation

- **[Architecture](../explanation/architecture.md)** - Complete architecture reference
- **[Data Models](../reference/api/data-models.md)** - API reference
- **[Source Tree](../reference/api/source-tree.md)** - Codebase structure
- **[ADRs](../reference/architecture/decisions/README.md)** - Architecture decisions
- **[Project Context](../../_bmad-output/project-context.md)** - AI agent rules

### Guides

- **[Quick Reference](../how-to-guides/common-workflows.md)** - Command cheat sheet
- **[Logging Guide](../how-to-guides/track-ingestion.md)** - Logging patterns
- **[Professional Setup](./professional-setup.md)** - Advanced setup

### Research

- **[docs/research/](../explanation/research/)** - Background research documents

---

## Getting Help

### Internal Resources

1. Check existing documentation (this guide, ADRs, README)
2. Review code comments and docstrings
3. Check CHANGELOG.md for recent changes
4. Consult TODO.md for known issues

### External Resources

- **Streamlit Docs:** https://docs.streamlit.io
- **Qdrant Docs:** https://qdrant.tech/documentation
- **sentence-transformers:** https://www.sbert.net

---

**Last Updated:** 2026-01-26
**Generated by:** document-project workflow
