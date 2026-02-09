# Alexandria API Contracts (MCP Server)

**Generated:** 2026-02-09
**Service:** Model Context Protocol Server
**Entry Point:** `scripts/mcp_server.py`
**Transport:** stdio (Claude Code integration)

---

## Overview

Alexandria exposes 14 MCP tools organized into three categories:

1. **Query Tools** (5) - Search, retrieve knowledge, manage guardians
2. **Ingest Tools - Calibre** (6) - Book ingestion from Calibre library
3. **Ingest Tools - Local Files** (3) - Direct file ingestion without Calibre

---

## Query Tools

### 1. alexandria_query

**Purpose:** Semantic search with optional hierarchical context

**Parameters:**
- `query` (string, required) - Natural language search query
- `limit` (int, optional) - Results to return (default: 5, max: 20)
- `threshold` (float, optional) - Similarity threshold 0.0-1.0 (default: 0.5)
- `context_mode` (string, optional) - Context retrieval strategy:
  - `"precise"` (default) - Only matched chunks
  - `"contextual"` - Include parent chapter context
  - `"comprehensive"` - Include parent + sibling chunks
- `response_pattern` (string, optional) - Response formatting guidance:
  - `"free"` (default) - No constraints
  - `"direct"` - Cite sources explicitly
  - `"synthesis"` - Cross-perspective analysis
  - `"extraction"` - Structured extraction with citations
  - `"critical"` - Find contradictions
  - Or pattern ID: `"tldr"`, `"cross_perspective"`, etc.
- `guardian` (string, optional) - Guardian persona to flavor the response (default: `"zec"`):
  - `"zec"` - Sharp, ironic meta-postman. Questions your assumptions.
  - `"vault_e"` - Neurotic archivist. Knows every duplicate and gap.
  - `"ariadne"` - Patient guide. Weaves paths through complex results.
  - `"hipatija"` - Intellectual challenger. Finds contradictions.
  - `"klepac"` - Formatting artisan. Quality guardian, detects BS.
  - `"lupita"` - Pig philosopher. Mljacka at pretentious queries.
  - `"alan_kay"` - Visionary. Systems thinking and paradigm shifts.
  - `"none"` - No guardian personality (plain Alexandria).

**Returns:**
```json
{
  "query": "...",
  "results": [
    {
      "score": 0.85,
      "book_title": "...",
      "author": "...",
      "section_name": "...",
      "text": "..."
    }
  ],
  "result_count": 5,
  "context_mode": "precise",
  "response_instruction": "...",  // guardian personality + pattern composed
  "guardian": "zec",
  "guardian_name": "Zec",
  "guardian_emoji": "...",
  "parent_chunks": [...],  // if contextual/comprehensive
  "hierarchy_stats": {...},  // if contextual/comprehensive
  "error": null
}
```

### 2. alexandria_guardians

**Purpose:** List available guardian personas for Alexandria responses

**Parameters:** None

**Returns:**
```json
{
  "guardians": [
    {
      "id": "zec",
      "name": "Zec",
      "emoji": "...",
      "role": "Meta-postman of Alexandria",
      "greeting": "..."
    }
  ],
  "default": "zec",
  "count": 11,
  "error": null
}
```

**Notes:** Use the guardian ID with `alexandria_query(guardian="...")` to activate a persona. Guardians are loaded from `.md` files in `docs/development/guardians/`. Adding a new guardian requires no code changes — just add an `.md` file with `alexandria:` YAML frontmatter.

### 3. alexandria_search

**Purpose:** Search Calibre library by metadata (not semantic)

**Parameters:**
- `author` (string, optional) - Author name (partial, case-insensitive)
- `title` (string, optional) - Book title (partial, case-insensitive)
- `language` (string, optional) - ISO language code (e.g., 'eng', 'hrv')
- `tags` (string, optional) - Comma-separated tags (books must have ALL)
- `limit` (int, optional) - Max results (default: 20, max: 100)

**Returns:**
```json
{
  "books": [
    {
      "id": 123,
      "title": "...",
      "author": "...",
      "language": "eng",
      "tags": ["philosophy", "ethics"],
      "series": "...",
      "series_index": 1.0,
      "formats": ["EPUB", "PDF"]
    }
  ],
  "count": 1,
  "error": null
}
```

### 4. alexandria_book

**Purpose:** Get detailed metadata for a specific book

**Parameters:**
- `book_id` (int, required) - Calibre database ID

**Returns:**
```json
{
  "book": {
    "id": 123,
    "title": "...",
    "author": "...",
    "language": "eng",
    "tags": [...],
    "series": "...",
    "series_index": 1.0,
    "isbn": "...",
    "publisher": "...",
    "pubdate": "2020-01-01",
    "rating": 5.0,
    "formats": ["EPUB", "PDF"]
  },
  "error": null
}
```

### 5. alexandria_stats

**Purpose:** Get collection and library statistics

**Parameters:** None

