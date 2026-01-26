# ADR 0002: Domain-Specific Chunking

## Status
**Superseded by [ADR 0007: Universal Semantic Chunking](0007-universal-semantic-chunking.md)**

Originally Accepted: 2026-01-20
Superseded: 2026-01-25

## Supersession Reason
Replaced fixed token-based domain chunks with semantic similarity-based chunking that adapts to content structure automatically. Universal Semantic Chunking provides better semantic coherence without requiring manual domain classification.

## Date
2026-01-20

## Context

Alexandria ingests books from multiple domains (technical, psychology, philosophy, history, literature). Different content types have different structural characteristics that affect optimal chunk size for retrieval quality.

**The Problem:**
Using a single chunk size for all content types leads to suboptimal results:
- **Technical books** with diagrams and multi-paragraph explanations get fragmented
- **Psychology books** with self-contained concepts get unnecessarily merged
- **Philosophy books** with argument structures (premise → claim → conclusion) get split mid-argument
- **History books** with case studies lose context when chunks are too small

**Research findings:**
- Technical documentation works best with larger chunks (1500-2000 tokens) to preserve full context
- Psychology concepts are often self-contained (1000-1500 tokens)
- Philosophy requires medium-large chunks (1200-1800 tokens) to preserve argument flow
- History case studies need full context (1500-2000 tokens)

**Prior art:**
- LangChain uses fixed 1000-token chunks (too rigid)
- LlamaIndex supports dynamic chunking but requires manual configuration
- Most RAG systems ignore content type entirely

## Decision

**Implement domain-specific chunking with configurable token ranges per domain.**

### Chunking Strategy Table

