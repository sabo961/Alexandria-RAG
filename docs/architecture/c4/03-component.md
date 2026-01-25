# C4 Level 3: Component Diagram (Scripts Package)

**Purpose:** Shows the internal structure of the Scripts Package container - the core business logic components.

---

## Diagram

View interactively: http://localhost:8081 → "Components" view

Or see `workspace.dsl` component definitions.

---

## Components

### 1. Ingestion Engine
**Files:** `batch_ingest.py`, `ingest_books.py`
**Purpose:** Processes books into chunks and uploads to Qdrant

**Responsibilities:**
- Extract text from EPUB/PDF/TXT/MD files
- Apply domain-specific chunking strategies
- Generate embeddings (sentence-transformers)
- Upload chunks to Qdrant with metadata
- Log to manifest system
- Resume interrupted batch ingestion

**Key Functions:**
- `ingest_book()` - Single book ingestion
- `batch_ingest()` - Multiple books with resume
- `extract_text_from_epub()` - EPUB text extraction
- `extract_text_from_pdf()` - PDF text extraction
- `create_chunks_from_sections()` - Chunking orchestrator

**Integration Points:**
- → Chunking Strategies (applies chunking)
- → Collection Management (logs manifest)
- → File System (reads books, moves to ingested/)
- → Qdrant (uploads chunks)

**Related Story:** [01-INGESTION.md](../../stories/01-INGESTION.md)

---

### 2. Universal Semantic Chunker
**Files:** `universal_chunking.py`, `ingest_books.py`
**Purpose:** Semantic-aware text chunking for optimal retrieval across all domains

**Responsibilities:**
- Split text into sentences using regex
- Generate embeddings for all sentences
- Calculate cosine similarity between consecutive sentences
- Break chunks at semantic topic boundaries (low similarity)
- Enforce min/max chunk size constraints
- Domain-agnostic approach (works for all content types)

**Algorithm:**
```
1. Split text into sentences
2. Embed all sentences (all-MiniLM-L6-v2)
3. For each sentence pair:
   - Calculate similarity with previous sentence
   - If similarity < threshold AND buffer >= min_size:
     → Create new chunk
   - Else: Add to current buffer
4. Enforce max_chunk_size safety cap
```

**Parameters:**

| Parameter | Default | Philosophy | Description |
|-----------|---------|------------|-------------|
| threshold | 0.55 | 0.45 | Lower = fewer breaks, larger chunks |
| min_chunk_size | 200 words | 200 words | Minimum context buffer |
| max_chunk_size | 1200 words | 1200 words | Safety cap for LLM limits |

**Philosophy Tuning:**
- Lower threshold (0.45) for tighter topic focus
- Preserves argument coherence through semantic similarity
- No hard-coded opposition detection needed

**Key Functions:**
- `UniversalChunker.chunk()` - Main chunking entry point
- `_split_sentences()` - Regex-based sentence splitting
- `_create_chunk_dict()` - Chunk metadata generation

**Benefits:**
- **Semantic integrity:** Breaks where topic changes, not at word count
- **Domain agnostic:** Same logic for technical, psychology, philosophy, literature
- **Adaptive:** Automatically adjusts to content structure
- **Context preservation:** Maintains minimum chunk size for LLM context

**Related Story:** [02-CHUNKING.md](../../stories/02-CHUNKING.md)
**Related ADR:** [ADR 0002: Domain-Specific Chunking](../decisions/0002-domain-specific-chunking.md) - Superseded by Universal Semantic approach

---

### 3. RAG Query Engine
**Files:** `rag_query.py`
**Purpose:** Semantic search with LLM answer generation

**Responsibilities:**
- Execute semantic search against Qdrant
- Apply similarity threshold filtering
- Fetch multiplier control (quality vs speed)
- Optional LLM reranking
- Generate natural language answers via OpenRouter
- Format results with source citations

**Query Pipeline:**
```
1. Embed query text (sentence-transformers)
2. Search Qdrant (fetch_multiplier × limit results)
3. Filter by similarity threshold (default: 0.3)
4. Optionally rerank with LLM
5. Send top chunks to OpenRouter
6. Generate answer with citations
7. Return RAGResult (answer, sources, metadata)
```

**Key Functions:**
- `perform_rag_query()` - Main entry point (CLI + GUI + agents)
- `search_qdrant()` - Semantic search with filters
- `generate_answer()` - OpenRouter API integration
- `format_context()` - Prepare chunks for LLM

**Configuration:**
- `fetch_multiplier` (default: 3) - How many extra results to fetch
- `similarity_threshold` (default: 0.3) - Minimum relevance score
- `temperature` (default: 0.7) - LLM creativity control
- `reranking` (default: False) - Enable LLM reranking

**Integration Points:**
- → Collection Management (verify collection exists)
- → Qdrant (semantic search)
- → OpenRouter (answer generation)

