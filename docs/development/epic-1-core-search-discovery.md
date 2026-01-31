---
epic: 1
title: "Core Book Search & Discovery"
status: in_progress
priority: P0
estimated_stories: 4
---

# Epic 1: Core Book Search & Discovery

Enable users to search and discover content across their book collection using semantic search with hierarchical chunking.

**User Outcome:** Users can find relevant passages in books using natural language queries, with configurable context modes (precise/contextual/comprehensive).

**FRs Covered:** FR-001 (search), FR-002 (hierarchical chunking), FR-003 (ingestion), NFR-003 (reliability)

**ADR References:** ADR-0007 (Universal Semantic Chunking), ADR-0006 (Collection Isolation)

**Current State:**
- ✅ Multi-format parsing (EPUB, PDF, TXT, MD, HTML) - `scripts/ingest_books.py`
- ✅ Hierarchical chunking (parent=chapter, child=semantic) - `scripts/chapter_detection.py`
- ✅ Context modes (precise, contextual, comprehensive) - MCP server
- ✅ Response patterns (direct, synthesis, critical, etc.) - `prompts/patterns.json`
- ✅ Universal semantic chunking - `scripts/universal_chunking.py`
- ❌ External metadata enrichment (OpenLibrary, Google Books, Wikidata)
- ❌ Copyright detection and status calculation
- ❌ Calibre metadata cleanup (skip tags, validate title/author)
- ❌ Retrieval quality metrics and self-test suite

**Target State:**
- All current features preserved
- External API metadata enrichment for better quality
- Copyright status detection for Phase 3+ compliance
- Clean Calibre metadata (no garbage tags)
- Quality metrics to measure retrieval accuracy

---

## Stories

### Story 1.1: External Metadata Enrichment

**Status:** ⏳ PENDING

As a **library curator**,
I want **book metadata enriched from external APIs (OpenLibrary, Google Books, Wikidata)**,
So that **I have verified, high-quality metadata instead of relying on unreliable Calibre data**.

**Acceptance Criteria:**

**Given** a book is being ingested
**When** metadata is extracted
**Then** the system queries OpenLibrary API first (primary source)
**And** queries Google Books API as fallback if OpenLibrary fails
**And** queries Wikidata for author death year (for copyright calculation)
**And** cross-validates metadata across 2+ sources when available
**And** extracts metadata from book content (EPUB metadata, PDF properties) as final fallback

**Given** external API calls fail (network error, rate limit)
**When** metadata enrichment is attempted
**Then** the system falls back to Calibre metadata with a warning log
**And** marks `metadata_source: "calibre_fallback"` in chunk payload
**And** continues ingestion without blocking

**Given** metadata from multiple sources conflicts
**When** title or author differs between sources
**Then** the system prioritizes: OpenLibrary > Google Books > Book content > Calibre
**And** logs the conflict for manual review
**And** stores all variants in metadata for debugging

**Technical Tasks:**

- [ ] Create `scripts/metadata_enrichment.py` module with:
  - [ ] `enrich_from_openlibrary(title, author) -> dict`
  - [ ] `enrich_from_google_books(title, author) -> dict`
  - [ ] `enrich_from_wikidata(author_name) -> dict` (for author_death_year)
  - [ ] `cross_validate_metadata(sources: list) -> dict` (merge + conflict resolution)
- [ ] OpenLibrary API integration:
  - Endpoint: `https://openlibrary.org/search.json?title={title}&author={author}`
  - Extract: title, author, publication_year, ISBN, publisher
  - Rate limit: 100 requests/minute (add exponential backoff)
- [ ] Google Books API integration:
  - Endpoint: `https://www.googleapis.com/books/v1/volumes?q=intitle:{title}+inauthor:{author}`
  - Extract: title, author, publication_year, ISBN, pageCount
  - Requires API key (optional, quota: 1000 requests/day)
- [ ] Wikidata SPARQL integration:
  - Query: `SELECT ?deathYear WHERE { ?author rdfs:label "{author}"@en . ?author wdt:P570 ?deathDate }`
  - Extract: author_death_year for copyright calculation
  - Rate limit: Respectful (1 request/second max)
