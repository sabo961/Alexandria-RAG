# Qdrant Payload Structure

**Purpose:** Document how book content is structured in Qdrant vector database.

---

## Payload Creation Flow

### Pipeline Overview

```
Book File (EPUB/PDF/TXT)
    ↓
1. EXTRACT TEXT → Sections with metadata
    ↓
2. CHUNK TEXT → Chunks with context
    ↓
3. GENERATE EMBEDDINGS → 384-dim vectors
    ↓
4. UPLOAD TO QDRANT → Points with payload
```

---

## Payload Structure

### Hierarchical Chunking (Current - 2026-01-30)

Alexandria uses **two-level hierarchical chunking**:
- **Parent chunks**: One per chapter/section (for context)
- **Child chunks**: Semantic chunks within each chapter (for precise retrieval)

#### Parent Chunk Payload

```json
{
  "id": "uuid",
  "vector": [0.123, -0.456, ...],
  "payload": {
    "text": "Chapter text truncated to ~8192 tokens for embedding...",
    "book_title": "Thinking, Fast and Slow",
    "author": "Daniel Kahneman",
    "language": "eng",
    "section_name": "Part I: Two Systems",

    // Hierarchical fields
    "chunk_level": "parent",
    "section_index": 1,
    "child_count": 43,
    "token_count": 8500,
    "full_text": "Complete untruncated chapter text...",

    // Ingestion metadata
    "ingested_at": "2026-01-30T12:00:00",
    "strategy": "hierarchical"
  }
}
```

#### Child Chunk Payload

```json
{
  "id": "uuid",
  "vector": [0.123, -0.456, ...],
  "payload": {
    "text": "Semantic chunk text (200-1200 words)...",
    "book_title": "Thinking, Fast and Slow",
    "author": "Daniel Kahneman",
    "language": "eng",
    "section_name": "Part I: Two Systems",

    // Hierarchical fields
    "chunk_level": "child",
    "parent_id": "uuid-of-parent-chunk",
    "sequence_index": 5,
    "sibling_count": 43,
    "token_count": 350,

    // Ingestion metadata
    "ingested_at": "2026-01-30T12:00:00",
    "strategy": "hierarchical"
  }
}
```

### Legacy Flat Structure (Pre-2026-01-30)

For older ingestions without hierarchical chunking:

```json
{
  "id": 0,
  "vector": [0.123, -0.456, ...],  // 384-dimensional embedding
  "payload": {
    // Core Content
    "text": "Table of Contents Title Page Copyright Dedication ...",
    "text_length": 575,

    // Book Metadata
    "book_title": "The Data Model Resource Book Vol 3: Universal Patterns...",
    "author": "Len Silverston",
    "domain": "technical",
    "language": "eng",

    // Location Metadata
    "section_name": "9781118080832toc.xhtml",
    "section_order": 1,
    "chunk_id": 0,

    // Ingestion Metadata
    "ingested_at": "2026-01-21T18:14:12.363110",
    "chunk_strategy": "technical-overlap",
    "embedding_model": "all-MiniLM-L6-v2",

    // Open WebUI Compatibility
    "metadata": {
      "source": "The Data Model Resource Book Vol 3: Universal Patterns...",
      "section": "9781118080832toc.xhtml",
      "domain": "technical",
      "language": "eng"
    }
  }
}
```

---

## Field-by-Field Explanation

### Core Content Fields

#### `text` (string)
**Source:** Extracted from book file, chunked based on domain strategy
**Purpose:** The actual content text that will be searched
**Example:** "Table of Contents Title Page Copyright Dedication ..."

**How it's created:**
```python
# From chunk_text() function
chunk = {
    'text': text_segment,  # Extracted from book
    'token_count': get_token_count(text_segment),
    ...
}
```

#### `text_length` (integer)
**Source:** Token count using tiktoken (cl100k_base encoding)
**Purpose:** Track chunk size for monitoring/optimization
**Example:** 575

**How it's calculated:**
```python
def get_token_count(text: str) -> int:
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))
```

---

### Hierarchical Fields (New in 2026-01-30)

#### `chunk_level` (string)
**Source:** Set during hierarchical ingestion
**Values:** `"parent"` or `"child"`
**Purpose:** Distinguish chapter-level chunks from semantic chunks

#### `parent_id` (string, child only)
**Source:** UUID of parent chunk
**Purpose:** Link child chunk to its parent chapter
**Usage:** Fetch parent context via `fetch_parent_chunks()`

#### `sequence_index` (integer, child only)
**Source:** Order within parent (0-indexed)
**Purpose:** Maintain reading order within chapter
**Example:** `5` means 6th chunk in chapter

#### `sibling_count` (integer, child only)
**Source:** Total children in same parent
**Purpose:** Know total chunks in chapter
**Example:** `43` means 43 total chunks in chapter

#### `section_index` (integer, parent only)
**Source:** Chapter order in book (0-indexed)
**Purpose:** Maintain chapter order
**Example:** `0` = first chapter, `1` = second chapter