**Related Story:** [03-RAG_QUERY.md](../../stories/03-RAG_QUERY.md)

---

### 4. Collection Management
**Files:** `collection_manifest.py`, `qdrant_utils.py`
**Purpose:** Track ingested books and manage Qdrant collections

**Responsibilities:**
- Maintain per-collection manifests (JSON/CSV)
- Track ingestion progress for resume
- Verify collection exists in Qdrant
- Collection operations (stats, search, copy, delete)
- Auto-reset manifests when collection deleted
- CSV export for human-readable reports

**Manifest Structure:**
```json
{
  "created_at": "2026-01-23T...",
  "last_updated": "2026-01-23T...",
  "books": [
    {
      "file_path": "c:/path/to/book.epub",
      "book_title": "Title",
      "author": "Author",
      "domain": "technical",
      "language": "ENG",
      "file_type": "EPUB",
      "chunks_count": 153,
      "file_size_mb": 34.2,
      "ingested_at": "2026-01-23T..."
    }
  ],
  "total_chunks": 153,
  "total_size_mb": 34.2
}
```

**Key Functions:**
- `log_book()` - Add book to manifest
- `is_book_ingested()` - Check if already processed
- `show_manifest()` - Display collection contents
- `export_to_csv()` - Human-readable export
- `verify_collection_exists()` - Auto-reset on deletion

**Files:**
- `logs/{collection_name}_manifest.json` - Master manifest
- `logs/{collection_name}_manifest.csv` - CSV export
- `scripts/batch_ingest_progress_{collection_name}.json` - Resume tracker

**Integration Points:**
- ← Ingestion Engine (logs new books)
- ← RAG Query Engine (checks collection status)
- → File System (reads/writes manifests)
- → Qdrant (collection operations)

**Related Story:** [06-COLLECTION_MANAGEMENT.md](../../stories/06-COLLECTION_MANAGEMENT.md)
**Related ADR:** [ADR 0004: Collection-Specific Manifests](../decisions/0004-collection-specific-manifests.md)

---

### 5. Calibre Integration
**Files:** `calibre_db.py`
**Purpose:** Direct SQLite access to Calibre library

**Responsibilities:**
- Query Calibre metadata.db directly
- Extract book metadata (title, author, series, tags, languages)
- Match files to books (fuzzy matching)
- Provide file paths for direct ingestion
- Library statistics (books, authors, formats, languages)

**CalibreBook Dataclass:**
```python
@dataclass
class CalibreBook:
    id: int
    title: str
    authors: List[str]
    formats: List[str]  # ['EPUB', 'PDF', 'MOBI']
    file_paths: List[str]
    languages: List[str]  # ISO codes
    tags: List[str]
    series: Optional[str]
    series_index: Optional[float]
    isbn: Optional[str]
    rating: Optional[int]
    timestamp: str
```

**Key Functions:**
- `get_all_books()` - Load entire library (~9,000 books in <2s)
- `search_books()` - Filter by author, title, language, format, tags
- `match_file_to_book()` - Find book by file path
- `get_stats()` - Library statistics

**Integration Points:**
- ← GUI (browse library)
- → Calibre Database (read-only queries)
- → Ingestion Engine (provides book paths)

**Related Story:** [05-CALIBRE_INTEGRATION.md](../../stories/05-CALIBRE_INTEGRATION.md)

---

## Component Interactions

### Ingestion Flow
```
Calibre Integration → Ingestion Engine (book path + metadata)
Ingestion Engine → Universal Semantic Chunker (split by semantic similarity)
Universal Semantic Chunker → Embedder (generate chunk embeddings)
Ingestion Engine → Collection Management (log to manifest)
Ingestion Engine → Qdrant (upload chunks with metadata)
```

### Query Flow
```
RAG Query Engine → Collection Management (verify collection)
RAG Query Engine → Qdrant (semantic search)
RAG Query Engine → OpenRouter (generate answer)
```

### Browse Flow
```
Calibre Integration → Calibre Database (query books)
Calibre Integration → GUI (return book list)
```

---

## Design Patterns

### 1. **Module Pattern**
Each component is a standalone Python module with clear interface.
- Single entry point function (e.g., `perform_rag_query()`)
- Usable by GUI, CLI, and AI agents
- No circular dependencies

### 2. **Configuration via Files**
- `domains.json` - Domain list and chunking config
- `{collection}_manifest.json` - Persistent state
- `.streamlit/secrets.toml` - API keys

### 3. **Progressive Enhancement**
- Basic ingestion works without Calibre DB
- RAG query works without OpenRouter (search-only mode)
- GUI optional (CLI works standalone)

---

## Related Views

- **Previous Level:** [Container Diagram](02-container.md)
- **Stories:** [All feature stories](../../stories/)
- **Code:** See `scripts/` directory for implementation

---

**Last Updated:** 2026-01-23
