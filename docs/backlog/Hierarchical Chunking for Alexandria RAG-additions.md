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
