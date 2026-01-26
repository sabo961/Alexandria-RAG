# Alexandria Data Models & API Reference

**Generated:** 2026-01-26
**Project:** Alexandria RAG System
**Scope:** Backend Python modules in `scripts/` package

---

## Overview

Alexandria uses a **modular architecture** with business logic separated into reusable Python modules. The main GUI (`alexandria_app.py`) is a thin layer that calls these scripts.

---

## Core Data Models

### CalibreBook (calibre_db.py)

Represents book metadata from Calibre library's SQLite database.

```python
@dataclass
class CalibreBook:
    id: int                          # Calibre internal book ID
    title: str                       # Book title
    author: str                      # Primary author(s), joined with " & "
    path: str                        # Relative path from library root
    language: str                    # ISO code (eng, hrv, jpn, etc.)
    tags: List[str]                  # Book tags/categories
    series: Optional[str]            # Series name (if part of series)
    series_index: Optional[float]    # Position in series
    isbn: Optional[str]              # ISBN identifier
    publisher: Optional[str]         # Publisher name
    pubdate: Optional[str]           # Publication date
    timestamp: str                   # Date added to Calibre
    rating: Optional[int]            # User rating (1-10 scale)
    formats: List[str]               # Available formats (.epub, .pdf, etc.)
```

**Used by:**
- Calibre integration tab in GUI
- Book ingestion metadata enrichment
- Collection manifests

---

### RAGResult (rag_query.py)

Represents search results from RAG query with optional LLM answer.

```python
@dataclass
class RAGResult:
    query: str                       # Original search query
    results: List[Dict]              # Qdrant search results
    answer: Optional[str] = None     # LLM-generated answer (if use_llm=True)
    reranked: bool = False           # Whether results were reranked by LLM
    llm_model: Optional[str] = None  # LLM model used (if any)
    total_time: Optional[float] = None   # Total query time in seconds
```

**Result Item Structure:**
```python
{
    'score': float,                  # Semantic similarity score (0-1)
    'title': str,                    # Book title
    'author': str,                   # Book author(s)
    'file_path': str,                # Source file path
    'text': str,                     # Chunk text content
    'metadata': dict                 # Additional metadata
}
```

---

### CollectionManifest (collection_manifest.py)

Tracks ingested books per Qdrant collection with metadata.

**Internal Structure:**
```python
{
    "collections": {
        "alexandria": {
            "collection_name": "alexandria",
            "created": "2026-01-20T10:30:00Z",
            "last_updated": "2026-01-26T15:45:00Z",
            "total_books": 42,
            "total_chunks": 3847,
            "books": [
                {
                    "file_path": "G:\\path\\to\\book.epub",
                    "title": "Book Title",
                    "author": "Author Name",
                    "ingested_at": "2026-01-20T12:00:00Z",
                    "chunk_count": 89,
                    "domain": "philosophy",
                    "language": "eng"
                }
            ]
        }
    }
}
```

**File Location:** `logs/collection_manifest_{collection_name}.json`

---

### UniversalChunker (universal_chunking.py)

Semantic chunking based on sentence embeddings and similarity thresholds.

```python
class UniversalChunker:
    def __init__(
        self,
        embedding_model,
        threshold: float = 0.5,      # Similarity threshold for splits
        min_chunk_size: int = 200,   # Minimum tokens per chunk
        max_chunk_size: int = 1200   # Maximum tokens per chunk
    )

    def chunk(self, text: str, domain: str = "general") -> List[str]:
        # Returns list of semantically coherent text chunks
```

**Domain-Specific Thresholds:**
- Philosophy: 0.45 (preserve arguments)
- Other domains: 0.55 (standard splitting)

---

## Module APIs

### 1. calibre_db.py - Calibre Library Interface

**Purpose:** Direct SQLite access to Calibre's metadata.db for book metadata.

**Public API:**

```python
class CalibreDB:
    def __init__(self, library_path: str = "G:\\My Drive\\alexandria")

    def get_all_books(self, limit: Optional[int] = None) -> List[CalibreBook]
        # Get all books with full metadata

    def search_books(
        self,
        title: str = None,
        author: str = None,
        language: str = None,
        tags: List[str] = None,
        series: str = None
    ) -> List[CalibreBook]
        # Search books by multiple criteria (fuzzy matching)

    def get_book_by_path(self, relative_path: str) -> Optional[CalibreBook]
        # Get book by Calibre path (e.g., "Author/Title")

    def get_book_by_id(self, book_id: int) -> Optional[CalibreBook]
        # Get book by Calibre internal ID

    def match_file_to_book(self, filename: str) -> Optional[CalibreBook]
        # Fuzzy match filename to Calibre book

    def get_available_languages(self) -> List[str]
        # Get all languages in library

    def get_available_tags(self) -> List[str]
        # Get all tags in library

    def get_available_series(self) -> List[str]
        # Get all series in library

    def get_stats(self) -> Dict
        # Get library statistics (total books, languages, tags, etc.)
```

