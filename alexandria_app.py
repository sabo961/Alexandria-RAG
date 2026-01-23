#!/usr/bin/env python3
"""
Alexandria of Temenos - Control Panel
RAG System Management Interface

Launch:
    streamlit run alexandria_app.py
"""

import streamlit as st
import sys
import os
from pathlib import Path

# Add scripts to path
sys.path.append(str(Path(__file__).parent / 'scripts'))

from generate_book_inventory import scan_calibre_library, write_inventory
from count_file_types import count_file_types
from collection_manifest import CollectionManifest
from ingest_books import generate_embeddings, ingest_book
from qdrant_utils import delete_collection_and_artifacts
from rag_query import perform_rag_query
from calibre_db import CalibreDB
import json
import time
import pandas as pd


def render_ingestion_diagnostics(result: dict, context_label: str) -> None:
    """Render ingestion diagnostics in an expander if present."""
    diagnostics = result.get("diagnostics") if isinstance(result, dict) else None
    if diagnostics:
        st.session_state["last_ingestion_diagnostics"] = {
            "context": context_label,
            "captured_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "diagnostics": diagnostics
        }
        with st.expander(f"🔍 Diagnostics ({context_label})"):
            st.json(diagnostics)


def load_gui_settings() -> dict:
    """Load persisted GUI settings (non-sensitive)."""
    settings_path = Path(__file__).parent / '.streamlit' / 'gui_settings.json'
    if not settings_path.exists():
        return {}

    try:
        with open(settings_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def save_gui_settings(settings: dict) -> None:
    """Persist GUI settings to disk."""
    settings_path = Path(__file__).parent / '.streamlit' / 'gui_settings.json'
    settings_path.parent.mkdir(exist_ok=True)
    with open(settings_path, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)

# Constants
MANIFEST_GLOB_PATTERN = '*_manifest.json'

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
    /* Main title styling - uses monospace from theme */
    .main-title {
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
        font-size: 1.2rem;
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
        font-style: italic;
    }

    /* Hidden fancy header (preserved for future use) */
    .fancy-header {
        display: none;
    }

    /* Section headers - uses monospace from theme */
    .section-header {
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

    /* Compact ingestion output */
    .element-container:has(p) {
        margin-bottom: 0.25rem;
    }

    .stMarkdown p {
        margin-bottom: 0.25rem;
        line-height: 1.4;
    }

    /* Subtle pagination arrow buttons */
    .pagination-nav .stButton > button { /* Pagination buttons */
        background-color: transparent !important;
        border: none !important; /* Remove border */
        color: #bbb !important; /* Lighter color */
        border: none !important;
        color: transparent !important; /* Make text invisible until hover */
        box-shadow: none !important; /* Remove shadow */
        padding: 0.2rem 0.5rem !important; /* Smaller padding */
        font-size: 1rem !important; /* Slightly smaller font */
        transition: all 0.15s ease !important;
    }

    .pagination-nav .stButton > button:hover {
        background-color: #f0f0f0 !important; /* Subtle background on hover */
        border: 1px solid #ccc !important; /* Add a subtle border on hover */
        color: #666 !important; /* Darker color on hover */
        background-color: #f8f9fa !important; /* Very subtle background on hover */
        border: none !important;
        color: #888 !important; /* Make text visible on hover */
        box-shadow: none !important; /* Keep shadow removed */
    }

    .pagination-nav .stButton > button:active {
        transform: translateY(1px);
        box-shadow: none !important; /* Keep shadow removed */
    }

    /* ============================================
       TERMINAL / MATRIX MODE (Dark Theme)
       Activated when user selects Dark mode
       ============================================ */

    /* Matrix Terminal Mode relies on [theme.dark] config for base colors
       (monospace font, green primary color, dark backgrounds)
       No additional CSS needed - Streamlit applies the theme automatically */
</style>
""", unsafe_allow_html=True)

# ============================================
# HELPER FUNCTIONS
# ============================================

def load_domains():
    """Load domain list from domains.json"""
    domains_file = Path(__file__).parent / 'scripts' / 'domains.json'
    try:
        with open(domains_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return [d['id'] for d in data['domains']]
    except Exception as e:
        # Fallback to hardcoded list if file doesn't exist
        return ["technical", "psychology", "philosophy", "history", "literature"]

def run_batch_ingestion(selected_files, ingest_dir, domain, collection_name, host, port, move_files):
    """Run batch ingestion for selected files with dynamic chunk optimization"""
    import sys
    from pathlib import Path

    # File format constants
    EPUB_EXT = '.epub'
    PDF_EXT = '.pdf'
    TXT_EXT = '.txt'
    MD_EXT = '.md'

    # Import from scripts
    scripts_path = Path(__file__).parent / 'scripts'
    sys.path.insert(0, str(scripts_path))
    from ingest_books import (
        extract_text_from_epub,
        extract_text_from_pdf,
        extract_text_from_txt,
        calculate_optimal_chunk_params,
        create_chunks_from_sections,
        generate_embeddings,
        upload_to_qdrant
    )

    # Resolve all file paths to absolute paths BEFORE changing directory
    selected_files = [str(Path(f).resolve()) for f in selected_files]
    ingest_dir = str(Path(ingest_dir).resolve())

    # Change to scripts directory for CollectionManifest to find logs folder
    import os
    original_cwd = os.getcwd()
    os.chdir(scripts_path)

    from collection_manifest import CollectionManifest

    results = {
        'total': len(selected_files),
        'completed': 0,
        'failed': 0,
        'errors': []
    }

    # Initialize collection-specific manifest
    manifest = CollectionManifest(collection_name=collection_name)

    # Verify collection exists in Qdrant (reset manifest if deleted)
    manifest.verify_collection_exists(collection_name, qdrant_host=host, qdrant_port=port)

    for file_path in selected_files:
        try:
            st.write(f"📖 Processing: {Path(file_path).name}")

            # Use unified ingest_book function
            # This ensures consistency with CLI and respects domain-specific strategies
            result = ingest_book(
                filepath=file_path,
                domain=domain,
                collection_name=collection_name,
                qdrant_host=host,
                qdrant_port=port
            )

            if result and result.get('success'):
                # Update manifest
                manifest.add_book(
                    collection_name=collection_name,
                    book_path=file_path,
                    book_title=result['title'],
                    author=result['author'],
                    domain=domain,
                    chunks_count=result['chunks'],
                    file_size_mb=result['file_size_mb']
                )

                # Move file if requested and show combined success message
                if move_files:
                    import shutil
                    # Ensure we are moving relative to original ingest dir if needed
                    # But ingest_book uses absolute path, so we use that
                    ingested_dir = Path(ingest_dir).parent / 'ingested'
                    ingested_dir.mkdir(exist_ok=True)
                    
                    target_path = ingested_dir / Path(file_path).name
                    shutil.move(file_path, target_path)
                    
                    st.success(f"✅ {Path(file_path).name} - {result['chunks']} chunks uploaded  \n📦 Moved to: {target_path}")
                    render_ingestion_diagnostics(result, Path(file_path).name)
                else:
                    st.success(f"✅ {Path(file_path).name} - {result['chunks']} chunks uploaded")
                    render_ingestion_diagnostics(result, Path(file_path).name)

                results['completed'] += 1
            else:
                error_msg = result.get('error', 'Unknown error')
                raise Exception(error_msg)

        except Exception as e:
            st.error(f"❌ Failed: {Path(file_path).name}")
            st.error(f"   Error: {str(e)}")
            results['failed'] += 1
            results['errors'].append({'file': Path(file_path).name, 'error': str(e)})

    # Restore original directory
    os.chdir(original_cwd)

    return results


def check_qdrant_health(host: str, port: int, timeout: int = 5) -> tuple[bool, str]:
    """
    Check if Qdrant server is reachable and responsive.

    Args:
        host: Qdrant host (IP or hostname)
        port: Qdrant port
        timeout: Connection timeout in seconds (default: 5)

    Returns:
        Tuple of (is_healthy, message)
        - is_healthy: True if Qdrant is reachable, False otherwise
        - message: Status message ("Connected" or error description)
    """
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(host=host, port=port, timeout=timeout)
        # Test connection by fetching collections
        client.get_collections()
        return True, "Connected"
    except Exception as e:
        error_msg = str(e)
        # Simplify common error messages
        if "Connection refused" in error_msg or "Failed to connect" in error_msg:
            return False, f"Cannot reach {host}:{port}"
        elif "timeout" in error_msg.lower():
            return False, f"Timeout connecting to {host}:{port}"
        else:
            return False, f"Error: {error_msg[:50]}"


# Header - monospace for both light and dark themes
st.markdown('<div class="main-title">ALEXANDRIA OF TEMENOS</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">The Great Library Reborn</div>', unsafe_allow_html=True)

# Initialize session state for Qdrant health (will be set by sidebar)
if 'qdrant_healthy' not in st.session_state:
    st.session_state.qdrant_healthy = None

# Show warning banner if Qdrant is offline (set by sidebar health check)
if st.session_state.qdrant_healthy is False:
    st.error("⚠️ **Qdrant Vector Database is offline!** Ingestion and queries will not work. Check Qdrant server status and configuration in sidebar.")

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Configuration")

    gui_settings = load_gui_settings()
    default_library_dir = gui_settings.get("library_dir", "G:\\My Drive\\alexandria")

    if "library_dir" not in st.session_state:
        st.session_state.library_dir = default_library_dir

    library_dir = st.text_input(
        "Library Directory",
        value=st.session_state.library_dir,
        help="Path to Calibre library"
    )

    if library_dir != st.session_state.library_dir:
        st.session_state.library_dir = library_dir
        gui_settings["library_dir"] = library_dir
        try:
            save_gui_settings(gui_settings)
            st.caption("💾 Library directory saved")
        except Exception as e:
            st.warning(f"⚠️ Could not save library directory: {e}")

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

    # Qdrant Health Check
    is_healthy, health_message = check_qdrant_health(qdrant_host, qdrant_port)

    # Store health status in session state for banner display
    st.session_state.qdrant_healthy = is_healthy

    if is_healthy:
        st.success(f"✅ Qdrant: {health_message}")
    else:
        st.error(f"❌ Qdrant: {health_message}")
        st.warning("⚠️ Ingestion and queries will not work until Qdrant is available")

    last_diagnostics = st.session_state.get("last_ingestion_diagnostics")
    if last_diagnostics:
        st.markdown("---")
        st.markdown("### 🔍 Latest Ingestion Diagnostics")
        st.caption(f"{last_diagnostics['context']} • {last_diagnostics['captured_at']}")
        with st.expander("Show diagnostics"):
            st.json(last_diagnostics.get("diagnostics", {}))

    st.markdown("---")
    st.markdown("### 🔑 OpenRouter")

    # Initialize session state for API key if not present
    if 'openrouter_api_key' not in st.session_state:
        # Try to load from secrets.toml first (persistent across restarts)
        try:
            st.session_state.openrouter_api_key = st.secrets.get("OPENROUTER_API_KEY", "")
        except Exception:
            st.session_state.openrouter_api_key = ""

    openrouter_api_key = st.text_input(
        "OpenRouter API Key",
        type="password",
        value=st.session_state.openrouter_api_key,
        help="Get your API key from https://openrouter.ai/keys"
    )

    if st.button("💾 Save Permanently", use_container_width=True):
        if openrouter_api_key:
            # Save to session state
            st.session_state.openrouter_api_key = openrouter_api_key

            # Save to secrets.toml for persistence across restarts
            secrets_path = Path(__file__).parent / '.streamlit' / 'secrets.toml'
            try:
                secrets_path.parent.mkdir(exist_ok=True)
                with open(secrets_path, 'w') as f:
                    f.write('# Streamlit Secrets - DO NOT COMMIT TO GIT\n')
                    f.write('# This file stores sensitive API keys and credentials\n\n')
                    f.write('# OpenRouter API Key\n')
                    f.write('# Get your key from: https://openrouter.ai/keys\n')
                    f.write(f'OPENROUTER_API_KEY = "{openrouter_api_key}"\n')
                st.success("✅ Saved!")
            except Exception as e:
                st.error(f"❌ Failed: {e}")
        else:
            st.warning("⚠️ Enter API key first")

    # Model selection - Fetch from OpenRouter API
    if openrouter_api_key:
        if st.button("🔄 Fetch Models", use_container_width=True):
            with st.spinner("Fetching..."):
                try:
                    import requests
                    response = requests.get(
                        "https://openrouter.ai/api/v1/models",
                        headers={"Authorization": f"Bearer {openrouter_api_key}"}
                    )

                    if response.status_code == 200:
                        models_data = response.json().get("data", [])

                        # Build models dict with pricing info
                        openrouter_models = {}
                        for model in models_data:
                            model_id = model.get("id", "")
                            model_name = model.get("name", model_id)

                            # Check if free (pricing = 0)
                            pricing = model.get("pricing", {})
                            prompt_price = float(pricing.get("prompt", "0"))
                            completion_price = float(pricing.get("completion", "0"))
                            is_free = (prompt_price == 0 and completion_price == 0)

                            # Add emoji indicator
                            emoji = "🆓" if is_free else "💰"
                            display_name = f"{emoji} {model_name}"

                            openrouter_models[display_name] = model_id

                        # Sort: free first, then by name
                        sorted_models = dict(sorted(
                            openrouter_models.items(),
                            key=lambda x: (0 if x[0].startswith("🆓") else 1, x[0])
                        ))

                        # Store in session state
                        st.session_state['openrouter_models'] = sorted_models
                        st.success(f"✅ {len(sorted_models)} models")
                    else:
                        st.error(f"Failed: {response.status_code}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    # Use cached models or show empty state
    if 'openrouter_models' in st.session_state and st.session_state['openrouter_models']:
        openrouter_models = st.session_state['openrouter_models']
        st.caption(f"🆓 = Free, 💰 = Paid")

        # Find default index (last selected model if exists)
        default_index = 0
        if 'last_selected_model' in st.session_state:
            try:
                default_index = list(openrouter_models.keys()).index(st.session_state['last_selected_model'])
            except (ValueError, KeyError):
                default_index = 0

        selected_model_name = st.selectbox(
            "Select Model",
            list(openrouter_models.keys()),
            index=default_index,
            help="Free models are great for testing"
        )

        # Save last selected model
        st.session_state['last_selected_model'] = selected_model_name
        selected_model = openrouter_models[selected_model_name]
    else:
        # No models fetched yet
        selected_model_name = None
        selected_model = None

# Check for archives to conditionally show the Restore tab
archive_dir = Path(__file__).parent / 'logs' / 'archive'
archived_manifests_exist = archive_dir.exists() and any(archive_dir.glob('*_manifest_*.json'))

# Main content
tabs_to_show = [
    "📚 Calibre Library",
    "📖 Ingested Books",
    "🔄 Ingestion",
]
if archived_manifests_exist:
    tabs_to_show.append("🗄️ Restore from Archive")
tabs_to_show.append("🔍 Query")

tabs = st.tabs(tabs_to_show)

tab_calibre = tabs[0]
tab_ingested = tabs[1]
tab_ingestion = tabs[2]
tab_restore = tabs[3] if archived_manifests_exist else None
tab_query = tabs[-1]


# ============================================
# TAB 0: Calibre Library Browser
# ============================================
with tab_calibre:
    st.markdown('<div class="section-header">📚 Calibre Library</div>', unsafe_allow_html=True)

    # Initialize Calibre DB (Simple initialization, uses sidebar library_dir)
    try:
        if 'calibre_db' not in st.session_state or str(st.session_state.calibre_db.library_path) != str(Path(library_dir)):
            with st.spinner("Connecting to Calibre database..."):
                st.session_state.calibre_db = CalibreDB(library_dir)
                if 'calibre_books' in st.session_state:
                    del st.session_state.calibre_books

        calibre_db = st.session_state.calibre_db

        # Get all books
        if 'calibre_books' not in st.session_state:
            with st.spinner("Loading books from Calibre... (this may take a moment)"):
                st.session_state.calibre_books = calibre_db.get_all_books()

        all_books = st.session_state.calibre_books

        # Stats at top
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📚 Total Books", f"{len(all_books):,}")

        # Count unique authors
        unique_authors = len(set(b.author for b in all_books))
        col2.metric("✍️ Authors", f"{unique_authors:,}")

        # Count languages
        unique_languages = len(set(b.language for b in all_books))
        col3.metric("🌍 Languages", f"{unique_languages}")

        # Count formats
        all_formats = set()
        for book in all_books:
            all_formats.update(book.formats)
        col4.metric("📁 Formats", f"{len(all_formats)}")

        st.markdown("---")

        # Filters
        st.markdown("#### 🔍 Filters")
        filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)

        with filter_col1:
            author_search = st.text_input("Author", placeholder="e.g., Mishima", key="calibre_author_search")

        with filter_col2:
            title_search = st.text_input("Title", placeholder="e.g., Steel", key="calibre_title_search")

        with filter_col3:
            # Get available languages
            available_languages = sorted(set(b.language for b in all_books if b.language))
            language_filter = st.multiselect("Language", options=available_languages, key="calibre_language_filter")

        with filter_col4:
            # Get available formats
            format_options = sorted(all_formats)
            format_filter = st.multiselect("Format", options=format_options, key="calibre_format_filter")

        # Apply filters
        filtered_books = all_books

        if author_search:
            filtered_books = [b for b in filtered_books if author_search.lower() in b.author.lower()]

        if title_search:
            filtered_books = [b for b in filtered_books if title_search.lower() in b.title.lower()]

        if language_filter:
            filtered_books = [b for b in filtered_books if b.language in language_filter]

        if format_filter:
            filtered_books = [b for b in filtered_books if any(fmt in b.formats for fmt in format_filter)]

        # Sort options
        sort_col1, sort_col2 = st.columns([3, 1])
        with sort_col1:
            st.info(f"📚 Showing {len(filtered_books):,} of {len(all_books):,} books")

        with sort_col2:
            sort_by = st.selectbox("Sort by", [
                "Date Added (newest)",
                "Date Added (oldest)",
                "Title (A-Z)",
                "Title (Z-A)",
                "Author (A-Z)",
                "Author (Z-A)"
            ], key="calibre_sort")

        # Apply sorting
        if "newest" in sort_by:
            filtered_books = sorted(filtered_books, key=lambda x: x.timestamp, reverse=True)
        elif "oldest" in sort_by:
            filtered_books = sorted(filtered_books, key=lambda x: x.timestamp)
        elif "Title (A-Z)" in sort_by:
            filtered_books = sorted(filtered_books, key=lambda x: x.title.lower())
        elif "Title (Z-A)" in sort_by:
            filtered_books = sorted(filtered_books, key=lambda x: x.title.lower(), reverse=True)
        elif "Author (A-Z)" in sort_by:
            filtered_books = sorted(filtered_books, key=lambda x: x.author.lower())
        elif "Author (Z-A)" in sort_by:
            filtered_books = sorted(filtered_books, key=lambda x: x.author.lower(), reverse=True)

        # Display as DataFrame with pagination
        if filtered_books:
            # Pagination controls at top
            pagination_col1, pagination_col2, pagination_col3 = st.columns([1, 2, 1])

            with pagination_col1:
                rows_per_page = st.selectbox(
                    "Rows",
                    options=[20, 50, 100, 200],
                    index=1,  # Default to 50
                    key="calibre_rows_per_page"
                )

            # Initialize current page in session state
            if 'calibre_current_page' not in st.session_state:
                st.session_state.calibre_current_page = 1

            # Calculate total pages
            total_books = len(filtered_books)
            total_pages = (total_books + rows_per_page - 1) // rows_per_page  # Ceiling division

            # Ensure current page is within bounds
            if st.session_state.calibre_current_page > total_pages:
                st.session_state.calibre_current_page = total_pages
            if st.session_state.calibre_current_page < 1:
                st.session_state.calibre_current_page = 1

            current_page = st.session_state.calibre_current_page

            with pagination_col2:
                st.markdown(f"<div style='text-align: center; padding-top: 8px;'>Page {current_page} of {total_pages} ({total_books:,} total)</div>", unsafe_allow_html=True)

            # Calculate slice for current page
            start_idx = (current_page - 1) * rows_per_page
            end_idx = min(start_idx + rows_per_page, total_books)

            # Build DataFrame for current page with global row numbers
            df_data = []
            for idx, book in enumerate(filtered_books[start_idx:end_idx]):
                # Format icons
                format_icons = []
                if 'epub' in book.formats:
                    format_icons.append('📕')
                if 'pdf' in book.formats:
                    format_icons.append('📄')
                if 'mobi' in book.formats or 'azw3' in book.formats:
                    format_icons.append('📱')
                if 'txt' in book.formats or 'md' in book.formats:
                    format_icons.append('📝')

                # Series info
                series_info = f"{book.series} #{book.series_index:.0f}" if book.series else ""

                # Global row number (1-based)
                global_row_num = start_idx + idx + 1

                df_data.append({
                    '#': global_row_num,
                    '': ' '.join(format_icons) if format_icons else '📄',
                    'Title': book.title[:60] + '...' if len(book.title) > 60 else book.title,
                    'Author': book.author[:30] + '...' if len(book.author) > 30 else book.author,
                    'Language': book.language.upper(),
                    'Series': series_info,
                    'Formats': ', '.join(book.formats[:3]),  # Show first 3 formats
                    'Added': book.timestamp[:10]
                })

            df = pd.DataFrame(df_data)
            # Hide default index since we have our own "#" column
            st.dataframe(df, use_container_width=True, height=500, hide_index=True)

            # Pagination controls - minimal with arrow buttons
            st.markdown("<div style='margin: 10px 0;'></div>", unsafe_allow_html=True)
            st.markdown('<div class="pagination-nav">', unsafe_allow_html=True)

            nav_col1, nav_col2, nav_col3 = st.columns([0.3, 6, 0.3])

            with nav_col1:
                if current_page > 1 and st.button("←", key="calibre_prev", type="secondary"):
                    st.session_state.calibre_current_page -= 1
                    st.rerun()

            with nav_col2:
                st.markdown(
                    f"<div style='text-align: center; padding-top: 8px; color: #666; font-size: 13px;'>"
                    f"Rows {start_idx + 1}–{end_idx} of {total_books:,} &nbsp;|&nbsp; Page {current_page} of {total_pages}"
                    f"</div>",
                    unsafe_allow_html=True
                )

            with nav_col3:
                if current_page < total_pages and st.button("→", key="calibre_next", type="secondary"):
                    st.session_state.calibre_current_page += 1
                    st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

            # Direct Ingestion Section (collapsible)
            st.markdown("---")
            with st.expander("🚀 Direct Ingestion from Calibre", expanded=False):
                st.info("💡 Browse the table above, then select books here to ingest directly into Alexandria.")

                # Ingestion configuration
                config_col1, config_col2, config_col3 = st.columns(3)

                with config_col1:
                    calibre_domain = st.selectbox(
                        "Domain",
                        load_domains(),
                        help="Content domain for chunking strategy",
                        key="calibre_ingest_domain"
                    )

                with config_col2:
                    calibre_collection = st.text_input(
                        "Collection Name",
                        value="alexandria",
                        help="Qdrant collection name",
                        key="calibre_ingest_collection"
                    )

                with config_col3:
                    preferred_format = st.selectbox(
                        "Preferred Format",
                        ["epub", "pdf", "txt", "md"],
                        help="Which format to use when multiple available",
                        key="calibre_preferred_format"
                    )

                st.markdown("---")

                # Selection scope toggle
                selection_scope = st.radio(
                    "Selection scope",
                    options=["Current page only", "All filtered books (up to 500)"],
                    index=0,
                    horizontal=True,
                    help="Choose whether to select from current page or all filtered results"
                )

                # Create book selection multiselect
                if selection_scope == "Current page only":
                    # Show only books from current page
                    books_to_show = filtered_books[start_idx:end_idx]
                    scope_text = f"current page ({len(books_to_show)} books)"
                else:
                    # Show all filtered books (up to 500 for performance)
                    books_to_show = filtered_books[:500]
                    scope_text = f"all filtered results ({min(len(filtered_books), 500)} books)"

                book_options = {}
                for book in books_to_show:
                    # Format icons
                    icon = '📕' if 'epub' in book.formats else '📄' if 'pdf' in book.formats else '📝'
                    label = f"{icon} {book.title} — {book.author} ({', '.join(book.formats[:2])})"
                    book_options[label] = book

                selected_labels = st.multiselect(
                    f"Select books to ingest (from {scope_text})",
                    options=list(book_options.keys()),
                    help="Type to search, or scroll to select books. Use filters above to narrow down the list."
                )

                selected_books = [book_options[label] for label in selected_labels]

                # Display selection summary and ingest button
                st.markdown("---")
                if selected_books:
                    st.info(f"📊 **Selected:** {len(selected_books)} book(s) ready for ingestion")

                    if st.button("🚀 Start Ingestion", type="primary", use_container_width=True):
                        # Show configuration being used
                        st.info(f"ℹ️ Ingesting to: {qdrant_host}:{qdrant_port} | Collection: {calibre_collection} | Domain: {calibre_domain}")

                        # Initialize manifest for tracking (collection-specific)
                        manifest = CollectionManifest(collection_name=calibre_collection)

                        # Progress tracking
                        progress_bar = st.progress(0)
                        status_text = st.empty()

                        success_count = 0
                        error_count = 0
                        errors = []
                        ingested_books = []

                        for idx, book in enumerate(selected_books):
                            # Update progress
                            progress = (idx + 1) / len(selected_books)
                            progress_bar.progress(progress)
                            status_text.text(f"Ingesting {idx + 1}/{len(selected_books)}: {book.title}")

                            try:
                                # Determine which format to use
                                format_to_use = None
                                if preferred_format in book.formats:
                                    format_to_use = preferred_format
                                else:
                                    # Fallback to first available format
                                    format_to_use = book.formats[0] if book.formats else None

                                if not format_to_use:
                                    errors.append(f"{book.title}: No supported format available")
                                    error_count += 1
                                    continue

                                # Construct absolute file path
                                # Strategy: Use the actual 'library_dir' variable from the sidebar
                                # to ensure we are looking relative to the user's current choice.
                                active_library_path = Path(library_dir)
                                book_dir = active_library_path / book.path

                                # Find the actual file
                                matching_files = list(book_dir.glob(f"*.{format_to_use}"))

                                if not matching_files:
                                    # Try one more fallback: if the database thinks it's on G: but sidebar says C:
                                    # calibre_db.library_path might be different from the sidebar 'library_dir'
                                    errors.append(f"{book.title}: File not found at {book_dir}")
                                    error_count += 1
                                    continue

                                file_path = matching_files[0]
                                st.write(f"📂 Accessing: {file_path}")

                                # Ingest the book
                                result = ingest_book(
                                    filepath=str(file_path),
                                    domain=calibre_domain,
                                    collection_name=calibre_collection,
                                    qdrant_host=qdrant_host,
                                    qdrant_port=qdrant_port
                                )

                                if result and result.get('success'):
                                    success_count += 1
                                    ingested_books.append({
                                        'file_path': result['filepath'],
                                        'book_title': result['title'],
                                        'author': result['author'],
                                        'domain': calibre_domain,
                                        'chunks': result['chunks'],
                                        'file_size_mb': result['file_size_mb']
                                    })
                                    render_ingestion_diagnostics(result, book.title)
                                else:
                                    error_msg = result.get('error', 'Failed to extract content or ingest') if result else 'Unknown error'
                                    errors.append(f"{book.title}: {error_msg}")
                                    error_count += 1
                                    if result:
                                        render_ingestion_diagnostics(result, book.title)

                            except Exception as e:
                                errors.append(f"{book.title}: {str(e)} \n   (Path: {str(file_path)})")
                                error_count += 1

                        # Final status
                        progress_bar.progress(1.0)
                        status_text.text("✅ Ingestion complete!")

                        # Update manifest with successfully ingested books
                        if ingested_books:
                            for book_info in ingested_books:
                                manifest.add_book(
                                    collection_name=calibre_collection,
                                    book_path=book_info['file_path'],
                                    book_title=book_info['book_title'],
                                    author=book_info['author'],
                                    domain=book_info['domain'],
                                    chunks_count=book_info['chunks'],
                                    file_size_mb=book_info['file_size_mb']
                                )
                            st.success(f"📝 Updated manifest with {len(ingested_books)} book(s)")

                        # Verify ingestion by checking collection
                        try:
                            from qdrant_client import QdrantClient
                            client = QdrantClient(host=qdrant_host, port=qdrant_port)
                            collection_info = client.get_collection(calibre_collection)
                            st.info(f"🔍 Collection '{calibre_collection}' now has {collection_info.points_count:,} total points")
                        except Exception as e:
                            st.warning(f"⚠️ Could not verify collection: {e}")

                        if success_count > 0:
                            st.success(f"✅ Successfully ingested {success_count} books!")

                        if error_count > 0:
                            st.error(f"❌ Failed to ingest {error_count} books")
                            with st.expander("Show errors"):
                                for error in errors:
                                    st.text(f"• {error}")
                else:
                    st.info("👆 Select books from the multiselect above to begin")

            if len(filtered_books) > 500:
                st.warning(f"⚠️ Showing first 500 books. {len(filtered_books) - 500} more books match your filters. Refine filters to see more.")

        else:
            st.warning("No books match the filters.")

    except Exception as e:
        st.error(f"❌ Error connecting to Calibre database: {e}")
        st.info("Make sure the Calibre library path is correct in the sidebar.")

# ============================================
# TAB 1: Ingested Books
# ============================================
with tab_ingested:
    st.markdown('<div class="section-header">📖 Ingested Books</div>', unsafe_allow_html=True)

    # Collection selector
    manifest_col1, manifest_col2 = st.columns([2, 2])

    with manifest_col1:
        try:
            # Load manifest to get available collections
            from pathlib import Path as PathLib
            manifest_dir = PathLib(__file__).parent / 'logs'
            manifest_files = list(manifest_dir.glob(MANIFEST_GLOB_PATTERN))

            if manifest_files:
                collection_names = [f.stem.replace('_manifest', '') for f in manifest_files]
                selected_collection = st.selectbox("Collection", collection_names, index=0, key="ingested_collection_select")
            else:
                st.warning("No collections found. Run ingestion first.")
                selected_collection = None
        except Exception as e:
            st.error(f"Error loading collections: {e}")
            selected_collection = None

    if selected_collection:
        try:
            # Load manifest for selected collection
            manifest = CollectionManifest(collection_name=selected_collection)

            if selected_collection in manifest.manifest['collections']:
                collection_data = manifest.manifest['collections'][selected_collection]
                books = collection_data['books']

                # Stats at top
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("📚 Books", f"{len(books)}")
                col2.metric("🧩 Chunks", f"{collection_data['total_chunks']:,}")
                col3.metric("💾 Size", f"{collection_data['total_size_mb']:.1f} MB")

                # Count formats
                formats_count = len(set(b.get('file_type', 'UNKNOWN') for b in books))
                col4.metric("📁 Formats", f"{formats_count}")

                st.markdown("---")

                # Filters
                st.markdown("#### 🔍 Filters")
                ing_filter_col1, ing_filter_col2, ing_filter_col3, ing_filter_col4 = st.columns(4)

                with ing_filter_col1:
                    ing_author_search = st.text_input("Author", placeholder="e.g., Mishima", key="ingested_author_search")

                with ing_filter_col2:
                    ing_title_search = st.text_input("Title", placeholder="e.g., Steel", key="ingested_title_search")

                with ing_filter_col3:
                    # Get available languages (with fallback for old manifests)
                    available_langs = sorted(set(b.get('language', 'unknown') for b in books))
                    ing_language_filter = st.multiselect("Language", options=available_langs, key="ingested_language_filter")

                with ing_filter_col4:
                    # Get available domains
                    available_domains = sorted(set(b['domain'] for b in books))
                    ing_domain_filter = st.multiselect("Domain", options=available_domains, key="ingested_domain_filter")

                # Format filter (separate row)
                ing_format_filter = st.multiselect("Format", options=['EPUB', 'PDF', 'TXT', 'MD', 'MOBI'], key="ingested_format_filter")

                # Apply filters
                filtered_books = books

                if ing_author_search:
                    filtered_books = [b for b in filtered_books if ing_author_search.lower() in b['author'].lower()]

                if ing_title_search:
                    filtered_books = [b for b in filtered_books if ing_title_search.lower() in b['book_title'].lower()]

                if ing_language_filter:
                    filtered_books = [b for b in filtered_books if b.get('language', 'unknown') in ing_language_filter]

                if ing_domain_filter:
                    filtered_books = [b for b in filtered_books if b['domain'] in ing_domain_filter]

                if ing_format_filter:
                    filtered_books = [b for b in filtered_books if b.get('file_type', PathLib(b['file_name']).suffix.upper().replace('.', '')) in ing_format_filter]

                # Sort options
                ing_sort_col1, ing_sort_col2 = st.columns([3, 1])
                with ing_sort_col1:
                    st.info(f"📚 Showing {len(filtered_books)} of {len(books)} books")

                with ing_sort_col2:
                    ing_sort_by = st.selectbox("Sort by", [
                        "Ingested (newest)",
                        "Ingested (oldest)",
                        "Title (A-Z)",
                        "Author (A-Z)",
                        "Chunks (most)",
                        "Size (largest)"
                    ], key="ingested_sort")

                # Apply sorting
                if "newest" in ing_sort_by:
                    filtered_books = sorted(filtered_books, key=lambda x: x['ingested_at'], reverse=True)
                elif "oldest" in ing_sort_by:
                    filtered_books = sorted(filtered_books, key=lambda x: x['ingested_at'])
                elif "Title" in ing_sort_by:
                    filtered_books = sorted(filtered_books, key=lambda x: x['book_title'].lower())
                elif "Author" in ing_sort_by:
                    filtered_books = sorted(filtered_books, key=lambda x: x['author'].lower())
                elif "Chunks" in ing_sort_by:
                    filtered_books = sorted(filtered_books, key=lambda x: x['chunks_count'], reverse=True)
                elif "Size" in ing_sort_by:
                    filtered_books = sorted(filtered_books, key=lambda x: x['file_size_mb'], reverse=True)

                # Display as DataFrame
                if filtered_books:
                    df_data = []
                    for book in filtered_books:
                        # Get file type
                        file_type = book.get('file_type')
                        if not file_type:
                            file_type = PathLib(book['file_name']).suffix.upper().replace('.', '')

                        # Icon
                        icon = {'EPUB': '📕', 'PDF': '📄', 'TXT': '📝', 'MD': '📝', 'MOBI': '📱'}.get(file_type, '📄')

                        # Language with fallback
                        language = book.get('language', 'unknown').upper()

                        df_data.append({
                            '': icon,
                            'Title': book['book_title'][:50] + '...' if len(book['book_title']) > 50 else book['book_title'],
                            'Author': book['author'][:30] + '...' if len(book['author']) > 30 else book['author'],
                            'Lang': language,
                            'Domain': book['domain'],
                            'Type': file_type,
                            'Chunks': book['chunks_count'],
                            'Size (MB)': f"{book['file_size_mb']:.2f}",
                            'Ingested': book['ingested_at'][:10]
                        })

                    df = pd.DataFrame(df_data)
                    st.dataframe(df, use_container_width=True, height=600)
                else:
                    st.warning("No books match the filters.")

                # Export button and Management Section
                st.markdown("---")
                manage_col1, manage_col2 = st.columns([1, 3])

                with manage_col1:
                    csv_file = PathLib(f'logs/{selected_collection}_manifest.csv')
                    if csv_file.exists():
                        with open(csv_file, 'r', encoding='utf-8') as f:
                            csv_data = f.read()
                        st.download_button(
                            label="📥 Download CSV",
                            data=csv_data,
                            file_name=f"{selected_collection}_manifest.csv",
                            mime="text/csv",
                            use_container_width=True
                        )

                with st.expander("⚙️ Collection Management"):
                    st.warning(f"**DANGER ZONE:** Actions performed here are permanent and cannot be undone.")
                    st.markdown(f"You are about to delete the entire **`{selected_collection}`** collection from Qdrant, along with its manifest files.")

                    # Confirmation state management
                    if 'confirm_delete' not in st.session_state:
                        st.session_state.confirm_delete = None

                    if st.session_state.confirm_delete != selected_collection:
                        if st.button(f"🗑️ Delete '{selected_collection}' Collection", use_container_width=True):
                            st.session_state.confirm_delete = selected_collection
                            st.rerun()
                    else:
                        st.error(f"**Are you sure?** This will permanently delete the Qdrant collection and all associated manifest files. This action cannot be undone.")
                        confirm_col1, confirm_col2 = st.columns(2)
                        with confirm_col1:
                            if st.button("🚨 YES, DELETE PERMANENTLY", use_container_width=True, type="primary"):
                                with st.spinner(f"Deleting collection '{selected_collection}' and all its data..."):
                                    delete_results = delete_collection_and_artifacts(collection_name=selected_collection, host=qdrant_host, port=qdrant_port)

                                if not delete_results['errors']:
                                    st.success(f"✅ Collection '{selected_collection}' and its artifacts have been deleted.")
                                    st.session_state.confirm_delete = None
                                    st.info("Refreshing app...")
                                    time.sleep(2)
                                    st.rerun()
                                else:
                                    st.error(f"❌ Failed to completely delete collection '{selected_collection}'.")
                                    for error in delete_results['errors']:
                                        st.error(f"- {error}")
                                    st.session_state.confirm_delete = None
                        with confirm_col2:
                            if st.button("Cancel", use_container_width=True):
                                st.session_state.confirm_delete = None
                                st.rerun()
            else:
                st.info(f"Collection '{selected_collection}' has no ingested books yet.")

        except Exception as e:
            st.error(f"Error loading manifest: {e}")
            import traceback
            st.code(traceback.format_exc())

# ============================================
# TAB 2: Ingestion
# ============================================
with tab_ingestion:
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
            load_domains(),
            help="Content domain for chunking strategy"
        )

        collection_name = st.text_input(
            "Collection Name",
            value="alexandria",
            help="Qdrant collection name"
        )

        # Advanced Settings Expander
        with st.expander("⚙️ Advanced Settings", expanded=False):
            st.markdown("#### Chunking Strategy")
            st.info("""
                🤖 **Automatic Optimization Enabled**

                Chunking parameters are automatically calculated based on:
                - Content size and structure
                - Domain-specific strategies
                - Token distribution analysis

                Target efficiency: 85-90% of optimal chunk count
            """)

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

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            start_ingest = st.button("🚀 Start Ingestion", use_container_width=True)
        with col_b:
            resume_ingest = st.button("▶️ Resume", use_container_width=True)
        with col_c:
            move_files = st.checkbox("Move completed files", value=True)

        if start_ingest:
            # Scan ingest directory to build selected files list
            app_root = Path(__file__).parent
            ingest_path = Path(ingest_dir) if Path(ingest_dir).is_absolute() else app_root / ingest_dir

            selected_files = []
            if ingest_path.exists():
                supported_formats = {'.epub', '.pdf', '.txt', '.md'}
                for file in sorted(ingest_path.iterdir()):
                    if file.is_file() and file.suffix.lower() in supported_formats:
                        checkbox_key = f"book_checkbox_{file.name}"
                        if st.session_state.get(checkbox_key, True):  # Default True if not found
                            selected_files.append(str(file))

            selected_count = len(selected_files)

            if selected_count == 0:
                st.error("❌ No books selected for ingestion!")
            else:
                # Display ingestion parameters
                st.info(f"""
                **Ingestion Parameters:**
                - Domain: {domain}
                - Collection: {collection_name}
                - Chunking: **Auto-optimized** (analyzes content for optimal size)
                - Embedding Model: {st.session_state.get('embedding_model', 'all-MiniLM-L6-v2')}
                - Move completed files: {move_files}
                - Files to process: {selected_count}
                """)

                # Run ingestion with dynamic optimization
                with st.spinner(f"Ingesting {selected_count} book(s)..."):
                    try:
                        results = run_batch_ingestion(
                            selected_files=selected_files,
                            ingest_dir=ingest_dir,
                            domain=domain,
                            collection_name=collection_name,
                            host=qdrant_host,
                            port=qdrant_port,
                            move_files=move_files
                        )

                        # Display results with visual separation
                        st.markdown("---")
                        st.success("✅ Ingestion complete!")
                        st.markdown("### Results:")
                        st.write(f"- **Total:** {results['total']}")
                        st.write(f"- **Completed:** {results['completed']}")
                        st.write(f"- **Failed:** {results['failed']}")

                        if results['errors']:
                            st.markdown("### Errors:")
                            for error in results['errors']:
                                st.error(f"❌ {error['file']}: {error['error']}")

                    except Exception as e:
                        st.error(f"❌ Ingestion failed: {str(e)}")

        if resume_ingest:
            st.warning("🚧 Resume functionality coming soon!")
            st.info("💡 For now, use: `python scripts/batch_ingest.py --directory ingest --resume`")

    with col2:
        st.markdown("#### Files in Ingest Folder")

        # Resolve ingest_dir relative to application root, not current working directory
        app_root = Path(__file__).parent
        ingest_path = Path(ingest_dir) if Path(ingest_dir).is_absolute() else app_root / ingest_dir

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

                # Initialize checkbox keys in session state (default all selected)
                for book in book_files:
                    checkbox_key = f"book_checkbox_{book['name']}"
                    if checkbox_key not in st.session_state:
                        st.session_state[checkbox_key] = True

                # Bulk selection controls
                col_all, col_none, col_epub = st.columns(3)
                with col_all:
                    if st.button("✅\nSelect All", key="select_all", use_container_width=True):
                        for book in book_files:
                            st.session_state[f"book_checkbox_{book['name']}"] = True
                        st.rerun()
                with col_none:
                    if st.button("❌\nDeselect All", key="deselect_all", use_container_width=True):
                        for book in book_files:
                            st.session_state[f"book_checkbox_{book['name']}"] = False
                        st.rerun()
                with col_epub:
                    if st.button("📕\nEPUB Only", key="epub_only", use_container_width=True):
                        for book in book_files:
                            st.session_state[f"book_checkbox_{book['name']}"] = (book['format'] == '.epub')
                        st.rerun()

                st.markdown("---")

                # Checkboxes for each book
                selected_count = 0
                for book in book_files:
                    icon = "📕" if book['format'] == '.epub' else "📄" if book['format'] == '.pdf' else "📝"
                    checkbox_key = f"book_checkbox_{book['name']}"

                    # Format file size: use KB for files < 1 MB, otherwise MB
                    if book['size_mb'] < 1.0:
                        size_str = f"{book['size_mb'] * 1024:.0f} KB"
                    else:
                        size_str = f"{book['size_mb']:.1f} MB"

                    is_selected = st.checkbox(
                        f"{icon} **{book['name']}** ({size_str})",
                        key=checkbox_key
                    )

                    if is_selected:
                        selected_count += 1

                st.markdown("---")
                st.info(f"✅ **{selected_count}** of **{len(book_files)}** books selected for ingestion")

            else:
                st.info("📭 Ingest folder is empty. Add books to start ingestion.")

                # Show upload section when no files
                st.markdown("#### 📤 Upload Books")
                st.caption("Add new books to the ingest folder using the upload section below")

        else:
            st.warning(f"⚠️ Ingest folder not found: {ingest_dir}")

        st.markdown("---")

        # File uploader section (at bottom)
        with st.expander("📤 Upload New Books", expanded=False):
            uploaded_files = st.file_uploader(
                "Choose book files to upload",
                type=['epub', 'pdf', 'txt', 'md'],
                accept_multiple_files=True,
                help="Upload EPUB, PDF, TXT, or MD files. Files will be saved to the ingest folder."
            )

            if uploaded_files:
                # Resolve ingest_dir relative to application root
                upload_app_root = Path(__file__).parent
                upload_ingest_path = Path(ingest_dir) if Path(ingest_dir).is_absolute() else upload_app_root / ingest_dir
                upload_ingest_path.mkdir(exist_ok=True)

                if st.button("💾 Save Uploaded Files", use_container_width=True):
                    saved_count = 0
                    for uploaded_file in uploaded_files:
                        file_path = upload_ingest_path / uploaded_file.name

                        # Check if file already exists
                        if file_path.exists():
                            st.warning(f"⚠️ {uploaded_file.name} already exists - skipping")
                            continue

                        # Save file
                        with open(file_path, 'wb') as f:
                            f.write(uploaded_file.getbuffer())
                        saved_count += 1

                    if saved_count > 0:
                        st.success(f"✅ Saved {saved_count} file(s) to ingest folder")
                        st.rerun()
                    else:
                        st.info("ℹ️ No new files to save")

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
# TAB 3: Restore from Archive
# ============================================
if tab_restore:
    with tab_restore:
        st.markdown('<div class="section-header">🗄️ Restore from Archive</div>', unsafe_allow_html=True)
        st.info("Restore books from a deleted collection's manifest back into a new or existing collection.")

        archive_files = list(archive_dir.glob('*_manifest_*.json'))
        if not archive_files:
            st.warning("No archived manifests found.")
        else:
            # Create a mapping from a user-friendly name to the file path
            archive_options = {}
            for f in sorted(archive_files, reverse=True):
                try:
                    # e.g., alexandria_test_manifest_20260123_123000.json -> alexandria_test (2026-01-23 12:30:00)
                    parts = f.stem.split('_manifest_')
                    collection_name = parts[0]
                    timestamp_str = parts[1]
                    # Prettier timestamp for display
                    from datetime import datetime
                    dt_obj = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    display_name = f"{collection_name} ({dt_obj.strftime('%Y-%m-%d %H:%M:%S')})"
                    archive_options[display_name] = f
                except (IndexError, ValueError):
                    # Fallback for weirdly named files
                    archive_options[f.name] = f

            selected_archive_display_name = st.selectbox(
                "Select an archived manifest to restore from",
                options=list(archive_options.keys())
            )

            if selected_archive_display_name:
                selected_archive_path = archive_options[selected_archive_display_name]
                
                try:
                    with open(selected_archive_path, 'r', encoding='utf-8') as f:
                        archived_manifest_data = json.load(f)

                    # The actual book data is nested inside the collection name
                    original_collection_name = selected_archive_path.stem.split('_manifest_')[0]
                    books_to_display = []
                    if original_collection_name in archived_manifest_data.get('collections', {}):
                        books_to_display = archived_manifest_data['collections'][original_collection_name].get('books', [])
                    
                    st.markdown("---")
                    if not books_to_display:
                        st.warning("This archived manifest contains no book records.")
                    else:
                        st.success(f"Found {len(books_to_display)} book records in **{selected_archive_display_name}**.")
                        
                        df_data = []
                        for book in books_to_display:
                            df_data.append({
                                'Select': False,
                                'Title': book.get('book_title', 'N/A'),
                                'Author': book.get('author', 'N/A'),
                                'Domain': book.get('domain', 'N/A'),
                                'File Path': book.get('file_path', 'N/A'),
                                'Chunks': book.get('chunks_count', 0),
                            })
                        
                        df = pd.DataFrame(df_data)
                        
                        st.markdown("##### 1. Select books to restore")
                        edited_df = st.data_editor(
                            df,
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "Select": st.column_config.CheckboxColumn(required=True),
                                "File Path": None # Hide file path from user
                            },
                            disabled=df.columns.drop("Select")
                        )
                        
                        selected_rows = edited_df[edited_df['Select']]

                        if not selected_rows.empty:
                            st.markdown("---")
                            st.markdown("##### 2. Configure target collection")
                            
                            ingest_col1, ingest_col2 = st.columns(2)
                            with ingest_col1:
                                restore_collection_name = st.text_input(
                                    "Restore to collection",
                                    value=f"{original_collection_name}_restored",
                                    help="Name of the new or existing collection to ingest books into."
                                )
                            with ingest_col2:
                                restore_domain = st.selectbox(
                                    "Set new domain for all",
                                    options=load_domains(),
                                    index=load_domains().index(selected_rows.iloc[0]['Domain']) if selected_rows.iloc[0]['Domain'] in load_domains() else 0,
                                    help="Select a new domain for all selected books for the restored collection."
                                )
                            
                            st.info(f"You are about to ingest **{len(selected_rows)}** book(s) into the **`{restore_collection_name}`** collection.")

                            if st.button("🚀 Restore Selected Books", type="primary", use_container_width=True):
                                progress_bar = st.progress(0)
                                status_text = st.empty()
                                success_count = 0
                                error_count = 0
                                errors = []
                                successfully_restored_paths = []

                                for idx, row in selected_rows.iterrows():
                                    progress = (idx + 1) / len(selected_rows)
                                    progress_bar.progress(progress)
                                    status_text.text(f"Restoring {idx + 1}/{len(selected_rows)}: {row['Title']}")
                                    
                                    file_path_to_ingest = row['File Path']
                                    
                                    # Check if the file still exists
                                    if not Path(file_path_to_ingest).exists():
                                        errors.append(f"{row['Title']}: File not found at {file_path_to_ingest}")
                                        error_count += 1
                                        continue

                                    try:
                                        result = ingest_book(
                                            filepath=file_path_to_ingest,
                                            domain=restore_domain,
                                            collection_name=restore_collection_name,
                                            qdrant_host=qdrant_host,
                                            qdrant_port=qdrant_port
                                        )

                                        if result and result.get('success'):
                                            success_count += 1
                                            successfully_restored_paths.append(file_path_to_ingest)
                                        else:
                                            error_msg = result.get('error', 'Failed to ingest') if result else 'Unknown error'
                                            errors.append(f"{row['Title']}: {error_msg}")
                                            error_count += 1
                                    except Exception as e:
                                        errors.append(f"{row['Title']}: {str(e)}")
                                        error_count += 1
                                
                                # After loop, update the archive manifest file
                                if successfully_restored_paths:
                                    try:
                                        with open(selected_archive_path, 'r', encoding='utf-8') as f:
                                            archive_data = json.load(f)
                                        
                                        original_collection_name = selected_archive_path.stem.split('_manifest_')[0]
                                        
                                        if original_collection_name in archive_data.get('collections', {}):
                                            original_books = archive_data['collections'][original_collection_name].get('books', [])
                                            
                                            books_to_keep = [
                                                book for book in original_books 
                                                if book.get('file_path') not in successfully_restored_paths
                                            ]
                                            
                                            archive_data['collections'][original_collection_name]['books'] = books_to_keep
                                            
                                            # If no books are left, we could consider deleting the archive file, but for now we'll leave it
                                            
                                            with open(selected_archive_path, 'w', encoding='utf-8') as f:
                                                json.dump(archive_data, f, indent=2, ensure_ascii=False)
                                            
                                            st.info(f"✅ Removed {len(successfully_restored_paths)} restored book(s) from the archive manifest.")

                                    except Exception as e:
                                        st.error(f"⚠️ Failed to update the archive manifest file after restore: {e}")

                                progress_bar.progress(1.0)
                                status_text.text("✅ Restore operation complete!")
                                st.markdown("---")

                                if success_count > 0:
                                    st.success(f"✅ Successfully restored {success_count} book(s) to '{restore_collection_name}'.")
                                if error_count > 0:
                                    st.error(f"❌ Failed to restore {error_count} book(s).")
                                    with st.expander("Show Errors"):
                                        for error in errors:
                                            st.write(f"- {error}")
                        else:
                            st.info("👆 Select books using the checkboxes above to begin the restore process.")


                except Exception as e:
                    st.error(f"Failed to read or parse the archive file: {selected_archive_path.name}")
                    st.error(str(e))

# ============================================
# TAB 4: Query
# ============================================
with tab_query:
    st.markdown('<div class="section-header">🔍 Query Interface</div>', unsafe_allow_html=True)

    # Get API key and model from sidebar
    openrouter_api_key = st.session_state.get('openrouter_api_key', '')
    selected_model_name = st.session_state.get('last_selected_model', None)

    # Get the actual model ID from session state
    if 'openrouter_models' in st.session_state and selected_model_name:
        openrouter_models = st.session_state['openrouter_models']
        selected_model = openrouter_models.get(selected_model_name)
    else:
        selected_model = None

    st.markdown("#### 💬 Query")

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        query_collection = st.selectbox("Collection", ["alexandria", "alexandria_test"])
    with col2:
        query_domain = st.selectbox("Domain Filter", ["all"] + load_domains())
    with col3:
        query_limit = st.number_input("Results", min_value=1, max_value=20, value=5)

    # Advanced query settings
    with st.expander("⚙️ Advanced Settings"):
        col1, col2, col3 = st.columns(3)
        with col1:
            similarity_threshold = st.slider(
                "Similarity Threshold",
                min_value=0.0,
                max_value=1.0,
                value=0.5,
                step=0.05,
                help="Filter out results below this similarity score (0.0 = all results, 1.0 = only perfect matches)"
            )
        with col2:
            fetch_multiplier = st.number_input(
                "Fetch Multiplier",
                min_value=1,
                max_value=10,
                value=3,
                help="Fetch limit × N results from Qdrant for better filtering/reranking. Higher = better quality, slower. (Min fetch: 20)"
            )
        with col3:
            enable_reranking = st.checkbox(
                "Enable LLM Reranking",
                value=False,
                help="Use LLM to rerank results by relevance (uses OpenRouter API, slower but more accurate)"
            )

        # Second row for Temperature
        st.markdown("")
        col1, col2, col3 = st.columns(3)
        with col1:
            temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=2.0,
                value=0.7,
                step=0.1,
                help="Controls randomness. Lower = more focused, Higher = more creative"
            )

            if enable_reranking:
                # Use fetched models if available, otherwise use small hardcoded set
                if 'openrouter_models' in st.session_state and st.session_state['openrouter_models']:
                    rerank_models = st.session_state['openrouter_models']
                else:
                    rerank_models = {
                        "⚠️ Fetch models first": None,
                    }

                # Find default index for reranking model
                default_rerank_index = 0
                if 'last_selected_rerank_model' in st.session_state and st.session_state['last_selected_rerank_model'] in rerank_models:
                    try:
                        default_rerank_index = list(rerank_models.keys()).index(st.session_state['last_selected_rerank_model'])
                    except (ValueError, KeyError):
                        default_rerank_index = 0

                rerank_model_name = st.selectbox(
                    "Reranking Model",
                    list(rerank_models.keys()),
                    index=default_rerank_index,
                    help="Model used for relevance scoring (free models = slower but no cost)"
                )

                # Save last selected reranking model
                st.session_state['last_selected_rerank_model'] = rerank_model_name
                rerank_model = rerank_models[rerank_model_name]
            else:
                rerank_model = None

    query = st.text_area(
        "Enter your question",
        placeholder="e.g., What does Silverston say about shipment patterns?",
        height=100
    )

    if st.button("🔍 Search", use_container_width=True):
        if not query:
            st.warning("⚠️ Please enter a query.")
        elif not openrouter_api_key:
            st.error("❌ Please enter your OpenRouter API key first.")
        elif not selected_model:
            st.error("❌ Please fetch available models first.")
        elif enable_reranking and not rerank_model:
            st.error("❌ Please fetch available models for reranking.")
        else:
            try:
                # Call unified RAG query function from scripts/rag_query.py
                result = perform_rag_query(
                    query=query,
                    collection_name=query_collection,
                    limit=query_limit,
                    domain_filter=query_domain if query_domain != "all" else None,
                    threshold=similarity_threshold,
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

                # Check if search was successful
                if result.error:
                    st.error(f"❌ Error: {result.error}")
                    st.info("💡 **Tip:** Make sure your OpenRouter API key is valid. Get one at https://openrouter.ai/keys")
                    st.info("🔑 Your API key should start with 'sk-or-v1-...'")
                elif not result.sources:
                    st.warning(f"⚠️ No results above similarity threshold {similarity_threshold:.2f}. Try lowering the threshold.")
                else:
                    # Display search info
                    st.info(f"🔍 Retrieved {result.initial_count} initial results from Qdrant")
                    if result.filtered_count < result.initial_count:
                        st.info(f"🎯 Filtered to {result.filtered_count} results above threshold ({similarity_threshold:.2f})")
                    if enable_reranking:
                        st.success(f"✅ Reranked to top {len(result.sources)} most relevant chunks")
                    else:
                        st.success(f"✅ Using top {len(result.sources)} filtered chunks")

                    # Display answer
                    if result.answer:
                        st.markdown("---")
                        st.markdown("### 💡 Answer")
                        st.markdown(result.answer)

                    # Display sources
                    st.markdown("---")
                    st.markdown("### 📚 Sources")
                    for idx, source in enumerate(result.sources, 1):
                        with st.expander(f"📖 Source {idx}: {source.get('book_title', 'Unknown')} (Relevance: {source.get('score', 0):.3f})"):
                            st.markdown(f"**Author:** {source.get('author', 'Unknown')}")
                            st.markdown(f"**Domain:** {source.get('domain', 'Unknown')}")
                            st.markdown(f"**Section:** {source.get('section_name', 'Unknown')}")
                            st.markdown("**Content:**")
                            text = source.get('text', '')
                            st.text(text[:500] + "..." if len(text) > 500 else text)

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                import traceback
                st.code(traceback.format_exc())

# Footer
st.markdown("---")
st.markdown(
    '<div style="text-align: center; color: #666; font-style: italic;">'
    '𝔸𝕝𝕖𝕩𝕒𝕟𝕕𝕣𝕚𝕒 𝕠𝕗 𝕋𝕖𝕞𝕖𝕟𝕠𝕤 • '
    'Built with ❤️ by 137 Team • 2026'
    '</div>',
    unsafe_allow_html=True
)
