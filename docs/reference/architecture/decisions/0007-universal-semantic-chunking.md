# ADR 0007: Universal Semantic Chunking

## Status
Accepted

## Date
2026-01-25

## Context

Previous chunking approaches (ADR 0002 domain-specific fixed chunks, ADR 0005 philosophical argument detection) were limited:

**Problems with ADR 0002 (Domain-Specific Fixed Chunks):**
- Fixed token windows (1200-1800 for philosophy) split mid-sentence
- Domain boundaries were arbitrary (technical vs psychology unclear)
- Required manual domain classification
- No semantic awareness

**Problems with ADR 0005 (Philosophical Argument Chunking):**
- Author-specific keyword patterns (Mishima, Nietzsche, Cioran)
- Required explicit opposition detection
- Only worked for philosophy domain
- High maintenance (new patterns per author)
- Keyword-based approach missed implicit arguments

**Root Cause:**
Both approaches used **structural heuristics** (token count, keywords) instead of **semantic understanding** of text content.

**Goal:**
Universal chunking algorithm that:
- Works across all domains (no manual classification)
- Preserves semantic coherence (chunks by meaning, not tokens)
- Adapts to content structure (philosophy, technical, literature)
- No author-specific patterns needed

## Decision

**Implement Universal Semantic Chunking using sentence embeddings and cosine similarity to detect natural semantic boundaries.**

### How It Works

#### 1. Sentence-Level Embeddings
```python
# Split text into sentences
sentences = text.split('. ')

# Generate embedding for each sentence
sentence_embeddings = embedding_model.encode(sentences)
# Result: Each sentence → 384-dim vector (all-MiniLM-L6-v2)
```

#### 2. Semantic Similarity Detection
```python
# Calculate cosine similarity between consecutive sentences
similarities = []
for i in range(len(sentence_embeddings) - 1):
    similarity = cosine_similarity(
        sentence_embeddings[i],
        sentence_embeddings[i+1]
    )
    similarities.append(similarity)
```

#### 3. Boundary Detection via Threshold
```python
# Low similarity = topic shift = chunk boundary
THRESHOLD = 0.55  # Default for most content
PHILOSOPHY_THRESHOLD = 0.45  # More lenient for philosophical arguments

chunk_boundaries = [i for i, sim in enumerate(similarities) if sim < threshold]
```

#### 4. Size Constraints
```python
MIN_CHUNK_SIZE = 200 tokens  # Avoid tiny chunks
MAX_CHUNK_SIZE = 1200 tokens # Prevent oversized chunks

# If chunk exceeds MAX, split at next boundary
# If chunk below MIN, merge with adjacent chunk
```

### Domain-Specific Thresholds (Automatic)

```python
DOMAIN_THRESHOLDS = {
    'philosophy': 0.45,  # More lenient (preserve longer arguments)
    'default': 0.55      # Stricter (tighter semantic boundaries)
}
```

