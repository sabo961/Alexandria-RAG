---
epic: 0
title: "Multi-Model Embedding Support"
status: in-progress
priority: P0
estimated_stories: 3
---

# Epic 0: Multi-Model Embedding Support

**FIRST PRIORITY** - Enable multiple embedding models with runtime selection. Supports A/B testing, gradual migration, and hardware-appropriate choices.

**User Outcome:** Users can choose embedding models per collection, compare quality, and leverage GPU acceleration when available.

**FRs Covered:** FR-001 (multi-model search), NFR-001 (performance), NFR-002 (collection-level model lock)

**ADR References:** ADR-0010 (GPU-Accelerated Embeddings), architecture-comprehensive.md (Multi-Model Registry)

**Current State:**
- Using `all-MiniLM-L6-v2` (384-dim, CPU-only)
- Model hardcoded in `scripts/ingest_books.py:213`
- No GPU support
- No embedding model tracking in Qdrant payloads
- 150 books currently ingested

**Target State:**
- Multi-model registry: `all-MiniLM-L6-v2` (384-dim) + `bge-large-en-v1.5` (1024-dim)
- Runtime model selection per collection
- GPU/CUDA support with CPU fallback
- Embedding model metadata tracked in Qdrant
- Query automatically uses collection's ingestion model

---

## Stories

### Story 0.1: Configure Multi-Model Embedding Support with GPU Acceleration

**Status:** 🔄 IN PROGRESS

As a **system administrator**,
I want **Alexandria to support multiple embedding models with runtime selection**,
So that **I can compare model quality, choose per collection, and leverage GPU when available**.

**Acceptance Criteria:**

**AC1: Model Registry**
**Given** Alexandria is configured
**When** I check the embedding configuration
**Then** a model registry exists with at least two models:
  - `minilm`: all-MiniLM-L6-v2 (384-dim)
  - `bge-large`: BAAI/bge-large-en-v1.5 (1024-dim)
**And** a default model is configured (bge-large)
**And** model selection is available at runtime via `model_id` parameter

**AC2: Multi-Model Caching**
**Given** multiple models are requested during a session
**When** I call `get_model("minilm")` then `get_model("bge-large")`
**Then** both models are loaded and cached separately
**And** subsequent calls return cached models (no reload)

**AC3: GPU/CPU Device Selection**
**Given** Alexandria is running on a machine with CUDA-capable GPU
**When** a model is loaded
**Then** it runs on GPU (CUDA) if available, falls back to CPU if not
**And** device selection is logged

**Given** Alexandria is running without GPU
**When** a model is loaded
**Then** a warning is logged about CPU-only mode
**And** embeddings are still generated correctly (slower but functional)

**Technical Tasks:**

- [ ] Add `EMBEDDING_MODELS` registry to `scripts/config.py`:
  ```python
  EMBEDDING_MODELS = {
      "minilm": {"name": "all-MiniLM-L6-v2", "dim": 384},
      "bge-large": {"name": "BAAI/bge-large-en-v1.5", "dim": 1024},
  }
  DEFAULT_EMBEDDING_MODEL = "bge-large"
  EMBEDDING_DEVICE = os.environ.get('EMBEDDING_DEVICE', 'auto')
  ```
- [ ] Update `EmbeddingGenerator` in `scripts/ingest_books.py`:
  - Change `_model = None` to `_models = {}` (dict cache)
  - Update `get_model(model_id: str = None)` to use registry and cache per model_id
  - Add GPU/CPU detection and logging
- [ ] Install PyTorch with CUDA support
- [ ] Test both models load and cache correctly
- [ ] Test GPU acceleration with bge-large
- [ ] Document multi-model setup in README.md

**Files Modified:**
- `scripts/config.py` (add EMBEDDING_MODELS registry)
- `scripts/ingest_books.py` (update EmbeddingGenerator for multi-model)
- `requirements.txt` (add torch with CUDA)
- `README.md` (multi-model documentation)

**Definition of Done:**
- Model registry with 2+ models configured
- EmbeddingGenerator caches multiple models
- Runtime model selection works via model_id
- GPU acceleration verified for bge-large
- CPU fallback tested and working
- All tests pass

---

### Story 0.2: Add Embedding Model Metadata to Qdrant Payloads

**Status:** ⏳ PENDING

As a **system maintainer**,
I want **chunk metadata to include embedding model information**,
So that **queries automatically use the correct model and I can track collection health**.

**Acceptance Criteria:**