#### `child_count` (integer, parent only)
**Source:** Number of child chunks created
**Purpose:** Track children without querying

#### `full_text` (string, parent only)
**Source:** Complete untruncated chapter text
**Purpose:** Provide full context when needed
**Note:** `text` field is truncated to ~8192 tokens for embedding

#### `strategy` (string)
**Source:** Set during ingestion
**Values:** `"hierarchical"` or `"universal-semantic"`
**Purpose:** Identify chunking approach used

---

### Book Metadata Fields

#### `book_title` (string)
**Source:** Extracted from book metadata (EPUB/PDF metadata or filename)
**Purpose:** Identify which book the chunk came from
**Example:** "The Data Model Resource Book Vol 3: Universal Patterns for Data Modeling"

**How it's extracted:**
```python
# EPUB
book = epub.read_epub(filepath)
metadata['title'] = book.get_metadata('DC', 'title')[0][0]

# PDF
doc = fitz.open(filepath)
metadata['title'] = doc.metadata.get('title', Path(filepath).stem)
```

#### `author` (string)
**Source:** Extracted from book metadata or set to "Unknown"
**Purpose:** Attribution and filtering by author
**Example:** "Len Silverston"

#### `language` (string)
**Source:** Calibre metadata or EPUB/PDF metadata
**Purpose:** Identify language for filtering and analysis
**Example:** `"eng"`, `"hrv"`, `"jpn"`

---

### Location Metadata Fields

#### `section_name` (string)
**Source:** Chapter/page identifier from book structure
**Purpose:** Navigate back to source location in original book
**Examples:**
- EPUB: `"9781118080832toc.xhtml"` (chapter HTML file)
- PDF: `"119"` (page number)
- TXT: `"filename.txt"` (file name)

#### `section_order` (integer)
**Source:** Sequential order of section in book
**Purpose:** Maintain reading order for context
**Example:** `1` (first section), `2` (second section), etc.

#### `chunk_id` (integer)
**Source:** Sequential ID within section
**Purpose:** Track chunk position within section
**Example:** `0` (first chunk in section), `1` (second chunk), etc.

---

### Ingestion Metadata Fields

#### `ingested_at` (ISO 8601 timestamp)
**Source:** `datetime.now().isoformat()` at upload time
**Purpose:** Track when data was ingested, useful for versioning
**Example:** `"2026-01-21T18:14:12.363110"`

#### `chunk_strategy` (string)
**Source:** Constructed from domain + "overlap"
**Purpose:** Track which chunking strategy was used
**Format:** `"{domain}-overlap"`
**Examples:**
- `"technical-overlap"` (1500-2000 tokens, 200 overlap)
- `"psychology-overlap"` (1000-1500 tokens, 150 overlap)

#### `embedding_model` (string)
**Source:** Hardcoded model name
**Purpose:** Track which embedding model generated vectors
**Example:** `"all-MiniLM-L6-v2"`

---

### Open WebUI Compatibility

#### `metadata` (object)
**Source:** Duplicate of key fields for Open WebUI
**Purpose:** Ensure compatibility with Open WebUI RAG interface
**Structure:**
```json
{
  "source": "book_title",
  "section": "section_name",
  "domain": "domain",
  "language": "language"
}
```

**Why it exists:** Open WebUI expects metadata in this nested format for citation display.

---

## Code Location

### Where Payload is Created

**File:** `scripts/ingest_books.py`
**Function:** `upload_to_qdrant()` (lines 354-418)

```python
def upload_to_qdrant(
    chunks: List[Dict],
    embeddings: List[List[float]],
    domain: str,
    collection_name: str = 'alexandria',
    qdrant_host: str = 'localhost',
    qdrant_port: int = 6333
):
    # ...

    for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        point = PointStruct(
            id=idx,
            vector=embedding,
            payload={
                # Core content
                "text": chunk['text'],
                "text_length": chunk['token_count'],

                # Book metadata
                "book_title": chunk['book_title'],
                "author": chunk['book_author'],
                "domain": domain,
                "language": chunk.get('language', 'unknown'),

                # Location metadata
                "section_name": chunk['section_name'],
                "section_order": chunk['section_order'],
                "chunk_id": chunk['chunk_id'],

                # Ingestion metadata
                "ingested_at": datetime.now().isoformat(),
                "chunk_strategy": f"{domain}-overlap",
                "embedding_model": "all-MiniLM-L6-v2",

                # Open WebUI compatibility
                "metadata": {
                    "source": chunk['book_title'],
                    "section": chunk['section_name'],
                    "domain": domain,
                    "language": chunk.get('language', 'unknown')
                }
            }
        )
        points.append(point)
```

---

## Data Flow Example

### Step-by-Step for EPUB

#### 1. Extract Text
```python
# From extract_text_from_epub()
chapters = [{
    'name': '9781118080832toc.xhtml',
    'text': 'Table of Contents Title Page Copyright...',
    'order': 1
}]

metadata = {
    'title': 'The Data Model Resource Book Vol 3...',
    'author': 'Len Silverston',
    'language': 'eng'
}
```