**Philosophy threshold (0.45):** Allows related but distinct concepts to stay together (e.g., "words" and "body" in Mishima's argument about physical action vs intellectual expression)

**Default threshold (0.55):** Tighter boundaries for technical/literature content

### Integration

```python
# scripts/universal_chunking.py
class UniversalChunker:
    def __init__(self, embedding_model, threshold=0.5,
                 min_chunk_size=200, max_chunk_size=1200):
        self.model = embedding_model
        self.threshold = threshold
        self.min_size = min_chunk_size
        self.max_size = max_chunk_size

    def chunk(self, text: str) -> List[str]:
        # 1. Split into sentences
        # 2. Generate embeddings
        # 3. Calculate similarities
        # 4. Detect boundaries (similarity < threshold)
        # 5. Enforce size constraints
        return chunks
```

## Consequences

### Positive
- ✅ **Domain-agnostic:** Works for all content types without manual classification
- ✅ **Semantic coherence:** Chunks preserve meaning, not arbitrary token windows
- ✅ **Adaptable:** Philosophy gets longer arguments, technical gets focused concepts
- ✅ **No maintenance:** No author-specific patterns to maintain
- ✅ **Unified pipeline:** Single chunking algorithm for entire library
- ✅ **Implicit argument detection:** Doesn't need explicit keyword patterns

### Negative
- ⚠️ **Slower:** Requires sentence embedding generation (vs simple token splitting)
- ⚠️ **Embedding dependency:** Tied to all-MiniLM-L6-v2 model
- ⚠️ **Threshold tuning:** Requires domain-specific threshold calibration
- ⚠️ **Short text handling:** Struggles with very short passages (<100 tokens)

### Neutral
- Domain thresholds still needed but simpler (single value vs multiple patterns)
- Re-ingestion required to apply new chunking to existing collections

## Implementation

### Components
- **Chunking Strategies Component** (in Scripts Package)

### Files
- `scripts/universal_chunking.py` (136 lines) - Core algorithm
  - `UniversalChunker` class
  - `chunk()` method - main entry point
  - `_calculate_similarities()` - cosine similarity matrix
  - `_detect_boundaries()` - threshold-based boundary detection
  - `_enforce_size_constraints()` - min/max size enforcement

- `scripts/ingest_books.py` - Integration into ingestion pipeline
  - Uses `UniversalChunker` for all domains
  - Domain-specific threshold selection
  - Replaces old `create_chunks_from_sections()`

- `scripts/experiment_semantic.py` (109 lines) - Testing/validation
  - CLI tool for threshold experimentation
  - Side-by-side comparison of different thresholds
  - Chunk quality analysis

### Configuration
```python
# Hardcoded in ingest_books.py (lines 398-407)
threshold = 0.45 if domain == 'philosophy' else 0.55
chunker = UniversalChunker(
    embedder,
    threshold=threshold,
    min_chunk_size=200,
    max_chunk_size=1200
)
```

**Note:** Parameters should be configurable via Settings sidebar (see project-context.md Critical Rule #6)

### Usage
```python
from universal_chunking import UniversalChunker
from sentence_transformers import SentenceTransformer

# Initialize
model = SentenceTransformer('all-MiniLM-L6-v2')
chunker = UniversalChunker(model, threshold=0.55)

# Chunk text
chunks = chunker.chunk(book_text)
```

## Validation Results

**Test Case (2026-01-25):**
- Ingested multiple books from different domains
- Philosophy: Preserved arguments without explicit keyword detection
- Technical: Tight concept boundaries
- Literature: Natural narrative breaks

**Comparison to ADR 0005:**
- Same query quality for philosophical texts
- Simpler implementation (no author patterns)
- Works for domains beyond philosophy

## Supersedes

This ADR supersedes:
- **ADR 0002: Domain-Specific Chunking** - Replaced fixed token windows with semantic boundaries
- **ADR 0005: Philosophical Argument Chunking** - Replaced keyword-based detection with semantic similarity

## Alternatives Considered

### Alternative 1: Keep Domain-Specific Fixed Chunks (ADR 0002)
**Rejected:** Splits mid-sentence, no semantic awareness

### Alternative 2: Keep Philosophical Keyword Detection (ADR 0005)
**Rejected:** Only works for philosophy, high maintenance

### Alternative 3: LLM-Based Chunking
**Approach:** Use GPT-4 to identify natural chunk boundaries
**Pros:** Perfect semantic understanding
**Cons:** Slow (requires LLM call per book), expensive, non-deterministic
**Rejected:** Not scalable to 9,000 books

### Alternative 4: Hierarchical Chunking
**Approach:** Multiple chunk granularities (sentence, paragraph, section)
**Pros:** Flexible retrieval at different levels
**Cons:** Storage overhead, query complexity
**Status:** Under research (see docs/backlog/Hierarchical Chunking for Alexandria RAG.md)

## Future Enhancements

### Planned
1. **Configurable parameters:** Move threshold/min/max to Settings sidebar
2. **Interactive tuning:** GUI for threshold experimentation (lost after Haiku refactor)
3. **Adaptive thresholds:** Learn optimal threshold per book based on structure
4. **Multi-granular chunking:** Explore hierarchical approach

### Research Questions
- Can we auto-detect optimal threshold per book?
- Does semantic chunking improve retrieval for web articles/transcripts?
- How to handle dialogue-heavy texts (plays, interviews)?

## Related Decisions
- [ADR 0001: Use Qdrant Vector DB](0001-use-qdrant-vector-db.md) - Semantic chunks stored in Qdrant
- [ADR 0003: GUI as Thin Layer](0003-gui-as-thin-layer.md) - Chunking logic in scripts/
- [ADR 0006: Separate Systems Architecture](0006-separate-systems-architecture.md) - Collections use same chunking

## References
- **Implementation:** `scripts/universal_chunking.py`
- **Experiment tool:** `scripts/experiment_semantic.py`
- **C4 Component Diagram:** [03-component.md](../c4/03-component.md) - Chunking Strategies
- **Technical spec:** [UNIVERSAL_SEMANTIC_CHUNKING.md](../technical/UNIVERSAL_SEMANTIC_CHUNKING.md)

---

**Author:** Claude Code (Haiku) + User (Sabo)
**Reviewers:** User (Sabo)
**Implementation Date:** 2026-01-25
**Integration Commit:** d3ea719 "feat(ingestion): implement universal semantic chunking"
