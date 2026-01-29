You're right. Here's the complete version - all in one place:

---

## **Feature: Hierarchical Chunking for Alexandria RAG**

### Problem Statement
Current semantic chunking produces high-quality atomic chunks but loses broader context. Complex queries requiring understanding of relationships between concepts, "why/how" questions, and summarization tasks suffer because the LLM only sees isolated fragments without the surrounding narrative structure.

### Proposed Solution
Implement two-level hierarchical chunking:
- **Parent chunks**: Chapter or major section level (from Calibre/EPUB structure)
- **Child chunks**: Current semantic chunks, linked to parent

Retrieval becomes two-stage:
1. Find relevant child chunks (existing flow)
2. Expand context by including parent chunk or sibling chunks in LLM prompt

---

### Data Schema

**Qdrant Payload Schema (Extended)**

```python
# Parent Chunk Payload
{
    "id": "uuid",
    "text": "Full chapter/section text (may be truncated for embedding)",
    "full_text": "Complete untruncated text for LLM context",
    "book_title": "Beyond Good and Evil",
    "author": "Friedrich Nietzsche",
    "domain": "philosophy",
    "language": "en",
    "chunk_level": "parent",                    # NEW
    "section_name": "Part One: On the Prejudices of Philosophers",
    "section_index": 1,                         # NEW - chapter order in book
    "child_count": 23,                          # NEW - number of children
    "token_count": 8500,                        # NEW - for context budgeting
    "ingested_at": "2026-01-25T10:00:00Z",
    "strategy": "hierarchical",
    "metadata": {
        "source": "Beyond Good and Evil",
        "domain": "philosophy",
        "calibre_id": 1234                      # NEW - link to Calibre DB
    }
}

# Child Chunk Payload
{
    "id": "uuid",
    "text": "Semantic chunk text",
    "book_title": "Beyond Good and Evil",
    "author": "Friedrich Nietzsche",
    "domain": "philosophy",
    "language": "en",
    "chunk_level": "child",                     # NEW
    "parent_id": "parent-uuid",                 # NEW - reference to parent
    "section_name": "Part One: On the Prejudices of Philosophers",
    "sequence_index": 5,                        # NEW - order within parent
    "sibling_count": 23,                        # NEW - total siblings
    "token_count": 350,
    "sentence_range": [45, 52],                 # NEW - for sentence window fallback
    "ingested_at": "2026-01-25T10:00:00Z",
    "strategy": "universal-semantic",
    "metadata": {
        "source": "Beyond Good and Evil",
        "domain": "philosophy",
        "parent_id": "parent-uuid"
    }
}
```

**Index Requirements**
```python
# Payload indices for efficient filtering
payload_indices = [
    ("chunk_level", "keyword"),      # Filter parent vs child
    ("parent_id", "keyword"),        # Fetch children by parent
    ("book_title", "keyword"),       # Existing
    ("domain", "keyword"),           # Existing
    ("sequence_index", "integer"),   # Order siblings
]
```

---

### API Contract

**Modified `perform_rag_query()` Signature**

```python
def perform_rag_query(
    query: str,
    collection_name: str = 'alexandria',
    limit: int = 5,
    domain_filter: Optional[str] = None,
    threshold: float = 0.5,
    
    # NEW: Hierarchical options
    context_mode: Literal["precise", "contextual", "comprehensive"] = "contextual",
    include_parent_text: bool = True,          # Include full parent in response
    sibling_window: int = 2,                   # ±N siblings in comprehensive mode
    max_context_tokens: int = 12000,           # Budget for LLM context
    
    # Existing options
    enable_reranking: bool = False,
    rerank_model: Optional[str] = None,
    generate_llm_answer: bool = False,
    answer_model: Optional[str] = None,
    openrouter_api_key: Optional[str] = None,
    host: str = '192.168.0.151',
    port: int = 6333,
    fetch_multiplier: int = 3,
    temperature: float = 0.7
) -> RAGResult:
```

**Extended `RAGResult` Dataclass**

```python
@dataclass
class RAGResult:
    query: str
    results: List[Dict[str, Any]]
    answer: Optional[str] = None
    filtered_count: int = 0
    reranked: bool = False
    initial_count: int = 0
    error: Optional[str] = None
    
    # NEW: Hierarchical metadata
    context_mode: str = "precise"
    parent_chunks: List[Dict[str, Any]] = field(default_factory=list)
    total_context_tokens: int = 0
    hierarchy_stats: Dict[str, Any] = field(default_factory=dict)
    # e.g., {"parents_fetched": 3, "siblings_fetched": 12, "fallback_used": False}
```

**New Internal Functions**

