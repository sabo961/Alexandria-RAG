# Alexandria MCP Server

The Alexandria MCP Server exposes the RAG knowledge base through the Model Context Protocol, enabling Claude Code and other MCP clients to query ~9,000 books.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Claude Code / Other MCP Clients                                │
└─────────────────────────────────────────────────────────────────┘
                              │ stdio
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Alexandria MCP Server (scripts/mcp_server.py)                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Query Tools:                                                ││
│  │  • alexandria_query          - Semantic search + RAG        ││
│  │  • alexandria_search         - Search Calibre metadata      ││
│  │  • alexandria_book           - Get book details by ID       ││
│  │  • alexandria_stats          - Collection statistics        ││
│  │                                                             ││
│  │ Ingest Tools (Calibre):                                      ││
│  │  • alexandria_ingest_preview - Preview books for ingestion  ││
│  │  • alexandria_ingest         - Ingest book into Qdrant      ││
│  │  • alexandria_batch_ingest   - Batch ingest multiple books  ││
│  │  • alexandria_test_chunking  - Test chunking parameters     ││
│  │                                                             ││
│  │ Ingest Tools (Local Files - no Calibre):                    ││
│  │  • alexandria_browse_local        - Browse local files      ││
│  │  • alexandria_ingest_file         - Ingest local file       ││
│  │  • alexandria_test_chunking_file  - Test chunking on file   ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
    ┌──────────┐       ┌───────────┐       ┌──────────┐
    │ Qdrant   │       │ Calibre   │       │OpenRouter│
    │ Vector DB│       │ SQLite DB │       │ LLM API  │
    └──────────┘       └───────────┘       └──────────┘
```

## Answer Generation

Alexandria supports two approaches for generating answers from retrieved chunks:

### Option 1: Claude Synthesizes (Default, Recommended)

```
User Question → MCP Server → Chunks → Claude Code → Answer
```

The MCP server returns relevant chunks, and **Claude Code synthesizes the answer directly**. This is the recommended approach:
- ✅ Best quality (Claude Opus/Sonnet)
- ✅ No additional API costs
- ✅ Integrated into conversation context

**Usage:** Just call `alexandria_query()` - Claude reads the chunks and answers.

### Option 2: OpenRouter LLM (Testing/CLI)

```
User Question → CLI → Chunks → OpenRouter API → Answer
```

Use OpenRouter to test retrieval quality with cheaper models:

```bash
# Test with Llama-3-8B (cheap baseline)
python rag_query.py "your question" --answer --model meta-llama/llama-3-8b-instruct