**CLI Usage:**
```bash
python scripts/calibre_db.py
```

---

### 2. collection_manifest.py - Ingestion Tracking

**Purpose:** Track which books are ingested into which Qdrant collections.

**Public API:**

```python
class CollectionManifest:
    def __init__(self, collection_name: str)

    def add_book(
        self,
        file_path: str,
        title: str,
        author: str,
        chunk_count: int,
        domain: str,
        language: str
    )
        # Add book to manifest after successful ingestion

    def book_exists(self, file_path: str) -> bool
        # Check if book already ingested

    def get_book_count(self) -> int
        # Get total books in collection

    def get_chunk_count(self) -> int
        # Get total chunks in collection

    def export_to_csv(self, output_path: str)
        # Export manifest as CSV for human readability
```

**File Format:** JSON at `logs/collection_manifest_{collection_name}.json`

---

### 3. ingest_books.py - Book Ingestion Pipeline

**Purpose:** Extract text from EPUB/PDF, chunk, embed, upload to Qdrant.

**Main Function:**

```python
def ingest_book(
    filepath: str,
    domain: str,
    collection: str,
    host: str = '192.168.0.151',
    port: int = 6333
) -> Dict
    # Returns: {'success': bool, 'chunks': int, 'diagnostics': dict}
```

**Pipeline Steps:**
1. `extract_text(filepath)` → Raw text + metadata
2. `UniversalChunker().chunk()` → Semantic chunks
3. `generate_embeddings(chunks)` → 384-dim vectors
4. `upload_to_qdrant()` → Store in vector DB
5. `CollectionManifest.add_book()` → Track ingestion

**Helper Functions:**

```python
def normalize_file_path(filepath: str) -> Tuple[str, str, bool, int]
    # Handle Windows long paths (>248 chars) with \\?\ prefix

def extract_text(filepath: str) -> Tuple[str, Dict]
    # Extract text from EPUB/PDF + metadata

def extract_metadata_only(filepath: str) -> Dict
    # Get metadata without full text extraction

def generate_embeddings(texts: List[str]) -> List[List[float]]
    # Generate embeddings using all-MiniLM-L6-v2
```

**CLI Usage:**
```bash
python scripts/ingest_books.py path/to/book.epub --domain philosophy --collection alexandria
```

---

### 4. rag_query.py - Semantic Search & RAG

**Purpose:** Query Qdrant, optionally rerank and generate LLM answers.

**Main Function:**

```python
def perform_rag_query(
    query: str,
    collection: str,
    limit: int = 5,
    use_llm: bool = False,
    llm_model: str = "anthropic/claude-3-5-sonnet-20241022",
    rerank: bool = False,
    host: str = '192.168.0.151',
    port: int = 6333
) -> RAGResult
    # Returns: RAGResult with search results + optional LLM answer
```

**Pipeline Modes:**

1. **Vector Search Only** (use_llm=False, rerank=False)
   - Search Qdrant by semantic similarity
   - Return top-k chunks

2. **Vector Search + Reranking** (rerank=True)
   - Search Qdrant
   - Rerank results using LLM
   - Return reordered results

3. **Full RAG** (use_llm=True)
   - Search Qdrant
   - Optionally rerank
   - Generate LLM answer from context

**Helper Functions:**

```python
def search_qdrant(query, collection, limit, host, port) -> List[Dict]
    # Search Qdrant vector DB

def rerank_with_llm(query, results, llm_model) -> List[Dict]
    # Rerank results using LLM for relevance

def generate_answer(query, results, llm_model) -> str
    # Generate answer using RAG context

def print_results(result: RAGResult, format: str = 'markdown')
    # Format results for display
```

**CLI Usage:**
```bash
python scripts/rag_query.py "What does Mishima say about words vs body?" --collection alexandria --use-llm
```

---

### 5. qdrant_utils.py - Qdrant Operations

**Purpose:** Manage Qdrant collections (list, stats, copy, delete).

**Public API:**

