---
epic: 4
title: "Production Scaling & Performance"
status: pending
priority: P2
estimated_stories: 2
---

# Epic 4: Production Scaling & Performance

Optimize ingestion and query performance for the 9,000 book target scale.

**User Outcome:** System handles 9,000 books (~1.35M chunks) with fast ingestion and sub-100ms query times.

**FRs Covered:** FR-003 (batch ingestion), NFR-001 (performance), NFR-005 (scalability)

**ADR References:** ADR-0010 (GPU Acceleration)

**Current State:**
- ✅ Batch ingest tool exists - `alexandria_batch_ingest()` in MCP server
- ✅ GPU acceleration planned (Epic 0)
- ❌ No parallel processing optimization
- ❌ No query performance monitoring
- ❌ tqdm progress bars cause Streamlit stderr issues (technical debt)

**Target State:**
- Batch ingestion with parallel processing (2-5 books at once)
- Query optimization (<100ms search, 0.15-5.5 sec with LLM)
- Progress callbacks instead of tqdm (Streamlit compatible)
- Performance telemetry (timing logs)
- 9,000 books ingested (~1.35M chunks, ~6GB vectors)

---

## Stories

### Story 4.1: Parallel Batch Ingestion Pipeline

**Status:** ⏳ PENDING

As a **library curator**,
I want **to ingest multiple books in parallel**,
So that **batch ingestion of 9,000 books completes in hours, not days**.

**Acceptance Criteria:**

**Given** I run batch ingest with `--parallel 5`
**When** ingestion starts
**Then** up to 5 books are processed simultaneously
**And** progress is tracked per book
**And** total throughput is ~5x faster than sequential

**Given** a book fails during parallel ingestion
**When** the error occurs
**Then** other books continue processing
**And** the failed book is logged for retry
**And** a summary report shows successes/failures

**Technical Tasks:**

- [ ] Implement parallel processing in `scripts/ingest_books.py`:
  ```python
  from concurrent.futures import ThreadPoolExecutor, as_completed

  def batch_ingest_parallel(
      book_ids: List[int],
      collection_name: str,
      max_workers: int = 3
  ):
      with ThreadPoolExecutor(max_workers=max_workers) as executor:
          futures = {
              executor.submit(ingest_book, book_id, collection_name): book_id
              for book_id in book_ids
          }
          for future in as_completed(futures):
              book_id = futures[future]
              try:
                  result = future.result()
                  logger.info(f"✅ Book {book_id} ingested")
              except Exception as e:
                  logger.error(f"❌ Book {book_id} failed: {e}")
  ```
- [ ] Replace tqdm with callback pattern (fix technical debt):
  ```python
  def ingest_with_callback(book_id, progress_callback=None):
      steps = ["extract", "chunk", "embed", "upload"]
      for i, step in enumerate(steps):
          # Do work
          if progress_callback:
              progress_callback(step, i+1, len(steps))
  ```
- [ ] Add batch progress tracking in MCP server
- [ ] Optimize embedding generation (batch encode, GPU acceleration from Epic 0)
- [ ] Add ingestion resume capability (checkpoint progress)

**Files Modified:**
- `scripts/ingest_books.py` (add parallel processing, callback pattern)
- `scripts/mcp_server.py` (update batch ingest tool)

**Definition of Done:**
- Parallel ingestion working with 2-5 workers
- Progress callbacks replace tqdm
- Failed books logged and reported
- Throughput 3-5x faster than sequential

---

### Story 4.2: Query Performance Optimization & Monitoring

**Status:** ⏳ PENDING

As a **system administrator**,
I want **query performance monitored and optimized**,
So that **search remains fast at 9,000 book scale (<100ms)**.

**Acceptance Criteria:**

**Given** I query the collection with 1.35M chunks
**When** semantic search is executed
**Then** search completes in <100ms (95th percentile)
**And** total query time is <6s (including LLM: 0.15-5.5s)

**Given** performance degrades
**When** monitoring detects slow queries (>200ms)
**Then** alerts are logged
**And** query details are captured (query text, filters, result count, timing)

**Technical Tasks:**

- [ ] Add performance telemetry in `scripts/rag_query.py`:
  ```python
  import time

  def perform_rag_query(query, top_k=5):
      timings = {}

      start = time.time()
      # Embedding generation
      embedding = generate_embeddings([query])[0]
      timings["embedding"] = time.time() - start

      start = time.time()
      # Qdrant search
      results = client.search(...)
      timings["search"] = time.time() - start

      start = time.time()
      # LLM answer generation
      answer = generate_answer(...)
      timings["llm"] = time.time() - start

      logger.info(f"Query timings: {timings}")
      return RAGResult(answer, results, metadata={"timings": timings})
  ```
- [ ] Add query optimization:
  - Enable Qdrant HNSW indexing (already default)
  - Add query result caching (LRU cache for common queries)
  - Optimize filter performance (index commonly filtered fields)
- [ ] Create performance monitoring dashboard (Grafana integration in Epic 7)
- [ ] Add slow query logging (>200ms threshold)

**Files Modified:**
- `scripts/rag_query.py` (add telemetry)
- `scripts/ingest_books.py` (add timing logs)

**Definition of Done:**
- Search completes in <100ms at 1.35M chunk scale
- Performance telemetry logged for all queries
- Slow queries detected and logged
- Query caching implemented

---

## Epic Summary

**Total Stories:** 2
**Status:** ⏳ PENDING

**Dependencies:**
- Epic 0 (GPU acceleration for faster embedding)

**Success Metrics:**
- 9,000 books ingested successfully (~1.35M chunks)
- Batch ingestion throughput: 3-5x faster with parallel processing
- Query search time: <100ms (95th percentile)
- Total query time: <6s (including LLM)
