#!/usr/bin/env python3
"""
Alexandria of Temenos - Control Panel
RAG System Management Interface

Launch:
    streamlit run alexandria_app.py
"""

import streamlit as st
import sys
from pathlib import Path

# Add scripts to path
sys.path.append(str(Path(__file__).parent / 'scripts'))

from generate_book_inventory import scan_calibre_library, write_inventory
from count_file_types import count_file_types
from collection_manifest import CollectionManifest
import json

# Page config
st.set_page_config(
    page_title="Alexandria of Temenos",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for fancy styling
st.markdown("""
<style>
    /* Main title styling */
    .main-title {
        font-family: 'Georgia', serif;
        font-size: 3.5rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
        letter-spacing: 2px;
    }

    .subtitle {
        font-family: 'Georgia', serif;
        font-size: 1.2rem;
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
        font-style: italic;
    }

    /* Section headers */
    .section-header {
        font-family: 'Georgia', serif;
        font-size: 1.8rem;
        font-weight: 600;
        color: #667eea;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #667eea;
        padding-bottom: 0.5rem;
    }

    /* Stats box */
    .stat-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        margin: 0.5rem;
    }

    .stat-number {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }

    .stat-label {
        font-size: 1rem;
        opacity: 0.9;
    }

    /* Button styling */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        font-size: 1rem;
        border-radius: 5px;
        font-weight: 600;
    }

    .stButton>button:hover {
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-title">𝔸𝕝𝕖𝕩𝕒𝕟𝕕𝕣𝕚𝕒 𝕠𝕗 𝕋𝕖𝕞𝕖𝕟𝕠𝕤</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">η Βιβλιοθήκη της Αλεξάνδρειας • The Great Library Reborn</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Configuration")

    library_dir = st.text_input(
        "Library Directory",
        value="G:\\My Drive\\alexandria",
        help="Path to Calibre library"
    )

    qdrant_host = st.text_input(
        "Qdrant Host",
        value="192.168.0.151",
        help="Qdrant server IP"
    )

    qdrant_port = st.number_input(
        "Qdrant Port",
        value=6333,
        help="Qdrant server port"
    )

    st.markdown("---")
    st.markdown("### 📊 Quick Stats")

    # Load stats if available
    manifest_file = Path("logs/collection_manifest.json")
    if manifest_file.exists():
        with open(manifest_file, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
            total_collections = len(manifest.get('collections', {}))
            total_chunks = sum(c.get('total_chunks', 0) for c in manifest.get('collections', {}).values())
            st.metric("Collections", total_collections)
            st.metric("Total Chunks", f"{total_chunks:,}")
    else:
        st.info("No manifest found. Run ingestion first.")

# Main content
tab1, tab2, tab3, tab4 = st.tabs(["📚 Library", "🔄 Ingestion", "🔍 Query", "📊 Statistics"])

# ============================================
# TAB 1: Library Management
# ============================================
with tab1:
    st.markdown('<div class="section-header">📚 Library Management</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Book Inventory")
        if st.button("🔄 Generate Book Inventory", use_container_width=True):
            with st.spinner("Scanning Calibre library..."):
                try:
                    books = scan_calibre_library(library_dir)
                    output_file = "docs/book-inventory.txt"
                    write_inventory(books, output_file)
                    st.success(f"✅ Found {len(books):,} books!")
                    st.info(f"📄 Inventory saved to: {output_file}")
                except Exception as e:
                    st.error(f"❌ Error: {e}")

        if st.button("📊 Count File Types", use_container_width=True):
            with st.spinner("Analyzing file types..."):
                try:
                    extensions, total_size_by_ext, files_by_ext = count_file_types(library_dir, recursive=True)

                    total_files = sum(extensions.values())
                    total_size = sum(total_size_by_ext.values())

                    st.success(f"✅ Found {total_files:,} files")

                    # Display top formats
                    st.markdown("**Top File Formats:**")
                    for ext, count in extensions.most_common(10):
                        percentage = (count / total_files) * 100
                        st.write(f"- `{ext}`: {count:,} files ({percentage:.1f}%)")

                except Exception as e:
                    st.error(f"❌ Error: {e}")

    with col2:
        st.markdown("#### Search Books")
        search_query = st.text_input("Search by author or title", placeholder="e.g., Silverston, Kahneman")

        if search_query:
            inventory_file = Path("docs/book-inventory.txt")
            if inventory_file.exists():
                with open(inventory_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    matches = [line for line in lines if search_query.lower() in line.lower()]

                if matches:
                    st.success(f"Found {len(matches)} matches:")
                    st.code('\n'.join(matches[:20]), language=None)  # Show first 20
                else:
                    st.warning("No matches found.")
            else:
                st.warning("⚠️ Book inventory not generated yet. Click 'Generate Book Inventory' first.")

# ============================================
# TAB 2: Ingestion
# ============================================
with tab2:
    st.markdown('<div class="section-header">🔄 Ingestion Pipeline</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("#### Batch Ingestion")

        ingest_dir = st.text_input(
            "Ingest Directory",
            value="ingest",
            help="Directory containing books to ingest"
        )

        domain = st.selectbox(
            "Domain",
            ["technical", "psychology", "philosophy", "history"],
            help="Content domain for chunking strategy"
        )

        collection_name = st.text_input(
            "Collection Name",
            value="alexandria",
            help="Qdrant collection name"
        )

        # Domain-specific chunking defaults
        DOMAIN_DEFAULTS = {
            "technical": {"min": 1500, "max": 2000, "overlap": 200},
            "psychology": {"min": 1000, "max": 1500, "overlap": 150},
            "philosophy": {"min": 1200, "max": 1800, "overlap": 175},
            "history": {"min": 1500, "max": 2000, "overlap": 200}
        }

        defaults = DOMAIN_DEFAULTS[domain]

        # Track domain changes and reset values when domain changes
        if 'last_domain' not in st.session_state:
            st.session_state.last_domain = domain

        if st.session_state.last_domain != domain:
            # Domain changed - delete old widget values and update tracking
            for key in ['min_tokens', 'max_tokens', 'overlap_tokens']:
                if key in st.session_state:
                    del st.session_state[key]
            st.session_state.last_domain = domain
            st.rerun()

        # Use domain defaults as the value for widgets
        min_tokens_default = defaults["min"]
        max_tokens_default = defaults["max"]
        overlap_tokens_default = defaults["overlap"]

        # Advanced Settings Expander
        with st.expander("⚙️ Advanced Settings", expanded=False):
            st.markdown("#### Chunking Strategy")

            col_min, col_max, col_overlap = st.columns(3)

            with col_min:
                st.number_input(
                    "Min Tokens",
                    min_value=500,
                    max_value=3000,
                    value=min_tokens_default,
                    step=100,
                    help="Minimum chunk size in tokens",
                    key="min_tokens"
                )

            with col_max:
                st.number_input(
                    "Max Tokens",
                    min_value=500,
                    max_value=3000,
                    value=max_tokens_default,
                    step=100,
                    help="Maximum chunk size in tokens",
                    key="max_tokens"
                )

            with col_overlap:
                st.number_input(
                    "Overlap",
                    min_value=0,
                    max_value=500,
                    value=overlap_tokens_default,
                    step=50,
                    help="Token overlap between chunks",
                    key="overlap_tokens"
                )

            st.markdown("#### Embedding Configuration")

            # Check if collection exists and has data
            collection_is_empty = True
            collection_model_locked = False
            try:
                from qdrant_client import QdrantClient
                client = QdrantClient(host=qdrant_host, port=qdrant_port)

                # Try to get collection info
                try:
                    collection_info = client.get_collection(collection_name)
                    points_count = collection_info.points_count
                    if points_count > 0:
                        collection_is_empty = False
                        collection_model_locked = True
                except Exception:
                    # Collection doesn't exist yet
                    collection_is_empty = True
            except Exception as e:
                st.warning(f"⚠️ Cannot connect to Qdrant: {e}")

            embedding_models = ["all-MiniLM-L6-v2", "all-mpnet-base-v2", "multi-qa-MiniLM-L6-cos-v1"]
            embedding_model_default = st.session_state.get('embedding_model', "all-MiniLM-L6-v2")

            if collection_model_locked:
                # Show locked model (disabled dropdown)
                st.selectbox(
                    "Embedding Model (🔒 Locked)",
                    embedding_models,
                    index=embedding_models.index(embedding_model_default),
                    help="⚠️ LOCKED: Collection already contains data. Changing embedding model requires creating a new collection.",
                    key="embedding_model",
                    disabled=True
                )
                st.warning("⚠️ **Embedding model is locked** because collection already contains data. To use a different model, create a new collection or delete existing data.")
            else:
                st.selectbox(
                    "Embedding Model",
                    embedding_models,
                    index=embedding_models.index(embedding_model_default),
                    help="Sentence transformer model for embeddings. WARNING: Cannot be changed after first ingestion!",
                    key="embedding_model"
                )

            batch_size_default = st.session_state.get('batch_size', 100)
            st.number_input(
                "Batch Upload Size",
                min_value=10,
                max_value=500,
                value=batch_size_default,
                step=10,
                help="Number of chunks to upload per batch",
                key="batch_size"
            )

            # Reset button
            col_reset, col_info = st.columns([1, 3])
            with col_reset:
                if st.button("🔄 Reset to Defaults", use_container_width=True):
                    # Delete keys to force reset on next rerun
                    for key in ['min_tokens', 'max_tokens', 'overlap_tokens']:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.session_state.needs_reset = True
                    st.rerun()
            with col_info:
                current_min = st.session_state.get('min_tokens', min_tokens_default)
                current_max = st.session_state.get('max_tokens', max_tokens_default)
                current_overlap = st.session_state.get('overlap_tokens', overlap_tokens_default)
                st.info(f"📊 {current_min}-{current_max} tokens, {current_overlap} overlap")

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            start_ingest = st.button("🚀 Start Ingestion", use_container_width=True)
        with col_b:
            resume_ingest = st.button("▶️ Resume", use_container_width=True)
        with col_c:
            move_files = st.checkbox("Move completed files", value=True)

        if start_ingest:
            # Count selected books
            if 'selected_books' in st.session_state:
                selected_count = sum(1 for selected in st.session_state.selected_books.values() if selected)
            else:
                selected_count = 0

            if selected_count == 0:
                st.error("❌ No books selected for ingestion!")
            else:
                st.success(f"✅ Ready to ingest {selected_count} book(s)")

                # Display ingestion parameters
                st.info(f"""
                **Ingestion Parameters:**
                - Domain: {domain}
                - Collection: {collection_name}
                - Min Tokens: {st.session_state.get('min_tokens', defaults['min'])}
                - Max Tokens: {st.session_state.get('max_tokens', defaults['max'])}
                - Overlap: {st.session_state.get('overlap_tokens', defaults['overlap'])}
                - Embedding Model: {st.session_state.get('embedding_model', 'all-MiniLM-L6-v2')}
                - Batch Size: {st.session_state.get('batch_size', 100)}
                """)

                st.warning("🚧 **Ingestion via GUI is under development!**")
                st.info("💡 For now, manually run:")
                st.code(f"python scripts/batch_ingest.py --directory {ingest_dir} --domain {domain} --collection {collection_name}")

        if resume_ingest:
            st.warning("🚧 Resume functionality coming soon!")
            st.info("💡 For now, use: `python scripts/batch_ingest.py --directory ingest --resume`")

    with col2:
        st.markdown("#### Files in Ingest Folder")

        ingest_path = Path(ingest_dir)
        if ingest_path.exists():
            book_files = []
            supported_formats = {'.epub', '.pdf', '.txt', '.md'}

            for file in sorted(ingest_path.iterdir()):
                if file.is_file() and file.suffix.lower() in supported_formats:
                    size_mb = file.stat().st_size / (1024 * 1024)
                    book_files.append({
                        'name': file.name,
                        'format': file.suffix.lower(),
                        'size_mb': size_mb,
                        'path': str(file)
                    })

            if book_files:
                st.success(f"📚 {len(book_files)} books ready to ingest")

                # Initialize session state for checkboxes
                if 'selected_books' not in st.session_state:
                    st.session_state.selected_books = {book['name']: True for book in book_files}

                # Bulk selection controls
                col_all, col_none, col_epub = st.columns(3)
                with col_all:
                    if st.button("✅ Select All", key="select_all", use_container_width=True):
                        for book in book_files:
                            st.session_state.selected_books[book['name']] = True
                        st.rerun()
                with col_none:
                    if st.button("❌ Deselect All", key="deselect_all", use_container_width=True):
                        for book in book_files:
                            st.session_state.selected_books[book['name']] = False
                        st.rerun()
                with col_epub:
                    if st.button("📕 EPUB Only", key="epub_only", use_container_width=True):
                        for book in book_files:
                            st.session_state.selected_books[book['name']] = (book['format'] == '.epub')
                        st.rerun()

                st.markdown("---")

                # Checkboxes for each book
                selected_count = 0
                for book in book_files:
                    icon = "📕" if book['format'] == '.epub' else "📄" if book['format'] == '.pdf' else "📝"

                    # Checkbox with book info
                    is_selected = st.checkbox(
                        f"{icon} **{book['name']}** ({book['size_mb']:.1f} MB)",
                        value=st.session_state.selected_books.get(book['name'], True),
                        key=f"book_{book['name']}"
                    )
                    st.session_state.selected_books[book['name']] = is_selected

                    if is_selected:
                        selected_count += 1

                st.markdown("---")
                st.info(f"✅ **{selected_count}** of **{len(book_files)}** books selected for ingestion")

            else:
                st.info("📭 Ingest folder is empty. Add books to start ingestion.")
        else:
            st.warning(f"⚠️ Ingest folder not found: {ingest_dir}")

        st.markdown("---")

        st.markdown("#### Ingestion Progress")
        progress_file = Path("scripts/batch_ingest_progress.json")
        if progress_file.exists():
            with open(progress_file, 'r', encoding='utf-8') as f:
                progress = json.load(f)

            st.metric("Completed", progress.get('completed_files', 0))
            st.metric("Failed", progress.get('failed_files', 0))

            if progress.get('total_files', 0) > 0:
                pct = (progress.get('completed_files', 0) / progress.get('total_files', 1)) * 100
                st.progress(pct / 100)
                st.caption(f"{pct:.1f}% complete")
        else:
            st.info("No ingestion in progress.")

# ============================================
# TAB 3: Query
# ============================================
with tab3:
    st.markdown('<div class="section-header">🔍 Query Interface</div>', unsafe_allow_html=True)

    query = st.text_area(
        "Enter your question",
        placeholder="e.g., What does Silverston say about shipment patterns?",
        height=100
    )

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        query_collection = st.selectbox("Collection", ["alexandria", "alexandria_test"])
    with col2:
        query_domain = st.selectbox("Domain Filter", ["all", "technical", "psychology", "philosophy", "history"])
    with col3:
        query_limit = st.number_input("Results", min_value=1, max_value=20, value=5)

    if st.button("🔍 Search", use_container_width=True):
        if query:
            st.warning("🚧 Query interface coming soon!")
            st.info(f"💡 For now, use: `python scripts/rag_query.py \"{query}\" --limit {query_limit}`")
        else:
            st.warning("⚠️ Please enter a query.")

# ============================================
# TAB 4: Statistics
# ============================================
with tab4:
    st.markdown('<div class="section-header">📊 Collection Statistics</div>', unsafe_allow_html=True)

    if manifest_file.exists():
        with open(manifest_file, 'r', encoding='utf-8') as f:
            manifest = json.load(f)

        st.markdown("#### Collections Overview")

        for collection_name, collection_data in manifest.get('collections', {}).items():
            with st.expander(f"📚 {collection_name}", expanded=True):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Books", collection_data.get('total_books', 0))
                with col2:
                    st.metric("Chunks", f"{collection_data.get('total_chunks', 0):,}")
                with col3:
                    st.metric("Size", f"{collection_data.get('total_size_mb', 0):.1f} MB")

                # Book list
                st.markdown("**Books in Collection:**")
                books = collection_data.get('books', [])
                if books:
                    for book in books[:10]:  # Show first 10
                        st.write(f"- **{book.get('book_title')}** by {book.get('author')} ({book.get('chunks_count')} chunks)")

                    if len(books) > 10:
                        st.caption(f"... and {len(books) - 10} more books")
    else:
        st.info("📭 No collections found. Run ingestion to create collections.")

    st.markdown("---")

    if st.button("🔄 Refresh Statistics"):
        st.rerun()

# Footer
st.markdown("---")
st.markdown(
    '<div style="text-align: center; color: #666; font-style: italic;">'
    '𝔸𝕝𝕖𝕩𝕒𝕟𝕕𝕣𝕚𝕒 𝕠𝕗 𝕋𝕖𝕞𝕖𝕟𝕠𝕤 • '
    'Built with ❤️ by BMad Team • 2026'
    '</div>',
    unsafe_allow_html=True
)