```python
def list_collections(host: str = '192.168.0.151', port: int = 6333)
    # List all Qdrant collections with stats

def get_collection_stats(
    collection_name: str,
    host: str = '192.168.0.151',
    port: int = 6333
) -> Dict
    # Get detailed collection statistics

def copy_collection(
    source: str,
    destination: str,
    host: str = '192.168.0.151',
    port: int = 6333
)
    # Copy collection (all points + metadata)

def delete_collection_and_artifacts(
    collection_name: str,
    host: str,
    port: int
) -> dict
    # Delete Qdrant collection + manifest + logs

def delete_collection_preserve_artifacts(
    collection_name: str,
    host: str,
    port: int
) -> dict
    # Delete Qdrant collection, keep manifest/logs

def search_collection(
    collection_name: str,
    query_text: str,
    limit: int = 5,
    host: str = '192.168.0.151',
    port: int = 6333
) -> List[Dict]
    # Search collection (wrapper around rag_query)
```

**CLI Usage:**
```bash
python scripts/qdrant_utils.py --list
python scripts/qdrant_utils.py --stats alexandria
python scripts/qdrant_utils.py --copy alexandria alexandria_backup
```

---

### 6. universal_chunking.py - Semantic Chunking

**Purpose:** Chunk text using semantic similarity (ADR 0007).

**Public API:**

```python
class UniversalChunker:
    def __init__(
        self,
        embedding_model,
        threshold: float = 0.5,
        min_chunk_size: int = 200,
        max_chunk_size: int = 1200
    )

    def chunk(self, text: str, domain: str = "general") -> List[str]
        # Returns semantically coherent chunks
```

**Algorithm:**
1. Split text into sentences
2. Embed each sentence
3. Calculate cosine similarity between consecutive sentences
4. Split where similarity < threshold
5. Enforce min/max chunk sizes

**Domain-Specific Behavior:**
- Philosophy domain: threshold=0.45 (preserve philosophical arguments)
- Other domains: threshold=0.55 (standard splitting)

---

## Integration Points

### GUI → Scripts Flow

```
alexandria_app.py (Streamlit GUI)
    ↓
    ├─ Calibre Tab → calibre_db.CalibreDB
    ├─ Ingestion Tab → ingest_books.ingest_book()
    ├─ Query Tab → rag_query.perform_rag_query()
    └─ Collections Tab → qdrant_utils.list_collections()
```

### Data Flow (Ingestion)

```
Book File (.epub/.pdf)
    → ingest_books.extract_text()
    → UniversalChunker.chunk()
    → generate_embeddings()
    → upload_to_qdrant()
    → CollectionManifest.add_book()
```

### Data Flow (Query)

```
User Query
    → rag_query.search_qdrant()
    → [optional] rerank_with_llm()
    → [optional] generate_answer()
    → RAGResult
```

---

## External Dependencies

### Qdrant Vector Database
- **Host:** 192.168.0.151:6333 (external server)
- **Distance Metric:** COSINE (hardcoded)
- **Embedding Model:** all-MiniLM-L6-v2 (384-dimensional)
- **Collections:** Multiple collections supported

### Calibre Library
- **Default Path:** `G:\My Drive\alexandria`
- **Database:** `metadata.db` (SQLite)
- **Book Storage:** `Author/Title/` directory structure

### OpenRouter API
- **Purpose:** LLM calls for RAG answer generation
- **Models:** Claude 3.5 Sonnet, GPT-4, etc.
- **API Key:** Stored in `.streamlit/secrets.toml`

---

## File Locations

| Purpose | Path | Format |
|---------|------|--------|
| Collection Manifests | `logs/collection_manifest_{name}.json` | JSON |
| CSV Export | `logs/alexandria_manifest.csv` | CSV |
| Calibre DB | `G:\My Drive\alexandria\metadata.db` | SQLite |
| Qdrant Data | External server (192.168.0.151) | Vector DB |

---

## CLI Entry Points

All scripts support CLI usage for batch operations:

```bash
# Ingest book
python scripts/ingest_books.py book.epub --domain philosophy --collection alexandria

# Query
python scripts/rag_query.py "search query" --collection alexandria --use-llm

# Calibre stats
python scripts/calibre_db.py

# Qdrant management
python scripts/qdrant_utils.py --list
python scripts/qdrant_utils.py --stats alexandria

# Generate inventory
python scripts/generate_book_inventory.py
```

---

**Related Documentation:**
- [Architecture Overview](architecture/ARCHITECTURE_SUMMARY.md)
- [ADR 0003: GUI as Thin Layer](architecture/decisions/0003-gui-as-thin-layer.md)
- [ADR 0007: Universal Semantic Chunking](architecture/decisions/0007-universal-semantic-chunking.md)
