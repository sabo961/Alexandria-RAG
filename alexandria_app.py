#!/usr/bin/env python3
"""
Alexandria of Temenos - Dashboard
Simplified single-page interface for library management and RAG queries.

Launch:
    streamlit run alexandria_app.py
"""

import streamlit as st
import sys
import json
import requests
from pathlib import Path

# Add scripts to path
project_root = Path(__file__).parent
scripts_root = project_root / "scripts"
if str(scripts_root) not in sys.path:
    sys.path.insert(0, str(scripts_root))

from config import (
    QDRANT_HOST, QDRANT_PORT, QDRANT_COLLECTION,
    CALIBRE_LIBRARY_PATH, OPENROUTER_API_KEY
)
from qdrant_utils import check_qdrant_connection, list_collections
from calibre_db import CalibreDB
from rag_query import perform_rag_query
from collection_manifest import CollectionManifest

# =============================================================================
# PAGE CONFIG
# =============================================================================
st.set_page_config(
    page_title="Alexandria",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

@st.cache_data(ttl=60)
def check_qdrant_status():
    """Check Qdrant connection (cached for 60s)."""
    connected, error = check_qdrant_connection(QDRANT_HOST, QDRANT_PORT)
    return connected, error

@st.cache_data(ttl=300)
def get_collection_stats():
    """Get collection statistics (cached for 5min)."""
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        collections = client.get_collections().collections
        stats = {}
        for coll in collections:
            info = client.get_collection(coll.name)
            stats[coll.name] = info.points_count
        return stats
    except Exception as e:
        return {"error": str(e)}

@st.cache_data(ttl=300)
def load_calibre_books():
    """Load books from Calibre (cached for 5min)."""
    try:
        db = CalibreDB(CALIBRE_LIBRARY_PATH)
        return db.get_all_books()
    except Exception as e:
        return None, str(e)

@st.cache_data(ttl=60)
def load_manifest(collection_name: str):
    """Load manifest for collection from SQLite."""
    try:
        manifest = CollectionManifest(collection_name=collection_name)
        books = manifest.get_books(collection_name)
        if not books:
            return None
        summary = manifest.get_summary(collection_name)
        return {
            'books': books,
            'total_chunks': summary.get('total_chunks', 0),
            'total_size_mb': summary.get('total_size_mb', 0),
        }
    except Exception:
        return None

@st.cache_data(ttl=60)
def get_books_from_qdrant(collection_name: str):
    """Fallback: Get book list directly from Qdrant payloads."""
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

        # Scroll through collection to get unique books
        books = {}
        offset = None

        while True:
            results, offset = client.scroll(
                collection_name=collection_name,
                limit=500,
                offset=offset,
                with_payload=True,
                with_vectors=False
            )

            if not results:
                break

            for point in results:
                p = point.payload
                book_key = (p.get('book_title', 'Unknown'), p.get('author', 'Unknown'))
                if book_key not in books:
                    books[book_key] = {
                        'book_title': p.get('book_title', 'Unknown'),
                        'author': p.get('author', 'Unknown'),
                        'language': p.get('language', '?'),
                        'chunks_count': 0
                    }
                books[book_key]['chunks_count'] += 1

            if offset is None:
                break

        return list(books.values())
    except Exception as e:
        return None

def load_prompt_patterns():
    """Load prompt patterns from JSON."""
    patterns_file = project_root / "prompts" / "patterns.json"
    if patterns_file.exists():
        with open(patterns_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# =============================================================================
# SIDEBAR - Configuration & Status
# =============================================================================
with st.sidebar:
    st.title("⚙️ Configuration")

    # Connection Status
    st.subheader("Connection Status")
    qdrant_ok, qdrant_error = check_qdrant_status()

    if qdrant_ok:
        st.success(f"🟢 Qdrant: {QDRANT_HOST}:{QDRANT_PORT}")
    else:
        st.error(f"🔴 Qdrant: Disconnected")
        with st.expander("Error details"):
            st.code(qdrant_error)

    # Calibre status
    calibre_path = Path(CALIBRE_LIBRARY_PATH)
    if calibre_path.exists():
        st.success(f"🟢 Calibre: Connected")
        st.caption(f"📁 {CALIBRE_LIBRARY_PATH}")
    else:
        st.error(f"🔴 Calibre: Path not found")

    st.divider()

    # Quick Stats
    st.subheader("📊 Quick Stats")

    if qdrant_ok:
        stats = get_collection_stats()
        if "error" not in stats:
            for coll_name, count in stats.items():
                st.metric(f"📦 {coll_name}", f"{count:,} chunks")
        else:
            st.warning("Could not load stats")

    # Calibre book count
    books = load_calibre_books()
    if books and not isinstance(books, tuple):
        st.metric("📚 Calibre Library", f"{len(books):,} books")

    st.divider()

    # OpenRouter Settings (as fragment to avoid full page reruns)
    @st.fragment
    def openrouter_settings():
        st.subheader("🤖 OpenRouter")

        if OPENROUTER_API_KEY:
            st.success("🔑 API Key configured")

            # Fetch Models button
            if st.button("🔄 Fetch Models", use_container_width=True, key="fetch_models"):
                with st.spinner("Fetching models..."):
                    try:
                        response = requests.get(
                            "https://openrouter.ai/api/v1/models",
                            headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
                        )
                        if response.status_code == 200:
                            models_data = response.json().get("data", [])
                            openrouter_models = {}
                            for model in models_data:
                                model_id = model.get("id", "")
                                model_name = model.get("name", model_id)
                                pricing = model.get("pricing", {})
                                prompt_price = float(pricing.get("prompt", "1") or "1")
                                is_free = prompt_price == 0
                                emoji = "🆓" if is_free else "💰"
                                display_name = f"{emoji} {model_name}"
                                openrouter_models[display_name] = model_id

                            # Sort: free first, then alphabetically
                            sorted_models = dict(sorted(
                                openrouter_models.items(),
                                key=lambda x: (not x[0].startswith("🆓"), x[0])
                            ))
                            st.session_state['openrouter_models'] = sorted_models
                            st.success(f"✅ {len(sorted_models)} models loaded")
                        else:
                            st.error(f"API error: {response.status_code}")
                    except Exception as e:
                        st.error(f"Failed: {e}")

            # Model dropdown (if models fetched)
            if 'openrouter_models' in st.session_state and st.session_state['openrouter_models']:
                models = st.session_state['openrouter_models']

                # Try to restore last selection
                default_idx = 0
                if 'selected_model_name' in st.session_state:
                    try:
                        default_idx = list(models.keys()).index(st.session_state['selected_model_name'])
                    except ValueError:
                        default_idx = 0

                selected_name = st.selectbox(
                    "Model",
                    list(models.keys()),
                    index=default_idx,
                    help="🆓 = Free models",
                    key="model_select"
                )
                st.session_state['selected_model_name'] = selected_name
                st.session_state['selected_model'] = models[selected_name]
            else:
                st.caption("Click 'Fetch Models' to load available models")
                st.session_state['selected_model'] = None
        else:
            st.warning("🔑 No API key")
            st.caption("Add OPENROUTER_API_KEY to .env")
            st.session_state['selected_model'] = None

    openrouter_settings()

    st.divider()

    # Refresh button
    if st.button("🔄 Refresh All", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# =============================================================================
# MAIN AREA
# =============================================================================
st.title("📚 Alexandria of Temenos")
st.caption("Knowledge Management Dashboard")

# =============================================================================
# SECTION 1: Calibre Library
# =============================================================================
with st.expander("📚 Calibre Library", expanded=False):
    books = load_calibre_books()

    if books is None or isinstance(books, tuple):
        st.error(f"Could not connect to Calibre: {books[1] if isinstance(books, tuple) else 'Unknown error'}")
    else:
        # Filters
        col1, col2, col3 = st.columns(3)

        with col1:
            # Author filter
            authors = sorted(set(b.author for b in books))
            selected_author = st.selectbox("Author", ["All"] + authors, key="calibre_author")

        with col2:
            # Language filter
            languages = sorted(set(b.language for b in books))
            selected_lang = st.selectbox("Language", ["All"] + languages, key="calibre_lang")

        with col3:
            # Search
            search_term = st.text_input("Search title", key="calibre_search")

        # Filter books
        filtered = books
        if selected_author != "All":
            filtered = [b for b in filtered if b.author == selected_author]
        if selected_lang != "All":
            filtered = [b for b in filtered if b.language == selected_lang]
        if search_term:
            filtered = [b for b in filtered if search_term.lower() in b.title.lower()]

        st.caption(f"Showing {len(filtered)} of {len(books)} books")

        # Display as table
        if filtered:
            import pandas as pd
            df = pd.DataFrame([
                {
                    "Title": b.title,
                    "Author": b.author,
                    "Language": b.language,
                    "Formats": ", ".join(b.formats),
                    "Tags": ", ".join(b.tags[:3]) if b.tags else ""
                }
                for b in filtered[:100]  # Limit to 100 for performance
            ])
            st.dataframe(df, use_container_width=True, hide_index=True)

            if len(filtered) > 100:
                st.caption("Showing first 100 results. Use filters to narrow down.")

# =============================================================================
# SECTION 2: Ingested Books
# =============================================================================
with st.expander("📖 Ingested Books (Qdrant)", expanded=False):
    if not qdrant_ok:
        st.error("Qdrant not connected")
    else:
        # Collection selector
        stats = get_collection_stats()
        if "error" not in stats:
            collections = list(stats.keys())
            selected_coll = st.selectbox("Collection", collections, key="ingested_coll")

            # Load manifest for selected collection
            manifest_data = load_manifest(selected_coll)

            if manifest_data and manifest_data.get('books'):
                # Use manifest data (has more metadata like ingest date)
                st.metric("Total Chunks", f"{manifest_data.get('total_chunks', 0):,}")
                st.caption("📋 Source: Manifest")

                books_data = manifest_data.get('books', [])
                import pandas as pd
                df = pd.DataFrame([
                    {
                        "Title": b.get('book_title', 'Unknown'),
                        "Author": b.get('author', 'Unknown'),
                        "Chunks": b.get('chunks_count', 0),
                        "Language": b.get('language', '?'),
                        "Ingested": b.get('ingested_at', '')[:10]
                    }
                    for b in books_data
                ])
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                # Fallback: Query Qdrant directly
                st.caption("📋 Source: Qdrant (no manifest)")

                with st.spinner("Scanning collection..."):
                    books_data = get_books_from_qdrant(selected_coll)

                if books_data:
                    total_chunks = sum(b['chunks_count'] for b in books_data)
                    st.metric("Total Chunks", f"{total_chunks:,}")

                    import pandas as pd
                    df = pd.DataFrame([
                        {
                            "Title": b.get('book_title', 'Unknown'),
                            "Author": b.get('author', 'Unknown'),
                            "Chunks": b.get('chunks_count', 0),
                            "Language": b.get('language', '?'),
                        }
                        for b in books_data
                    ])
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.info("Collection is empty or could not be read.")
        else:
            st.error("Could not load collections")

# =============================================================================
# SECTION 3: Speaker's Corner
# =============================================================================
with st.expander("🗣️ Speaker's Corner", expanded=True):
    if not qdrant_ok:
        st.error("Qdrant not connected - cannot query")
    elif not OPENROUTER_API_KEY:
        st.warning("OpenRouter API key not configured")
        st.caption("Speaker's Corner requires OpenRouter for answer generation.")
        st.caption("Add OPENROUTER_API_KEY to your .env file.")
    else:
        # Load patterns
        patterns = load_prompt_patterns()

        # Query input
        st.subheader("💬 Your Question")
        query = st.text_area(
            "What do you want to know?",
            placeholder="e.g., What are the key principles of data modeling?",
            key="speaker_query",
            label_visibility="collapsed"
        )

        # Pattern selection (as fragment to avoid full page reruns)
        @st.fragment
        def pattern_selector():
            st.subheader("📝 Response Pattern")

            # Flatten patterns for dropdown
            pattern_options = {"None (just answer)": None}
            for category, items in patterns.items():
                for p in items:
                    display_name = f"{category.title()}: {p['name']}"
                    pattern_options[display_name] = p

            selected_pattern_name = st.selectbox(
                "How should the AI process the results?",
                list(pattern_options.keys()),
                key="speaker_pattern",
                label_visibility="collapsed"
            )
            selected_pattern = pattern_options[selected_pattern_name]

            # Store in session state for use outside fragment
            st.session_state['current_pattern'] = selected_pattern

            # Show pattern details
            if selected_pattern:
                st.info(f"💡 **Use case:** {selected_pattern.get('use_case', '')}")
                st.caption(f"🌡️ Temperature: {selected_pattern.get('temperature', 0.7)}")
                with st.expander("Pattern template"):
                    st.write(selected_pattern.get('template', ''))

        pattern_selector()
        selected_pattern = st.session_state.get('current_pattern')

        # Settings
        col1, col2, col3 = st.columns(3)
        with col1:
            num_results = st.slider("Chunks to retrieve", 3, 15, 5, key="speaker_chunks")
        with col2:
            threshold = st.slider("Similarity threshold", 0.0, 1.0, 0.3, 0.05, key="speaker_threshold")
        with col3:
            if selected_pattern:
                temperature = st.slider(
                    "Temperature", 0.0, 1.5,
                    selected_pattern.get('temperature', 0.7), 0.1,
                    key="speaker_temp"
                )
            else:
                temperature = st.slider("Temperature", 0.0, 1.5, 0.7, 0.1, key="speaker_temp")

        # Run button
        if st.button("🚀 Ask Alexandria", type="primary", use_container_width=True):
            if not query.strip():
                st.warning("Please enter a question")
            else:
                # Build final prompt
                if selected_pattern:
                    final_prompt = f"{query}\n\n---\nResponse instruction: {selected_pattern['template']}"
                else:
                    final_prompt = query

                with st.spinner("Searching knowledge base..."):
                    try:
                        result = perform_rag_query(
                            query=query,
                            collection_name=QDRANT_COLLECTION,
                            limit=num_results,
                            threshold=threshold,
                            host=QDRANT_HOST,
                            port=QDRANT_PORT,
                            generate_llm_answer=True,
                            answer_model=st.session_state.get('selected_model'),
                            openrouter_api_key=OPENROUTER_API_KEY,
                            temperature=temperature,
                            system_prompt=selected_pattern['template'] if selected_pattern else None
                        )

                        # Display answer
                        st.subheader("📜 Answer")
                        if result.answer:
                            st.markdown(result.answer)
                        else:
                            st.warning("No answer generated")

                        # Display sources
                        with st.expander(f"📚 Sources ({len(result.results)} chunks)"):
                            for i, chunk in enumerate(result.results, 1):
                                st.markdown(f"**{i}. {chunk.get('book_title', 'Unknown')}** by {chunk.get('author', 'Unknown')}")
                                st.caption(f"Score: {chunk.get('score', 0):.3f} | {chunk.get('section_name', '')}")
                                st.text(chunk.get('text', '')[:500] + "...")
                                st.divider()

                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                        with st.expander("Details"):
                            import traceback
                            st.code(traceback.format_exc())

# =============================================================================
# FOOTER
# =============================================================================
st.divider()
st.caption("Alexandria of Temenos • Built with Streamlit • 2026")