# Test with Claude Haiku (mid-tier)
python rag_query.py "your question" --answer --model anthropic/claude-3-haiku
```

**Use cases:**
- 🧪 **QA Testing** - If a weak model gives good answers, chunks are relevant
- 💻 **CLI without Claude Code** - Standalone usage
- 📊 **Batch processing** - Automated queries

**Configuration:**
```toml
# .streamlit/secrets.toml
OPENROUTER_API_KEY = "sk-or-v1-..."
```

**Models for testing (OpenRouter):**

| Model | Cost | Purpose |
|-------|------|---------|
| `meta-llama/llama-3-8b-instruct` | ~$0.05/M | Baseline test |
| `mistralai/mistral-7b-instruct` | ~$0.05/M | Alternative baseline |
| `anthropic/claude-3-haiku` | ~$0.25/M | Mid-tier validation |
| `anthropic/claude-3.5-sonnet` | ~$3/M | Production comparison |

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `QDRANT_HOST` | Yes | `192.168.0.151` | Qdrant server hostname |
| `QDRANT_PORT` | Yes | `6333` | Qdrant server port |
| `CALIBRE_LIBRARY_PATH` | Yes | `G:\My Drive\alexandria` | Path to Calibre library |
| `QDRANT_COLLECTION` | No | `alexandria` | Qdrant collection name |
| `LOCAL_INGEST_PATH` | No | `~/Downloads` | Default directory for local file browsing |

### .mcp.json Configuration

Add to your project's `.mcp.json`:

```json
{
  "mcpServers": {
    "alexandria": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "C:/Users/goran/source/repos/Temenos/Akademija/Alexandria",
        "python",
        "scripts/mcp_server.py"
      ],
      "env": {
        "QDRANT_HOST": "192.168.0.151",
        "QDRANT_PORT": "6333",
        "CALIBRE_LIBRARY_PATH": "G:\\My Drive\\alexandria"
      }
    }
  }
}
```

## Query Tools

### alexandria_query

Semantic search across the knowledge base. Returns relevant chunks that Claude reads directly to generate answers.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `query` | string | required | Natural language question |
| `limit` | int | `5` | Results to return (1-20) |
| `threshold` | float | `0.5` | Similarity threshold (0.0-1.0) |
| `context_mode` | string | `"precise"` | How much context to include (see below) |

**Context Modes:**

| Mode | Description | Speed | Use Case |
|------|-------------|-------|----------|
| `precise` | Only matched chunks | ⚡ Fast | Exact citations, fact-checking |
| `contextual` | Matched chunks + parent chapter context | 🔄 Medium | Understanding surrounding context |
| `comprehensive` | Matched + parent + sibling chunks | 🐢 Slow | Deep analysis of a topic |

**Returns:**

```json
{
  "query": "database normalization",
  "results": [
    {
      "score": 0.82,
      "book_title": "The Data Model Resource Book",
      "author": "Len Silverston",
      "section_name": "Chapter 3: Data Normalization",
      "text": "Normalization is the process of..."
    }
  ],
  "result_count": 5,
  "context_mode": "precise",
  "error": null
}
```

**Returns (contextual/comprehensive mode):**

```json
{
  "query": "loss aversion",
  "results": [...],
  "result_count": 5,
  "context_mode": "contextual",
  "parent_chunks": [
    {
      "id": "parent-uuid",
      "book_title": "Thinking, Fast and Slow",
      "section_name": "Chapter 26: Prospect Theory",
      "text": "Chapter introduction and context..."
    }
  ],
  "hierarchy_stats": {
    "context_mode": "contextual",
    "parent_chunks_fetched": 3,
    "unique_chapters": 2
  },
  "error": null
}
```

**Examples:**

```
# Simple search (precise mode, default)
alexandria_query("database normalization")

# More results with stricter threshold
alexandria_query("cognitive load", limit=10, threshold=0.7)

# Get chapter context with results
alexandria_query("loss aversion", context_mode="contextual")

# Deep analysis with all surrounding context
alexandria_query("antifragility", context_mode="comprehensive")
```

### alexandria_search

Search Calibre library by metadata.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `author` | string | `null` | Author name (partial, case-insensitive) |
| `title` | string | `null` | Book title (partial, case-insensitive) |
| `language` | string | `null` | ISO code: `eng`, `hrv`, `jpn`, etc. |
| `tags` | string | `null` | Comma-separated tags (AND logic) |
| `limit` | int | `20` | Max results (1-100) |

**Returns:**

```json
{
  "books": [
    {
      "id": 123,
      "title": "The Data Model Resource Book",
      "author": "Len Silverston",
      "language": "eng",
      "tags": ["technical", "databases"],
      "series": null,
      "series_index": null,
      "formats": ["epub", "pdf"]
    }
  ],
  "count": 1,
  "error": null
}
```

### alexandria_book

Get detailed metadata for a book by Calibre ID.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `book_id` | int | required | Calibre database ID |

**Returns:**

```json
{
  "book": {
    "id": 123,
    "title": "The Data Model Resource Book",
    "author": "Len Silverston",
    "language": "eng",
    "tags": ["technical", "databases"],
    "series": "Data Model Resource Book",
    "series_index": 1.0,
    "isbn": "978-0471380238",
    "publisher": "Wiley",
    "pubdate": "2001-01-15",
    "rating": 8,
    "formats": ["epub", "pdf"]
  },
  "error": null
}
```

### alexandria_stats

Get collection and library statistics.

**Returns:**

```json
{
  "calibre": {
    "total_books": 9234,
    "total_authors": 3421,
    "formats": {"epub": 8500, "pdf": 2100, "mobi": 500},
    "languages": {"eng": 7000, "hrv": 1500, "jpn": 200}
  },
  "qdrant": {
    "connected": true,
    "collection_name": "alexandria",
    "points_count": 450000,
    "vector_size": 384,
    "status": "green"
  },
  "error": null
}
```

## Ingest Tools

### alexandria_ingest_preview

Preview books available for ingestion from Calibre library.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `author` | string | `null` | Filter by author name |
| `title` | string | `null` | Filter by book title |
| `language` | string | `null` | Filter by language code |
| `format_filter` | string | `"epub"` | Format: `epub`, `pdf`, or `any` |
| `limit` | int | `20` | Max results (1-50) |

**Returns:**

```json
{
  "books": [
    {
      "id": 123,
      "title": "The Data Model Resource Book",
      "author": "Len Silverston",
      "language": "eng",
      "formats": ["epub", "pdf"],
      "selected_format": "EPUB",
      "file_path": "G:\\My Drive\\alexandria\\Silverston, Len\\The Data Model Resource Book (123)\\The Data Model Resource Book - Len Silverston.epub"
    }
  ],
  "count": 1,
  "format_filter": "epub",
  "error": null
}
```

**Examples:**

```
# Find EPUB books by author
alexandria_ingest_preview(author="Fowler", format_filter="epub")

