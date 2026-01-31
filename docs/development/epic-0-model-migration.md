---
epic: 0
title: "bge-large Model Migration"
status: pending
priority: P0
estimated_stories: 3
---

# Epic 0: bge-large Model Migration

**FIRST PRIORITY** - Migrate embedding model to bge-large-en-v1.5 for superior search quality. GPU acceleration is a bonus (10x speedup), but quality improvement is the primary goal.

**User Outcome:** Users experience dramatically improved search relevance and precision when querying the book collection.

**FRs Covered:** FR-001 (partial - model upgrade), NFR-001 (performance), NFR-002 (immutability window)

**ADR References:** ADR-0010 (GPU-Accelerated Embeddings)

**Current State:**
- Using `all-MiniLM-L6-v2` (384-dim, CPU-only)
- Model hardcoded in `scripts/ingest_books.py:213`
- No GPU support
- No embedding model tracking in Qdrant payloads
- 150 books currently ingested

**Target State:**
- Using `bge-large-en-v1.5` (1024-dim, best-in-class)
- Configurable model selection
- GPU/CUDA support with CPU fallback
- Embedding model metadata tracked in Qdrant
- All 150 books re-ingested with new model

---

## Stories

### Story 0.1: Configure bge-large-en-v1.5 Model with GPU Support

**Status:** ⏳ PENDING

As a **system administrator**,
I want **to configure Alexandria to use bge-large-en-v1.5 with GPU acceleration**,
So that **embedding generation is both higher quality and 10x faster**.

**Acceptance Criteria:**

**Given** Alexandria is running on a machine with CUDA-capable GPU
**When** the embedding model is loaded
**Then** bge-large-en-v1.5 is used instead of all-MiniLM-L6-v2
**And** the model runs on GPU (CUDA) if available, falls back to CPU if not
**And** embedding dimension is 1024 (not 384)
**And** model selection is configurable via environment variable

**Given** Alexandria is running on a machine without GPU
**When** the embedding model is loaded
**Then** bge-large-en-v1.5 runs on CPU with graceful degradation
**And** a warning is logged about CPU-only mode
**And** embeddings are still generated correctly (slower but functional)

**Technical Tasks:**

- [ ] Add `EMBEDDING_MODEL` config variable to `scripts/config.py` (default: `BAAI/bge-large-en-v1.5`)
- [ ] Add `EMBEDDING_DEVICE` config variable (default: `auto` - detect GPU, fallback CPU)
- [ ] Install PyTorch with CUDA support: `pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118`
- [ ] Update `EmbeddingGenerator.get_model()` in `scripts/ingest_books.py` to:
  - Accept `model_name` parameter from config
  - Detect CUDA availability: `torch.cuda.is_available()`
  - Set device: `device = 'cuda' if torch.cuda.is_available() else 'cpu'`
  - Load model with device: `SentenceTransformer(model_name, device=device)`
  - Log model name, device, and embedding dimension
- [ ] Update `EmbeddingGenerator.generate_embeddings()` to verify output dimension is 1024
- [ ] Test embedding generation on sample text (verify CUDA usage via `nvidia-smi`)
- [ ] Document GPU setup in README.md (CUDA toolkit version, driver requirements)

**Files Modified:**
- `scripts/config.py` (add EMBEDDING_MODEL, EMBEDDING_DEVICE)
- `scripts/ingest_books.py` (update EmbeddingGenerator class)
- `requirements.txt` (add torch with CUDA)
- `README.md` (GPU setup documentation)

**Definition of Done:**
- Config variables added and documented
- PyTorch CUDA installed
- bge-large-en-v1.5 loads successfully on GPU
- Embedding dimension verified as 1024
- CPU fallback tested and working
- All tests pass

---

### Story 0.2: Add Embedding Model Metadata to Qdrant Payloads

**Status:** ⏳ PENDING

As a **system maintainer**,
I want **chunk metadata to include embedding model information**,
So that **I can identify which chunks need re-ingestion when models change**.

**Acceptance Criteria:**

**Given** a book is being ingested
**When** chunks are uploaded to Qdrant
**Then** each chunk payload includes:
  - `embedding_model`: "BAAI/bge-large-en-v1.5"
  - `embedding_dimension`: 1024
  - `ingest_version`: "2.0" (semantic version for tracking)
  - `chunking_strategy`: "hierarchical" or "flat"
  - `chunk_fingerprint`: SHA1 hash of (book_id + section + order + text)

**Given** chunks from multiple embedding models exist in Qdrant
**When** querying the collection
**Then** I can filter by `embedding_model` to find all chunks needing migration
**And** chunk fingerprints allow duplicate detection across re-ingestions

**Technical Tasks:**