- [ ] Integrate into `ingest_book()` pipeline in `scripts/ingest_books.py`:
  ```python
  # After extract_text(), before chunking:
  enriched_metadata = enrich_metadata(
      calibre_metadata=metadata,
      title=metadata['title'],
      author=metadata['author']
  )
  # Use enriched_metadata for chunk payloads
  ```
- [ ] Add metadata provenance tracking:
  - `metadata_source`: "openlibrary" | "google_books" | "book_content" | "calibre_fallback"
  - `metadata_confidence`: "high" (2+ sources agree) | "medium" (1 source) | "low" (fallback)
- [ ] Add configuration for API keys in `scripts/config.py`:
  - `GOOGLE_BOOKS_API_KEY` (optional)
  - `ENABLE_METADATA_ENRICHMENT` (default: True)
- [ ] Error handling and logging:
  - Log all API failures (network, rate limit, parsing errors)
  - Continue ingestion on failure (don't block)
  - Generate metadata enrichment report (success rate, sources used)

**Files Modified:**
- `scripts/metadata_enrichment.py` (new)
- `scripts/ingest_books.py` (integrate enrichment)
- `scripts/config.py` (add API configuration)
- `requirements.txt` (add `requests`, `SPARQLWrapper`)

**Definition of Done:**
- Metadata enrichment module created and tested
- OpenLibrary, Google Books, Wikidata integration working
- Cross-validation logic implemented
- Integrated into ingestion pipeline
- Graceful degradation on API failures
- Documentation updated with API setup instructions

---

### Story 1.2: Copyright Detection & Status Calculation

**Status:** ⏳ PENDING

As a **system administrator preparing for Phase 3 public access**,
I want **copyright status calculated and stored for each book**,
So that **I can filter content by copyright status for legal compliance**.

**Acceptance Criteria:**

**Given** a book is ingested with publication_year and author_death_year
**When** copyright status is calculated
**Then** the system applies these rules:
  - Pre-1928 publication → `copyright_status: "public_domain"`
  - Author death + 70 years → `copyright_status: "public_domain"`
  - Otherwise → `copyright_status: "copyrighted"`
  - Missing data → `copyright_status: "unknown"`

**Given** copyright status is determined
**When** chunks are uploaded to Qdrant
**Then** each chunk payload includes:
  - `copyright_status`: "public_domain" | "copyrighted" | "unknown"
  - `publication_year`: int (from enriched metadata)
  - `author_death_year`: int | null (from Wikidata)
  - `copyright_calculation_date`: ISO timestamp

**Given** a user queries the collection in Phase 3+
**When** copyright filtering is enabled
**Then** only `copyright_status: "public_domain"` chunks are returned for free-tier users
**And** all chunks are returned for PRO-tier users (with proper access control)

**Technical Tasks:**

- [ ] Create `scripts/copyright_detection.py` module:
  ```python
  def calculate_copyright_status(
      publication_year: Optional[int],
      author_death_year: Optional[int],
      current_year: int = 2026
  ) -> str:
      """
      Returns: "public_domain" | "copyrighted" | "unknown"

      Rules:
      1. Pre-1928 → public domain (US law)
      2. Author death + 70 years → public domain (EU/US harmonized)
      3. Otherwise → copyrighted
      4. Missing data → unknown
      """
      if publication_year and publication_year < 1928:
          return "public_domain"

      if author_death_year and (current_year - author_death_year) > 70:
          return "public_domain"

      if publication_year or author_death_year:
          return "copyrighted"

      return "unknown"
  ```
- [ ] Integrate into metadata enrichment pipeline (Story 1.1)
- [ ] Add copyright fields to chunk metadata in `scripts/ingest_books.py`:
  - Extend chunk payload with copyright_status, publication_year, author_death_year
  - Store copyright_calculation_date for audit trail
- [ ] Add Qdrant filter helper in `scripts/qdrant_utils.py`:
  ```python
  def build_copyright_filter(user_tier: str) -> Optional[Filter]:
      """Build Qdrant filter for copyright compliance."""
      if user_tier == "free":
          return FieldCondition(
              key="copyright_status",
              match=MatchValue(value="public_domain")
          )
      # PRO tier sees everything
      return None
  ```
- [ ] Document copyright rules and legal basis in `docs/architecture/architecture-comprehensive.md`
- [ ] Add unit tests for copyright calculation edge cases:
  - Pre-1928 books
  - Author death + 70 years
  - Missing publication year
  - Missing author death year
  - Conflicting data

**Files Modified:**
- `scripts/copyright_detection.py` (new)
- `scripts/metadata_enrichment.py` (integrate copyright calculation)
- `scripts/ingest_books.py` (add copyright fields to chunks)
- `scripts/qdrant_utils.py` (add copyright filter helper)
- `docs/architecture/architecture-comprehensive.md` (document legal basis)

**Definition of Done:**
- Copyright calculation logic implemented and tested
- Copyright status stored in all chunk payloads
- Qdrant filter helper created for Phase 3+ use
- Legal rules documented
- Unit tests pass

---

### Story 1.3: Calibre Metadata Cleanup & Validation

**Status:** ⏳ PENDING

As a **data quality engineer**,
I want **Calibre metadata cleaned and validated**,
So that **garbage tags are excluded and only reliable metadata is used**.

**Acceptance Criteria:**

**Given** a book is ingested from Calibre library
**When** Calibre metadata is extracted
**Then** Calibre tags are SKIPPED entirely (not stored in Qdrant)
**And** title and author are extracted with caution flag: `calibre_title_untrusted: true`
**And** external API metadata is preferred over Calibre metadata
**And** Calibre metadata is only used as last resort fallback

**Given** Calibre metadata conflicts with external API metadata
**When** merging metadata sources
**Then** the system prioritizes: External API > Book content > Calibre
**And** logs the conflict for review
**And** stores both versions for debugging: `calibre_title`, `verified_title`

**Given** chunk metadata is uploaded to Qdrant
**When** viewing chunk payload
**Then** the payload includes:
  - `title`: string (verified from external API)
  - `author`: string (verified from external API)
  - `calibre_title`: string (original, for debugging only)
  - `calibre_author`: string (original, for debugging only)
  - `metadata_source`: "openlibrary" | "google_books" | "calibre_fallback"

**Technical Tasks:**

- [ ] Update `scripts/calibre_db.py` to skip tags extraction:
  - Remove tag queries from `get_book_metadata()`
  - Document why tags are skipped (unreliable user-generated data)
- [ ] Update metadata merging logic in `scripts/metadata_enrichment.py`:
  - Priority: External API > Book content > Calibre
  - Store both `verified_title` and `calibre_title` for debugging
  - Add `metadata_trust_level` field: "high" | "medium" | "low"
- [ ] Add metadata validation rules:
  - Title must not be empty or "Unknown"
  - Author must not be "Unknown Author" (mark as null instead)
  - Publication year must be 1000-2026 (sanity check)
- [ ] Update chunk payload structure in `scripts/ingest_books.py`:
  - Primary fields: `title`, `author` (verified)
  - Debug fields: `calibre_title`, `calibre_author` (original)
  - Provenance: `metadata_source`, `metadata_trust_level`
- [ ] Add logging for metadata quality issues:
  - Log when Calibre metadata is rejected
  - Log when external API verification fails
  - Generate metadata quality report per ingestion

**Files Modified:**
- `scripts/calibre_db.py` (remove tags extraction)
- `scripts/metadata_enrichment.py` (update merging logic)
- `scripts/ingest_books.py` (update chunk payload structure)

**Definition of Done:**
- Calibre tags are no longer stored in Qdrant
- External API metadata is prioritized
- Metadata validation rules implemented
- Debugging fields preserved (calibre_title, calibre_author)
- Quality logging added
- All tests pass

---

### Story 1.4: Retrieval Quality Metrics & Self-Test Suite

**Status:** ⏳ PENDING

As a **quality assurance engineer**,
I want **automated retrieval quality metrics and self-test suite**,
So that **I can detect regressions in search accuracy after changes**.

**Acceptance Criteria:**

**Given** a canonical set of test questions and expected sources
**When** retrieval quality tests are run
**Then** the system measures:
  - **Recall**: % of expected sources found in top-K results
  - **Precision**: % of returned results that are relevant
  - **Source Attribution**: % of LLM answers that cite retrieved sources (not hallucinate)

**Given** a code change affects retrieval (new model, chunking, ranking)
**When** self-test suite is run
**Then** quality metrics are compared against baseline
**And** regression is flagged if recall drops > 10%
**And** a detailed report shows which questions failed

**Given** the system generates an answer with sources
**When** source attribution is measured
**Then** the system checks:
  - Did the answer cite any retrieved chunks?
  - Did the answer introduce facts NOT in retrieved chunks? (hallucination)
  - What % of the answer is grounded in sources?

**Technical Tasks:**

- [ ] Create `tests/retrieval/test_quality.py`:
  ```python
  CANONICAL_QUESTIONS = [
      {
          "query": "What is Nietzsche's view on suffering?",
          "expected_sources": ["nietzsche_beyond_good_evil", "nietzsche_genealogy_morals"],
          "expected_concepts": ["suffering", "will to power", "eternal return"]
      },
      # ... 20-30 canonical questions covering key books
  ]

  def test_retrieval_recall():
      """Measure recall@5 for canonical questions."""
      for q in CANONICAL_QUESTIONS:
          results = perform_rag_query(q["query"], top_k=5)
          found = [r for r in results if r["book_id"] in q["expected_sources"]]
          recall = len(found) / len(q["expected_sources"])
          assert recall >= 0.7, f"Low recall for: {q['query']}"
  ```
- [ ] Implement source attribution checker in `scripts/rag_query.py`:
  ```python
  def measure_source_attribution(answer: str, retrieved_chunks: list) -> dict:
      """
      Returns: {
          "cited_sources": int,  # How many chunks were cited
          "hallucination_risk": float,  # 0.0-1.0 (facts not in sources)
          "grounding_score": float  # 0.0-1.0 (% of answer grounded)
      }
      """
      # Use LLM to check if answer cites sources
      # Flag facts in answer that don't appear in any chunk
  ```
- [ ] Create baseline metrics file: `tests/retrieval/baseline_metrics.json`
  ```json
  {
      "recall@5": 0.82,
      "precision@5": 0.91,
      "source_attribution": 0.88,
      "last_updated": "2026-01-31"
  }
  ```
- [ ] Add regression detection script: `scripts/check_retrieval_regression.py`
  - Compare current metrics against baseline
  - Fail if recall drops > 10% or precision drops > 15%
  - Generate detailed report showing failing questions
- [ ] Integrate into CI/CD (future - Epic 5):
  - Run self-test suite on every model/chunking change
  - Block merge if regression detected
- [ ] Document test questions and expected behavior in `docs/testing/retrieval-quality.md`

**Files Modified:**
- `tests/retrieval/test_quality.py` (new)
- `tests/retrieval/baseline_metrics.json` (new)
- `scripts/rag_query.py` (add source attribution checker)
- `scripts/check_retrieval_regression.py` (new)
- `docs/testing/retrieval-quality.md` (new)

**Definition of Done:**
- 20-30 canonical test questions defined
- Recall, precision, source attribution metrics implemented
- Baseline metrics captured
- Regression detection script working
- Documentation complete
- All tests pass

---

## Epic Summary

**Total Stories:** 4
**Status:** 🔄 IN PROGRESS (hierarchical chunking, context modes, response patterns DONE; metadata enrichment, copyright detection, quality metrics PENDING)

**Completed Features (from TODO.md):**
- ✅ Hierarchical Chunking (Phase 0+1) - `scripts/chapter_detection.py`
- ✅ Context modes (precise/contextual/comprehensive) - MCP server
- ✅ Response patterns (direct/synthesis/critical) - `prompts/patterns.json`
- ✅ Multi-format parsing (EPUB/PDF/TXT/MD/HTML) - `scripts/ingest_books.py`

**Pending Features:**
- ⏳ External metadata enrichment (OpenLibrary, Google Books, Wikidata)
- ⏳ Copyright detection and status calculation
- ⏳ Calibre metadata cleanup (skip tags)
- ⏳ Retrieval quality metrics and self-test suite

**Dependencies:**
- OpenLibrary API (free, no key required)
- Google Books API (optional, requires API key for >1000 req/day)
- Wikidata SPARQL endpoint (free, rate-limited)

**Risks:**
- External API rate limits (mitigation: exponential backoff, caching)
- API availability/downtime (mitigation: graceful fallback to Calibre metadata)
- Metadata quality varies by book (mitigation: cross-validation, provenance tracking)

**Success Metrics:**
- >80% of books have enriched metadata from external APIs
- Copyright status calculated for 100% of books (even if "unknown")
- Calibre tags excluded from all new ingestions
- Retrieval recall@5 > 80% on canonical test questions
