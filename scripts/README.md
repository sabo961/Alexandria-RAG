# Alexandria Ingestion Scripts

Python scripts for ingesting books into Qdrant vector database.

## Setup

### 1. Install Dependencies

```bash
pip install -r ../requirements.txt
```

### 2. Configure Environment

Run the interactive configuration wizard to set up your environment:

```bash
python configure.py
```

Or copy `.env.example` to `.env` and edit manually:

```bash
cp ../.env.example ../.env
# Edit .env with your values
```

Configuration variables:
- `QDRANT_HOST` - Qdrant server hostname (e.g., 192.168.0.151)
- `QDRANT_PORT` - Qdrant server port (default: 6333)
- `QDRANT_COLLECTION` - Default collection name (default: alexandria)
- `CALIBRE_LIBRARY_PATH` - Path to your Calibre library
- `LOCAL_INGEST_PATH` - Default browse directory for ingestion
- `OPENROUTER_API_KEY` - API key for LLM features (optional)

### 3. Verify Qdrant is Running

Qdrant must be running (host/port configured in `.env`).

```bash
# Test connection
python qdrant_utils.py list

# Or check current configuration
python configure.py --show
```

## Usage

### Ingest a Single Book

```bash
# EPUB book
python ingest_books.py --file "path/to/book.epub"

# PDF book
python ingest_books.py --file "path/to/book.pdf"

# Custom collection
python ingest_books.py --file "book.epub" --collection alexandria_test

# With hierarchical chunking (default)
python ingest_books.py --file "book.epub" --hierarchical
```

### Manage Collections

```bash
# List all collections
python qdrant_utils.py list

# Get collection statistics
python qdrant_utils.py stats alexandria

# Copy collection (all data)
python qdrant_utils.py copy alexandria_v1 alexandria_v2

# Delete collection (with confirmation)
python qdrant_utils.py delete alexandria_test

# Create alias (point "alexandria" to "alexandria_v3")
python qdrant_utils.py alias alexandria_v3 alexandria

# Delete specific points by book
python qdrant_utils.py delete-points alexandria --book "The Goal"
```

### Search / Test Retrieval

```bash
# Basic search
python qdrant_utils.py search alexandria "database normalization patterns" --limit 10
```

## Chunking Strategy

Alexandria uses **Universal Semantic Chunking** for all content:

| Parameter | Default | Description |
|-----------|---------|-------------|
| **threshold** | 0.5 | Semantic similarity threshold for splits |
| **min_chunk_size** | 100 | Minimum tokens per chunk |
| **max_chunk_size** | 1500 | Maximum tokens per chunk |

Content type (technical, philosophy, etc.) is determined by the content itself, not pre-assigned labels.

### Hierarchical Chunking (Default)

Books are chunked into a two-level hierarchy:
- **Parent chunks**: Chapter/section level (full context)
- **Child chunks**: Semantic segments (for precise retrieval)

This enables contextual retrieval where matching child chunks can fetch their parent context.

## Examples

### Example 1: Ingest Book with Default Settings

```bash
python ingest_books.py --file "../ingest/Silverston Vol 3.epub"
```

**What happens:**
1. Extracts chapters from EPUB
2. Creates hierarchical parent/child chunks
3. Generates embeddings using configured model (default: `bge-m3` 1024-dim, multilingual)
4. Uploads to Qdrant collection `alexandria`

### Example 2: Batch Ingestion

```bash
# Process entire folder
python batch_ingest.py --directory ../ingest --collection alexandria

# Resume after failure
python batch_ingest.py --directory ../ingest --resume
```

### Example 3: RAG Query with Response Patterns

```bash
# Basic query
python rag_query.py "What does Silverston say about shipments?" --limit 5

# With LLM answer generation
python rag_query.py "database normalization" --answer --model openai/gpt-4o-mini

# Contextual retrieval (includes parent chunks)
python rag_query.py "loss aversion" --context-mode contextual
```

### Example 4: Clean Up Test Data

```bash
# Delete entire test collection
python qdrant_utils.py delete alexandria_test --confirm

# Or delete specific book from collection
python qdrant_utils.py delete-points alexandria --book "Test Book Title"
```

## Supported File Formats

- **EPUB** - Full support (text extraction, chapter preservation)
- **PDF** - Full support (text extraction, page preservation)
- **TXT** - Full support (plain text)
- **MD** - Full support (Markdown treated as plain text)
- **MOBI** - Not yet implemented (convert to EPUB with Calibre first)

## MCP Server Integration

Alexandria includes an MCP (Model Context Protocol) server for integration with Claude Code and other AI tools:

```bash
# Run MCP server
python mcp_server.py
```

Available MCP tools:
- `alexandria_query` - Semantic search with optional response patterns
- `alexandria_search` - Metadata search (author, title, language)
- `alexandria_ingest` - Ingest books from file path
- `alexandria_stats` - Collection statistics

## Troubleshooting

**For comprehensive troubleshooting, see [Troubleshooting Guide](../docs/how-to-guides/troubleshoot-ingestion.md)**

**Quick Fixes:**

### Error: `ModuleNotFoundError: No module named 'ebooklib'`
```bash
pip install EbookLib
```

### Error: `Connection refused to localhost:6333`
Qdrant is not running. Check Docker container:
```bash
docker ps | grep qdrant
```

### Error: `Embedding model download stuck`
Sentence-transformers downloads model on first run. Be patient or:
```bash
# Pre-download models
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-m3')"
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

## Available Scripts

| Script | Purpose |
|--------|---------|
| `ingest_books.py` | Single book ingestion |
| `batch_ingest.py` | Batch processing with resume |
| `rag_query.py` | Query with LLM-ready output |
| `qdrant_utils.py` | Collection management |
| `mcp_server.py` | MCP server for AI integration |
| `collection_manifest.py` | Manifest management |
| `calibre_db.py` | Calibre library integration |
| `config.py` | Centralized configuration |

---

**Last Updated:** 2026-01-30
