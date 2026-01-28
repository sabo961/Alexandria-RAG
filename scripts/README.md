# Alexandria Ingestion Scripts

Python skripte za ingestiju knjiga u Qdrant vektorsku bazu.

## Setup

### 1. Install Dependencies

```bash
pip install -r ../requirements.txt
```

### 2. Verify Qdrant is Running

Qdrant mora biti pokrenut na `localhost:6333` (ili specificiraj drugačiji host/port).

```bash
# Test connection
python qdrant_utils.py list
```

## Usage

### Ingest a Single Book

```bash
# EPUB book (technical domain)
python ingest_books.py --file "path/to/silverston.epub" --domain technical

# PDF book (psychology domain)
python ingest_books.py --file "path/to/kahneman.pdf" --domain psychology

# Text file (philosophy domain)
python ingest_books.py --file "path/to/kant.txt" --domain philosophy

# Custom collection
python ingest_books.py --file "book.epub" --domain technical --collection alexandria_test
```

### Manage Collections

```bash
# List all collections
python qdrant_utils.py list

# Get collection statistics
python qdrant_utils.py stats alexandria

# Copy collection (all data)
python qdrant_utils.py copy alexandria_v1 alexandria_v2

# Copy collection (filter by domain)
python qdrant_utils.py copy alexandria alexandria_technical --domain technical

# Delete collection (with confirmation)
python qdrant_utils.py delete alexandria_test

# Create alias (point "alexandria" to "alexandria_v3")
python qdrant_utils.py alias alexandria_v3 alexandria

# Delete specific points
python qdrant_utils.py delete-points alexandria --domain technical --book "The Goal"
```

### Search / Test Retrieval

```bash
# Basic search
python qdrant_utils.py search alexandria "database normalization patterns" --limit 10

# Search with domain filter
python qdrant_utils.py search alexandria "cognitive load" --domain psychology --limit 5
```

## Domain-Specific Chunking Strategies

Ingestion skripta automatski primjenjuje domain-specific chunking:

| Domain | Chunk Size (tokens) | Overlap | Rationale |
|--------|---------------------|---------|-----------|
| **technical** | 1500-2000 | 200 | Technical explanations need full context (diagrams, code, multi-paragraph) |
| **psychology** | 1000-1500 | 150 | Psychological concepts often self-contained (System 1/2, 6 principles) |
| **philosophy** | 1200-1800 | 180 | Philosophical arguments require setup → claim → justification structure |
| **history** | 1500-2000 | 200 | Historical case studies need context (who, what, when, why, outcome) |

## Examples

### Example 1: Ingest Technical Book (Silverston)

```bash
python ingest_books.py \
  --file "../ingest/The Data Model Resource Book Vol 3_ Universal Patterns for Data Modeling - Len Silverston.epub" \
  --domain technical \
  --collection alexandria_test
```

**Note:** Qdrant server is at `192.168.0.151:6333` (configured as default in scripts)

**What happens:**
1. Extracts chapters from EPUB
2. Chunks text into ~1500-2000 token chunks with 200 token overlap
3. Generates embeddings using `all-MiniLM-L6-v2` (384-dim)
4. Uploads to Qdrant collection `alexandria`

### Example 2: Ingest Psychology Book (Kahneman)

```bash
python ingest_books.py \
  --file "C:/Users/goran/Documents/Books/Kahneman - Thinking Fast and Slow.pdf" \
  --domain psychology \
  --collection alexandria
```

**What happens:**
1. Extracts pages from PDF
2. Chunks text into ~1000-1500 token chunks with 150 token overlap
3. Generates embeddings
4. Uploads to Qdrant

### Example 3: Experiment with Different Chunk Sizes

```bash
# Test 1: Small chunks
python ingest_books.py --file "book.epub" --domain technical --collection alexandria_v1_small

# Test 2: Large chunks
python ingest_books.py --file "book.epub" --domain technical --collection alexandria_v2_large

# Test 3: Domain-specific (default)
python ingest_books.py --file "book.epub" --domain technical --collection alexandria_v3_domain

# Compare retrieval quality
python qdrant_utils.py search alexandria_v1_small "database normalization" --limit 5
python qdrant_utils.py search alexandria_v2_large "database normalization" --limit 5
python qdrant_utils.py search alexandria_v3_domain "database normalization" --limit 5
```

### Example 4: Clean Up Test Data

```bash
# Delete entire test collection
python qdrant_utils.py delete alexandria_test --confirm

# Or delete specific book from collection
python qdrant_utils.py delete-points alexandria --book "Test Book Title"
```

## Supported File Formats

- ✅ **EPUB** - Full support (text extraction, chapter preservation)
- ✅ **PDF** - Full support (text extraction, page preservation)
- ✅ **TXT** - Full support (plain text)
- ✅ **MD** - Full support (Markdown treated as plain text)
- ⚠️ **MOBI** - Not yet implemented (convert to EPUB with Calibre first)

## Open WebUI Integration

Ingested data je automatski kompatibilan s Open WebUI:

1. Payload sadrži `metadata` field koji Open WebUI očekuje
2. Chunks su automatski pretraživi kroz Open WebUI RAG interface
3. Možeš filtrirati po domeni/autoru/knjizi kroz Open WebUI