**Returns:**
```json
{
  "calibre": {
    "total_books": 9000,
    "total_authors": 1200,
    "formats": {"EPUB": 6500, "PDF": 2500},
    "languages": {"eng": 7000, "hrv": 500, "jpn": 300}
  },
  "qdrant": {
    "connected": true,
    "collection_name": "alexandria",
    "points_count": 450000,
    "vector_size": 1024,
    "status": "green"
  },
  "error": null
}
```

---

## Ingest Tools (Calibre)

### 6. alexandria_ingest_preview

**Purpose:** Preview books available for ingestion from Calibre

**Parameters:**
- `author` (string, optional) - Filter by author
- `title` (string, optional) - Filter by title
- `language` (string, optional) - Filter by language
- `format_filter` (string, optional) - Preferred format: 'epub', 'pdf', 'any' (default: 'epub')
- `limit` (int, optional) - Max results (default: 20, max: 50)

**Returns:**
```json
{
  "books": [
    {
      "id": 123,
      "title": "...",
      "author": "...",
      "language": "eng",
      "formats": ["EPUB", "PDF"],
      "selected_format": "EPUB",
      "file_path": "G:\\..."
    }
  ],
  "count": 1,
  "format_filter": "epub",
  "error": null
}
```

### 7. alexandria_ingest

**Purpose:** Ingest a book from Calibre into Qdrant

**Parameters:**
- `book_id` (int, required) - Calibre book ID
- `collection` (string, optional) - Target collection (default: env QDRANT_COLLECTION)
- `format_preference` (string, optional) - 'epub' or 'pdf' (default: 'epub')
- `hierarchical` (bool, optional) - Use two-level chunking (default: true)
- `threshold` (float, optional) - Chunking threshold 0.0-1.0 (default: 0.55)
- `min_chunk_size` (int, optional) - Min words per chunk (default: 200)
- `max_chunk_size` (int, optional) - Max words per chunk (default: 1200)

**Returns:**
```json
{
  "success": true,
  "title": "...",
  "author": "...",
  "language": "eng",
  "chunks": 202,
  "hierarchical": true,
  "chunking_params": {
    "threshold": 0.55,
    "min_chunk_size": 200,
    "max_chunk_size": 1200
  },
  "file_size_mb": 1.5,
  "collection": "alexandria",
  "format": "EPUB",
  "progress": "[██████] 100%",
  "steps": ["📖 Found: '...'", "...", "✅ Successfully ingested!"],
  "error": null
}
```

### 8. alexandria_batch_ingest

**Purpose:** Batch ingest multiple books

**Parameters:**
- `book_ids` (list[int], optional) - List of Calibre book IDs
- `author` (string, optional) - Search by author (alternative to book_ids)
- `title` (string, optional) - Search by title
- `language` (string, optional) - Filter by language
- `limit` (int, optional) - Max books (default: 10, max: 50)
- `collection`, `format_preference`, `hierarchical`, `threshold`, `min_chunk_size`, `max_chunk_size` - Same as alexandria_ingest

**Returns:**
```json
{
  "total": 10,
  "succeeded": 8,
  "skipped": 1,
  "failed": 1,
  "results": [
    {
      "id": 123,
      "title": "...",
      "author": "...",
      "status": "success",
      "chunks": 202,
      "error": null
    }
  ],
  "summary": "📚 Batch ingest complete: 8/10 succeeded, 1 skipped, 1 failed",
  "error": null
}
```

### 9. alexandria_test_chunking

**Purpose:** Test chunking parameters WITHOUT uploading

**Parameters:**
- `book_id` (int, required)
- `threshold` (float, optional) - Default: 0.55
- `min_chunk_size`, `max_chunk_size` (int, optional)
- `format_preference` (string, optional)

**Returns:**
```json
{
  "success": true,
  "title": "...",
  "parameters": {"threshold": 0.55, "min": 200, "max": 1200},
  "stats": {
    "total_chunks": 202,
    "avg_words": 450,
    "min_words": 200,
    "max_words": 1200
  },
  "samples": [
    {"chunk_num": 1, "words": 450, "text": "..."},
    {"chunk_num": 50, "words": 380, "text": "..."},
    {"chunk_num": 150, "words": 520, "text": "..."}
  ],
  "error": null
}
```

### 10. alexandria_compare_chunking

**Purpose:** Compare multiple threshold values to find optimal chunking

**Parameters:**
- `book_id` (int, required)
- `format_preference` (string, optional)

**Returns:**
```json
{
  "success": true,
  "title": "...",
  "author": "...",
  "total_sentences": 5000,
  "total_words": 80000,
  "similarity_distribution": {
    "min": 0.2,
    "max": 0.95,
    "mean": 0.65,
    "median": 0.68
  },
  "comparisons": [
    {
      "threshold": 0.40,
      "chunks": 120,
      "avg_words": 666,
      "coherence": 0.82,
      "semantic_breaks": 95,
      "forced_breaks": 25,
      "sample_breaks": [...]
    },
    {
      "threshold": 0.55,
      "chunks": 202,
      "avg_words": 396,
      "coherence": 0.75,
      "semantic_breaks": 180,
      "forced_breaks": 22,
      "sample_breaks": [...]
    }
  ],
  "recommendation": 0.55,
  "recommendation_reason": "Best balance of chunk size and semantic coherence"
}
```