# All formats for a title
alexandria_ingest_preview(title="Design Patterns", format_filter="any")
```

### alexandria_ingest

Ingest a book from Calibre library into Qdrant. Returns progress tracking with visual indicator and step-by-step status.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `book_id` | int | required | Calibre book ID (from preview/search) |
| `collection` | string | `null` | Target collection (default: env `QDRANT_COLLECTION`) |
| `format_preference` | string | `"epub"` | Preferred format: `epub` or `pdf` |
| `hierarchical` | bool | `true` | Use two-level chunking (parent chapters + child chunks) |
| `threshold` | float | `0.55` | Similarity threshold (0.0-1.0). Lower = larger chunks |
| `min_chunk_size` | int | `200` | Minimum words per chunk |
| `max_chunk_size` | int | `1200` | Maximum words per chunk |

**Hierarchical Chunking:**

When `hierarchical=true` (default), the ingestion creates a two-level structure:
- **Parent chunks**: One per chapter/section, contains full chapter text (truncated for embedding)
- **Child chunks**: Semantic chunks within each chapter, linked to parent via `parent_id`

This enables `context_mode="contextual"` queries that return chapter context along with matched chunks.

Set `hierarchical=false` for flat chunking (legacy mode, no parent-child relationship).

**Returns:**

```json
{
  "success": true,
  "title": "The Data Model Resource Book",
  "author": "Len Silverston",
  "language": "eng",
  "chunks": 245,
  "hierarchical": true,
  "file_size_mb": 2.34,
  "collection": "alexandria",
  "format": "EPUB",
  "progress": "[██████] 100%",
  "steps": [
    "📖 Found: 'The Data Model Resource Book' by Len Silverston",
    "📁 Using EPUB format",
    "🔍 File located",
    "📋 Not previously ingested",
    "⚙️ Ingesting 'The Data Model Resource Book' (hierarchical mode)...",
    "💾 Manifest updated",
    "✅ Successfully ingested 'The Data Model Resource Book'!"
  ],
  "error": null
}
```

**Example Workflow:**

```
# 1. Preview available books
alexandria_ingest_preview(author="Silverston")

# 2. Ingest with hierarchical chunking (default)
alexandria_ingest(book_id=123)

# 3. Custom chunking parameters (smaller chunks)
alexandria_ingest(book_id=123, threshold=0.7, max_chunk_size=800)