**Given** a book is being ingested with a specific model
**When** chunks are uploaded to Qdrant
**Then** each chunk payload includes:
  - `embedding_model_id`: "bge-large" (registry key for query matching)
  - `embedding_model_name`: "BAAI/bge-large-en-v1.5" (full name for reference)
  - `embedding_dimension`: 1024 (for validation)
  - `ingest_version`: "2.0" (semantic version for tracking)

**Given** I query a collection
**When** the query executes
**Then** the query reads `embedding_model_id` from existing chunks
**And** uses the same model for query embedding generation
**And** warns if mixed models are detected in collection

**Technical Tasks:**

- [ ] Define ingest version constant in `scripts/config.py`: `INGEST_VERSION = "2.0"`
- [ ] Update `upload_to_qdrant()` in `scripts/ingest_books.py`:
  - Accept `model_id` parameter
  - Get model config via `EmbeddingGenerator().get_model_config(model_id)`
  - Add `embedding_model_id`, `embedding_model_name`, `embedding_dimension` to payload
  - Add `ingest_version` to payload
- [ ] Update query logic in `scripts/rag_query.py`:
  - Read `embedding_model_id` from first result chunk
  - Pass `model_id` to `EmbeddingGenerator().get_model(model_id)`
  - Warn if collection has mixed models
- [ ] Add collection model detection helper:
  ```python
  def get_collection_model(collection_name: str) -> str:
      """Get embedding model used by collection (from first chunk)."""
      # Sample one chunk, return embedding_model_id
  ```
- [ ] ✅ Update QDRANT_PAYLOAD_STRUCTURE.md (already done)

**Files Modified:**
- `scripts/config.py` (add INGEST_VERSION constant)
- `scripts/ingest_books.py` (update upload_to_qdrant with model metadata)
- `scripts/rag_query.py` (auto-detect and use collection's model)
- ✅ `docs/architecture/technical/QDRANT_PAYLOAD_STRUCTURE.md` (already updated)

**Definition of Done:**
- Ingested chunks contain `embedding_model_id`, `embedding_model_name`, `embedding_dimension`
- Query auto-detects collection model and uses correct embedder
- Mixed model warning works when collection has inconsistent models
- Tests pass for both minilm and bge-large ingestion

---

### Story 0.3: Re-ingest Book Collection with Specified Model

**Status:** ⏳ PENDING

As a **library curator**,
I want **to re-ingest books with a specified embedding model**,
So that **I can upgrade collections to better models or create A/B test collections**.

**Acceptance Criteria:**

**Given** books are ingested in a collection
**When** I run the migration script with `--model bge-large` flag
**Then** all books are re-ingested with specified model
**And** old chunks are deleted from Qdrant
**And** new chunks with correct `embedding_model_id` are uploaded
**And** progress callback reports X/N completed
**And** manifest files are updated with new model metadata

**Given** a book fails during re-ingestion
**When** the error occurs
**Then** the error is logged with book details
**And** the script continues with remaining books
**And** a summary report lists all failures at the end

**Technical Tasks:**

- [ ] Add `force_reingest` and `model_id` parameters to `ingest_book()` in `scripts/ingest_books.py`
  - Bypasses manifest check when `force_reingest=True`
  - Deletes existing chunks for book_id before re-ingesting
  - Uses specified `model_id` for embedding generation
- [ ] Create CLI tool: `scripts/reingest_collection.py`
  ```python
  # Usage: python reingest_collection.py --collection alexandria --model bge-large
  # 1. Get all book_ids from collection (or from Calibre)
  # 2. For each book:
  #    - Delete old chunks from Qdrant
  #    - Ingest with model_id and force_reingest=True
  #    - Report progress via callback
  # 3. Generate summary (success/failure counts, timing)
  ```
- [ ] Add `--dry-run` flag to preview without executing
- [ ] Add progress callback (Streamlit compatible, no tqdm)
- [ ] Test on 5 sample books first
- [ ] Full re-ingestion of collection

**Files Modified:**
- `scripts/ingest_books.py` (add force_reingest + model_id parameters)
- `scripts/reingest_collection.py` (new CLI tool)
- `scripts/collection_manifest.py` (update manifest with model metadata)

**Definition of Done:**
- Re-ingestion CLI works with `--model` flag
- Dry-run mode previews without changes
- Progress callback works (Streamlit compatible)
- Manifest updated with correct `embedding_model_id`
- Test collection re-ingested successfully
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
