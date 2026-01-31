# Test Coverage Backlog

**Date:** 2026-01-30
**Priority:** Medium-High
**Status:** Idea

## Current State

Overall test coverage: **~4%** (130 tests, 118 passing after fixes)

### Well-Tested Modules

| Module | Coverage | Tests | Status |
|--------|----------|-------|--------|
| `html_sanitizer.py` | 70% | 71 | Excellent |
| `calibre_db.py` | 24% | 27 | Adequate |
| `config.py` | ~70% | ~5 | Good |

### Critical Gaps (0% Coverage)

| Module | LOC | Risk | Priority |
|--------|-----|------|----------|
| `mcp_server.py` | 1,637 | **CRITICAL** | P0 |
| `rag_query.py` | 879 | **CRITICAL** | P0 |
| `ingest_books.py` | 951 | **CRITICAL** | P1 |
| `universal_chunking.py` | 136 | HIGH | P1 |
| `qdrant_utils.py` | 643 | HIGH | P2 |
| `chapter_detection.py` | 572 | HIGH | P2 |
| `collection_manifest.py` | 488 | MEDIUM | P3 |

## Recommended Test Suites

### P0: MCP Server Tests (`test_mcp_server.py`)

```python
# Tool registration and discovery
def test_all_tools_registered()
def test_tool_docstrings_present()

# Query tools
def test_alexandria_query_basic()
def test_alexandria_query_with_context_modes()
def test_alexandria_search_by_author()
def test_alexandria_book_by_id()
def test_alexandria_stats()

# Ingest tools
def test_alexandria_ingest_preview()
def test_alexandria_test_chunking()
def test_alexandria_compare_chunking()

# Error handling
def test_query_with_invalid_collection()
def test_ingest_nonexistent_book()
def test_connection_failure_handling()
```

### P0: RAG Query Tests (`test_rag_query.py`)

```python
# Basic query functionality
def test_perform_rag_query_returns_results()
def test_perform_rag_query_empty_collection()
def test_perform_rag_query_no_matches()

# Filtering and ranking
def test_similarity_threshold_filtering()
def test_result_limit_respected()
def test_language_filter_applied()

# LLM integration (mocked)
def test_generate_llm_answer_with_context()
def test_rerank_results()

# Error handling
def test_query_handles_qdrant_timeout()
def test_query_handles_invalid_collection()
```

### P1: Ingest Tests (`test_ingest_books.py`)

```python
# Text extraction
def test_extract_text_from_epub()
def test_extract_text_from_pdf()
def test_extract_text_from_txt()
def test_extract_text_unsupported_format()

# Chunking
def test_ingest_creates_chunks()
def test_threshold_affects_chunk_count()
def test_min_chunk_size_respected()
def test_max_chunk_size_forces_break()

# Metadata
def test_calibre_enrichment()
def test_metadata_overrides()

# Compare mode
def test_compare_chunking_returns_recommendations()
def test_compare_multiple_thresholds()
```

### P1: Universal Chunking Tests (`test_universal_chunking.py`)

```python
# Core algorithm
def test_chunk_splits_on_topic_change()
def test_chunk_respects_min_size()
def test_chunk_respects_max_size()
def test_chunk_with_empty_text()

# Semantic similarity
def test_high_similarity_keeps_together()
def test_low_similarity_causes_break()
def test_threshold_affects_breaks()

# Edge cases
def test_single_sentence()
def test_very_long_sentence()
def test_all_similar_sentences()
```

## Infrastructure Improvements

### Missing

- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Coverage reporting
- [ ] Pre-commit hooks
- [ ] Test markers (unit/integration/e2e)
- [ ] pytest.ini configuration

### Recommended pytest.ini

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
markers =
    unit: Unit tests (fast, no external dependencies)
    integration: Integration tests (may require Qdrant)
    e2e: End-to-end tests (full pipeline)
    slow: Slow tests (skip with -m "not slow")
```

## Implementation Plan

### Phase 1: Critical Path (1-2 days)
- [ ] `test_universal_chunking.py` - Core algorithm, smallest module
- [ ] `test_rag_query.py` - Main user-facing functionality
- [ ] Basic CI setup

### Phase 2: MCP Coverage (2-3 days)
- [ ] `test_mcp_server.py` - All 12 tools
- [ ] `test_ingest_books.py` - Ingestion pipeline

### Phase 3: Supporting Modules (1-2 days)
- [ ] `test_qdrant_utils.py`
- [ ] `test_chapter_detection.py`
- [ ] `test_collection_manifest.py`

### Phase 4: Integration Tests (ongoing)
- [ ] Full ingest -> query pipeline
- [ ] Multi-book batch operations
- [ ] Performance benchmarks

## Notes

- Security tests (XSS, SQL injection) are already well covered
- UI tests reduced to smoke tests only (GUI is secondary interface)
- Consider running integration tests only on BUCO (where Qdrant lives)