- [ ] Define ingest version constant in `scripts/config.py`: `INGEST_VERSION = "2.0"`
- [ ] Add metadata fields to chunk creation in `scripts/universal_chunking.py`:
  - `embedding_model`: from config
  - `embedding_dimension`: from model
  - `ingest_version`: from config
  - `chunking_strategy`: "hierarchical" if parent/child, else "flat"
- [ ] Implement `calculate_chunk_fingerprint()` function:
  ```python
  import hashlib
  def calculate_chunk_fingerprint(book_id: str, section: str, order: int, text: str) -> str:
      content = f"{book_id}|{section}|{order}|{text}"
      return hashlib.sha1(content.encode('utf-8')).hexdigest()
  ```
- [ ] Update `upload_to_qdrant()` in `scripts/ingest_books.py` to include new metadata fields
- [ ] Update existing Qdrant schema documentation to reflect new fields
- [ ] Add migration detection query: Find all chunks with `embedding_model != "BAAI/bge-large-en-v1.5"`

**Files Modified:**
- `scripts/config.py` (add INGEST_VERSION constant)
- `scripts/universal_chunking.py` (add metadata fields to chunk creation)
- `scripts/ingest_books.py` (update upload_to_qdrant, add fingerprint calculation)
- `docs/architecture/architecture-comprehensive.md` (update Qdrant schema docs)

**Definition of Done:**
- All new metadata fields present in uploaded chunks
- Chunk fingerprints are unique and deterministic
- Migration detection query returns correct results
- Documentation updated
- All tests pass

---

### Story 0.3: Re-ingest Book Collection with New Model

**Status:** ⏳ PENDING

As a **library curator**,
I want **to re-ingest all existing books with the new embedding model**,
So that **search results benefit from superior bge-large-en-v1.5 embeddings**.

**Acceptance Criteria:**

**Given** 150 books are currently ingested with all-MiniLM-L6-v2
**When** I run the migration script with `--force-reingest` flag
**Then** all books are re-ingested with bge-large-en-v1.5
**And** old chunks (all-MiniLM-L6-v2) are deleted from Qdrant
**And** new chunks (bge-large-en-v1.5) are uploaded
**And** progress is displayed for each book (X/150 completed)
**And** manifest files are updated with new ingest metadata

**Given** a book fails during re-ingestion
**When** the error occurs
**Then** the error is logged with book details
**And** the script continues with remaining books
**And** a summary report lists all failures at the end

**Technical Tasks:**

- [ ] Add `force_reingest` parameter to `ingest_book()` function in `scripts/ingest_books.py`
  - Bypasses manifest check when `force_reingest=True`
  - Deletes existing chunks for book_id before re-ingesting
- [ ] Create migration script: `scripts/migrate_to_bge_large.py`
  ```python
  # Pseudocode:
  # 1. Load all book_ids from Calibre
  # 2. For each book:
  #    - Delete old chunks from Qdrant (filter by book_id + old embedding_model)
  #    - Ingest with force_reingest=True
  #    - Update manifest
  #    - Log progress
  # 3. Generate migration report (success/failure counts, timing)
  ```
- [ ] Add `--batch-size` parameter to control parallel processing (default: 1, max: 5)
- [ ] Add `--dry-run` flag to preview migration without executing
- [ ] Implement progress bar using callback pattern (not tqdm - Streamlit compatibility)
- [ ] Test migration on 5 sample books first
- [ ] Run full migration on all 150 books
- [ ] Verify search quality improvement with test queries

**Files Modified:**
- `scripts/ingest_books.py` (add force_reingest parameter, delete logic)
- `scripts/migrate_to_bge_large.py` (new migration script)
- `scripts/collection_manifest.py` (update manifest with new metadata)

**Definition of Done:**
- Migration script successfully re-ingests all 150 books
- Old chunks deleted, new chunks uploaded
- Manifests updated with bge-large-en-v1.5 metadata
- No data loss (all books re-ingested successfully)
- Search quality visibly improved (test with sample queries)
- Migration report generated and reviewed

---

## Epic Summary

**Total Stories:** 3
**Status:** ⏳ PENDING
**Estimated Effort:** 2-3 days

**Dependencies:**
- CUDA-capable GPU (optional but recommended for 10x speedup)
- PyTorch with CUDA support
- Sufficient disk space for temporary storage during migration

**Risks:**
- GPU driver compatibility issues (mitigation: CPU fallback)
- Long migration time for 150 books on CPU (mitigation: run overnight)
- Potential Qdrant storage spike during migration (mitigation: delete old chunks before uploading new)

**Success Metrics:**
- All 150 books re-ingested with bge-large-en-v1.5
- Embedding dimension: 1024 (verified)
- Search quality improvement: Subjective testing with sample queries
- GPU acceleration: 10x faster ingestion (~0.3 sec/book vs 3 sec/book on CPU)
