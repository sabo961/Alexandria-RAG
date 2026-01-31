---
epic: 2
title: "Multi-Collection Organization"
status: in_progress
priority: P1
estimated_stories: 3
---

# Epic 2: Multi-Collection Organization

Enable users to organize books into isolated collections with independent settings and tracking.

**User Outcome:** Users can manage multiple book collections (e.g., work vs personal, fiction vs technical) with separate settings and quotas.

**FRs Covered:** FR-004 (collection management), NFR-003 (reliability via isolation)

**ADR References:** ADR-0006 (Collection Isolation), ADR-0004 (Collection-Specific Manifests)

**Current State:**
- ✅ Collection manifests implemented - `scripts/collection_manifest.py`
- ✅ Qdrant utilities (list, stats, copy, delete, search) - `scripts/qdrant_utils.py`
- ✅ Collection-specific manifest files (`{collection}_manifest.json`)
- ✅ Manifest verification against Qdrant
- ❌ No multi-collection creation wizard or UI
- ❌ No per-collection configuration (chunking params, quotas)
- ❌ No usage quotas or limits enforcement
- ❌ No collection metadata (owner, description, settings)

**Target State:**
- Users can create multiple isolated collections
- Each collection has independent settings (chunking params, quotas)
- Collection isolation enforced (no cross-contamination)
- Usage tracked per collection (book count, chunk count, storage)
- Quotas enforced with warnings and limits
- Prepares for Phase 2+ multi-tenancy (user-owned collections)

---

## Stories

### Story 2.1: Collection Creation & Configuration

**Status:** ⏳ PENDING

As a **library curator**,
I want **to create and configure multiple collections with independent settings**,
So that **I can organize books by category with different chunking parameters per collection**.

**Acceptance Criteria:**

**Given** I want to create a new collection
**When** I run `python scripts/manage_collections.py create my_fiction --description "Fiction library"`
**Then** a new Qdrant collection `my_fiction` is created
**And** a manifest file `logs/my_fiction_manifest.json` is initialized
**And** collection metadata is stored with: owner, created_at, description, settings

**Given** I want to configure chunking parameters for a collection
**When** I run `python scripts/manage_collections.py configure my_fiction --threshold 0.55 --min-chunk 250 --max-chunk 1200`
**Then** the collection settings are updated in metadata
**And** future ingestions to this collection use these parameters
**And** existing chunks are NOT re-ingested (settings apply to new ingestions only)

**Given** I want to view collection settings
**When** I run `python scripts/manage_collections.py show my_fiction`
**Then** the output displays:
  - Collection name, description, owner
  - Created date, last updated
  - Chunking parameters (threshold, min/max chunk size)
  - Usage stats (book count, chunk count, storage MB)
  - Quota limits (if set)

**Technical Tasks:**

- [ ] Create `scripts/manage_collections.py` CLI tool:
  ```python
  # Commands:
  # create <name> --description "..." --owner "..." --threshold X --min-chunk Y --max-chunk Z
  # configure <name> --threshold X --min-chunk Y --max-chunk Z --quota-books N --quota-chunks M
  # show <name>
  # list  # Show all collections
  # delete <name> --confirm  # Safety check
  ```
- [ ] Extend `CollectionManifest` class in `scripts/collection_manifest.py`:
  - Add `metadata` field to manifest:
    ```json
    {
        "metadata": {
            "owner": "sabo",
            "created_at": "2026-01-31T10:30:00Z",
            "description": "Fiction library",
            "settings": {
                "chunking": {
                    "threshold": 0.5,
                    "min_chunk_size": 200,
                    "max_chunk_size": 1500
                },
                "quotas": {
                    "max_books": null,
                    "max_chunks": null,
                    "max_storage_mb": null
                }
            }
        },
        "collections": { ... }
    }
    ```
  - Add methods: `get_settings()`, `update_settings()`, `get_metadata()`
- [ ] Update `ingest_book()` in `scripts/ingest_books.py`:
  - Load collection settings from manifest before chunking
  - Use collection-specific chunking parameters (override defaults)
  - Log which settings were used: `logger.info(f"Using chunking params from collection '{collection_name}': threshold={threshold}")`
- [ ] Create Qdrant collection with custom vector params:
  ```python
  def create_collection(
      collection_name: str,
      vector_size: int = 1024,  # bge-large-en-v1.5
      distance: Distance = Distance.COSINE
  ):
      client.create_collection(
          collection_name=collection_name,
          vectors_config=VectorParams(size=vector_size, distance=distance)
      )
  ```
- [ ] Add collection metadata to Qdrant payload (for filtering):
  - `collection_name`: string (for multi-collection queries)
  - `collection_owner`: string (Phase 2+ for access control)
- [ ] Document collection management workflow in `docs/user-docs/tutorials/managing-collections.md`