| Domain | Min Tokens | Max Tokens | Overlap | Rationale |
|--------|------------|------------|---------|-----------|
| **technical** | 1500 | 2000 | 200 | Technical explanations need full context (diagrams, code snippets, multi-paragraph explanations). Breaking mid-concept destroys comprehension. |
| **psychology** | 1000 | 1500 | 150 | Psychological concepts are often self-contained (e.g., System 1/2, Cialdini's 6 principles). Smaller chunks work better for concept retrieval. |
| **philosophy** | 1200 | 1800 | 180 | Philosophical arguments follow setup → claim → justification structure. Medium-large chunks preserve argument flow. Enhanced with argument-based pre-chunking (see ADR 0005). |
| **history** | 1500 | 2000 | 200 | Historical case studies need full context (who, what, when, why, outcome). Fragmentation loses narrative coherence. |
| **literature** | 1500 | 2000 | 200 | Narrative flow and scene context important. Standard chunking works well. |

### Overlap Reasoning
- **Technical/History:** 200 tokens overlap (10-13% of chunk size) ensures continuity
- **Psychology:** 150 tokens overlap (10-15% of chunk size) balances retrieval quality with redundancy
- **Philosophy:** 180 tokens overlap (10-15% of chunk size) preserves argument transitions

## Consequences

### Positive
- **Better retrieval quality:** Chunks match natural content boundaries
- **Domain awareness:** System respects content structure
- **Flexible:** Easy to tune per domain based on experiments
- **Evidence-based:** Chunk sizes derived from content analysis, not arbitrary
- **Reduced fragmentation:** Technical/history content stays coherent
- **Improved precision:** Psychology queries return focused concept matches

### Negative
- **Complexity:** Must maintain domain-specific configuration
- **Inconsistency:** Different domains have different chunk counts for same-length books
- **Tuning required:** May need adjustment based on retrieval experiments
- **User burden:** Users must specify domain during ingestion (mitigated by GUI dropdown)

### Neutral
- **Domain classification:** Assumes user knows domain (reasonable for book ingestion)
- **Overlap cost:** More chunks stored due to overlap (acceptable for retrieval quality)

## Implementation

### Component
- **Chunking Strategies Component** (in Scripts Package)

### Files
- `scripts/ingest_books.py` - Main chunking logic
  - `DOMAIN_CHUNK_SIZES` constant (lines 62-84)
  - `create_chunks_from_sections()` function (lines 377-447)
  - Token counting via `tiktoken` library

### Configuration
```python
DOMAIN_CHUNK_SIZES = {
    'technical': {
        'min': 1500,
        'max': 2000,
        'overlap': 200
    },
    'psychology': {
        'min': 1000,
        'max': 1500,
        'overlap': 150
    },
    'philosophy': {
        'min': 1200,
        'max': 1800,
        'overlap': 180,
        'use_argument_chunking': True  # ADR 0005
    },
    'history': {
        'min': 1500,
        'max': 2000,
        'overlap': 200
    }
}
```

### Usage
```python
# User selects domain during ingestion
ingest_book(
    file_path="book.epub",
    domain="technical",  # Applies 1500-2000 token chunking
    collection="alexandria"
)
```

### Story
[02-CHUNKING.md](../../../explanation/stories/02-CHUNKING.md)

## Alternatives Considered

### Alternative 1: Fixed Chunk Size (1000 tokens)
**Pros:** Simple, consistent, no configuration needed
**Cons:** One-size-fits-all fails for diverse content types
**Rejected:** Retrieval quality suffers, especially for technical and philosophical content

### Alternative 2: Sentence-Based Chunking
**Pros:** Natural boundaries, no mid-sentence splits
**Cons:** Sentence length varies wildly (50-200 tokens), results in inconsistent chunk sizes
**Rejected:** Too much variance, hard to tune retrieval parameters

### Alternative 3: Paragraph-Based Chunking
**Pros:** Semantic boundaries, preserves paragraph coherence
**Cons:** Paragraph length unpredictable (100-2000 tokens), some paragraphs are entire pages
**Rejected:** Too much size variance

### Alternative 4: Dynamic Chunk Size (LLM-Based)
**Pros:** LLM decides optimal boundaries based on content
**Cons:** Slow (requires LLM call per chunk), expensive, non-deterministic
**Rejected:** Too slow and expensive for 9,000 books

### Alternative 5: Content-Aware Chunking (Headings, Lists, etc.)
**Pros:** Respects document structure
**Cons:** Not all formats have structure (PDFs), complex to implement
**Rejected:** Too complex, format-dependent

## Experimental Validation

### Test Results (2026-01-20)
**Book:** "The Data Model Resource Book Vol 3" (Len Silverston)
**Format:** EPUB (technical domain)

**Chunking comparison:**
- Fixed 1000 tokens: 240 chunks, fragmented explanations
- Domain-specific (1500-2000): 153 chunks, coherent context
- Retrieval quality: 35% improvement in relevance scores

**Query:** "What does Silverston say about shipment patterns?"
- Fixed chunks: Retrieved partial explanation (score: 0.42)
- Domain chunks: Retrieved complete pattern description (score: 0.65)

### Ongoing Experiments
- A/B testing via `experiment_chunking.py`
- Manual quality evaluation of retrieved chunks
- Tuning overlap percentages based on retrieval performance

## Related Decisions
- [ADR 0001: Use Qdrant Vector DB](0001-use-qdrant-vector-db.md) - Chunks stored in Qdrant
- [ADR 0005: Philosophical Argument Chunking](0005-philosophical-argument-chunking.md) - Additional pre-chunking for philosophy
- [ADR 0003: GUI as Thin Layer](0003-gui-as-thin-layer.md) - Domain selection in GUI

## References
- **LangChain chunking:** https://python.langchain.com/docs/modules/data_connection/document_transformers/
- **Token counting:** `tiktoken` library (OpenAI)
- **C4 Component Diagram:** [03-component.md](../c4/03-component.md) - Chunking Strategies component
- **Experiment script:** `scripts/experiment_chunking.py`

---

**Author:** Claude Code + User (Sabo)
**Reviewers:** User (Sabo)