# 4. Flat chunking (legacy)
alexandria_ingest(book_id=123, hierarchical=false)
```

### alexandria_batch_ingest

Batch ingest multiple books at once. Provide either a list of book IDs or search criteria.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `book_ids` | list[int] | `null` | List of Calibre book IDs to ingest |
| `author` | string | `null` | Search by author (alternative to book_ids) |
| `title` | string | `null` | Search by title (alternative to book_ids) |
| `language` | string | `null` | Filter by language code |
| `limit` | int | `10` | Maximum books to ingest (1-50) |
| `collection` | string | `null` | Target collection |
| `format_preference` | string | `"epub"` | Preferred format |
| `hierarchical` | bool | `true` | Use hierarchical chunking |
| `threshold` | float | `0.55` | Similarity threshold |
| `min_chunk_size` | int | `200` | Minimum words per chunk |
| `max_chunk_size` | int | `1200` | Maximum words per chunk |

**Returns:**

```json
{
  "total": 5,
  "succeeded": 3,
  "skipped": 1,
  "failed": 1,
  "results": [
    {"id": 123, "title": "Book A", "author": "Author", "status": "success", "chunks": 245},
    {"id": 456, "title": "Book B", "author": "Author", "status": "skipped", "error": "Already ingested"},
    {"id": 789, "title": "Book C", "author": "Author", "status": "failed", "error": "No readable format"}
  ],
  "summary": "📚 Batch ingest complete: 3/5 succeeded, 1 skipped, 1 failed",
  "error": null
}
```

**Examples:**

```
# Ingest specific books by ID
alexandria_batch_ingest(book_ids=[123, 456, 789])

# Ingest all Nietzsche books (up to 10)
alexandria_batch_ingest(author="Nietzsche", limit=10)

# Ingest English philosophy books
alexandria_batch_ingest(author="Nietzsche", language="eng", limit=5)

# Custom chunking for technical books
alexandria_batch_ingest(
    author="Silverston",
    limit=5,
    threshold=0.6,
    max_chunk_size=1000
)
```

### alexandria_test_chunking

Test chunking parameters on a book WITHOUT uploading to Qdrant.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `book_id` | int | required | Calibre book ID |
| `threshold` | float | `0.55` | Similarity threshold (0.0-1.0). Lower = fewer breaks |
| `min_chunk_size` | int | `200` | Minimum words per chunk |
| `max_chunk_size` | int | `1200` | Maximum words per chunk |
| `format_preference` | string | `"epub"` | Preferred format |

**Returns:**

```json
{
  "success": true,
  "file": "path/to/book.epub",
  "title": "The Data Model Resource Book",
  "author": "Len Silverston",
  "parameters": {
    "threshold": 0.55,
    "min_chunk_size": 200,
    "max_chunk_size": 1200
  },
  "stats": {
    "total_chunks": 245,
    "total_words": 85000,
    "total_chars": 450000,
    "avg_words_per_chunk": 347.0,
    "min_words": 200,
    "max_words": 1198
  },
  "samples": [
    {
      "index": 0,
      "word_count": 320,
      "preview": "First chunk text preview..."
    }
  ],
  "error": null
}
```

**Example:**

```
# Test with more aggressive chunking
alexandria_test_chunking(book_id=123, threshold=0.7, max_chunk_size=800)
```

## Local File Ingest Tools (No Calibre Required)

### alexandria_browse_local

Browse local files available for ingestion.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `path` | string | `LOCAL_INGEST_PATH` | Directory to browse |
| `recursive` | bool | `false` | Search subdirectories |

**Returns:**

```json
{
  "path": "C:/Downloads",
  "files": [
    {
      "name": "book.epub",
      "size_mb": 1.25,
      "format": "EPUB",
      "full_path": "C:/Downloads/book.epub"
    }
  ],
  "count": 1,
  "error": null
}
```

**Examples:**

```
# Browse default location (~/Downloads or LOCAL_INGEST_PATH)
alexandria_browse_local()