```python
def fetch_parent_chunks(
    child_ids: List[str],
    collection_name: str,
    client: QdrantClient
) -> Dict[str, Dict]:
    """
    Fetch parent chunks for given children.
    Returns: {parent_id: parent_payload}
    """

def fetch_sibling_chunks(
    parent_id: str,
    center_sequence: int,
    window: int,
    collection_name: str,
    client: QdrantClient
) -> List[Dict]:
    """
    Fetch siblings within ±window of center_sequence.
    Returns ordered list of sibling payloads.
    """

def assemble_hierarchical_context(
    children: List[Dict],
    parents: Dict[str, Dict],
    siblings: Dict[str, List[Dict]],
    max_tokens: int,
    mode: str
) -> Tuple[str, int]:
    """
    Assemble final context string for LLM.
    Returns: (context_string, actual_token_count)
    
    Priority order for token budget:
    1. Matched children (always included)
    2. Parent summaries (truncated if needed)
    3. Siblings (included if budget allows)
    """

def detect_chapter_boundaries(
    epub_items: List,
    fallback_strategy: str = "page_count"
) -> List[Dict]:
    """
    Extract chapter/section structure from EPUB.
    
    Returns: [
        {"title": "Chapter 1", "text": "...", "index": 0},
        ...
    ]
    
    Fallback strategies:
    - "page_count": Split every N pages
    - "token_count": Split every M tokens
    - "single": Entire book as one parent
    """
```

---

### Retrieval Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        HIERARCHICAL RAG PIPELINE                            │
└─────────────────────────────────────────────────────────────────────────────┘

User Query: "Why does Nietzsche reject traditional morality?"
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 1: EMBEDDING & CHILD SEARCH                                            │
│                                                                             │
│   query_vector = embed(query)                                               │
│   children = qdrant.search(                                                 │
│       vector=query_vector,                                                  │
│       filter={"chunk_level": "child", "domain": domain_filter},            │
│       limit=limit * fetch_multiplier                                        │
│   )                                                                         │
│                                                                             │
│   Output: [child_1, child_2, child_3, ...] with scores                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 2: THRESHOLD FILTERING                                                 │
│                                                                             │
│   filtered = [c for c in children if c.score >= threshold]                 │
│                                                                             │
│   Output: Top N children above threshold                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 3: CONTEXT MODE BRANCHING                                              │
│                                                                             │
│   if context_mode == "precise":                                             │
│       → Skip to Step 6 (children only)                                      │
│                                                                             │
│   if context_mode == "contextual":                                          │
│       → Continue to Step 4 (fetch parents)                                  │
│                                                                             │
│   if context_mode == "comprehensive":                                       │
│       → Continue to Step 4 + Step 5 (parents + siblings)                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 4: FETCH PARENT CHUNKS                                                 │
│                                                                             │
│   parent_ids = unique([c.parent_id for c in filtered])                     │
│   parents = qdrant.retrieve(ids=parent_ids)                                │
│                                                                             │
│   # Deduplicate - multiple children may share parent                        │
│   Output: {parent_id: parent_payload}                                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼ (only if comprehensive)
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 5: FETCH SIBLING CHUNKS                                                │
│                                                                             │
│   for child in top_3_children:                                              │
│       siblings = qdrant.scroll(                                             │
│           filter={                                                          │
│               "parent_id": child.parent_id,                                │
│               "sequence_index": [child.seq - window, child.seq + window]   │
│           }                                                                 │
│       )                                                                     │
│                                                                             │
│   Output: {child_id: [sibling_1, sibling_2, ...]}                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 6: CONTEXT ASSEMBLY                                                    │
│                                                                             │
│   context = assemble_hierarchical_context(                                  │
│       children=filtered,                                                    │
│       parents=parents,                                                      │
│       siblings=siblings,                                                    │
│       max_tokens=max_context_tokens                                         │
│   )                                                                         │
│                                                                             │
│   Token budget allocation:                                                  │
│   ┌────────────────────────────────────────┐                               │
│   │ Children (matched)      │ 40% budget   │                               │
│   │ Parent context          │ 40% budget   │                               │
│   │ Siblings (if room)      │ 20% budget   │                               │
│   └────────────────────────────────────────┘                               │
│                                                                             │
│   Output: Assembled context string                                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 7: OPTIONAL RERANKING                                                  │
│                                                                             │
│   if enable_reranking:                                                      │
│       reranked = rerank_with_llm(children, query, rerank_model)            │
│                                                                             │
│   # Note: Reranking operates on children, not assembled context            │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 8: LLM ANSWER GENERATION                                               │
│                                                                             │
│   if generate_llm_answer:                                                   │
│       prompt = build_rag_prompt(                                            │
│           query=query,                                                      │
│           context=assembled_context,    # Includes parent/sibling context  │
│           children=filtered              # For citation                     │
│       )                                                                     │
│       answer = openrouter.complete(prompt, model=answer_model)             │
│                                                                             │
│   Output: RAGResult with answer + sources + hierarchy_stats                │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### Ingestion Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      HIERARCHICAL INGESTION PIPELINE                        │
└─────────────────────────────────────────────────────────────────────────────┘

Input: book.epub
           │
           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 1: EXTRACT & DETECT STRUCTURE                                          │
