# Alexandria Development Guide

**Generated:** 2026-01-30
**Project:** Alexandria RAG System
**For:** Developers setting up and working with Alexandria codebase

---

## Prerequisites

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| **Python** | 3.14+ | Primary language |
| **uv** | Latest | Python package manager |
| **Git** | Latest | Version control |
| **Claude Code** | Latest | MCP Client (primary interface) |

### External Systems

| System | Access | Purpose |
|--------|--------|---------|
| **Qdrant Server** | 192.168.0.151:6333 | Vector database |
| **Calibre Library** | G:\My Drive\alexandria | Book metadata |
| **OpenRouter API** | API key (optional) | LLM calls for RAG answers |

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
- FastMCP (MCP Server framework)
- Qdrant client (vector DB)
- sentence-transformers (embeddings)
- PyTorch (ML framework)
- EbookLib, PyMuPDF (book parsing)
- BeautifulSoup4, lxml (HTML parsing)
- NumPy, scikit-learn (semantic analysis)
- pytest, black, flake8 (dev tools)

### 4. Configure MCP Server

Edit `.mcp.json` in your Claude Code configuration:

```json
{
  "mcpServers": {
    "alexandria": {
      "command": "uv",
      "args": ["run", "--directory", "C:/path/to/Alexandria", "python", "scripts/mcp_server.py"],
      "env": {
        "QDRANT_HOST": "192.168.0.151",
        "QDRANT_PORT": "6333",
        "CALIBRE_LIBRARY_PATH": "G:\\My Drive\\alexandria"
      }
    }
  }
}
```

**Note:** Restart Claude Code after configuration changes.

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

## Using Alexandria

### MCP Server (Primary Interface)

After configuring `.mcp.json`, Alexandria tools are available in Claude Code:

**Query Tools:**
- `alexandria_query` - Semantic search with context modes
- `alexandria_search` - Search Calibre by metadata
- `alexandria_book` - Get book details by ID
- `alexandria_stats` - Collection statistics

**Ingest Tools:**
- `alexandria_ingest` - Ingest single book from Calibre
- `alexandria_batch_ingest` - Ingest multiple books
- `alexandria_ingest_file` - Ingest local file

**Example Usage:**
```
User: What does Silverston say about shipment patterns?
Claude: [calls alexandria_query("shipment pattern", context_mode="contextual")]

User: Ingest all Nietzsche books
Claude: [calls alexandria_batch_ingest(author="Nietzsche", limit=10)]
```

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
python scripts/ingest_books.py --file path/to/book.epub \
    --collection alexandria \
    --host 192.168.0.151 \
    --port 6333
```

**Arguments:**
- `--file` - Path to .epub or .pdf file
- `--collection` - Qdrant collection name
- `--hierarchical` - Enable hierarchical chunking (default: True)
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

### Modify Chunking Parameters

1. Edit `scripts/config.py` for default values
2. Or pass `--threshold`, `--min-chunk-size`, `--max-chunk-size` to CLI
3. Test with sample books to verify quality

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

### CLI Debug Mode

```bash
cd scripts
python rag_query.py "test query" --limit 1
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

```bash
# Use batch_ingest.py
python scripts/batch_ingest.py \
    --directory ingest/ \
    --collection alexandria \
    --resume  # Skip already processed files
```

### Progress Tracking

MCP Server includes progress tracking for long operations:
```python
# Progress is reported via MCP notifications
# Claude Code displays progress in real-time
```

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

### MCP Server Not Responding

**Cause:** Configuration or connection issue

**Fix:**
1. Check `.mcp.json` configuration
2. Restart Claude Code
3. Verify Qdrant connection: `python scripts/qdrant_utils.py --list`

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
- **[Project Context](../../project-context.md)** - AI agent rules

### Guides

- **[Quick Reference](../how-to/common-workflows.md)** - Command cheat sheet
- **[Logging Guide](../how-to/track-ingestion.md)** - Logging patterns

### Research

- **[docs/research/](../research/)** - Background research documents

---

## Getting Help

### Internal Resources

1. Check existing documentation (this guide, ADRs, README)
2. Review code comments and docstrings
3. Check CHANGELOG.md for recent changes
4. Consult TODO.md for known issues

### External Resources

- **MCP Protocol:** https://modelcontextprotocol.io
- **Qdrant Docs:** https://qdrant.tech/documentation
- **sentence-transformers:** https://www.sbert.net

---

**Last Updated:** 2026-01-30
**Updated for:** MCP-first architecture