---

## Ingest Tools (Local Files)

### 11. alexandria_browse_local

**Purpose:** Browse local files available for ingestion

**Parameters:**
- `path` (string, optional) - Directory to browse (default: env LOCAL_INGEST_PATH)
- `recursive` (bool, optional) - Search subdirectories (default: false)

**Returns:**
```json
{
  "path": "C:/Users/Sabo/Downloads",
  "files": [
    {
      "name": "book.epub",
      "size_mb": 1.5,
      "format": "EPUB",
      "full_path": "C:/Users/Sabo/Downloads/book.epub"
    }
  ],
  "count": 1,
  "error": null
}
```

### 12. alexandria_ingest_file

**Purpose:** Ingest a local file without Calibre

**Parameters:**
- `file_path` (string, required) - Absolute path to book file
- `title` (string, optional) - Book title (required if not in file metadata)
- `author` (string, optional) - Book author (required if not in file metadata)
- `language` (string, optional) - Language code
- `collection`, `hierarchical`, `threshold`, `min_chunk_size`, `max_chunk_size` - Same as alexandria_ingest

**Returns (Success):**
```json
{
  "success": true,
  "title": "...",
  "author": "...",
  "language": "eng",
  "chunks": 202,
  "hierarchical": true,
  "chunking_params": {...},
  "file_size_mb": 1.5,
  "collection": "alexandria",
  "format": "EPUB",
  "progress": "[██████] 100%",
  "steps": [...],
  "error": null
}
```

**Returns (Missing Metadata):**
```json
{
  "success": false,
  "needs_metadata": true,
  "file_path": "...",
  "file_name": "book.pdf",
  "file_size_mb": 1.5,
  "format": "PDF",
  "extracted": {
    "title": null,
    "author": null,
    "language": "eng"
  },
  "missing_fields": ["title", "author"],
  "progress": "[███░░░] 50%",
  "steps": [...],
  "error": "Missing required metadata: title, author. Please provide: alexandria_ingest_file(file_path=\"...\", title=\"...\", author=\"...\")"
}
```

### 13. alexandria_test_chunking_file

**Purpose:** Test chunking on local file WITHOUT uploading

**Parameters:**
- `file_path` (string, required)
- `threshold`, `min_chunk_size`, `max_chunk_size` (same as alexandria_test_chunking)

**Returns:** Same format as `alexandria_test_chunking`

---

## Authentication & Security

**Current Status:** No authentication implemented (Phase 1 - open access)

**Future Plans:**
- Phase 2: User accounts with API keys
- Phase 3: Collection-level access control based on copyright status
- Phase 4: SSO integration for team collections

---

## Error Handling

All tools return errors in a consistent format:

```json
{
  "success": false,
  "error": "Human-readable error message",
  ...context-specific fields...
}
```

**Common Error Types:**
- File not found (Calibre library, book files)
- Qdrant connection failures
- Book already ingested
- Missing metadata
- Unsupported file formats
- Permission denied

---

## Environment Configuration

**Required:**
- `QDRANT_HOST` - Qdrant server (default: 192.168.0.151)
- `QDRANT_PORT` - Qdrant port (default: 6333)
- `CALIBRE_LIBRARY_PATH` - Path to Calibre library
- `QDRANT_COLLECTION` - Collection name (default: alexandria)

**Optional:**
- `LOCAL_INGEST_PATH` - Default local file browse directory
- `OPENROUTER_API_KEY` - For CLI LLM testing (not used by MCP)

---

## Integration Notes

**Claude Code Integration:**
- Transport: stdio
- Configuration: `.mcp.json` in project root
- Tools exposed via FastMCP framework
- Logging: WARNING level (minimized for MCP)

**Typical Workflow:**
1. `alexandria_stats` - Check collection status
2. `alexandria_query` - Semantic search
3. `alexandria_ingest_preview` - Find books to add
4. `alexandria_test_chunking` - Test parameters
5. `alexandria_ingest` - Add book to collection

---

## Performance Characteristics

**Query Performance:**
- Semantic search: ~100-500ms (depends on Qdrant load)
- Context modes: +50-200ms for parent/sibling retrieval
- Metadata search: ~50-200ms (SQLite query)

**Ingestion Performance:**
- Text extraction: 1-5 seconds (EPUB/PDF)
- Chunking: 5-15 seconds (depends on book size)
- Embedding generation: 10-60 seconds (GPU: fast, CPU: slow)
- Upload to Qdrant: 2-5 seconds
- **Total:** 20-90 seconds per book (GPU mode ~30s avg)

**Batch Ingestion:**
- GPU mode: ~30 books/hour
- CPU mode: ~10 books/hour
- Progress tracking via `steps` array in response