│                                                                             │
│   text, metadata = extract_text(filepath)                                   │
│   chapters = detect_chapter_boundaries(epub_items)                         │
│                                                                             │
│   Detection heuristics (in order):                                          │
│   1. EPUB NCX/TOC (most reliable)                                          │
│   2. HTML heading tags (h1, h2)                                            │
│   3. Calibre metadata (if available)                                       │
│   4. Fallback: every 5000 tokens = 1 parent                                │
│                                                                             │
│   Output: [                                                                 │
│       {"title": "Preface", "text": "...", "index": 0},                     │
│       {"title": "Part I", "text": "...", "index": 1},                      │
│       ...                                                                   │
│   ]                                                                         │
└─────────────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 2: CREATE PARENT CHUNKS                                                │
│                                                                             │
│   for chapter in chapters:                                                  │
│       parent_id = uuid()                                                    │
│                                                                             │
│       # Truncate for embedding if needed                                    │
│       embed_text = truncate(chapter.text, max_tokens=8192)                 │
│       parent_embedding = embed(embed_text)                                  │
│                                                                             │
│       parent_chunk = {                                                      │
│           "id": parent_id,                                                  │
│           "text": embed_text,                                               │
│           "full_text": chapter.text,      # Untruncated for retrieval      │
│           "chunk_level": "parent",                                          │
│           "section_name": chapter.title,                                    │
│           "section_index": chapter.index,                                   │
│           ...                                                               │
│       }                                                                     │
│                                                                             │
│   Output: List of parent chunks with IDs                                    │
└─────────────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 3: SEMANTIC CHUNKING PER PARENT                                        │
│                                                                             │
│   for parent in parents:                                                    │
│       children = universal_chunker.chunk(                                   │
│           text=parent.full_text,                                            │
│           metadata={                                                        │
│               "parent_id": parent.id,                                       │
│               "section_name": parent.section_name,                          │
│               ...                                                           │
│           }                                                                 │
│       )                                                                     │
│                                                                             │
│       # Assign sequence indices                                             │
│       for i, child in enumerate(children):                                  │
│           child["sequence_index"] = i                                       │
│           child["sibling_count"] = len(children)                           │
│           child["chunk_level"] = "child"                                   │
│                                                                             │
│       parent.child_count = len(children)                                   │
│                                                                             │
│   Output: All children with parent links and sequence info                  │
└─────────────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 4: GENERATE EMBEDDINGS                                                 │
│                                                                             │
│   parent_embeddings = embed([p.text for p in parents])                     │
│   child_embeddings = embed([c.text for c in all_children])                 │
│                                                                             │
│   # Batched for efficiency                                                  │
└─────────────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 5: UPLOAD TO QDRANT                                                    │
│                                                                             │
│   # Delete existing chunks for this book (if re-ingesting)                 │
│   qdrant.delete(filter={"book_title": book_title})                         │
│                                                                             │
│   # Upload parents first                                                    │
│   qdrant.upsert(parents, embeddings=parent_embeddings)                     │
│                                                                             │
│   # Upload children                                                         │
│   qdrant.upsert(children, embeddings=child_embeddings)                     │
│                                                                             │
│   Output: Collection updated with hierarchical structure                    │
└─────────────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 6: UPDATE MANIFEST                                                     │
│                                                                             │
│   manifest.add_book(                                                        │
│       ...                                                                   │
│       parent_count=len(parents),                                           │
│       child_count=len(all_children),                                       │
│       hierarchy_enabled=True                                               │
│   )                                                                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### Migration Strategy

**Approach: Incremental Re-ingestion**

Existing 9K books don't need big-bang migration. Strategy:

1. **Schema is additive** - new fields won't break old queries
2. **Mixed collection supported** - old chunks (no parent_id) coexist with new hierarchical chunks
3. **Fallback in retrieval** - if `parent_id` missing, skip context expansion gracefully
4. **Priority re-ingestion** - re-ingest high-value books first (frequently queried)

**Migration Script**

```python
# scripts/migrate_to_hierarchical.py

def migrate_collection(
    collection_name: str,
    priority_books: List[str] = None,   # Re-ingest these first
    batch_size: int = 10,
    dry_run: bool = True
):
    """
    Incrementally migrate collection to hierarchical format.
    
    1. If priority_books specified, migrate those first
    2. Otherwise, migrate by most-queried (if analytics available) or alphabetically
    3. Each book: delete old chunks → re-ingest with hierarchy
    4. Progress tracked in migration_progress.json
    """
```

**Migration Phases**

| Phase | Scope | Duration | Risk |
|-------|-------|----------|------|
| 1 | Schema update (additive) | 1 hour | None - backward compatible |
| 2 | New ingestions use hierarchy | Immediate | None - new books only |
| 3 | Re-ingest top 100 books | 1-2 days | Low - can rollback per-book |
| 4 | Background migration of remaining 8.9K | 2-3 weeks | Low - async, interruptible |

---

### Configuration

**New Config Options (`config.py` or environment)**

```python
# Hierarchical Chunking Config
HIERARCHY_ENABLED = True                      # Master switch
HIERARCHY_DEFAULT_MODE = "contextual"         # Default context_mode
HIERARCHY_SIBLING_WINDOW = 2                  # ±N siblings
HIERARCHY_MAX_CONTEXT_TOKENS = 12000          # Token budget for assembly
HIERARCHY_PARENT_MAX_TOKENS = 8192            # Max tokens for parent embedding

# Chapter Detection Config
CHAPTER_DETECTION_STRATEGY = "auto"           # auto | epub_toc | headers | fallback
CHAPTER_FALLBACK_TOKEN_COUNT = 5000           # Tokens per parent in fallback mode
CHAPTER_MIN_SIZE_TOKENS = 500                 # Don't create tiny parents

# Parent Embedding Config
PARENT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"   # Same as children by default
PARENT_STORE_FULL_TEXT = True                 # Store untruncated text
```