**Test u Open WebUI:**
1. Otvori Open WebUI (http://localhost:3000 ili slično)
2. Odaberi RAG model
3. Postavi pitanje: *"What does Silverston say about shipment patterns?"*
4. Open WebUI će automatski queryati Qdrant i prikazati relevantne chunks

## Troubleshooting

**📚 For comprehensive troubleshooting, see [Troubleshooting Guide](../docs/how-to-guides/troubleshoot-ingestion.md)**

**Quick Fixes:**

### Error: `ModuleNotFoundError: No module named 'ebooklib'`
```bash
pip install EbookLib
```

### Error: `Connection refused to localhost:6333`
Qdrant nije pokrenut. Provjeri Docker container:
```bash
docker ps | grep qdrant
```

### Error: `Embedding model download stuck`
Sentence-transformers skida model prvi put. Budi strpljiv ili:
```bash
# Pre-download model
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

### Chunks are too small/large
Prilagodi chunking strategiju u `ingest_books.py`:
```python
DOMAIN_CHUNK_SIZES = {
    'technical': {'min': 1500, 'max': 2000, 'overlap': 200},
    # ... adjust values
}
```

## Professional Workflow (VS Code)

### Development Setup

```bash
# 1. Open project in VS Code
code "c:\Users\goran\source\repos\Temenos\Akademija\Alexandria"

# 2. Open integrated terminal (Ctrl+`)
# 3. Navigate to scripts folder
cd scripts

# 4. Verify Python environment
python --version  # Should be Python 3.14

# 5. Test Qdrant connection
python qdrant_utils.py list
```

### Workflow Scripts

#### 1. Single Book Ingestion
```bash
# Interactive development - ingest one book at a time
python ingest_books.py \
  --file "../ingest/Silverston Vol 3.epub" \
  --domain technical \
  --collection alexandria_test
```

#### 2. Batch Ingestion (NEW!)
```bash
# Process entire folder - production workflow
python batch_ingest.py \
  --directory ../ingest \
  --domain technical \
  --collection alexandria \
  --resume  # Skip already processed files

# Resume after failure
python batch_ingest.py --directory ../ingest --domain technical --resume
```

#### 3. Chunking Experiments (NEW!)
```bash
# A/B test different chunk sizes
python experiment_chunking.py \
  --file "../ingest/Silverston Vol 3.epub" \
  --strategies small,medium,large \
  --collection-prefix test

# Custom chunk size comparison
python experiment_chunking.py \
  --file "../ingest/book.pdf" \
  --custom-sizes "1000:1500:150,2000:2500:200"
```

#### 4. RAG Query (NEW!)
```bash
# Query with formatted output for LLM
python rag_query.py "What does Silverston say about shipments?" --limit 5

# Export as JSON for programmatic use
python rag_query.py "database normalization" --format json > results.json

# Domain-specific search
python rag_query.py "cognitive load" --domain psychology --limit 3
```

#### 5. Collection Management
```bash
# Quick stats
python qdrant_utils.py stats alexandria_test

# Search testing
python qdrant_utils.py search alexandria_test "shipment lifecycle" --limit 5

# Copy collection for experimentation
python qdrant_utils.py copy alexandria_test alexandria_backup

# Clean up experiments
python qdrant_utils.py delete experiment_small --confirm
```

### Typical Development Session

```bash
# 1. Ingest new books
python batch_ingest.py --directory ../ingest/new_books --domain psychology

# 2. Check results
python qdrant_utils.py stats alexandria

# 3. Test retrieval quality
python rag_query.py "test query about new book content" --limit 5

# 4. If quality is poor, experiment with chunking
python experiment_chunking.py \
  --file "../ingest/new_books/problematic_book.pdf" \
  --strategies small,large

# 5. Compare results
python qdrant_utils.py search experiment_small "test query" --limit 3
python qdrant_utils.py search experiment_large "test query" --limit 3
```

### VS Code Tips

#### Recommended Extensions
- Python (Microsoft)
- Pylance (fast type checking)
- Python Debugger
- Markdown Preview Enhanced

#### Debugging Scripts
Set breakpoints in VS Code and debug with F5:
```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug Ingest",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/scripts/ingest_books.py",
      "args": [
        "--file", "../ingest/test.epub",
        "--domain", "technical"
      ],
      "console": "integratedTerminal"
    }
  ]
}
```

#### Terminal Shortcuts
- **Ctrl+`** - Toggle terminal
- **Ctrl+Shift+`** - New terminal
- **Ctrl+C** - Stop running script

---

## Available Scripts

| Script | Purpose | Complexity |
|--------|---------|------------|
| `ingest_books.py` | Single book ingestion | Basic |
| `batch_ingest.py` | Batch processing with resume | Intermediate |
| `experiment_chunking.py` | A/B test chunking strategies | Advanced |
| `rag_query.py` | Query with LLM-ready output | Basic |
| `qdrant_utils.py` | Collection management | Basic |

---

## Next Steps

1. **Ingest 10 representative books** (PoC faza) - Use `batch_ingest.py`
2. **Test retrieval quality** (manual evaluation) - Use `rag_query.py`
3. **Experiment with chunking strategies** - Use `experiment_chunking.py`
4. **Full ingestion pipeline** (batch processing 9000 books) - Production `batch_ingest.py`

---

**Last Updated:** 2026-01-21
**Author:** Claude Code (Alexandria project)
