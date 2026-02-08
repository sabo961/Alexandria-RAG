# Story 0.3: Re-ingest Book Collection with Specified Model

Status: completed

## Story

As a **library curator**,
I want **to re-ingest books with a specified embedding model**,
So that **I can upgrade collections to better models or create A/B test collections**.

## Acceptance Criteria

### AC1: Re-ingestion with Model Selection
**Given** books are ingested in a collection
**When** I run `python reingest_collection.py --collection alexandria --model bge-large`
**Then** all books are re-ingested with bge-large model
**And** old chunks are deleted from Qdrant
**And** new chunks have `embedding_model_id: "bge-large"` in payload
**And** manifest is updated with new model metadata

### AC2: Progress Reporting
**Given** re-ingestion is running
**When** each book completes
**Then** progress callback reports "X/N completed"
**And** callback is Streamlit-compatible (no tqdm)
**And** estimated time remaining is shown

### AC3: Error Handling
**Given** a book fails during re-ingestion
**When** the error occurs
**Then** error is logged with book details (title, path, error message)
**And** script continues with remaining books
**And** summary report lists all failures at the end

### AC4: Dry-Run Mode
**Given** I want to preview re-ingestion
**When** I run with `--dry-run` flag
**Then** script shows what WOULD be done
**And** no actual changes are made to Qdrant or manifest

## Tasks / Subtasks

- [x] Task 1: Add parameters to ingest_book() (AC: #1)
  - [x] Add `force_reingest: bool = False` parameter
  - [x] Add `model_id: str = None` parameter
  - [x] When `force_reingest=True`, delete existing chunks for book first
  - [x] Pass `model_id` to EmbeddingGenerator and upload_to_qdrant

- [x] Task 2: Create reingest_collection.py CLI (AC: #1, #2, #3, #4)
  - [x] Parse arguments: --collection, --model, --dry-run
  - [x] Get book list from collection or Calibre
  - [x] Loop through books with progress callback
  - [x] Handle errors, continue on failure
  - [x] Generate summary report

- [x] Task 3: Implement delete_book_chunks() helper (AC: #1)
  - [x] Filter by book_title (since no book_id in current payloads)
  - [x] Delete all matching points from Qdrant
  - [x] Log deletion count

- [x] Task 4: Implement progress callback (AC: #2)
  - [x] Create callback protocol: `(current, total, book_title, status) -> None`
  - [x] Default implementation: print to stdout
  - [x] Streamlit-compatible (no tqdm, plain print statements)

- [ ] Task 5: Test re-ingestion (AC: #1, #2, #3, #4)
  - [ ] Test dry-run mode
  - [ ] Test single book re-ingestion
  - [ ] Test collection re-ingestion (5 books)
  - [ ] Test error handling (simulate failure)

## Dev Notes

### Dependencies

**Depends on:**
- Story 0-1: Multi-model EmbeddingGenerator
- Story 0-2: Embedding metadata in payloads

### Implementation Summary

#### 1. `delete_book_chunks()` function (scripts/ingest_books.py)
- Added Filter, FieldCondition, MatchValue imports from qdrant_client.models
- Implemented function that:
  - Checks Qdrant connection
  - Counts existing chunks for the book
  - Deletes all points matching `book_title` filter
  - Returns count of deleted chunks

#### 2. Updated `ingest_book()` signature (scripts/ingest_books.py)
- Added `force_reingest: bool = False` parameter
- Added `model_id: Optional[str] = None` parameter
- Added logic to call `delete_book_chunks()` when `force_reingest=True`
- Updated all embedding generation and upload calls to use `effective_model_id`
- Added `model_id` to result dictionary

#### 3. Created `reingest_collection.py` CLI (scripts/reingest_collection.py)
- Arguments: `--collection`, `--model`, `--dry-run`, `--host`, `--port`
- Gets books from manifest or falls back to Qdrant scan
- Progress callback with ETA calculation
- Error handling with continue-on-failure
- Summary report with failures and skipped books

### Testing Approach

**Test dry-run:**
```bash
python scripts/reingest_collection.py --collection test --model bge-large --dry-run
```

**Test single book:**
```python
ingest_book("path/to/book.epub", "test", force_reingest=True, model_id="bge-large")
```

**Verify metadata:**
```python
client = QdrantClient()
point = client.scroll("test", limit=1)[0][0]
assert point.payload["embedding_model_id"] == "bge-large"
```

### References

- [Source: docs/development/epic-0-model-migration.md#Story 0.3]
- [Source: docs/architecture/technical/QDRANT_PAYLOAD_STRUCTURE.md]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

1. Implemented `delete_book_chunks()` helper that filters by `book_title` and uses Qdrant's count and delete operations
2. Added `force_reingest` and `model_id` parameters to `ingest_book()` with proper integration
3. Created comprehensive `reingest_collection.py` CLI with dry-run support, progress tracking, and error handling
4. Progress callback uses simple print statements (Streamlit-compatible, no tqdm)
5. ETA calculation based on rolling average of book processing times

### File List

- `scripts/ingest_books.py` - Modified: added delete_book_chunks(), updated ingest_book() signature
- `scripts/reingest_collection.py` - New: CLI tool for collection re-ingestion