**GUI Config (Speaker's Corner)**

```python
# Streamlit session state defaults
st.session_state.setdefault("context_mode", "contextual")
st.session_state.setdefault("show_parent_context", True)
st.session_state.setdefault("sibling_window", 2)
```

---

### Error Handling

**Error Scenarios & Responses**

| Scenario | Detection | Response | User Message |
|----------|-----------|----------|--------------|
| Parent chunk not found | `parent_id` lookup returns None | Fallback to precise mode | "Extended context unavailable for this result" |
| Chapter detection fails | `chapters` list empty | Single parent for entire book | Warning in logs, continue |
| Parent too large for embedding | `token_count > 8192` | Truncate with `...` marker | None (internal handling) |
| Context assembly exceeds budget | `total_tokens > max_context_tokens` | Prioritized truncation | None (internal handling) |
| Sibling fetch timeout | Qdrant timeout | Skip siblings, use parent only | "Partial context retrieved" |
| Mixed collection (old + new chunks) | `parent_id` missing | Graceful degradation | None (transparent fallback) |

**Logging Levels**

```python
# Normal operation
logger.info(f"Hierarchical retrieval: {len(parents)} parents, {len(siblings)} siblings")

# Degraded operation
logger.warning(f"Parent not found for chunk {chunk_id}, falling back to precise mode")

# Configuration issues
logger.error(f"Chapter detection failed for {book_title}, using fallback strategy")
```

---

### Monitoring & Observability

**Metrics to Track**

```python
# Prometheus-style metrics (or simple counters for MVP)

metrics = {
    # Retrieval metrics
    "rag_queries_total": Counter,                    # Total queries
    "rag_queries_by_mode": Counter(labels=["mode"]), # precise/contextual/comprehensive
    "rag_context_tokens_used": Histogram,            # Token usage distribution
    "rag_parents_fetched": Histogram,                # Parents per query
    "rag_siblings_fetched": Histogram,               # Siblings per query
    "rag_fallback_used": Counter,                    # Times fallback triggered
    
    # Latency metrics
    "rag_child_search_latency_ms": Histogram,
    "rag_parent_fetch_latency_ms": Histogram,
    "rag_sibling_fetch_latency_ms": Histogram,
    "rag_total_latency_ms": Histogram,
    
    # Ingestion metrics
    "ingest_parents_created": Counter,
    "ingest_children_created": Counter,
    "ingest_chapter_detection_method": Counter(labels=["method"]),  # epub_toc/headers/fallback
}
```

**Health Check Additions**

```python
def health_check_hierarchical(collection_name: str) -> Dict:
    """
    Check hierarchical data integrity.
    
    Returns:
    {
        "total_parents": 1234,
        "total_children": 45678,
        "orphan_children": 0,         # Children with invalid parent_id
        "empty_parents": 0,           # Parents with no children
        "avg_children_per_parent": 37,
        "hierarchy_coverage": 0.95    # % of chunks with valid hierarchy
    }
    """
```

---

### GUI Changes (Speaker's Corner)

**Sidebar Additions**

```python
# New context mode selector (after existing query settings)
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 Context Depth")

context_mode = st.sidebar.radio(
    "Retrieval mode",
    options=["precise", "contextual", "comprehensive"],
    index=1,  # Default: contextual
    format_func=lambda x: {
        "precise": "⚡ Precise (fast, atomic chunks)",
        "contextual": "📖 Contextual (+ chapter context)",
        "comprehensive": "📚 Comprehensive (+ surrounding passages)"
    }[x],
    help="Controls how much context is retrieved alongside matched chunks"
)

show_hierarchy = st.sidebar.checkbox(
    "Show context hierarchy",
    value=True,
    help="Display parent chapter and sibling chunks in results"
)

if context_mode == "comprehensive":
    sibling_window = st.sidebar.slider(
        "Sibling window",
        min_value=1,
        max_value=5,
        value=2,
        help="Number of surrounding passages to include (±N)"
    )
else:
    sibling_window = 2  # Default, not shown
```

**Query Call Update**

```python
# Modified perform_rag_query call (lines ~2081-2096)
result = perform_rag_query(
    query=query,
    collection_name=query_collection,
    limit=query_limit,
    domain_filter=query_domain if query_domain != "all" else None,
    threshold=similarity_threshold,
    
    # NEW: Hierarchical options
    context_mode=context_mode,
    include_parent_text=show_hierarchy,
    sibling_window=sibling_window,
    max_context_tokens=12000,
    
    # Existing options
    enable_reranking=enable_reranking,
    rerank_model=rerank_model if enable_reranking else None,
    generate_llm_answer=True,
    answer_model=selected_model,
    openrouter_api_key=openrouter_api_key,
    host=qdrant_host,
    port=qdrant_port,
    fetch_multiplier=fetch_multiplier,
    temperature=temperature
)
```

**Results Display Enhancement**

```python
# Replace existing sources display (lines ~2122-2131)
st.markdown("---")
st.markdown("### 📚 Sources")

for idx, source in enumerate(result.sources, 1):
    score = source.get('score', 0)
    book_title = source.get('book_title', 'Unknown')
    section_name = source.get('section_name', 'Unknown')
    
    with st.expander(
        f"📖 Source {idx}: {book_title} (Relevance: {score:.3f})",
        expanded=(idx == 1)  # First result expanded by default
    ):
        # Metadata row
        col1, col2, col3 = st.columns(3)
        col1.markdown(f"**Author:** {source.get('author', 'Unknown')}")
        col2.markdown(f"**Domain:** {source.get('domain', 'Unknown')}")
        col3.markdown(f"**Section:** {section_name}")
        
        # Matched chunk (highlighted)
        st.markdown("#### 🎯 Matched Passage")
        st.info(source.get('text', '')[:1000])
        
        # Parent context (if available and enabled)
        if show_hierarchy:
            parent_context = source.get('parent_context')
            if parent_context:
                st.markdown("#### 📖 Chapter Context")
                with st.expander(f"View full chapter: {section_name}", expanded=False):
                    # Truncate very long chapters
                    display_text = parent_context[:3000]
                    if len(parent_context) > 3000:
                        display_text += "\n\n[... truncated ...]"
                    st.text(display_text)
            else:
                st.caption("ℹ️ Chapter context not available for this chunk")
        
        # Siblings (if comprehensive mode)
        if context_mode == "comprehensive":
            siblings = source.get('siblings', [])
            if siblings:
                st.markdown("#### 📄 Surrounding Passages")
                for sib in siblings:
                    seq = sib.get('sequence_index', '?')
                    sib_text = sib.get('text', '')[:300]
                    st.caption(f"[{seq}] {sib_text}...")
            elif show_hierarchy:
                st.caption("ℹ️ No surrounding passages available")
```

**Session State Additions**

```python
# Add to session state initialization (near line ~365)
if 'context_mode' not in st.session_state:
    st.session_state.context_mode = "contextual"
if 'show_hierarchy' not in st.session_state:
    st.session_state.show_hierarchy = True
if 'sibling_window' not in st.session_state:
    st.session_state.sibling_window = 2
```

**Settings Persistence (Optional)**

```python
# Add to gui_settings.json schema
{
    "library_dir": "G:\\My Drive\\alexandria",
    "show_ingestion_diagnostics": true,
    "context_mode": "contextual",        # NEW
    "show_hierarchy": true,              # NEW
    "sibling_window": 2                  # NEW
}
```

**Graceful Degradation for Mixed Collections**

```python
# Handle old chunks without hierarchy data
def display_source_with_fallback(source: dict, show_hierarchy: bool, context_mode: str):
    """Display source with graceful fallback for non-hierarchical chunks."""
    
    has_hierarchy = source.get('parent_id') is not None
    
    if not has_hierarchy and show_hierarchy:
        st.caption("⚠️ Extended context unavailable (legacy chunk format)")
    
    # Continue with normal display...
```

---

### Acceptance Criteria

**AC1: Data Model**
- [ ] Child chunks contain valid `parent_id` pointing to existing parent chunk
- [ ] Parent chunks have `chunk_level: "parent"` and contain full chapter/section text
- [ ] `sequence_index` correctly orders children within parent (0-indexed, contiguous)
- [ ] `sibling_count` matches actual number of children for parent
- [ ] `token_count` accurately reflects token count (within 5% of actual)
- [ ] Existing queries (without hierarchical features) continue to work unchanged
- [ ] Payload indices created for `chunk_level`, `parent_id`, `sequence_index`

**AC2: Ingestion**
- [ ] EPUB ingestion creates parent chunk per chapter with chapter title as `section_name`
- [ ] EPUB TOC/NCX parsing extracts chapter boundaries correctly
- [ ] PDF ingestion creates parent chunk per detected section (headers or fallback)
- [ ] TXT/MD ingestion uses token-based fallback (1 parent per 5000 tokens)
- [ ] All child chunks from same chapter share identical `parent_id`
- [ ] Re-ingestion of existing books correctly replaces old chunks (no orphans)
- [ ] Re-ingestion preserves hierarchy integrity (no broken parent_id references)
- [ ] Manifest tracks parent_count and child_count separately
- [ ] Ingestion logs chapter detection method used
- [ ] Parent chunks store both truncated (for embedding) and full text (for retrieval)

**AC3: Retrieval - Precise Mode**
- [ ] `context_mode="precise"` returns only child chunks (existing behavior)
- [ ] No additional Qdrant queries made for parents/siblings
- [ ] Latency unchanged from current implementation (<100ms p95)

**AC4: Retrieval - Contextual Mode**
- [ ] `context_mode="contextual"` fetches parent for each unique parent_id in results
- [ ] Parent text included in `parent_context` field of each result
- [ ] Duplicate parent fetches avoided (fetch each parent once)
- [ ] Token budget respected - parent text truncated if needed
- [ ] Graceful fallback if parent_id missing (old chunks)
- [ ] Latency increase <150ms vs precise mode

**AC5: Retrieval - Comprehensive Mode**
- [ ] `context_mode="comprehensive"` fetches siblings within ±sibling_window
- [ ] Siblings ordered by sequence_index in response
- [ ] Siblings deduplicated (matched chunk not repeated as sibling)
- [ ] Token budget allocation: 40% children, 40% parents, 20% siblings
- [ ] Latency increase <300ms vs precise mode

**AC6: Context Assembly**
- [ ] `assemble_hierarchical_context()` respects max_context_tokens
- [ ] Priority: children first, then parents, then siblings
- [ ] Truncation clearly marked with `[truncated]` indicator
- [ ] No context duplication (child text not repeated in parent context)
- [ ] Output is valid UTF-8, no encoding issues

**AC7: LLM Answer Generation**
- [ ] RAG prompt includes parent context when available
- [ ] Citations reference both chunk and parent chapter
- [ ] Answer quality improved on "why/how" queries (manual eval)
- [ ] No hallucinated cross-references between unrelated chapters

**AC8: GUI (Speaker's Corner)**
- [ ] Context mode selector visible in sidebar
- [ ] Results display parent context in expandable section
- [ ] Comprehensive mode shows siblings in UI
- [ ] "Show context hierarchy" toggle works
- [ ] No UI errors when hierarchy data missing (graceful degradation)

**AC9: Performance**
- [ ] Precise mode: <100ms p95 latency
- [ ] Contextual mode: <250ms p95 latency
- [ ] Comprehensive mode: <500ms p95 latency
- [ ] Ingestion speed: <10% slower than non-hierarchical
- [ ] Storage increase: <60% (parents + metadata overhead)

**AC10: Migration**
- [ ] Mixed collection (old + new chunks) works without errors
- [ ] Migration script can be interrupted and resumed
- [ ] Per-book rollback possible
- [ ] No data loss during migration

---

### Test Cases

**TC1: Ingestion - EPUB with clear chapters**
```
Given: "Beyond Good and Evil" EPUB (has 9 parts + preface)
When: Ingested with hierarchical chunking enabled
Then: 
  - 10 parent chunks created (1 per major section)
  - ~150-300 child chunks created (depending on threshold)
  - Each child has valid parent_id
  - Collection stats show parent_count=10, child_count=~200
  - Manifest updated with hierarchy_enabled=True
```

**TC2: Ingestion - PDF without clear structure**
```
Given: Scanned PDF with no TOC metadata, 50 pages
When: Ingested with hierarchical chunking enabled
Then:
  - Fallback: ~5-10 parent chunks (based on token count)
  - Children still created via semantic chunking
  - Log message: "No chapter structure detected, using token-based fallback"
  - All children have valid parent_id
```

**TC3: Ingestion - Small TXT file**
```
Given: Plain text file, 2000 tokens total
When: Ingested with hierarchical chunking enabled
Then:
  - 1 parent chunk (entire file)
  - ~5-15 child chunks (semantic)
  - All children reference single parent
```

**TC4: Retrieval - Contextual mode basic**
```
Given: Query "Why does Nietzsche reject traditional morality?"
       Collection has hierarchical Nietzsche books
When: perform_rag_query(query, context_mode="contextual")
Then:
  - Returns child chunks mentioning morality critique
  - Each result includes `parent_context` field
  - Parent context is full chapter text (truncated if >8K tokens)
  - hierarchy_stats shows {"parents_fetched": N, "fallback_used": False}
```

**TC5: Retrieval - Sibling expansion**
```
Given: Query "Explain the shipment pattern"
       Match is chunk at sequence_index=5 in chapter with 12 children
       sibling_window=2
When: perform_rag_query(query, context_mode="comprehensive")
Then:
  - Returns matched child chunk (seq 5)
  - siblings list contains chunks at seq 3, 4, 6, 7
  - Siblings ordered by sequence_index
  - Matched chunk NOT duplicated in siblings
```

**TC6: Retrieval - Token budget enforcement**
```
Given: Query matches 5 children from 3 different long chapters
       max_context_tokens=8000
       Each parent is 5000 tokens
When: perform_rag_query(query, context_mode="contextual", max_context_tokens=8000)
Then:
  - total_context_tokens <= 8000
  - Some parent contexts truncated with [truncated] marker
  - All 5 matched children included (they fit in 40% budget)
```

**TC7: Retrieval - Backward compatibility with old chunks**
```
Given: Collection has mix of old chunks (no parent_id) and new hierarchical chunks
       Query matches 3 old chunks and 2 new chunks
When: perform_rag_query(query, context_mode="contextual")
Then:
  - Query executes without error
  - New chunks have parent_context
  - Old chunks have parent_context=None (or empty)
  - Log warning: "Parent not found for N chunks, using fallback"
  - hierarchy_stats shows {"fallback_used": True}
```

**TC8: Retrieval - Empty results**
```
Given: Query "quantum entanglement in medieval poetry"
       No matching chunks above threshold
When: perform_rag_query(query, context_mode="contextual")
Then:
  - results=[]
  - parent_chunks=[]
  - No errors
  - hierarchy_stats shows {"parents_fetched": 0}
```

**TC9: Re-ingestion**
```
Given: Book "Thinking Fast and Slow" already in collection (old format, 500 chunks)
When: Re-ingested with hierarchical chunking
Then:
  - Old 500 chunks deleted
  - New parent chunks created (~30 chapters)
  - New child chunks created (~600)
  - Manifest updated with new counts
  - No orphan chunks (scroll full collection, no stale parent_ids)
```

**TC10: Performance baseline**
```
Given: 100 benchmark queries
       Collection with 50K hierarchical chunks
When: Run each query in precise, contextual, comprehensive modes
Then:
  - Precise: p50 <50ms, p95 <100ms
  - Contextual: p50 <150ms, p95 <250ms  
  - Comprehensive: p50 <250ms, p95 <500ms
```

**TC11: Chapter detection - EPUB with NCX**
```
Given: EPUB with valid NCX navigation document
When: detect_chapter_boundaries() called
Then:
  - Chapters extracted from NCX
  - Chapter titles match NCX labels
  - Chapter order matches NCX sequence
  - Log: "Chapter detection: epub_ncx, found 12 chapters"
```

**TC12: Chapter detection - EPUB without NCX**
```
Given: EPUB with no NCX, but has <h1> tags in content
When: detect_chapter_boundaries() called
Then:
  - Chapters extracted from h1 tags
  - Falls back to h2 if no h1
  - Log: "Chapter detection: html_headers, found 8 chapters"
```

**TC13: Chapter detection - Fallback**
```
Given: EPUB with no NCX and no recognizable headers
When: detect_chapter_boundaries() called
Then:
  - Fallback: split every 5000 tokens
  - Chapter names: "Section 1", "Section 2", etc.
  - Log: "Chapter detection: fallback_tokens, created 15 sections"
```

**TC14: GUI - Context mode switching**
```
Given: User in Speaker's Corner
When: User changes context mode from "precise" to "comprehensive"
       Then submits query
Then:
  - Query uses comprehensive mode
  - Results show sibling passages
  - Parent context visible in expander
  - No JavaScript/rendering errors
```

**TC15: GUI - Graceful degradation**
```
Given: User queries collection with only old-format chunks
When: Context mode is "contextual"
Then:
  - Results display normally
  - "Chapter context" section shows "Not available for this result"
  - No error messages or crashes
```

---

### Success Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Answer quality (why/how queries) | +20% improvement | Manual scoring 1-5 on 50 test queries |
| Answer quality (cross-reference) | +30% improvement | Manual scoring on 20 cross-ref queries |
| Hallucination rate | <5% fabricated refs | Manual audit of 100 answers |
| Retrieval coverage | >80% use parent context | hierarchy_stats.parents_fetched tracking |
| User satisfaction | Positive feedback | Qualitative from Speaker's Corner usage |
| Latency (contextual) | <250ms p95 | Automated benchmark suite |
| Latency (comprehensive) | <500ms p95 | Automated benchmark suite |
| Migration completion | 100% of 9K books | Manifest tracking |

---

### Effort Estimate

| Phase | Task | Effort | Dependency |
|-------|------|--------|------------|
| 1 | Data model & schema | 0.5 day | None |
| 2 | Chapter detection logic | 1 day | Phase 1 |
| 3 | Ingestion pipeline changes | 1.5 days | Phase 2 |
| 4 | Parent/sibling retrieval functions | 1 day | Phase 1 |
| 5 | Context assembly logic | 1 day | Phase 4 |
| 6 | RAG query integration | 0.5 day | Phase 5 |
| 7 | GUI updates | 1 day | Phase 6 |
| 8 | Migration script | 0.5 day | Phase 3 |
| 9 | Testing & edge cases | 1 day | All |
| 10 | Documentation | 0.5 day | All |
| **Total** | | **8.5 days** | |

---

### Dependencies

| Dependency | Status | Notes |
|------------|--------|-------|
| Calibre chapter metadata | ✅ Available | Via `ebooklib` NCX parsing |
| Qdrant payload schema | ✅ Flexible | Additive, non-breaking |
| OpenRouter API | ✅ Existing | For answer generation |
| `all-MiniLM-L6-v2` | ✅ Existing | Same model for parents |
| Storage capacity | ✅ Abundant | Qdrant has TB available |

---

### Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Chapter detection fails on poorly structured books | Low | Medium | Fallback to token-based parents, log warning |
| Parent chunks too large for embedding model | Medium | Low | Truncate to 8192 tokens, store full text separately |
| Re-ingestion breaks existing bookmarks/references | Low | Low | Document chunk ID changes, provide mapping |
| LLM context window exceeded with parent+children | Medium | Medium | Smart truncation with token budget, prioritize children |
| Latency exceeds targets | Medium | Low | Add caching for frequently-fetched parents |
| Mixed collection causes edge cases | Low | Medium | Comprehensive fallback handling, tested in TC7 |

---

### Open Questions (Decisions Required)

| Question | Options | Recommendation |
|----------|---------|----------------|
| Parent embedding model | Same as children vs larger model | Same (all-MiniLM-L6-v2) - consistency over marginal quality gain |
| Max parent token size | 4K / 8K / 16K | 8K - balances coverage vs embedding quality |
| Default context mode | precise / contextual / comprehensive | contextual - best quality/speed tradeoff |
| GUI: Parent context display | Inline vs accordion vs separate tab | Accordion (expandable) - doesn't clutter default view |
| Sibling window default | 1 / 2 / 3 | 2 - enough context without overwhelming |
| Migration priority | Alphabetical / by-domain / by-usage | By-domain (philosophy first - benefits most) |

---

### Rollback Plan

**If hierarchical causes issues:**

1. **Immediate** (no code change): Set `HIERARCHY_ENABLED=False` in config - falls back to precise mode for all queries

2. **Short-term**: Re-ingest affected books without hierarchy flag - restores flat structure

3. **Nuclear option**: Delete collection and re-ingest from scratch using old pipeline (preserved in git history)

**Rollback triggers:**
- Latency >2x targets for >24 hours
- Answer quality regression reported by users
- Data integrity issues (orphan children, broken refs)

---

### Documentation Updates Required

| Document | Changes |
|----------|---------|
| `scripts/README.md` | Add hierarchical chunking section, new CLI flags |
| `rag_query.py` docstring | Update with context_mode parameter |
| GUI help text | Explain context modes |
| `ARCHITECTURE.md` (new) | Document hierarchical data model |
| Manifest schema | Add parent_count, child_count, hierarchy_enabled fields |

---

### Post-Implementation Tasks

- [ ] Run full benchmark suite
- [ ] Document actual latency numbers
- [ ] Create "Top 100 priority books" list for Phase 3 migration
- [ ] Schedule background migration job for remaining 8.9K books
- [ ] Set up monitoring dashboard for hierarchy metrics
- [ ] Collect user feedback after 2 weeks
- [ ] Evaluate need for Phase 2 improvements (caching, larger models)

---

---

## Implementation Phasing (Recommended)

### Strategy: Clean Slate Approach
**Decision:** Delete existing indexes and re-ingest from scratch with hierarchical chunking enabled. Avoids mixed collection complexity and migration overhead.

### Phase 0: Basic Hierarchy (2 days)
**Goal:** Prove the concept with minimal GUI changes
- [ ] Implement parent/child data schema in Qdrant
- [ ] Add chapter detection logic (EPUB NCX/TOC + fallback)
- [ ] Modify ingestion pipeline to create parent chunks
- [ ] Implement `fetch_parent_chunks()` function
- [ ] Basic contextual retrieval (no GUI yet)
- [ ] Test with 5 books (Nietzsche, psychology classics)

**Success Criteria:**
- Parent chunks created with valid chapter boundaries
- Child chunks have correct parent_id references
- No orphan chunks or broken links

### Phase 1: Contextual Mode + GUI (1 day)
**Goal:** Make it usable in Speaker's Corner
- [ ] Add context mode selector to Streamlit sidebar
- [ ] Modify `perform_rag_query()` to support `context_mode` parameter
- [ ] Display parent context in results (expandable section)
- [ ] Update session state management

**Success Criteria:**
- Users can toggle contextual mode in GUI
- Parent chapter context visible in query results
- Latency <250ms p95 for contextual mode

### Phase 2: Evaluation (0.5 days)
**Goal:** Validate approach before full implementation
- [ ] Test 20 "why/how" questions (manual quality scoring)
- [ ] Compare answer quality: precise vs contextual
- [ ] Measure latency impact
- [ ] Collect user feedback

**Go/No-Go Decision:**
- ✅ GO if: answer quality +20%, latency acceptable, positive feedback
- ❌ NO-GO if: no improvement or major issues → rollback

### Phase 3: Comprehensive Mode (1 day)
**Goal:** Add sibling context for deep research queries
- [ ] Implement `fetch_sibling_chunks()` function
- [ ] Add sibling window slider to GUI
- [ ] Display surrounding passages in results
- [ ] Token budget enforcement

**Success Criteria:**
- Comprehensive mode shows ±N sibling chunks
- Total context stays within token budget
- Latency <500ms p95

### Phase 4: Full Re-ingestion (2-3 days)
**Goal:** Re-ingest entire library with hierarchical chunking
- [ ] Delete existing Qdrant collections
- [ ] Batch re-ingest all 9,000 books
- [ ] Resume capability if interrupted
- [ ] Update all manifests with hierarchy metadata

**Success Criteria:**
- All books successfully re-ingested
- Manifest tracking shows parent_count + child_count
- No data loss

### Phase 5: Production Hardening (1 day)
**Goal:** Monitoring, docs, optimization
- [ ] Add hierarchy metrics to health checks
- [ ] Document new API parameters
- [ ] Performance optimization (if needed)
- [ ] Update README and user guides

---

**Priority**: P1 (promoted from P2 - implement before Librarians)

**Owner**: TBD

**Last Updated**: 2026-01-29