#### 2. Chunk Text
```python
# From chunk_text()
chunk = {
    'text': 'Table of Contents Title Page...',
    'token_count': 575,
    'section_name': '9781118080832toc.xhtml',
    'section_order': 1,
    'chunk_id': 0,
    'book_title': 'The Data Model Resource Book Vol 3...',
    'book_author': 'Len Silverston',
    'language': 'eng'
}
```

#### 3. Generate Embedding
```python
# From EmbeddingGenerator
embedding = [0.123, -0.456, ...]  # 384 dimensions
```

#### 4. Create Qdrant Point
```python
# From upload_to_qdrant()
point = PointStruct(
    id=0,
    vector=embedding,  # 384-dim vector
    payload={
        "text": chunk['text'],
        "text_length": 575,
        "book_title": "The Data Model Resource Book Vol 3...",
        "author": "Len Silverston",
        "domain": "technical",
        "language": "eng",
        "section_name": "9781118080832toc.xhtml",
        "section_order": 1,
        "chunk_id": 0,
        "ingested_at": "2026-01-21T18:14:12.363110",
        "chunk_strategy": "technical-overlap",
        "embedding_model": "all-MiniLM-L6-v2",
        "metadata": {
            "source": "The Data Model Resource Book Vol 3...",
            "section": "9781118080832toc.xhtml",
            "domain": "technical",
            "language": "eng"
        }
    }
)
```

---

## Differences: PDF vs EPUB

### EPUB Payload
```json
{
  "section_name": "9781118080832c01.xhtml",  // Chapter HTML file
  "section_order": 1,                         // Chapter 1
  "chunk_id": 0,                              // First chunk in chapter
  "text_length": 1450                         // ~1450 tokens (large chunk)
}
```

### PDF Payload
```json
{
  "section_name": "119",       // Page number
  "section_order": 119,        // Page 119
  "chunk_id": 0,               // Only chunk on that page
  "text_length": 200           // ~200 tokens (page-based chunk)
}
```

**Key Difference:** PDFs use page numbers as sections, EPUBs use chapter files.

---

## Querying Payload Fields

### Filter by Domain
```python
from qdrant_client.models import Filter, FieldCondition, MatchValue

results = client.query_points(
    collection_name="alexandria",
    query=query_vector,
    query_filter=Filter(
        must=[FieldCondition(key="domain", match=MatchValue(value="technical"))]
    )
)
```

### Filter by Book
```python
results = client.query_points(
    collection_name="alexandria",
    query=query_vector,
    query_filter=Filter(
        must=[FieldCondition(key="book_title", match=MatchValue(value="Silverston"))]
    )
)
```

### Filter by Author
```python
results = client.query_points(
    collection_name="alexandria",
    query=query_vector,
    query_filter=Filter(
        must=[FieldCondition(key="author", match=MatchValue(value="Len Silverston"))]
    )
)
```

---

## Modifying Payload Structure

### Adding New Fields

**Location:** `scripts/ingest_books.py`, line ~377

```python
payload={
    # Existing fields...

    # Add your custom field here
    "custom_field": "custom_value",
}
```

### Example: Add ISBN Field

```python
# In upload_to_qdrant()
payload={
    "text": chunk['text'],
    "text_length": chunk['token_count'],
    "book_title": chunk['book_title'],
    "author": chunk['book_author'],
    "domain": domain,

    # NEW: Add ISBN
    "isbn": chunk.get('isbn', 'N/A'),  # Add to chunk dict earlier

    # ... rest of fields
}
```

---

## Best Practices

### 1. Keep Payload Lean
- ❌ Don't duplicate data unnecessarily
- ✅ Store only what's needed for search/filter/display

### 2. Use Consistent Field Names
- ❌ `book_title`, `bookTitle`, `title` (inconsistent)
- ✅ `book_title` (snake_case, consistent)

### 3. Include Timestamps
- ✅ `ingested_at` allows versioning and tracking

### 4. Preserve Source Location
- ✅ `section_name` + `section_order` + `chunk_id` = exact location

### 5. Tag Ingestion Strategy
- ✅ `chunk_strategy` + `embedding_model` = reproducibility

---

## Summary

**Payload Structure Creation:**
1. Extract text from book → sections with metadata
2. Chunk text → chunks with location info
3. Generate embeddings → 384-dim vectors
4. Combine into Qdrant point → vector + payload

**Key Payload Components:**
- **Content:** `text`, `text_length`
- **Book Info:** `book_title`, `author`, `domain`, `language`
- **Location:** `section_name`, `section_order`, `chunk_id`
- **Tracking:** `ingested_at`, `chunk_strategy`, `embedding_model`
- **Compatibility:** `metadata` (nested, for Open WebUI)

**Code Location:** `scripts/ingest_books.py` → `upload_to_qdrant()` function

---

**Last Updated:** 2026-01-30 (Added hierarchical chunking payload structure)
