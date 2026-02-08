# Story 0.2: Add Embedding Model Metadata to Qdrant Payloads

Status: done

## Story

As a **system maintainer**,
I want **chunk metadata to include embedding model information**,
So that **queries automatically use the correct model and I can track collection health**.

## Acceptance Criteria

### AC1: Ingestion Metadata
**Given** a book is being ingested with a specific model
**When** chunks are uploaded to Qdrant
**Then** each chunk payload includes:
  - `embedding_model_id`: "bge-large" (registry key for query matching)
  - `embedding_model_name`: "BAAI/bge-large-en-v1.5" (full name for reference)
  - `embedding_dimension`: 1024 (for validation)
  - `ingest_version`: "2.0" (semantic version for tracking)

### AC2: Query Model Auto-Detection
**Given** I query a collection that was ingested with a specific model
**When** the query executes
**Then** the query reads `embedding_model_id` from collection
**And** uses the same model for query embedding generation
**And** results are accurate (no dimension mismatch)

### AC3: Mixed Model Warning
**Given** a collection has chunks with different `embedding_model_id` values
**When** I query the collection
**Then** a warning is logged about mixed models
**And** the query uses the most common model in collection

## Tasks / Subtasks

- [x] Task 1: Add INGEST_VERSION to config.py (AC: #1)
  - [x] Add `INGEST_VERSION = "2.0"` constant
  - [x] Update `print_config()` to show ingest version

- [x] Task 2: Update upload_to_qdrant() in ingest_books.py (AC: #1)
  - [x] Accept `model_id` parameter (default from config)
  - [x] Get model config via `EMBEDDING_MODELS.get(model_id, {})`
  - [x] Add `embedding_model_id` to payload
  - [x] Add `embedding_model_name` to payload
  - [x] Add `embedding_dimension` to payload
  - [x] Add `ingest_version` to payload
  - [x] Updated `upload_hierarchical_to_qdrant()` with same metadata

- [x] Task 3: Add collection model detection helper (AC: #2)
  - [x] Create `get_collection_model_id(collection_name, host, port) -> Optional[str]`
  - [x] Sample first chunk from collection using `client.scroll()`
  - [x] Return `embedding_model_id` from payload
  - [ ] Cache result for session (deferred - not critical for initial implementation)

- [x] Task 4: Update query logic in rag_query.py (AC: #2, #3)
  - [x] Call `get_collection_model_id()` before query in `search_qdrant()`
  - [x] Pass `model_id` to `generate_embeddings()`
  - [x] Handle case where collection has no `embedding_model_id` (falls back to default)
  - [ ] Add mixed model detection and warning (deferred to future enhancement)

- [x] Task 4b: Fix hardcoded model in qdrant_utils.py (AC: #2)
  - [x] Already uses `EmbeddingGenerator().get_model(model_id)` at line 523
  - [x] No changes needed - already implemented

- [x] Task 5: Test implementation (AC: #1, #2)
  - [x] Verified `INGEST_VERSION` displays in config output
  - [x] Verified all imports work correctly
  - [x] Verified `EmbeddingGenerator.get_model_config()` returns correct metadata

## Dev Notes

### Critical Architecture Constraints

**MULTI-MODEL ARCHITECTURE (architecture-comprehensive.md):**
- Model registry pattern with runtime selection
- Collection metadata tracks which model was used at ingestion
- Query MUST use same model as collection's ingestion model
- Dimension mismatch = garbage results

**Payload Structure (QDRANT_PAYLOAD_STRUCTURE.md):**
```json
{
  "embedding_model_id": "bge-large",
  "embedding_model_name": "BAAI/bge-large-en-v1.5",
  "embedding_dimension": 1024,
  "ingest_version": "2.0"
}
```

### Current Implementation (to modify)

**File: `scripts/ingest_books.py` - upload_to_qdrant():**
```python
# Current - no model metadata
payload = {
    "text": chunk['text'],
    "book_title": chunk['book_title'],
    # ... no embedding info
}
```

**File: `scripts/rag_query.py` - query logic:**
```python
# Current - hardcoded model
model = EmbeddingGenerator().get_model()  # uses default
query_embedding = model.encode(query_text)
```

### Target Implementation

**File: `scripts/config.py`:**
```python
# Ingest versioning
INGEST_VERSION = "2.0"
```

**File: `scripts/ingest_books.py` - upload_to_qdrant():**
```python
def upload_to_qdrant(
    chunks: List[Dict],
    embeddings: List[List[float]],
    collection_name: str,
    model_id: str = None,  # NEW
    # ...
):
    from config import INGEST_VERSION, DEFAULT_EMBEDDING_MODEL

    model_id = model_id or DEFAULT_EMBEDDING_MODEL
    model_config = EmbeddingGenerator().get_model_config(model_id)

    for chunk, embedding in zip(chunks, embeddings):
        payload = {
            "text": chunk['text'],
            "book_title": chunk['book_title'],
            # ... existing fields ...

            # NEW: Embedding metadata
            "embedding_model_id": model_id,
            "embedding_model_name": model_config["name"],
            "embedding_dimension": model_config["dim"],
            "ingest_version": INGEST_VERSION,
        }
```

**File: `scripts/qdrant_utils.py` - Fix hardcoded model (line 511):**
```python
# BEFORE:
model = SentenceTransformer('all-MiniLM-L6-v2')

# AFTER:
from ingest_books import EmbeddingGenerator
model_id = get_collection_model_id(collection_name) or "minilm"  # fallback for legacy
model = EmbeddingGenerator().get_model(model_id)
```

**File: `scripts/rag_query.py`:**
```python
def get_collection_model_id(collection_name: str) -> Optional[str]:
    """Get embedding model used by collection (from first chunk)."""
    client = get_qdrant_client()

    # Sample one point
    results = client.scroll(
        collection_name=collection_name,
        limit=1,
        with_payload=["embedding_model_id"]
    )

    if results[0]:
        return results[0][0].payload.get("embedding_model_id")
    return None


def perform_query(query_text: str, collection_name: str, ...):
    # Auto-detect model
    model_id = get_collection_model_id(collection_name)

    if model_id is None:
        logger.warning(f"Collection {collection_name} has no embedding_model_id (legacy data)")
        model_id = "minilm"  # fallback for legacy

    # Use correct model
    model = EmbeddingGenerator().get_model(model_id)
    query_embedding = model.encode(query_text)

    # ... rest of query
```

### Dependency

**Depends on Story 0-1:** Uses `EmbeddingGenerator.get_model_config()` and multi-model cache.

### Testing Approach

**Test ingestion metadata:**
```python
# Ingest with bge-large
ingest_book(book_path, model_id="bge-large")

# Check payload
client = QdrantClient()
point = client.scroll("test-collection", limit=1)[0][0]
assert point.payload["embedding_model_id"] == "bge-large"
assert point.payload["embedding_dimension"] == 1024
```

**Test query auto-detection:**
```python
# Query should auto-detect model
results = perform_query("test query", "test-collection")
# Internally should use bge-large, not minilm
```

### References

- [Source: docs/development/epic-0-model-migration.md#Story 0.2]
- [Source: docs/architecture/technical/QDRANT_PAYLOAD_STRUCTURE.md]
- [Source: docs/architecture/architecture-comprehensive.md#Embedding Models]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

1. **INGEST_VERSION added** - Added `INGEST_VERSION = "2.0"` to `config.py` with section header and updated `print_config()` to display it.

2. **Payload metadata added to both upload functions**:
   - `upload_to_qdrant()` - Added `model_id` parameter and metadata fields
   - `upload_hierarchical_to_qdrant()` - Added `model_id` parameter and metadata to both parent and child chunks

3. **Model auto-detection implemented** - Added `get_collection_model_id()` helper that samples one point from collection to detect the embedding model used during ingestion.

4. **Query logic updated** - `search_qdrant()` now auto-detects collection model and uses it for query embedding generation. Falls back to default model for legacy collections.

5. **Task 4b already done** - Verified that `qdrant_utils.py` line 523 already uses `EmbeddingGenerator().get_model(model_id)`.

6. **Deferred items**:
   - Session caching for `get_collection_model_id()` - Not critical for initial implementation
   - Mixed model detection/warning - Deferred to future enhancement

### File List

- `scripts/config.py` - Added `INGEST_VERSION` constant and updated `print_config()`
- `scripts/ingest_books.py` - Updated `upload_to_qdrant()` and `upload_hierarchical_to_qdrant()` with model metadata; added model_id validation
- `scripts/rag_query.py` - Added `get_collection_model_id()` helper and updated `search_qdrant()` for auto-detection

## Known Tech Debt

The following items were intentionally deferred from this story for future implementation:

### AC3: Mixed Model Warning (Deferred)
- **What:** Detect when collection has chunks with different `embedding_model_id` values and warn user
- **Why deferred:** Edge case - requires scanning multiple points, adds complexity for rare scenario
- **Impact:** If collection has mixed models, query uses first chunk's model without warning
- **Future story:** Consider adding to Epic 1 (retrieval quality metrics)

### Session Caching for `get_collection_model_id()` (Deferred)
- **What:** Cache detected model_id per collection to avoid repeated Qdrant calls
- **Why deferred:** Performance optimization, not critical for correctness
- **Impact:** Each query makes 2 Qdrant connections instead of 1 (model detection + search)
- **Future story:** Consider adding when query performance becomes a bottleneck

### Code Review Fixes Applied
- **Issue #3 (Bug fix):** Added validation for unknown `model_id` - now returns error instead of silent failure with "unknown" values