# Browse specific directory with subdirectories
alexandria_browse_local(path="C:/Books", recursive=true)
```

### alexandria_ingest_file

Ingest a local file directly into Qdrant. **Asks for metadata if missing.**

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `file_path` | string | required | Absolute path to book file (EPUB, PDF, TXT, MD, HTML) |
| `title` | string | `null` | Book title (required if not in file) |
| `author` | string | `null` | Book author (required if not in file) |
| `language` | string | `null` | Language code: `eng`, `hrv`, etc. |
| `collection` | string | `null` | Target collection (default: env `QDRANT_COLLECTION`) |
| `hierarchical` | bool | `true` | Use two-level chunking (parent chapters + child chunks) |
| `threshold` | float | `0.55` | Similarity threshold (0.0-1.0). Lower = larger chunks |
| `min_chunk_size` | int | `200` | Minimum words per chunk |
| `max_chunk_size` | int | `1200` | Maximum words per chunk |

**Returns (success):**

```json
{
  "success": true,
  "title": "My Book",
  "author": "John Doe",
  "language": "eng",
  "chunks": 150,
  "hierarchical": true,
  "file_size_mb": 1.25,
  "collection": "alexandria",
  "format": "EPUB",
  "progress": "[██████] 100%",
  "steps": [
    "📁 Found: my_book.epub (1.3 MB)",
    "📋 Not previously ingested",
    "🔍 Metadata: 'My Book' by John Doe",
    "⚙️ Ingesting (hierarchical mode)...",
    "💾 Manifest updated",
    "✅ Successfully ingested 'My Book'!"
  ],
  "error": null
}
```

**Returns (needs metadata):**

```json
{
  "success": false,
  "needs_metadata": true,
  "file_path": "C:/Downloads/scan.pdf",
  "file_name": "scan.pdf",
  "file_size_mb": 2.5,
  "format": "PDF",
  "extracted": {
    "title": null,
    "author": null,
    "language": "eng"
  },
  "missing_fields": ["title", "author"],
  "progress": "[███░░░] 50%",
  "steps": [
    "📁 Found: scan.pdf (2.5 MB)",
    "📋 Not previously ingested",
    "⚠️ Missing metadata: title, author"
  ],
  "error": "Missing required metadata: title, author. Please provide..."
}
```

**Workflow:**

```
# Step 1: Browse for files
alexandria_browse_local(path="C:/Downloads")

# Step 2: Try to ingest (may ask for metadata)
alexandria_ingest_file(file_path="C:/Downloads/scan.pdf")
# Response: needs_metadata=true, missing_fields=["title", "author"]

# Step 3: Provide missing metadata
alexandria_ingest_file(
    file_path="C:/Downloads/scan.pdf",
    title="My Book",
    author="John Doe"
)
# Response: success=true
```

### alexandria_test_chunking_file

Test chunking parameters on a local file WITHOUT uploading to Qdrant.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `file_path` | string | required | Absolute path to book file |
| `threshold` | float | `0.55` | Similarity threshold (0.0-1.0) |
| `min_chunk_size` | int | `200` | Minimum words per chunk |
| `max_chunk_size` | int | `1200` | Maximum words per chunk |

**Returns:** Same as `alexandria_test_chunking`

**Example:**

```
alexandria_test_chunking_file(
    file_path="/downloads/book.epub",
    threshold=0.7,
    max_chunk_size=800
)
```

## Usage Examples

### From Claude Code

After configuring `.mcp.json`, Claude Code can access Alexandria:

```
User: What does Silverston say about the shipment pattern?

Claude: [calls alexandria_query("shipment pattern")]
        Based on "The Data Model Resource Book" by Len Silverston...
```

```
User: Ingest the MCP agents book

Claude: [calls alexandria_ingest_preview(title="MCP agents")]
        Found 1 matching book...

        [calls alexandria_ingest(book_id=456)]
        Successfully ingested: 234 chunks created
```

### Local Testing

```bash
# Run server directly
python scripts/mcp_server.py

# Test with MCP inspector
npx @modelcontextprotocol/inspector python scripts/mcp_server.py
```

## Troubleshooting

### "Cannot connect to Qdrant"

1. Check VPN connection if Qdrant is remote
2. Verify `QDRANT_HOST` and `QDRANT_PORT` environment variables
3. Test connectivity: `curl http://192.168.0.151:6333/dashboard`

### "Calibre library not found"

1. Verify `CALIBRE_LIBRARY_PATH` points to directory containing `metadata.db`
2. Check path uses correct slashes for your OS

### No results from query

1. Lower `threshold` (try 0.3)
2. Check if collection has content: `alexandria_stats()`

### Book already ingested

The manifest tracks ingested books. To re-ingest:
1. Delete the collection in Qdrant
2. Delete manifest file: `logs/{collection}_manifest.json`
3. Re-ingest

## Dependencies

The MCP server requires:

- `mcp>=1.0.0` - Model Context Protocol SDK
- All existing Alexandria dependencies (sentence-transformers, qdrant-client, etc.)

Install with:

```bash
pip install -r requirements.txt
```