**Files Modified:**
- `scripts/manage_collections.py` (new CLI tool)
- `scripts/collection_manifest.py` (extend with metadata and settings)
- `scripts/ingest_books.py` (load collection settings)
- `scripts/qdrant_utils.py` (add create_collection helper)
- `docs/user-docs/tutorials/managing-collections.md` (new)

**Definition of Done:**
- `manage_collections.py` CLI tool created and working
- Collections can be created with custom settings
- Settings stored in manifest and applied during ingestion
- Collection metadata tracked (owner, created_at, description)
- Documentation complete
- All tests pass

---

### Story 2.2: Collection Isolation & Safety

**Status:** ⏳ PENDING

As a **system administrator**,
I want **strict collection isolation enforced**,
So that **operations on one collection never affect another (prevent cross-contamination)**.

**Acceptance Criteria:**

**Given** I query collection "my_fiction"
**When** the search is executed
**Then** ONLY chunks from "my_fiction" are returned
**And** chunks from "alexandria" or other collections are EXCLUDED
**And** collection name is validated before query execution

**Given** I delete a book from collection "my_fiction"
**When** the deletion is executed
**Then** ONLY chunks with `collection_name="my_fiction"` AND `book_id=X` are deleted
**And** chunks from other collections are NOT affected
**And** a safety check confirms collection name before deletion

**Given** I attempt to ingest into a non-existent collection
**When** the ingestion starts
**Then** an error is raised: "Collection 'xyz' does not exist. Create it first."
**And** the book is NOT ingested
**And** the user is prompted to run `manage_collections.py create xyz`

**Technical Tasks:**

- [ ] Add collection name validation in `scripts/qdrant_utils.py`:
  ```python
  def validate_collection_exists(collection_name: str, client: QdrantClient) -> bool:
      """Validate collection exists before operations."""
      collections = [c.name for c in client.get_collections().collections]
      if collection_name not in collections:
          raise ValueError(f"Collection '{collection_name}' does not exist. Create it first: manage_collections.py create {collection_name}")
      return True
  ```
- [ ] Update `perform_rag_query()` in `scripts/rag_query.py`:
  - Validate collection_name before querying
  - Add collection filter to Qdrant search:
    ```python
    filter = Filter(
        must=[
            FieldCondition(
                key="collection_name",
                match=MatchValue(value=collection_name)
            )
        ]
    )
    ```
  - Log collection isolation: `logger.debug(f"Query restricted to collection: {collection_name}")`
- [ ] Update deletion logic in `scripts/ingest_books.py`:
  - Require both `collection_name` AND `book_id` for deletion
  - Add safety check: confirm collection exists and user owns it (Phase 2+)
  - Delete with filter:
    ```python
    client.delete(
        collection_name=collection_name,
        points_selector=Filter(
            must=[
                FieldCondition(key="collection_name", match=MatchValue(value=collection_name)),
                FieldCondition(key="book_id", match=MatchValue(value=book_id))
            ]
        )
    )
    ```
- [ ] Add collection isolation tests in `tests/test_collection_isolation.py`:
  - Test: Query to collection A does not return chunks from collection B
  - Test: Delete from collection A does not affect collection B
  - Test: Ingest to non-existent collection raises error
- [ ] Add audit logging for cross-collection operations (Phase 1 preparation):
  - Log collection access: who, what, when
  - Log collection modifications: create, delete, configure
  - Store in SQLite audit.db (Epic 7 integration)

**Files Modified:**
- `scripts/qdrant_utils.py` (add validation)
- `scripts/rag_query.py` (add collection filter)
- `scripts/ingest_books.py` (add deletion safety checks)
- `tests/test_collection_isolation.py` (new)

**Definition of Done:**
- Collection name validated before all operations
- Qdrant queries filtered by collection_name
- Deletion requires both collection_name and book_id
- Isolation tests pass (no cross-contamination)
- Audit logging prepared (Phase 1)

---

### Story 2.3: Collection Usage Quotas & Monitoring

**Status:** ⏳ PENDING

As a **system administrator preparing for Phase 2+ multi-user access**,
I want **usage quotas enforced per collection**,
So that **users cannot exceed their allocated storage or book limits**.

**Acceptance Criteria:**

**Given** a collection has quota `max_books: 100`
**When** the 101st book is ingested
**Then** the ingestion is rejected with error: "Quota exceeded: max_books=100"
**And** the book is NOT added to the collection
**And** the user is notified to upgrade quota or delete books

**Given** a collection has quota `max_storage_mb: 500`
**When** ingesting a book would exceed storage limit
**Then** the ingestion is rejected with error: "Storage quota exceeded: 500 MB"
**And** estimated storage is calculated before ingestion (chunk count × avg chunk size)
**And** the user is notified to free up space

**Given** a collection is approaching quota limit (80% full)
**When** usage is checked
**Then** a warning is logged: "⚠️  Collection 'my_fiction' at 82% of book quota (82/100)"
**And** the warning is displayed in `manage_collections.py show my_fiction`
**And** an alert is sent to collection owner (Phase 2+)

**Technical Tasks:**

- [ ] Add quota tracking to `CollectionManifest` class:
  ```python
  def check_quota(self, collection_name: str, quota_type: str) -> dict:
      """
      Check quota status for a collection.

      Returns: {
          "used": 45,
          "limit": 100,
          "percentage": 45.0,
          "status": "ok" | "warning" | "exceeded"
      }
      """
      settings = self.get_settings(collection_name)
      quotas = settings["quotas"]

      if quota_type == "books":
          used = len(self.manifest["collections"][collection_name]["books"])
          limit = quotas.get("max_books")
      elif quota_type == "chunks":
          used = self.get_chunk_count(collection_name)
          limit = quotas.get("max_chunks")
      elif quota_type == "storage":
          used = self.get_storage_mb(collection_name)
          limit = quotas.get("max_storage_mb")

      if limit is None:
          return {"status": "unlimited"}

      percentage = (used / limit) * 100
      if percentage >= 100:
          return {"used": used, "limit": limit, "percentage": percentage, "status": "exceeded"}
      elif percentage >= 80:
          return {"used": used, "limit": limit, "percentage": percentage, "status": "warning"}
      else:
          return {"used": used, "limit": limit, "percentage": percentage, "status": "ok"}
  ```
- [ ] Add quota enforcement in `ingest_book()`:
  ```python
  # Before ingestion
  manifest = CollectionManifest(collection_name=collection_name)
  quota_check = manifest.check_quota(collection_name, "books")

  if quota_check["status"] == "exceeded":
      raise QuotaExceededError(f"Book quota exceeded: {quota_check['used']}/{quota_check['limit']}")

  if quota_check["status"] == "warning":
      logger.warning(f"⚠️  Approaching book quota: {quota_check['percentage']:.1f}% ({quota_check['used']}/{quota_check['limit']})")
  ```
- [ ] Add storage estimation before ingestion:
  ```python
  def estimate_storage_mb(text: str, avg_chunk_size: int = 500) -> float:
      """Estimate storage required for book ingestion."""
      estimated_chunks = len(text) / avg_chunk_size
      # Each chunk: text (500 bytes avg) + embedding (1024 floats × 4 bytes) + metadata (200 bytes avg)
      bytes_per_chunk = 500 + (1024 * 4) + 200
      total_bytes = estimated_chunks * bytes_per_chunk
      return total_bytes / (1024 * 1024)  # Convert to MB
  ```
- [ ] Update `manage_collections.py show` command:
  - Display quota status with color coding:
    - Green: 0-79% used
    - Yellow: 80-99% used (warning)
    - Red: 100%+ used (exceeded)
  - Show estimated time to quota exhaustion (based on ingestion rate)
- [ ] Add quota metrics to collection manifest:
  ```json
  {
      "usage": {
          "book_count": 45,
          "chunk_count": 3200,
          "storage_mb": 285.4,
          "last_updated": "2026-01-31T15:30:00Z"
      }
  }
  ```
- [ ] Create quota monitoring script: `scripts/check_collection_quotas.py`
  - Run via cron (daily check)
  - Alert on collections approaching quota (80%+)
  - Generate quota usage report

**Files Modified:**
- `scripts/collection_manifest.py` (add quota tracking methods)
- `scripts/ingest_books.py` (add quota enforcement)
- `scripts/manage_collections.py` (update show command with quota display)
- `scripts/check_collection_quotas.py` (new monitoring script)

**Definition of Done:**
- Quota tracking implemented (books, chunks, storage)
- Quota enforcement prevents over-limit ingestion
- Warnings displayed at 80% quota usage
- Storage estimation working
- Quota monitoring script created
- All tests pass

---

## Epic Summary

**Total Stories:** 3
**Status:** 🔄 IN PROGRESS (manifests and Qdrant utils done; creation wizard, quotas, isolation pending)

**Completed Features:**
- ✅ Collection manifests - `scripts/collection_manifest.py`
- ✅ Qdrant collection utilities - `scripts/qdrant_utils.py`
- ✅ Collection-specific tracking (manifest files)

**Pending Features:**
- ⏳ Collection creation wizard & configuration
- ⏳ Per-collection chunking parameters
- ⏳ Collection isolation enforcement
- ⏳ Usage quotas and monitoring

**Dependencies:**
- None (standalone epic)

**Risks:**
- Quota enforcement may slow down ingestion (mitigation: async quota checks)
- Collection isolation requires careful filter implementation (mitigation: comprehensive tests)
- Storage estimation may be inaccurate (mitigation: periodic actual storage measurement)

**Success Metrics:**
- Users can create and manage multiple collections
- Collection isolation tests pass (0% cross-contamination)
- Quota enforcement prevents over-limit ingestion
- Per-collection settings applied correctly during ingestion
