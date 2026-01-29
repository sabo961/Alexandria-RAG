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
from dataclasses import dataclass, field
from datetime import datetime

# Add project root to path so the scripts package resolves for Pylance/runtime
project_root = Path(__file__).parent
scripts_root = project_root / "scripts"
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))
if str(scripts_root) not in sys.path:
    sys.path.append(str(scripts_root))

from scripts.generate_book_inventory import scan_calibre_library, write_inventory
from scripts.count_file_types import count_file_types
from scripts.collection_manifest import CollectionManifest

from scripts.qdrant_utils import delete_collection_preserve_artifacts, delete_collection_and_artifacts
from scripts.rag_query import perform_rag_query, RAGResult

# Force reload of calibre_db to pick up DISTINCT changes
import importlib
if 'scripts.calibre_db' in sys.modules:
    importlib.reload(sys.modules['scripts.calibre_db'])
from scripts.calibre_db import CalibreDB

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
        if st.session_state.get("show_ingestion_diagnostics", True):
            with st.expander(f"🔍 Diagnostics ({context_label})"):
                st.json(diagnostics)


@st.cache_data
def load_gui_settings() -> dict:
    """Load persisted GUI settings (non-sensitive)."""
    # Construct path to settings file in .streamlit directory (parallel to this script)
    settings_path = Path(__file__).parent / '.streamlit' / 'gui_settings.json'

    # Return empty dict if settings file doesn't exist yet (first run)
    if not settings_path.exists():
        return {}

    try:
        # Read and parse JSON settings file
        with open(settings_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        # Return empty dict if file is corrupted or unreadable (defensive programming)
        return {}


def save_gui_settings(settings: dict) -> None:
    """Persist GUI settings to disk."""
    # Construct path to settings file in .streamlit directory
    settings_path = Path(__file__).parent / '.streamlit' / 'gui_settings.json'

    # Create .streamlit directory if it doesn't exist (exist_ok prevents error on re-creation)
    settings_path.parent.mkdir(exist_ok=True)

    # Write settings dict to JSON file with pretty formatting and Unicode support
    with open(settings_path, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)

    # Invalidate Streamlit's cache so next load_gui_settings() call reads fresh data
    load_gui_settings.clear()


def load_css() -> None:
    """Load custom CSS from assets/style.css"""
    # Construct path to CSS file in assets directory
    css_path = Path(__file__).parent / "assets" / "style.css"

    # Only inject CSS if file exists (graceful degradation if assets missing)
    if css_path.exists():
        with open(css_path, 'r', encoding='utf-8') as f:
            # Inject CSS into Streamlit's HTML output using markdown with <style> tag
            # unsafe_allow_html=True required to render raw HTML/CSS
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def load_keyboard_shortcuts() -> None:
    """Load keyboard shortcuts JavaScript from assets/keyboard_shortcuts.js"""
    js_path = Path(__file__).parent / "assets" / "keyboard_shortcuts.js"
    if js_path.exists():
        with open(js_path, 'r', encoding='utf-8') as f:
            js_code = f.read()
            # Use components.html to properly inject JavaScript
            import streamlit.components.v1 as components
            components.html(
                f"<script>{js_code}</script>",
                height=0,
                width=0
            )


def format_rag_result_as_json(result: RAGResult) -> str:
    """Format RAG result as JSON string

    Args:
        result: RAGResult object to format

    Returns:
        JSON string with query, filtered_count, reranked, results, answer fields
    """
    output = {
        'query': result.query,
        'filtered_count': result.filtered_count,
        'reranked': result.reranked,
        'results': result.results,
        'answer': result.answer
    }
    return json.dumps(output, indent=2, ensure_ascii=False)


# ============================================
# APP STATE MANAGEMENT
# ============================================
# Streamlit reruns the entire script on every interaction, so we use
# st.session_state to persist data across reruns. This AppState dataclass
# consolidates all state into a single object for easier management and
# type safety (instead of scattered st.session_state keys).

@dataclass
class AppState:
    """Consolidated session state management for Alexandria application

    This dataclass provides type-safe, centralized state management for the entire
    Streamlit app. Instead of using scattered st.session_state["key"] references,
    we group related state into logical sections and access them via app_state.field.

    Benefits:
    - Type hints enable IDE autocomplete and catch typos early
    - Logical grouping makes state dependencies clearer
    - Default values documented in one place
    - Easier to track what state exists across the app
    """

    # Configuration - persisted user settings and system state
    library_dir: str = ""  # Path to Calibre library directory (user-configured)
    openrouter_api_key: str = ""  # API key for OpenRouter LLM access (user-configured)
    qdrant_healthy: bool = None  # Qdrant server connectivity status (None = not checked yet)
    show_ingestion_diagnostics: bool = True  # Whether to display ingestion debug info

    # Calibre tab state - manages book browsing and selection
    # Uses set for O(1) lookup when checking if book is selected
    calibre_selected_books: set = field(default_factory=set)  # Book IDs selected for ingestion
    calibre_current_page: int = 1  # Current page in paginated book table
    calibre_books: list = field(default_factory=list)  # Filtered/sorted book list for current view
    calibre_db: object = None  # CalibreDB instance (cached to avoid reopening database)
    calibre_table_reset: int = 0  # Increment to force Streamlit table re-render (workaround for stale UI)

    # Ingestion state - tracks multi-step ingestion workflow
    confirm_delete: str = None  # Book ID pending deletion confirmation (prevents accidental deletes)
    ingest_metadata_preview: list = field(default_factory=list)  # Metadata extracted before ingestion confirmation
    ingest_ready_to_confirm: bool = False  # Whether user has reviewed metadata and can proceed
    last_ingestion_diagnostics: dict = field(default_factory=dict)  # Debug info from last ingestion run

    # Query/Models state - persists user's LLM model selections across reruns
    # Stored separately so we can pre-select last-used models in dropdowns
    last_selected_model: str = None  # Last main LLM model selected for RAG queries
    last_selected_rerank_model: str = None  # Last reranking model selected for query refinement
    openrouter_models: dict = field(default_factory=dict)  # Available models from OpenRouter API

    # UI state - controls tab navigation and special UI behaviors
    force_speaker_tab: bool = False  # When True, programmatically switch to Speaker tab (e.g., after TTS generation)


def get_app_state() -> AppState:
    """Get or create the global app state

    Streamlit's session_state persists across script reruns but loses type information.
    This function ensures AppState is initialized exactly once per session and provides
    type-safe access to state throughout the app.

    Pattern: Singleton initialization within Streamlit session
    - First call: Creates AppState() with defaults and stores in session_state
    - Subsequent calls: Returns existing AppState instance

    Returns:
        AppState: The singleton state object for this session
    """
    if "app_state" not in st.session_state:
        # Initialize state on first access (Streamlit session start)
        st.session_state.app_state = AppState()
    return st.session_state.app_state


# Constants
MANIFEST_GLOB_PATTERN = '*_manifest.json'

# Page config
st.set_page_config(
    page_title="Alexandria of Temenos",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS from assets/style.css
load_css()

# Load keyboard shortcuts from assets/keyboard_shortcuts.js
load_keyboard_shortcuts()

# ============================================
# HELPER FUNCTIONS
# ============================================

@st.cache_data
def load_domains():
    """Load domain list from domains.json"""
    # Construct path to domains configuration file in scripts directory
    domains_file = Path(__file__).parent / 'scripts' / 'domains.json'

    try:
        # Read domains JSON file
        with open(domains_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Extract just the 'id' field from each domain object (e.g., ["technical", "psychology", ...])
            # This returns a flat list of domain IDs for dropdowns/selectors
            return [d['id'] for d in data['domains']]
    except Exception as e:
        # Fallback to hardcoded list if file doesn't exist or is corrupted
        # Ensures app can still function without domains.json (defensive programming)
        return ["technical", "psychology", "philosophy", "history", "literature"]

def run_batch_ingestion(selected_files, ingest_dir, domain, collection_name, host, port, move_files):
    """Run batch ingestion for selected files with dynamic chunk optimization

    Orchestrates the complete ingestion workflow: file processing, chunking, embedding,
    Qdrant storage, manifest tracking, and optional file relocation. This function is
    called from the Streamlit UI and provides progress feedback through st.write/st.success.

    Workflow:
    1. Resolve file paths to absolute (prevent issues after directory changes)
    2. Change to scripts directory (so CollectionManifest finds logs folder)
    3. Initialize manifest for tracking ingested books
    4. Process each file: ingest_book -> manifest update -> optional file move
    5. Restore original directory and return aggregated results

    Args:
        selected_files: List of file paths to ingest (relative or absolute)
        ingest_dir: Directory containing files to ingest (used for move destination)
        domain: Knowledge domain (history/science/etc) for chunking strategy selection
        collection_name: Qdrant collection to store embeddings in
        host: Qdrant server hostname
        port: Qdrant server port
        move_files: If True, move successfully ingested files to 'ingested' subfolder

    Returns:
        dict: {'total': int, 'completed': int, 'failed': int, 'errors': [{'file': str, 'error': str}]}
    """
    import sys
    from pathlib import Path

    # File format constants (currently unused but reserved for future format-specific handling)
    EPUB_EXT = '.epub'
    PDF_EXT = '.pdf'
    TXT_EXT = '.txt'
    MD_EXT = '.md'

    # Add scripts directory to Python path so imports can find ingest_book module
    # This allows GUI and CLI to share the same ingestion logic without code duplication
    scripts_path = Path(__file__).parent / 'scripts'
    sys.path.insert(0, str(scripts_path))
    from scripts.ingest_books import ingest_book, extract_metadata_only

    # Convert all paths to absolute BEFORE changing directory below
    # Critical: After os.chdir(), relative paths will resolve incorrectly
    # So we capture absolute paths now while still in Streamlit's working directory
    selected_files = [str(Path(f).resolve()) for f in selected_files]
    ingest_dir = str(Path(ingest_dir).resolve())

    # Change working directory to scripts folder so CollectionManifest can find logs/ directory
    # CollectionManifest writes ingestion metadata to logs/<collection>_manifest.json
    # and expects logs/ to be a sibling of the current directory
    import os
    original_cwd = os.getcwd()  # Save current directory to restore after ingestion
    os.chdir(scripts_path)

    # Import CollectionManifest AFTER chdir so it initializes with correct base path
    from scripts.collection_manifest import CollectionManifest

    # Initialize results tracker for batch progress reporting
    # Streamlit UI displays these aggregated stats after batch completes
    results = {
        'total': len(selected_files),  # Total files in batch
        'completed': 0,                 # Successfully ingested and added to manifest
        'failed': 0,                    # Failed ingestion (exceptions caught)
        'errors': []                    # List of {file, error} dicts for detailed error reporting
    }

    # Initialize collection-specific manifest for tracking ingested books
    # Manifest persists metadata (title, author, chunks, domain) to logs/<collection>_manifest.json
    # This enables features like "Ingested Books" tab, re-ingestion prevention, and deletion tracking
    manifest = CollectionManifest(collection_name=collection_name)

    # Verify collection exists in Qdrant before starting batch ingestion
    # If collection was deleted externally (via Qdrant UI), reset manifest to prevent orphaned entries
    # This prevents manifest showing books that no longer exist in vector database
    manifest.verify_collection_exists(collection_name, qdrant_host=host, qdrant_port=port)

    # Process each selected file sequentially
    # (Could be parallelized in future, but sequential processing simplifies progress reporting)
    for file_path in selected_files:
        try:
            # Show file currently being processed in Streamlit UI
            # Provides real-time feedback so users know batch is progressing
            st.write(f"📖 Processing: {Path(file_path).name}")

            # Delegate to unified ingest_book function (shared with CLI)
            # ingest_book handles: text extraction, chunking (domain-aware), embedding, Qdrant upload
            # Using shared function ensures GUI and CLI produce identical chunking/embeddings
            result = ingest_book(
                filepath=file_path,
                domain=domain,  # Selects chunking strategy (e.g., history uses narrative-aware chunking)
                collection_name=collection_name,
                qdrant_host=host,
                qdrant_port=port
            )

            # Check if ingestion succeeded (result contains success flag + metadata)
            if result and result.get('success'):
                # Add book to manifest for tracking and UI display
                # Manifest enables "Ingested Books" tab to show what's in collection
                # and prevents re-ingestion of same book (duplicate detection)
                manifest.add_book(
                    collection_name=collection_name,
                    book_path=file_path,                  # Store original path for reference
                    book_title=result['title'],           # Extracted from metadata or filename
                    author=result['author'],              # Extracted from metadata or 'Unknown'
                    domain=domain,                        # Knowledge domain for filtering in UI
                    chunks_count=result['chunks'],        # Number of chunks stored in Qdrant
                    file_size_mb=result['file_size_mb'], # File size for storage analytics
                    language=result.get('language')       # Detected language (optional)
                )

                # Handle optional file relocation after successful ingestion
                # If enabled, moves ingested files to 'ingested' subfolder to keep inbox clean
                if move_files:
                    import shutil
                    # Create 'ingested' folder as sibling to 'ingest' directory
                    # Example: data/ingest/ -> data/ingested/
                    # exist_ok=True prevents error if folder already exists from previous runs
                    ingested_dir = Path(ingest_dir).parent / 'ingested'
                    ingested_dir.mkdir(exist_ok=True)

                    # Move file to ingested folder (preserves filename)
                    # shutil.move handles cross-filesystem moves and overwrites existing files
                    target_path = ingested_dir / Path(file_path).name
                    shutil.move(file_path, target_path)

                    # Show success message with ingestion stats AND move confirmation
                    # Includes: chunk count, sentence count, chunking strategy, new location
                    st.success(f"✅ **{Path(file_path).name}**\n\n📊 **{result['chunks']} chunks** | {result.get('sentences', '?')} sentences\n🧠 Strategy: {result.get('strategy', 'Standard')}\n📦 Moved to: `{target_path}`")

                    # Render optional diagnostics expander with chunking details
                    # (diagnostics contain chunk size distribution, overlap stats, etc.)
                    render_ingestion_diagnostics(result, Path(file_path).name)
                else:
                    # Show success message without move confirmation (file stays in original location)
                    st.success(f"✅ **{Path(file_path).name}**\n\n📊 **{result['chunks']} chunks** | {result.get('sentences', '?')} sentences\n🧠 Strategy: {result.get('strategy', 'Standard')}")
                    render_ingestion_diagnostics(result, Path(file_path).name)

                # Increment successful ingestion counter for batch summary
                results['completed'] += 1
            else:
                # ingest_book returned failure (success=False or None)
                # Extract error message from result dict or use generic fallback
                error_msg = result.get('error', 'Unknown error')
                raise Exception(error_msg)  # Re-raise to trigger except block below

        except Exception as e:
            # Ingestion failed (could be: file read error, chunking failure, Qdrant connection issue, etc.)
            # Show error in Streamlit UI but continue processing remaining files in batch
            st.error(f"❌ Failed: {Path(file_path).name}")
            st.error(f"   Error: {str(e)}")

            # Track failure in results for batch summary
            results['failed'] += 1
            results['errors'].append({'file': Path(file_path).name, 'error': str(e)})

    # Restore original working directory after batch completes
    # Critical: If we don't restore, subsequent Streamlit reruns will have wrong working directory
    # which breaks relative path resolution in other parts of the app
    os.chdir(original_cwd)

    # Return aggregated results for batch summary display
    # Streamlit UI uses this to show: "Completed: X/Y, Failed: Z"
    return results


def ingest_items_batch(
    items,
    extract_item_fn,
    domain: str,
    collection_name: str,
    qdrant_host: str,
    qdrant_port: int,
    move_files: bool = False,
    ingested_dir: Path = None,
    progress_callback=None,
    status_callback=None
) -> dict:
    """
    Consolidates ingestion logic for multiple items (Calibre books, folder files, etc).
    Reduces code duplication between Calibre and Folder ingestion routes.

    Args:
        items: List of items to ingest (books, rows, dicts, etc)
        extract_item_fn: Callable that takes an item and returns (filepath, metadata_overrides dict)
                        Example: lambda book: (str(book.file_path), {'title': book.title, 'author': book.author})
        domain: Content domain for chunking strategy
        collection_name: Qdrant collection name
        qdrant_host: Qdrant server host
        qdrant_port: Qdrant server port
        move_files: Whether to move successfully ingested files to ingested_dir
        ingested_dir: Directory to move files to (required if move_files=True)
        progress_callback: Callable(current_idx, total) for progress updates
        status_callback: Callable(status_text) for status messages

    Returns:
        {
            'success_count': int,
            'error_count': int,
            'errors': list[str],
            'total': int
        }
    """
    from scripts.ingest_books import ingest_book
    from scripts.collection_manifest import CollectionManifest
    import shutil

    # Force reload of ingest_books module to pick up changes
    import sys
    import importlib
    if 'scripts.ingest_books' in sys.modules:
        importlib.reload(sys.modules['scripts.ingest_books'])
        from scripts.ingest_books import ingest_book

    # Convert items to list if it's an iterator (e.g., from itertuples())
    items = list(items) if not isinstance(items, list) else items

    # Initialize manifest
    manifest = CollectionManifest(collection_name=collection_name)
    manifest.verify_collection_exists(collection_name, qdrant_host=qdrant_host, qdrant_port=qdrant_port)

    results = {
        'total': len(items),
        'success_count': 0,
        'error_count': 0,
        'errors': []
    }

    for idx, item in enumerate(items):
        try:
            # Extract filepath and metadata overrides from item
            filepath, metadata_overrides = extract_item_fn(item)

            # Update progress
            if progress_callback:
                progress_callback((idx + 1) / len(items))

            # Update status
            item_title = metadata_overrides.get('title', Path(filepath).name)
            if status_callback:
                status_callback(f"Ingesting {idx + 1}/{len(items)}: {item_title}")

            # Debug: Show what we're passing to ingest_book
            filepath_str = str(filepath)
            app_state = get_app_state()

            # Initialize diagnostic log in session state if diagnostics enabled
            if app_state.show_ingestion_diagnostics:
                if "diagnostic_log" not in st.session_state:
                    st.session_state["diagnostic_log"] = []
                st.session_state["diagnostic_log"].append(f"📤 Book {idx+1}/{len(items)}: Calling ingest_book() with author_override={repr(metadata_overrides.get('author'))}")

            # Ingest the item with metadata overrides
            try:
                result = ingest_book(
                    filepath=filepath_str,
                    domain=domain,
                    collection_name=collection_name,
                    qdrant_host=qdrant_host,
                    qdrant_port=qdrant_port,
                    title_override=metadata_overrides.get('title'),
                    author_override=metadata_overrides.get('author'),
                    language_override=metadata_overrides.get('language')
                )
                if app_state.show_ingestion_diagnostics:
                    if result and 'debug_author' in result:
                        st.session_state["diagnostic_log"].append(f"  ↳ Backend debug_author: {result['debug_author']}")
                    st.session_state["diagnostic_log"].append(f"  ↳ Final author in result: {result.get('author')}")
            except Exception as ex:
                if app_state.show_ingestion_diagnostics:
                    st.session_state["diagnostic_log"].append(f"  ❌ ingest_book() raised {ex.__class__.__name__}: {ex}")
                import traceback
                error_trace = traceback.format_exc()
                if app_state.show_ingestion_diagnostics:
                    st.session_state["diagnostic_log"].append(f"  ```\n{error_trace}\n  ```")
                result = {'success': False, 'error': f"{ex.__class__.__name__}: {ex}"}

            if result and result.get('success'):
                # Add to manifest
                manifest.add_book(
                    collection_name=collection_name,
                    book_path=str(filepath),
                    book_title=result.get('title', item_title),
                    author=result.get('author', metadata_overrides.get('author', 'Unknown')),
                    domain=domain,
                    chunks_count=result.get('chunks', 0),
                    file_size_mb=result.get('file_size_mb', 0),
                    language=result.get('language')
                )

                # Move file if requested
                if move_files and ingested_dir:
                    target_path = ingested_dir / Path(filepath).name
                    shutil.move(filepath, target_path)

                results['success_count'] += 1
            else:
                error_msg = result.get('error', 'Unknown error') if result else 'Failed to ingest'
                results['errors'].append(f"{item_title}: {error_msg}")
                results['error_count'] += 1

        except Exception as e:
            item_title = metadata_overrides.get('title', 'Unknown') if 'metadata_overrides' in locals() else 'Unknown'
            results['errors'].append(f"{item_title}: {str(e)}")
            results['error_count'] += 1

    # Add completion summary to diagnostic log
    app_state = get_app_state()
    if app_state.show_ingestion_diagnostics and "diagnostic_log" in st.session_state:
        st.session_state["diagnostic_log"].append("")
        st.session_state["diagnostic_log"].append(f"✅ **INGESTION COMPLETED**")
        st.session_state["diagnostic_log"].append(f"   Success: {results['success_count']}, Failed: {results['error_count']}, Total: {results['total']}")

    return results


@st.cache_data(ttl=30)
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


# ============================================
# HEADER AND BRANDING
# ============================================
# Display app logo and title using custom CSS classes defined in assets/style.css
# Layout: logo (1 col width) + title (5 col width) + spacer (1 col width)
logo_path = Path(__file__).parent / "assets" / "logo.png"
if logo_path.exists():
    # Three-column layout for logo + title (gracefully handles missing logo)
    logo_col, title_col, _ = st.columns([1, 5, 1])
    with logo_col:
        st.image(str(logo_path), width=120)  # Fixed width for consistent branding
    with title_col:
        st.markdown('<div class="main-title">ALEXANDRIA OF TEMENOS</div>', unsafe_allow_html=True)
else:
    # Fallback if logo asset is missing (defensive design)
    st.markdown('<div class="main-title">ALEXANDRIA OF TEMENOS</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">The Great Library Reborn</div>', unsafe_allow_html=True)

# ============================================
# APP STATE INITIALIZATION
# ============================================
# Get consolidated app state (singleton pattern - initialized once per session)
# See AppState dataclass and get_app_state() above for state management architecture
app_state = get_app_state()

# Initialize app state from persisted GUI settings on first load
# Pattern: Load persisted settings → populate app state → sidebar updates both
# This ensures user preferences survive Streamlit reruns and session restarts
gui_settings = load_gui_settings()  # Loads from .streamlit/gui_settings.json
if not app_state.library_dir:
    # Set default library directory from saved settings or fallback to default path
    # Note: This only runs if library_dir is empty (first session or cleared state)
    app_state.library_dir = gui_settings.get("library_dir", "G:\\My Drive\\alexandria")
if app_state.show_ingestion_diagnostics is None:
    # Initialize diagnostics toggle from saved preference (default: True for visibility)
    app_state.show_ingestion_diagnostics = gui_settings.get("show_ingestion_diagnostics", True)

# ============================================
# QDRANT STATUS WARNING BANNER
# ============================================
# Display persistent warning if Qdrant is offline (checked in sidebar below)
# Why: Users may not see sidebar error if they're focused on main content
# Placement: Top of page ensures visibility before attempting ingestion/queries
if app_state.qdrant_healthy is False:
    st.error("⚠️ **Qdrant Vector Database is offline!** Ingestion and queries will not work. Check Qdrant server status and configuration in sidebar.")

# ============================================
# SIDEBAR CONFIGURATION
# ============================================
# Sidebar provides global configuration that persists across tabs and sessions
# Organization: Library settings → Qdrant settings → OpenRouter API key → Model selection
with st.sidebar:
    st.markdown("### ⚙️ Configuration")

    # --------------------------------------------------
    # CALIBRE LIBRARY SETTINGS
    # --------------------------------------------------
    # Library directory path used by Calibre ingestion tab to connect to metadata.db
    # Pattern: text_input returns empty string if cleared, so we use "or app_state.library_dir" fallback
    library_dir = st.text_input(
        "Library Directory",
        value=app_state.library_dir,  # Pre-fill from app state (loaded from saved settings)
        help="Path to Calibre library"
    ) or app_state.library_dir  # Fallback prevents empty string from clearing state

    # Track if ANY settings changed (to trigger single save at end)
    # Why: Batching saves improves performance and avoids multiple file writes per rerun
    settings_changed = False

    # Detect library directory change and update both app state AND gui_settings
    # App state: ephemeral (session-only), gui_settings: persistent (saved to disk)
    if library_dir != app_state.library_dir:
        app_state.library_dir = library_dir
        gui_settings["library_dir"] = library_dir
        settings_changed = True

    # Diagnostics toggle - controls visibility of ingestion debug info (file paths, chunking stats)
    # Useful for troubleshooting ingestion issues without cluttering UI for normal users
    show_diagnostics = st.checkbox(
        "Show ingestion diagnostics",
        value=app_state.show_ingestion_diagnostics,  # Pre-fill from app state
        help="Toggle diagnostics display for the latest ingestion run"
    )

    # Detect diagnostics toggle change and update both state stores
    if show_diagnostics != app_state.show_ingestion_diagnostics:
        app_state.show_ingestion_diagnostics = show_diagnostics
        gui_settings["show_ingestion_diagnostics"] = show_diagnostics
        settings_changed = True

    # Persist settings to disk if any changes detected (single write for all changes)
    # Pattern: Optimistic save - show success caption immediately, warn on failure
    if settings_changed:
        try:
            save_gui_settings(gui_settings)  # Writes to .streamlit/gui_settings.json
            st.caption("💾 Settings saved")
        except Exception as e:
            # Non-blocking warning - settings will still work for current session
            st.warning(f"⚠️ Could not save settings: {e}")

    # --------------------------------------------------
    # QDRANT VECTOR DATABASE CONNECTION
    # --------------------------------------------------
    # Qdrant stores embeddings and enables semantic search for RAG queries
    # Host/Port configuration allows connecting to different Qdrant instances (dev/prod)
    qdrant_host = st.text_input(
        "Qdrant Host",
        value="192.168.0.151",  # Default to local network Qdrant server
        help="Qdrant server IP"
    )

    qdrant_port = st.number_input(
        "Qdrant Port",
        value=6333,  # Qdrant's default HTTP API port
        help="Qdrant server port"
    )

    # --------------------------------------------------
    # QDRANT HEALTH CHECK
    # --------------------------------------------------
    # Runs on every sidebar rerun to verify Qdrant connectivity
    # check_qdrant_health() defined above - attempts to connect and get server version
    # Returns: (is_healthy: bool, health_message: str)
    is_healthy, health_message = check_qdrant_health(qdrant_host, qdrant_port)

    # Store health status in app state for warning banner display (rendered above sidebar)
    # Why: Banner needs to check health status even if sidebar is collapsed
    app_state.qdrant_healthy = is_healthy

    # Display health status in sidebar (green success or red error)
    # Pattern: Visual feedback + action guidance (warn user that features won't work)
    if is_healthy:
        st.success(f"✅ Qdrant: {health_message}")
    else:
        st.error(f"❌ Qdrant: {health_message}")
        st.warning("⚠️ Ingestion and queries will not work until Qdrant is available")

    # --------------------------------------------------
    # INGESTION DIAGNOSTICS DISPLAY (OPTIONAL)
    # --------------------------------------------------
    # Show last ingestion run's diagnostics if available and toggle is enabled
    # Diagnostics include: file paths, chunking stats, embedding dimensions, Qdrant upload status
    # Stored in app_state.last_ingestion_diagnostics by ingestion functions
    last_diagnostics = app_state.last_ingestion_diagnostics
    if last_diagnostics and app_state.show_ingestion_diagnostics:
        st.markdown("---")
        st.markdown("### 🔍 Latest Ingestion Diagnostics")
        st.caption(f"{last_diagnostics['context']} • {last_diagnostics['captured_at']}")
        # Expander keeps diagnostics collapsed by default (reduce sidebar clutter)
        with st.expander("Show diagnostics"):
            st.json(last_diagnostics.get("diagnostics", {}))

    st.markdown("---")
    st.markdown("### 🔑 OpenRouter")

    # --------------------------------------------------
    # OPENROUTER API KEY MANAGEMENT
    # --------------------------------------------------
    # OpenRouter provides unified API access to multiple LLM providers (GPT-4, Claude, etc.)
    # API key required for Speaker tab (RAG query answering)
    # Persistence strategy: app_state (session) ← secrets.toml (disk) for survival across restarts

    # Initialize app state for API key if not present (first load or cleared state)
    if not app_state.openrouter_api_key:
        # Try to load from secrets.toml first (persistent across restarts)
        # secrets.toml is Streamlit's standard location for sensitive config
        try:
            app_state.openrouter_api_key = st.secrets.get("OPENROUTER_API_KEY", "")
        except Exception:
            # secrets.toml doesn't exist yet or is malformed - safe to ignore
            app_state.openrouter_api_key = ""

    # Password input for API key (type="password" masks input for security)
    # Pre-filled from app state if already loaded from secrets.toml
    openrouter_api_key = st.text_input(
        "OpenRouter API Key",
        type="password",
        value=app_state.openrouter_api_key,
        help="Get your API key from https://openrouter.ai/keys"
    )

    # Manual save button - writes API key to secrets.toml for persistence
    # Why manual save? Prevents accidental auto-save of invalid/test keys
    if st.button("💾 Save Permanently", use_container_width=True):
        if openrouter_api_key:
            # Update session state first (immediate availability for current session)
            app_state.openrouter_api_key = openrouter_api_key

            # Write to secrets.toml for persistence across Streamlit restarts
            # Pattern: Write with helpful comments to guide manual editing if needed
            secrets_path = Path(__file__).parent / '.streamlit' / 'secrets.toml'
            try:
                secrets_path.parent.mkdir(exist_ok=True)  # Create .streamlit/ if missing
                with open(secrets_path, 'w') as f:
                    # Write with instructional comments (secrets.toml must NOT be committed)
                    f.write('# Streamlit Secrets - DO NOT COMMIT TO GIT\n')
                    f.write('# This file stores sensitive API keys and credentials\n\n')
                    f.write('# OpenRouter API Key\n')
                    f.write('# Get your key from: https://openrouter.ai/keys\n')
                    f.write(f'OPENROUTER_API_KEY = "{openrouter_api_key}"\n')
                st.success("✅ Saved!")
            except Exception as e:
                # Non-critical error - key still works for current session
                st.error(f"❌ Failed: {e}")
        else:
            # Validation: prevent saving empty key
            st.warning("⚠️ Enter API key first")

    # --------------------------------------------------
    # MODEL SELECTION - FETCH FROM OPENROUTER API
    # --------------------------------------------------
    # Fetch available models from OpenRouter API (only shown if API key is configured)
    # Pattern: User clicks "Fetch Models" → API call → sort by pricing → store in state → dropdown
    if openrouter_api_key:
        if st.button("🔄 Fetch Models", use_container_width=True):
            # Force switch to Speaker tab after fetching (so user sees where to use models)
            st.session_state["force_speaker_tab"] = True
            with st.spinner("Fetching..."):
                try:
                    import requests
                    # Call OpenRouter API to get list of available models with pricing
                    response = requests.get(
                        "https://openrouter.ai/api/v1/models",
                        headers={"Authorization": f"Bearer {openrouter_api_key}"}
                    )

                    if response.status_code == 200:
                        models_data = response.json().get("data", [])

                        # Build models dict: display_name → model_id
                        # Display name includes emoji indicator for pricing visibility
                        openrouter_models = {}
                        for model in models_data:
                            model_id = model.get("id", "")  # API identifier (e.g., "openai/gpt-4")
                            model_name = model.get("name", model_id)  # Human-readable name

                            # Check if free (pricing = 0 for both prompt and completion)
                            # Why: Free models are ideal for testing without usage costs
                            pricing = model.get("pricing", {})
                            prompt_price = float(pricing.get("prompt", "0"))
                            completion_price = float(pricing.get("completion", "0"))
                            is_free = (prompt_price == 0 and completion_price == 0)

                            # Add emoji indicator for quick visual identification
                            # 🆓 = Free (great for testing), 💰 = Paid (production-quality)
                            emoji = "🆓" if is_free else "💰"
                            display_name = f"{emoji} {model_name}"

                            openrouter_models[display_name] = model_id

                        # Sort models: free first (encourage testing), then alphabetically
                        # Why: Free models should be most discoverable for new users
                        sorted_models = dict(sorted(
                            openrouter_models.items(),
                            key=lambda x: (0 if x[0].startswith("🆓") else 1, x[0])
                        ))

                        # Store in app state (persists across sidebar interactions)
                        app_state.openrouter_models = sorted_models
                        st.success(f"✅ {len(sorted_models)} models")
                    else:
                        st.error(f"Failed: {response.status_code}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    # --------------------------------------------------
    # MODEL DROPDOWN (CACHED MODELS)
    # --------------------------------------------------
    # Show model selector if models have been fetched (stored in session state)
    # Pattern: Dropdown remembers last selection using default_index persistence
    if 'openrouter_models' in st.session_state and app_state.openrouter_models:
        openrouter_models = app_state.openrouter_models
        st.caption(f"🆓 = Free, 💰 = Paid")

        # Find default index from last selected model (UX: avoid forcing user to re-select)
        # Try to match last_selected_model against current models list, fallback to index 0
        default_index = 0
        if 'last_selected_model' in st.session_state:
            try:
                default_index = list(openrouter_models.keys()).index(app_state.last_selected_model)
            except (ValueError, KeyError):
                # Last selected model no longer available (API changed) - use first model
                default_index = 0

        # Dropdown shows display_name (with emoji), stores model_id for API calls
        selected_model_name = st.selectbox(
            "Select Model",
            list(openrouter_models.keys()),
            index=default_index,
            help="Free models are great for testing"
        )

        # Save last selected model to app state (for default_index on next rerun)
        app_state.last_selected_model = selected_model_name
        # Resolve display name to actual model ID for OpenRouter API calls
        selected_model = openrouter_models[selected_model_name]
    else:
        # No models fetched yet - empty state (user needs to click "Fetch Models" first)
        selected_model_name = None
        selected_model = None

# ============================================
# FRAGMENT: Query Tab
# ============================================
# Fragment isolation: Query tab interactions (dropdown changes, text input, button clicks)
# don't need to reload the entire app (e.g., Calibre table, ingested books list).
# This improves responsiveness and prevents unnecessary re-execution of expensive operations.
@st.fragment
def render_query_tab():
    """Isolated Query tab - prevents full app rerun on query interactions

    RAG query flow:
    1. User selects collection, domain, and result limit
    2. User configures advanced settings (similarity threshold, fetch multiplier, reranking)
    3. User enters query and clicks Search
    4. System retrieves chunks from Qdrant using vector similarity
    5. Optional: LLM reranks chunks for better relevance
    6. LLM generates answer based on retrieved context
    7. Sources displayed with metadata for provenance tracking
    """
    st.markdown('<div class="section-header">🔍 Query Interface</div>', unsafe_allow_html=True)

    # ==================================================
    # RETRIEVE MODEL CONFIGURATION FROM APP STATE
    # ==================================================
    # Fragment has access to app state configured in sidebar (API key, models)
    # This pattern keeps sidebar configuration separate from query execution
    app_state = get_app_state()
    openrouter_api_key = app_state.openrouter_api_key  # API key for LLM access
    selected_model_name = app_state.last_selected_model  # User's last selected model (display name)

    # Resolve display name to actual model ID for OpenRouter API
    # Models are stored as {display_name: model_id} in app_state.openrouter_models
    if app_state.openrouter_models and selected_model_name:
        selected_model = app_state.openrouter_models.get(selected_model_name)
    else:
        # No models fetched yet - will trigger validation error on search
        selected_model = None

    # ==================================================
    # QUERY INPUT CONTROLS
    # ==================================================
    st.markdown("#### 💬 Query")

    # Three-column layout for basic query configuration
    # Column widths [2, 1, 1] give more space to collection selector
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        # Collection selection - allows switching between prod and test without restarting app
        query_collection = st.selectbox("Collection", ["alexandria", "alexandria_test"])
    with col2:
        # Domain filtering - narrow search to specific knowledge areas (e.g., data_modeling, devops)
        # load_domains() reads from data/domains/ directory structure
        query_domain = st.selectbox("Domain Filter", ["all"] + load_domains())
    with col3:
        # Limit final results returned to user (after filtering/reranking)
        # Max 20 to prevent UI overload and excessive token usage
        query_limit = st.number_input("Results", min_value=1, max_value=20, value=5)

    # ==================================================
    # ADVANCED SETTINGS (COLLAPSIBLE)
    # ==================================================
    # Expander keeps UI clean for basic users while power users can fine-tune
    with st.expander("⚙️ Advanced Settings"):
        # First row: similarity threshold, fetch multiplier, reranking toggle
        col1, col2, col3 = st.columns(3)
        with col1:
            # Similarity threshold filters out low-quality matches
            # Lower = more results (potentially less relevant), Higher = fewer but more precise
            # Default 0.5 balances recall and precision for most queries
            similarity_threshold = st.slider(
                "Similarity Threshold",
                min_value=0.0,
                max_value=1.0,
                value=0.5,
                step=0.05,
                help="Filter out results below this similarity score (0.0 = all results, 1.0 = only perfect matches)"
            )
        with col2:
            # Fetch multiplier: retrieve (limit × multiplier) chunks from Qdrant BEFORE filtering
            # Example: limit=5, multiplier=3 → fetch 15 chunks, then filter to top 5
            # Why: Gives reranker and threshold filter more candidates to choose from
            # Trade-off: Higher = better quality but slower and more token usage
            fetch_multiplier = st.number_input(
                "Fetch Multiplier",
                min_value=1,
                max_value=10,
                value=3,
                help="Fetch limit × N results from Qdrant for better filtering/reranking. Higher = better quality, slower. (Min fetch: 20)"
            )
        with col3:
            # LLM reranking: Use another LLM to score relevance of retrieved chunks
            # Why: Vector similarity != semantic relevance for complex queries
            # Example: "What does Silverston say about X?" needs context understanding
            enable_reranking = st.checkbox(
                "Enable LLM Reranking",
                value=False,
                help="Use LLM to rerank results by relevance (uses OpenRouter API, slower but more accurate)"
            )

        # Second row: Temperature and conditional reranking model selector
        st.markdown("")  # Spacing between rows
        col1, col2, col3 = st.columns(3)
        with col1:
            # Temperature controls LLM answer generation creativity
            # Lower (0.0-0.5): Factual, deterministic answers (better for knowledge retrieval)
            # Higher (1.0-2.0): Creative, diverse answers (better for brainstorming)
            temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=2.0,
                value=0.7,
                step=0.1,
                help="Controls randomness. Lower = more focused, Higher = more creative"
            )

            # ==================================================
            # RERANKING MODEL SELECTION (CONDITIONAL)
            # ==================================================
            # Only show reranking model selector if reranking is enabled
            # Placed in temperature column to keep layout balanced
            if enable_reranking:
                # Reuse models fetched from OpenRouter (same as main model selector)
                # Fallback to warning message if user hasn't fetched models yet
                if 'openrouter_models' in st.session_state and app_state.openrouter_models:
                    rerank_models = app_state.openrouter_models
                else:
                    # Placeholder dict - will trigger validation error if user tries to search
                    rerank_models = {
                        "⚠️ Fetch models first": None,
                    }

                # Restore last selected reranking model for convenience
                # Separate from main model selection so users can use different models
                # Example: Fast free model for reranking, expensive model for answer generation
                default_rerank_index = 0
                if 'last_selected_rerank_model' in st.session_state and app_state.last_selected_rerank_model in rerank_models:
                    try:
                        # Find index of last selected model in current models list
                        default_rerank_index = list(rerank_models.keys()).index(app_state.last_selected_rerank_model)
                    except (ValueError, KeyError):
                        # Model no longer available (e.g., removed from OpenRouter) - reset to first
                        default_rerank_index = 0

                rerank_model_name = st.selectbox(
                    "Reranking Model",
                    list(rerank_models.keys()),
                    index=default_rerank_index,
                    help="Model used for relevance scoring (free models = slower but no cost)"
                )

                # Persist reranking model selection across reruns
                app_state.last_selected_rerank_model = rerank_model_name
                # Resolve display name to model ID
                rerank_model = rerank_models[rerank_model_name]
            else:
                # Reranking disabled - don't pass model to query function
                rerank_model = None

    # ==================================================
    # QUERY TEXT INPUT
    # ==================================================
    # Large text area encourages detailed questions for better RAG results
    # Example placeholder guides users toward author-specific queries
    query = st.text_area(
        "Enter your question",
        placeholder="e.g., What does Silverston say about shipment patterns?",
        height=100
    )

    # ==================================================
    # SEARCH BUTTON AND VALIDATION
    # ==================================================
    if st.button("🔍 Search", use_container_width=True):
        # Validation chain: fail fast with clear error messages
        # This prevents wasted API calls and confusing errors from downstream code
        if not query:
            st.warning("⚠️ Please enter a query.")
        elif not openrouter_api_key:
            st.error("❌ Please enter your OpenRouter API key first.")
        elif not selected_model:
            st.error("❌ Please fetch available models first.")
        elif enable_reranking and not rerank_model:
            st.error("❌ Please fetch available models for reranking.")
        else:
            # All validations passed - execute RAG query
            try:
                # ==================================================
                # RAG QUERY EXECUTION
                # ==================================================
                # Delegate to unified RAG query function (handles vector search, reranking, answer generation)
                # This keeps UI code clean and allows CLI/API reuse of RAG logic
                result = perform_rag_query(
                    query=query,
                    collection_name=query_collection,
                    limit=query_limit,
                    # Convert "all" to None for qdrant_utils filter logic
                    domain_filter=query_domain if query_domain != "all" else None,
                    threshold=similarity_threshold,
                    enable_reranking=enable_reranking,
                    rerank_model=rerank_model if enable_reranking else None,
                    generate_llm_answer=True,  # Always generate answer in UI (CLI might skip this)
                    answer_model=selected_model,
                    openrouter_api_key=openrouter_api_key,
                    host=qdrant_host,  # Global config from main app
                    port=qdrant_port,
                    fetch_multiplier=fetch_multiplier,
                    temperature=temperature
                )

                # ==================================================
                # RESULT RENDERING
                # ==================================================
                # Handle three result states: error, no results, success
                if result.error:
                    # API key invalid, network error, Qdrant unavailable, etc.
                    st.error(f"❌ Error: {result.error}")
                    # Contextual help for most common error (invalid API key)
                    st.info("💡 **Tip:** Make sure your OpenRouter API key is valid. Get one at https://openrouter.ai/keys")
                    st.info("🔑 Your API key should start with 'sk-or-v1-...'")
                elif not result.sources:
                    # Query succeeded but no chunks passed similarity threshold
                    # Guide user to adjust threshold (common issue for niche queries)
                    st.warning(f"⚠️ No results above similarity threshold {similarity_threshold:.2f}. Try lowering the threshold.")
                else:
                    # Success - display retrieval statistics for transparency
                    # Users can validate that filtering/reranking worked as expected
                    st.info(f"🔍 Retrieved {result.initial_count} initial results from Qdrant")
                    if result.filtered_count < result.initial_count:
                        # Show how many chunks were filtered out by threshold
                        st.info(f"🎯 Filtered to {result.filtered_count} results above threshold ({similarity_threshold:.2f})")
                    if enable_reranking:
                        # Indicate reranking was applied (final count may differ from filtered count)
                        st.success(f"✅ Reranked to top {len(result.sources)} most relevant chunks")
                    else:
                        # No reranking - show final count after threshold filtering
                        st.success(f"✅ Using top {len(result.sources)} filtered chunks")

                    # ==================================================
                    # DISPLAY LLM-GENERATED ANSWER
                    # ==================================================
                    # Answer is synthesized from retrieved chunks using selected LLM
                    if result.answer:
                        st.markdown("---")
                        st.markdown("### 💡 Answer")
                        st.markdown(result.answer)

                    # ==================================================
                    # DISPLAY SOURCE CHUNKS (PROVENANCE)
                    # ==================================================
                    # Show retrieved chunks so users can verify answer accuracy
                    # Each source includes metadata (book, author, domain, section, relevance score)
                    st.markdown("---")
                    st.markdown("### 📚 Sources")
                    for idx, source in enumerate(result.sources, 1):
                        # Expander keeps UI clean - users can inspect sources if needed
                        # Header shows book title and relevance score for quick scanning
                        with st.expander(f"📖 Source {idx}: {source.get('book_title', 'Unknown')} (Relevance: {source.get('score', 0):.3f})"):
                            st.markdown(f"**Author:** {source.get('author', 'Unknown')}")
                            st.markdown(f"**Domain:** {source.get('domain', 'Unknown')}")
                            st.markdown(f"**Section:** {source.get('section_name', 'Unknown')}")
                            st.markdown("**Content:**")
                            # Truncate long chunks to prevent UI overload
                            # Users can click into book if they need full context
                            text = source.get('text', '')
                            st.text(text[:500] + "..." if len(text) > 500 else text)

            except Exception as e:
                # Catch-all for unexpected errors (e.g., Qdrant connection loss mid-query)
                st.error(f"❌ Error: {str(e)}")
                # Show full traceback for debugging (helpful for reporting issues)
                import traceback
                st.code(traceback.format_exc())

# ============================================
# FRAGMENT: Ingested Books Filters and Table
# ============================================
@st.fragment
def render_ingested_books_filters_and_table(books, collection_data, selected_collection):
    """Isolated Ingested Books filters and table - prevents full app rerun on filter interactions"""
    # Render filter controls in 4-column layout
    # Each filter has a unique key to preserve state across fragment reruns
    st.markdown("#### 🔍 Filters")
    ing_filter_col1, ing_filter_col2, ing_filter_col3, ing_filter_col4 = st.columns(4)

    with ing_filter_col1:
        # Text input for author name (case-insensitive partial match)
        ing_author_search = st.text_input("Author", placeholder="e.g., Mishima", key="ingested_author_search")

    with ing_filter_col2:
        # Text input for book title (case-insensitive partial match)
        ing_title_search = st.text_input("Title", placeholder="e.g., Steel", key="ingested_title_search")

    with ing_filter_col3:
        # Extract unique languages from ingested books (with fallback to 'unknown')
        # Multiselect allows filtering by multiple languages simultaneously
        available_langs = sorted(set(b.get('language', 'unknown') for b in books))
        ing_language_filter = st.multiselect("Language", options=available_langs, key="ingested_language_filter")

    with ing_filter_col4:
        # Extract unique domains from ingested books (e.g., 'philosophy', 'fiction')
        # Domain is a required field in the manifest, so no fallback needed
        available_domains = sorted(set(b['domain'] for b in books))
        ing_domain_filter = st.multiselect("Domain", options=available_domains, key="ingested_domain_filter")

    # Format filter in separate row for better visual layout
    # Covers common ebook and text formats supported by the ingestion pipeline
    ing_format_filter = st.multiselect("Format", options=['EPUB', 'PDF', 'TXT', 'MD', 'MOBI'], key="ingested_format_filter")

    # Apply filters sequentially - each filter narrows down the result set
    # Start with all ingested books and progressively filter based on user input
    filtered_books = books

    # Author filter: case-insensitive substring match
    # Example: "mishima" matches "Yukio Mishima"
    if ing_author_search:
        filtered_books = [b for b in filtered_books if ing_author_search.lower() in b['author'].lower()]

    # Title filter: case-insensitive substring match
    # Example: "steel" matches "The Decay of the Angel"
    if ing_title_search:
        filtered_books = [b for b in filtered_books if ing_title_search.lower() in b['book_title'].lower()]

    # Language filter: exact match against selected languages
    # Only applied if user selected at least one language
    if ing_language_filter:
        filtered_books = [b for b in filtered_books if b.get('language', 'unknown') in ing_language_filter]

    # Domain filter: exact match against selected domains
    # Example: selecting ["philosophy", "science"] shows only books in those domains
    if ing_domain_filter:
        filtered_books = [b for b in filtered_books if b['domain'] in ing_domain_filter]

    # Format filter: match file type from manifest or extract from filename
    # Falls back to extracting extension if file_type field not in manifest
    if ing_format_filter:
        filtered_books = [b for b in filtered_books if b.get('file_type', PathLib(b['file_name']).suffix.upper().replace('.', '')) in ing_format_filter]

    # Display filter results summary and sort controls
    # Column layout: wider info panel (3 units) + narrower sort dropdown (1 unit)
    ing_sort_col1, ing_sort_col2 = st.columns([3, 1])
    with ing_sort_col1:
        # Show count of filtered vs total books (e.g., "Showing 42 of 250 books")
        st.info(f"📚 Showing {len(filtered_books)} of {len(books)} books")

    with ing_sort_col2:
        # Sort dropdown with common sorting options for ingested books
        # Default sort is by ingestion date (newest first) to see recent additions
        ing_sort_by = st.selectbox("Sort by", [
            "Ingested (newest)",
            "Ingested (oldest)",
            "Title (A-Z)",
            "Author (A-Z)",
            "Chunks (most)",
            "Size (largest)"
        ], key="ingested_sort")

    # Apply sorting based on selected option
    # Uses lambda functions to extract sort keys from book dictionaries
    if "newest" in ing_sort_by:
        # Sort by ingestion timestamp (ISO format: YYYY-MM-DDTHH:MM:SS)
        # Reverse=True puts newest timestamps first
        filtered_books = sorted(filtered_books, key=lambda x: x['ingested_at'], reverse=True)
    elif "oldest" in ing_sort_by:
        # Sort by ingestion timestamp, oldest first (chronological order)
        filtered_books = sorted(filtered_books, key=lambda x: x['ingested_at'])
    elif "Title" in ing_sort_by:
        # Alphabetical sort by title (case-insensitive via .lower())
        filtered_books = sorted(filtered_books, key=lambda x: x['book_title'].lower())
    elif "Author" in ing_sort_by:
        # Alphabetical sort by author name (case-insensitive)
        filtered_books = sorted(filtered_books, key=lambda x: x['author'].lower())
    elif "Chunks" in ing_sort_by:
        # Sort by chunk count (higher = more granular indexing)
        # Reverse=True shows books with most chunks first (useful for debugging chunking strategy)
        filtered_books = sorted(filtered_books, key=lambda x: x['chunks_count'], reverse=True)
    elif "Size" in ing_sort_by:
        # Sort by file size in MB (largest first)
        # Useful for identifying large books that may need optimization
        filtered_books = sorted(filtered_books, key=lambda x: x['file_size_mb'], reverse=True)

    # Build and display DataFrame table of ingested books
    # DataFrame provides sortable/searchable view with rich formatting
    if filtered_books:
        df_data = []
        # Enumerate to add row numbers (starting from 1 for user-facing display)
        for idx, book in enumerate(filtered_books, start=1):
            # Extract file type from manifest or derive from filename extension
            # Manifest stores file_type as uppercase string (e.g., 'EPUB', 'PDF')
            file_type = book.get('file_type')
            if not file_type:
                # Fallback: extract extension from filename (e.g., 'book.epub' → 'EPUB')
                file_type = PathLib(book['file_name']).suffix.upper().replace('.', '')

            # Map file type to visual icon for quick format recognition
            # Defaults to generic document icon (📄) for unknown formats
            icon = {'EPUB': '📕', 'PDF': '📄', 'TXT': '📝', 'MD': '📝', 'MOBI': '📱'}.get(file_type, '📄')

            # Language display with fallback to 'unknown' (uppercase for consistency)
            language = book.get('language', 'unknown').upper()

            # Build row dictionary with display-friendly formatting
            df_data.append({
                '#': idx,  # Row number for reference
                '': icon,  # Visual format indicator (empty column header for icon-only display)
                'Title': book['book_title'][:50] + '...' if len(book['book_title']) > 50 else book['book_title'],  # Truncate long titles
                'Author': book['author'][:30] + '...' if len(book['author']) > 30 else book['author'],  # Truncate long author names
                'Lang': language,  # ISO language code or 'UNKNOWN'
                'Domain': book['domain'],  # Knowledge domain (e.g., 'philosophy', 'science')
                'Type': file_type,  # File format (EPUB, PDF, etc.)
                'Chunks': book['chunks_count'],  # Number of text chunks in vector DB
                'Size (MB)': f"{book['file_size_mb']:.2f}",  # File size formatted to 2 decimals
                'Ingested': book['ingested_at'][:10]  # Extract date portion of ISO timestamp (YYYY-MM-DD)
            })

        # Convert list of dicts to pandas DataFrame for Streamlit's dataframe component
        df = pd.DataFrame(df_data)
        # Render as interactive table (sortable columns, scrollable)
        # height=600 provides enough rows visible without excessive scrolling
        # hide_index=True removes pandas' default numeric index (we have our own '#' column)
        st.dataframe(df, use_container_width=True, height=600, hide_index=True)
    else:
        # Show warning if no books match the current filter combination
        st.warning("No books match the filters.")

    # Export button and Management Section
    # Horizontal rule separates data view from management actions
    st.markdown("---")
    manage_col1, manage_col2 = st.columns([1, 3])

    with manage_col1:
        # Provide CSV export of collection manifest for external analysis
        # CSV manifest contains all book metadata in spreadsheet-friendly format
        csv_file = PathLib(f'logs/{selected_collection}_manifest.csv')
        if csv_file.exists():
            # Read CSV file contents for download
            with open(csv_file, 'r', encoding='utf-8') as f:
                csv_data = f.read()
            # Download button triggers browser download (doesn't reload page)
            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name=f"{selected_collection}_manifest.csv",
                mime="text/csv",
                use_container_width=True
            )

    # Collection Management Expander - DANGER ZONE for deletion operations
    # Collapsed by default to prevent accidental clicks
    with st.expander("⚙️ Collection Management"):
        # Warning banner to signal destructive operations
        st.warning(f"**DANGER ZONE:** Actions performed here are permanent and cannot be undone.")
        st.markdown(
            f"You are about to delete the entire **`{selected_collection}`** collection from Qdrant. "
            "Choose whether to preserve artifacts or permanently remove them."
        )

        # Radio button to choose deletion mode
        # Default is "Preserve artifacts" (index=0) for safer default behavior
        delete_mode = st.radio(
            "Delete mode",
            options=[
                "Preserve artifacts (move to logs/deleted)",  # Moves JSON manifests to deleted/ for potential restore
                "Hard delete (remove artifacts permanently)"  # Deletes vector collection AND manifest files
            ],
            index=0,
            help="Preserve keeps manifests for restore; hard delete removes them permanently."
        )

        # Confirmation state management using two-step confirmation pattern
        # Step 1: User clicks "Delete" button → sets confirm_delete to collection name
        # Step 2: User must click "YES, DELETE PERMANENTLY" in confirmation UI
        # This prevents accidental deletion from single-click mistakes
        if 'confirm_delete' not in st.session_state:
            app_state.confirm_delete = None

        # Check if we're in confirmation state for this specific collection
        if app_state.confirm_delete != selected_collection:
            # Initial state: Show "Delete Collection" button
            if st.button(f"🗑️ Delete '{selected_collection}' Collection", use_container_width=True):
                # Set confirmation flag to trigger second confirmation step
                app_state.confirm_delete = selected_collection
                st.rerun()  # Rerun to show confirmation UI
        else:
            # Confirmation state: Show warning and final confirmation buttons
            # Dynamic warning message based on deletion mode
            confirmation_label = (
                "**Are you sure?** This will permanently delete the Qdrant collection. "
                "Artifacts will be preserved in logs/deleted."
                if delete_mode.startswith("Preserve")
                else "**Are you sure?** This will permanently delete the Qdrant collection and all associated artifacts. This action cannot be undone."
            )
            st.error(confirmation_label)

            # Two-button layout: Confirm (left) and Cancel (right)
            confirm_col1, confirm_col2 = st.columns(2)
            with confirm_col1:
                # Final confirmation button (red primary style for danger action)
                if st.button("🚨 YES, DELETE PERMANENTLY", use_container_width=True, type="primary"):
                    # Choose deletion function based on mode
                    if delete_mode.startswith("Preserve"):
                        spinner_label = f"Deleting collection '{selected_collection}' and preserving artifacts..."
                        delete_action = delete_collection_preserve_artifacts  # Moves manifests to logs/deleted/
                    else:
                        spinner_label = f"Deleting collection '{selected_collection}' and removing artifacts..."
                        delete_action = delete_collection_and_artifacts  # Removes everything

                    # Execute deletion with loading spinner (can take several seconds for large collections)
                    with st.spinner(spinner_label):
                        delete_results = delete_action(
                            collection_name=selected_collection,
                            host=qdrant_host,
                            port=qdrant_port
                        )

                    # Check deletion results and show appropriate feedback
                    if not delete_results['errors']:
                        # Success: Show success message based on mode
                        if delete_mode.startswith("Preserve"):
                            st.success(
                                f"✅ Collection '{selected_collection}' deleted. Artifacts preserved in logs/deleted."
                            )
                        else:
                            st.success(
                                f"✅ Collection '{selected_collection}' deleted and artifacts removed permanently."
                            )
                        # Clear confirmation state and refresh app to update collection list
                        app_state.confirm_delete = None
                        st.info("Refreshing app...")
                        time.sleep(2)  # Brief pause so user can read success message
                        st.rerun()
                    else:
                        # Failure: Show error messages from deletion operation
                        st.error(f"❌ Failed to completely delete collection '{selected_collection}'.")
                        for error in delete_results['errors']:
                            st.error(f"- {error}")
                        app_state.confirm_delete = None  # Clear confirmation state
            with confirm_col2:
                # Cancel button to abort deletion and return to normal state
                if st.button("Cancel", use_container_width=True):
                    app_state.confirm_delete = None  # Clear confirmation state
                    st.rerun()  # Rerun to hide confirmation UI

# ============================================
# SKELETON LOADER
# ============================================
def render_table_skeleton(rows=5):
    """Render skeleton loading placeholder for Calibre book table.

    Args:
        rows: Number of skeleton rows to display (default: 5)
    """
    skeleton_html = '<div style="margin-top: 1rem;">'

    for _ in range(rows):
        skeleton_html += '''
        <div class="skeleton-row">
            <div class="skeleton-cell skeleton-cell-small"></div>
            <div class="skeleton-cell skeleton-cell-small"></div>
            <div class="skeleton-cell skeleton-cell-small"></div>
            <div class="skeleton-cell skeleton-cell-large"></div>
            <div class="skeleton-cell skeleton-cell-medium"></div>
            <div class="skeleton-cell skeleton-cell-small"></div>
            <div class="skeleton-cell skeleton-cell-medium"></div>
            <div class="skeleton-cell skeleton-cell-medium"></div>
            <div class="skeleton-cell skeleton-cell-small"></div>
        </div>
        '''

    skeleton_html += '</div>'
    st.markdown(skeleton_html, unsafe_allow_html=True)


# ============================================
# FRAGMENT: Calibre Filters and Table
# ============================================
@st.fragment
def render_calibre_filters_and_table(all_books, calibre_db):
    """Isolated Calibre filters and table - prevents full app rerun on filter interactions"""
    # Get consolidated app state for Calibre tab
    app_state = get_app_state()

    # Get ingestion collection from session state and library_dir
    calibre_collection = st.session_state.get("calibre_ingest_collection", "alexandria")
    library_dir = app_state.library_dir

    # Load manifest to check which books are already ingested
    ingested_file_paths = set()

    # Initialize diagnostic log for manifest loading if diagnostics enabled
    # ONLY log if: (1) diagnostics enabled, (2) no existing diagnostic_log (means no active ingestion),
    #              (3) haven't logged yet, (4) not dismissed
    diagnostic_key = f"manifest_diagnostics_loaded_{calibre_collection}"
    should_log_diagnostics = (
        app_state.show_ingestion_diagnostics and
        "diagnostic_log" not in st.session_state and  # Don't interfere with ingestion diagnostics
        diagnostic_key not in st.session_state and
        "diagnostics_dismissed" not in st.session_state  # Don't show after user dismissed
    )

    if should_log_diagnostics:
        st.session_state["diagnostic_log"] = []
        st.session_state["diagnostic_log"].append(f"📂 **Manifest Loading (Collection: {calibre_collection})**")

    try:
        manifest = CollectionManifest(collection_name=calibre_collection)
        if calibre_collection in manifest.manifest['collections']:
            library_path = Path(library_dir)
            manifest_books = manifest.manifest['collections'][calibre_collection]['books']

            # Debug output if diagnostics enabled
            if should_log_diagnostics:
                st.session_state["diagnostic_log"].append(f"  📊 Collection has {len(manifest_books)} books")
                st.session_state["diagnostic_log"].append(f"  📁 Library path: {library_path}")

            for idx, book in enumerate(manifest_books):
                # Convert absolute path to relative path (relative to library_dir)
                # Manifest stores: C:\...\library\Author\Book (ID)\filename.epub
                # We want: author/book (id) (DIRECTORY ONLY, normalized, lowercase)
                # Calibre book.path is also just the directory: Author/Book (ID)
                absolute_path = Path(book['file_path'])
                try:
                    relative_path = absolute_path.relative_to(library_path)
                    # Extract parent directory (book directory, not file path)
                    book_directory = relative_path.parent
                    normalized = book_directory.as_posix().lower()
                    ingested_file_paths.add(normalized)

                    # Debug: Show first 3 conversions
                    if should_log_diagnostics and idx < 3:
                        st.session_state["diagnostic_log"].append(f"  • Manifest book {idx+1}: {absolute_path.name}")
                        st.session_state["diagnostic_log"].append(f"    → Book directory: {book_directory}")
                        st.session_state["diagnostic_log"].append(f"    → Normalized: {normalized}")
                except ValueError as e:
                    # Path is not relative to library_dir, skip it
                    if should_log_diagnostics:
                        st.session_state["diagnostic_log"].append(f"  ⚠️ Could not make relative: {absolute_path.name}")
                    pass

            if should_log_diagnostics:
                st.session_state["diagnostic_log"].append(f"  ✅ Total ingested paths loaded: {len(ingested_file_paths)}")
                if ingested_file_paths:
                    sample_paths = list(ingested_file_paths)[:3]
                    st.session_state["diagnostic_log"].append(f"  📋 Sample paths: {', '.join(sample_paths)}")
                # Set flag to prevent re-logging on subsequent fragment reruns
                st.session_state[diagnostic_key] = True
    except Exception as e:
        if should_log_diagnostics:
            st.session_state["diagnostic_log"].append(f"  ❌ Manifest loading error: {e}")
            st.session_state[diagnostic_key] = True  # Set flag even on error
        pass  # Manifest doesn't exist yet or collection not created

    # Extract all available formats from books for filter dropdown
    # Using set ensures each format appears only once in the filter options
    all_formats = set()
    for book in all_books:
        all_formats.update(book.formats)

    # Render filter controls in 4-column layout
    # Each filter input has a unique key to preserve state across fragment reruns
    st.markdown("#### 🔍 Filters")
    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)

    with filter_col1:
        # Text input for author name (case-insensitive partial match)
        author_search = st.text_input("Author", placeholder="e.g., Mishima", key="calibre_author_search")

    with filter_col2:
        # Text input for book title (case-insensitive partial match)
        title_search = st.text_input("Title", placeholder="e.g., Steel", key="calibre_title_search")

    with filter_col3:
        # Extract unique languages from all books (filter out None/empty values)
        # Multiselect allows filtering by multiple languages simultaneously
        available_languages = sorted(set(b.language for b in all_books if b.language))
        language_filter = st.multiselect("Language", options=available_languages, key="calibre_language_filter")

    with filter_col4:
        # Multiselect for file formats (epub, pdf, mobi, etc.)
        # Users can select multiple formats to see books available in any of them
        format_options = sorted(all_formats)
        format_filter = st.multiselect("Format", options=format_options, key="calibre_format_filter")

    # Apply filters sequentially - each filter narrows down the result set
    # Start with all books and progressively filter based on user input
    filtered_books = all_books

    # Author filter: case-insensitive substring match
    # Example: "mishima" matches "Yukio Mishima"
    if author_search:
        filtered_books = [b for b in filtered_books if author_search.lower() in b.author.lower()]

    # Title filter: case-insensitive substring match
    # Example: "steel" matches "The Decay of the Angel"
    if title_search:
        filtered_books = [b for b in filtered_books if title_search.lower() in b.title.lower()]

    # Language filter: exact match against selected languages
    # Only applied if user selected at least one language
    if language_filter:
        filtered_books = [b for b in filtered_books if b.language in language_filter]

    # Format filter: book must have at least one of the selected formats
    # Example: selecting ["epub", "pdf"] shows books with epub OR pdf (or both)
    if format_filter:
        filtered_books = [b for b in filtered_books if any(fmt in b.formats for fmt in format_filter)]

    # Display filter results summary and sort controls
    # Column layout: wider info panel (3 units) + narrower sort dropdown (1 unit)
    sort_col1, sort_col2 = st.columns([3, 1])
    with sort_col1:
        # Show count of filtered vs total books (e.g., "Showing 42 of 1,234 books")
        st.info(f"📚 Showing {len(filtered_books):,} of {len(all_books):,} books")

    with sort_col2:
        # Sort dropdown with common sorting options
        # Default sort is by date added (newest first) for Calibre workflow
        sort_by = st.selectbox("Sort by", [
            "Date Added (newest)",
            "Date Added (oldest)",
            "Title (A-Z)",
            "Title (Z-A)",
            "Author (A-Z)",
            "Author (Z-A)"
        ], key="calibre_sort")

    # Apply selected sorting to filtered book list
    # Uses lambda for dynamic sort key extraction with case-insensitive string sorting
    if "newest" in sort_by:
        # Most recent additions first (Calibre timestamp is ISO format, sortable as string)
        filtered_books = sorted(filtered_books, key=lambda x: x.timestamp, reverse=True)
    elif "oldest" in sort_by:
        # Oldest additions first
        filtered_books = sorted(filtered_books, key=lambda x: x.timestamp)
    elif "Title (A-Z)" in sort_by:
        # Alphabetical by title (case-insensitive)
        filtered_books = sorted(filtered_books, key=lambda x: x.title.lower())
    elif "Title (Z-A)" in sort_by:
        # Reverse alphabetical by title
        filtered_books = sorted(filtered_books, key=lambda x: x.title.lower(), reverse=True)
    elif "Author (A-Z)" in sort_by:
        # Alphabetical by author (case-insensitive)
        filtered_books = sorted(filtered_books, key=lambda x: x.author.lower())
    elif "Author (Z-A)" in sort_by:
        # Reverse alphabetical by author
        filtered_books = sorted(filtered_books, key=lambda x: x.author.lower(), reverse=True)

    # Track filter state to detect changes and show loading skeleton
    # Tuple is hashable and immutable, perfect for state comparison
    # Convert lists to tuples since lists aren't hashable
    current_filter_state = (
        author_search,
        title_search,
        tuple(language_filter) if language_filter else (),  # Empty tuple if no filters selected
        tuple(format_filter) if format_filter else (),
        sort_by
    )

    # Compare with previous filter state to detect user changes
    # When filters change on large datasets, show brief skeleton for visual feedback
    previous_filter_state = st.session_state.get("calibre_filter_state")
    filters_changed = previous_filter_state != current_filter_state
    st.session_state["calibre_filter_state"] = current_filter_state

    # Create empty container that will hold either skeleton or actual table
    # Using st.empty() allows us to replace content without adding extra DOM elements
    table_container = st.empty()

    # Show skeleton flash for large datasets when filters change
    # Threshold of 100 books prevents skeleton flash on small datasets (where it's instant anyway)
    # Provides visual feedback that the filter is being applied
    if filters_changed and len(filtered_books) > 100:
        with table_container.container():
            render_table_skeleton(rows=5)

    # Display filtered books as paginated DataFrame
    if filtered_books:
        # Clear skeleton (if shown) before rendering actual table
        table_container.empty()

        # calibre_selected_books already initialized in AppState, persists across reruns
        # Don't reset it here or user selections will be lost

        # Pagination controls at top - 3-column layout for rows selector, page info, and spacing
        pagination_col1, pagination_col2, pagination_col3 = st.columns([1, 2, 1])

        with pagination_col1:
            # Rows per page selector - default to 50 (index=1)
            # Persisted via session_state key so selection survives page navigation
            rows_per_page = st.selectbox(
                "Rows",
                options=[20, 50, 100, 200],
                index=1,  # Default to 50 rows
                key="calibre_rows_per_page"
            )

        # Initialize current page to 1 on first load
        # Check session_state directly since AppState may not have initialized this yet
        if 'calibre_current_page' not in st.session_state:
            app_state.calibre_current_page = 1

        # Calculate total pages using ceiling division
        # Formula: (total + per_page - 1) // per_page handles remainder without importing math.ceil
        total_books = len(filtered_books)
        total_pages: int = (total_books + rows_per_page - 1) // rows_per_page

        # Validate and clamp current page to valid range [1, total_pages]
        # Defensive: handle non-int values that might get into session_state
        raw_page = st.session_state.get('calibre_current_page')
        try:
            current_page: int = int(raw_page) if raw_page is not None else 1
        except (TypeError, ValueError):
            # Fallback to page 1 if session_state contains invalid value
            current_page = 1

        # Clamp to valid range (handles edge cases like filter changes reducing total pages)
        current_page = max(1, min(current_page, total_pages))
        app_state.calibre_current_page = current_page

        with pagination_col2:
            # Center-aligned page info (e.g., "Page 2 of 10 (487 total)")
            st.markdown(f"<div style='text-align: center; padding-top: 8px;'>Page {current_page} of {total_pages} ({total_books:,} total)</div>", unsafe_allow_html=True)

        # Calculate array slice indices for current page
        # Zero-indexed: page 1 shows [0:50], page 2 shows [50:100], etc.
        start_idx = (current_page - 1) * rows_per_page
        end_idx = min(start_idx + rows_per_page, total_books)  # Clamp to avoid out-of-bounds

        # Build DataFrame rows for current page slice
        # Each row represents one book with metadata and selection state
        df_data = []
        selected_ids = app_state.calibre_selected_books  # Set of book IDs selected for ingestion

        for idx, book in enumerate(filtered_books[start_idx:end_idx]):
            # Map file formats to visual icons for quick recognition
            # Icons appear in unnamed column for compact visual format indicator
            format_icons = []
            if 'epub' in book.formats:
                format_icons.append('📕')  # EPUB = book emoji
            if 'pdf' in book.formats:
                format_icons.append('📄')  # PDF = document emoji
            if 'mobi' in book.formats or 'azw3' in book.formats:
                format_icons.append('📱')  # Kindle formats = mobile emoji
            if 'txt' in book.formats or 'md' in book.formats:
                format_icons.append('📝')  # Plain text formats = memo emoji

            # Format series information (e.g., "The Sea of Fertility #3")
            # Empty string if book is not part of a series
            series_info = f"{book.series} #{book.series_index:.0f}" if book.series else ""

            # Calculate global row number across all pages (1-based for human readability)
            # Example: Page 2 with 50 rows/page starts at row 51
            global_row_num = start_idx + idx + 1

            # Check if book already exists in Qdrant collection
            # Match logic: normalize both paths to lowercase POSIX format and compare directories
            # book.path from Calibre: "Author/Book (ID)" (relative directory path)
            # ingested_file_paths: set of normalized directories from manifest
            book_path = Path(book.path).as_posix().lower()
            is_already_ingested = book_path in ingested_file_paths

            # Diagnostic logging: show first 3 book path matching operations
            # Only logs if diagnostics enabled AND manifest diagnostics were logged this render
            if should_log_diagnostics and idx < 3:
                if idx == 0:  # Add section header before first book
                    st.session_state["diagnostic_log"].append(f"\n📖 **Calibre Book Matching:**")
                st.session_state["diagnostic_log"].append(f"  • Book {idx+1}: {book.title[:40]}")
                st.session_state["diagnostic_log"].append(f"    → Raw path: {book.path}")
                st.session_state["diagnostic_log"].append(f"    → Normalized: {book_path}")
                st.session_state["diagnostic_log"].append(f"    → In manifest? {is_already_ingested}")
                if is_already_ingested:
                    st.session_state["diagnostic_log"].append(f"    ✓ MATCH FOUND")

            # Construct DataFrame row with all columns
            # Select column: checkbox showing current selection state (True if book.id in selected_ids)
            # Id column: hidden from display but needed for tracking selections
            df_data.append({
                'Select': book.id in selected_ids,  # Checkbox state
                'Id': book.id,  # Hidden column (used in form submission handler)
                '#': global_row_num,  # Global row number
                '': ' '.join(format_icons) if format_icons else '📄',  # Format icons (unnamed column)
                'Status': '✓ Ingested' if is_already_ingested else '',  # Ingestion status indicator
                'Title': book.title[:60] + '...' if len(book.title) > 60 else book.title,  # Truncated title
                'Author': book.author[:30] + '...' if len(book.author) > 30 else book.author,  # Truncated author
                'Language': book.language.upper(),  # Language code in uppercase
                'Series': series_info,  # Series name and index (or empty)
                'Formats': ', '.join(book.formats[:3]),  # First 3 formats (comma-separated)
                'Added': book.timestamp[:10]  # Date added (YYYY-MM-DD)
            })

        # Convert list of dicts to pandas DataFrame for st.data_editor
        df = pd.DataFrame(df_data)

        # Get reset token to force form re-render when needed (e.g., after clearing selections)
        # Incrementing this token creates a new form with a different key, resetting internal state
        table_reset_token = st.session_state.get("calibre_table_reset", 0)

        # Wrap data_editor in a form to batch checkbox changes
        # Without form: each checkbox toggle causes immediate rerun (poor UX on large tables)
        # With form: user makes multiple selections, then clicks "Update Selection" once
        with st.form(key=f"calibre_table_form_{current_page}_{table_reset_token}"):
            # Calculate dynamic table height based on number of rows
            # Prevents excessive whitespace on small pages while capping max height
            row_height_px = 35  # Height per data row
            header_height_px = 38  # Height of column headers
            table_padding_px = 12  # Top/bottom padding
            max_table_height = 500  # Maximum height before scrolling
            dynamic_table_height = min(
                max_table_height,
                header_height_px + (row_height_px * max(len(df), 1)) + table_padding_px
            )

            # Render interactive data table with checkboxes
            # data_editor returns edited DataFrame when form is submitted
            edited_df = st.data_editor(
                df,
                use_container_width=True,  # Expand to fill available width
                height=dynamic_table_height,  # Dynamic height based on row count
                hide_index=True,  # Hide pandas index column
                column_config={
                    "Select": st.column_config.CheckboxColumn(required=True),  # Make Select column a checkbox
                    "Id": None,  # Hide Id column (but keep in DataFrame for submission handler)
                    "Status": st.column_config.TextColumn(
                        "Status",
                        width="small",  # Narrow column width
                        help="Shows if book is already ingested to Qdrant"  # Tooltip on hover
                    )
                },
                disabled=df.columns.drop(["Select"]),  # Only Select column is editable
                key=f"calibre_table_editor_{current_page}_{table_reset_token}"  # Unique key per page/reset
            )

            # Form submit button - triggers selection update handler
            apply_selection = st.form_submit_button("✅ Update Selection")

        # Handle form submission - update global selection state with page edits
        if apply_selection:
            # Get all book IDs on current page (regardless of selection state)
            page_ids = set(edited_df["Id"].tolist())

            # Get IDs of books selected on this page (where Select checkbox is True)
            page_selected_ids = set(edited_df.loc[edited_df["Select"], "Id"].tolist())

            # Merge page selections with global selection state
            # 1. Start with existing global selections
            updated_selected_ids = set(app_state.calibre_selected_books)

            # 2. Remove all IDs from current page (clear old page selections)
            updated_selected_ids.difference_update(page_ids)

            # 3. Add back the newly selected IDs from current page
            updated_selected_ids.update(page_selected_ids)

            # CRITICAL: Write directly to session_state to ensure persistence across reruns
            # app_state is a reference to session_state.app_state, so this persists properly
            st.session_state.app_state.calibre_selected_books = updated_selected_ids

            # Force full rerun to update ingestion section with new selection count
            st.rerun()

        # Bottom pagination navigation - Previous/Next buttons
        # Add spacing before pagination controls
        st.markdown("<div style='margin: 10px 0;'></div>", unsafe_allow_html=True)
        st.markdown('<div class="pagination-nav">', unsafe_allow_html=True)  # CSS class for custom styling

        # 3-column layout: narrow columns for buttons, wide center for page info
        nav_col1, nav_col2, nav_col3 = st.columns([0.3, 6, 0.3])

        with nav_col1:
            # Previous page button - only shown if not on first page
            # Decrement current_page and rerun to navigate backwards
            if current_page > 1 and st.button("←", key="calibre_prev", type="secondary"):
                app_state.calibre_current_page -= 1
                st.rerun()

        with nav_col2:
            # Center-aligned page info showing current row range and page numbers
            # Example: "Rows 51–100 of 487 | Page 2 of 10"
            st.markdown(
                f"<div style='text-align: center; padding-top: 8px; color: #666; font-size: 13px;'>"
                f"Rows {start_idx + 1}–{end_idx} of {total_books:,} &nbsp;|&nbsp; Page {current_page} of {total_pages}"
                f"</div>",
                unsafe_allow_html=True
            )

        with nav_col3:
            # Next page button - only shown if not on last page
            # Increment current_page and rerun to navigate forward
            if current_page < total_pages and st.button("→", key="calibre_next", type="secondary"):
                app_state.calibre_current_page += 1
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)  # Close pagination-nav div
    else:
        # No books match the current filters
        # Clear skeleton (if shown) and table_container will remain empty
        table_container.empty()

# ============================================
# TAB NAVIGATION SETUP
# ============================================
# Dynamic tab configuration: tabs shown depend on system state (e.g., archived manifests exist)
# Tab ordering can be programmatically changed (e.g., force Speaker tab to front after model fetch)

# --------------------------------------------------
# CONDITIONAL TAB VISIBILITY
# --------------------------------------------------
# Check if deleted manifest archives exist to determine if "Restore deleted" tab should show
# Archive directory structure: logs/deleted/<collection>_manifest_<timestamp>.json
archive_dir = Path(__file__).parent / 'logs' / 'deleted'
archived_manifests_exist = archive_dir.exists() and any(archive_dir.glob('*_manifest_*.json'))

# --------------------------------------------------
# TAB CONSTRUCTION
# --------------------------------------------------
# Build tab list dynamically - some tabs are always shown, others are conditional
speaker_tab_label = "🔍 Speaker's corner"  # Named separately for forced tab switching logic
tabs_to_show = [
    "📚 Calibre ingestion",   # Always shown - browse and ingest from Calibre library
    "🔄 Folder ingestion",    # Always shown - batch ingest from filesystem folder
    "📖 Qdrant collections",  # Always shown - view ingested books and manage collections
]
if archived_manifests_exist:
    # Conditionally add Restore tab if deleted manifests are available
    # Why: Don't clutter UI with empty tab when no archives exist
    tabs_to_show.append("🗄️ Restore deleted")
tabs_to_show.append(speaker_tab_label)  # Always shown - RAG query interface

# --------------------------------------------------
# FORCED TAB NAVIGATION
# --------------------------------------------------
# Programmatically switch active tab by reordering tabs_to_show list
# Pattern: Set force_speaker_tab flag → move speaker tab to front → clear flag
# Use case: After fetching models, switch to Speaker tab to show where models are used
if st.session_state.get("force_speaker_tab"):
    # Move speaker tab to front (first tab becomes active in Streamlit)
    tabs_to_show = [speaker_tab_label] + [tab for tab in tabs_to_show if tab != speaker_tab_label]
    st.session_state["force_speaker_tab"] = False  # Clear flag to prevent sticky behavior

# --------------------------------------------------
# TAB RENDERING
# --------------------------------------------------
# Create tab UI and build lookup dict for programmatic tab access
# Pattern: tabs_by_label allows accessing tabs by string label instead of positional index
tabs = st.tabs(tabs_to_show)  # Streamlit creates tab navigation UI
tabs_by_label = dict(zip(tabs_to_show, tabs))  # Map: "📚 Calibre ingestion" → tab object

# Extract tab references for use in "with tab_calibre:" blocks below
# Note: tab_restore may be None if no archives exist (handled with conditional rendering)
tab_calibre = tabs_by_label["📚 Calibre ingestion"]
tab_ingestion = tabs_by_label["🔄 Folder ingestion"]
tab_ingested = tabs_by_label["📖 Qdrant collections"]
tab_restore = tabs_by_label.get("🗄️ Restore deleted")  # .get() returns None if key missing
tab_query = tabs_by_label[speaker_tab_label]


# ============================================
# TAB 0: Calibre Library Browser
# ============================================
with tab_calibre:
    st.markdown('<div class="section-header">📚 Calibre Library</div>', unsafe_allow_html=True)

    # Initialize Calibre DB (Simple initialization, uses sidebar library_dir)
    try:
        # Force recreate CalibreDB to pick up module changes
        if 'calibre_db' not in st.session_state or str(st.session_state.calibre_db.library_path) != str(Path(library_dir)):
            with st.spinner("Connecting to Calibre database..."):
                # Clear both db and books cache to force fresh load
                if 'calibre_db' in st.session_state:
                    del st.session_state.calibre_db
                if 'calibre_books' in st.session_state:
                    del st.session_state.calibre_books

                st.session_state.calibre_db = CalibreDB(library_dir)

        calibre_db = st.session_state.calibre_db

        # Get all books - add refresh button during debug
        col_refresh, col_spacer = st.columns([1, 5])
        with col_refresh:
            if st.button("🔄 Refresh Books", help="Reload books from Calibre DB"):
                if 'calibre_books' in st.session_state:
                    del st.session_state.calibre_books
                st.rerun()

        # Create skeleton placeholder container
        skeleton_placeholder = st.empty()

        if 'calibre_books' not in st.session_state:
            # Show skeleton loader while loading
            with skeleton_placeholder.container():
                st.info("📚 Loading books from Calibre... (this may take a moment)")
                render_table_skeleton(rows=10)

            # Load books from database
            st.session_state.calibre_books = calibre_db.get_all_books()

            # Clear skeleton once loaded
            skeleton_placeholder.empty()
        else:
            # Clear placeholder if books already loaded
            skeleton_placeholder.empty()

        all_books = st.session_state.calibre_books

        # Debug: Check for duplicates
        son_of_hamas_books = [b for b in all_books if 'Son of Hamas' in b.title]
        if len(son_of_hamas_books) > 1:
            st.warning(f"⚠️ DEBUG: Found {len(son_of_hamas_books)} copies of 'Son of Hamas' in all_books!")
            for i, book in enumerate(son_of_hamas_books):
                st.write(f"  Copy {i+1}: ID={book.id}, author='{book.author}'")

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

        # Call isolated fragment for filters and table
        render_calibre_filters_and_table(all_books, calibre_db)

        # ============================================
        # INGESTION SECTION (OUTSIDE FRAGMENT)
        # ============================================
        st.markdown("---")

        # Get app state to access selected books
        app_state = get_app_state()
        selected_ids = app_state.calibre_selected_books
        selected_books = [book for book in all_books if book.id in selected_ids]

        # Get ingestion configuration from session state
        calibre_domain = st.session_state.get("calibre_ingest_domain", "technical")
        calibre_collection = st.session_state.get("calibre_ingest_collection", "alexandria")
        preferred_format = st.session_state.get("calibre_preferred_format", "epub")
        qdrant_host = st.session_state.get("qdrant_host", "192.168.0.151")
        qdrant_port = st.session_state.get("qdrant_port", 6333)
        library_dir = app_state.library_dir  # Use library_dir from app_state (set in sidebar)

        # Only show ingestion section if books are selected
        # Keep expander open if ingestion just completed (results available) so user can see message and dismiss
        should_expand_ingestion = "last_ingestion_results" in st.session_state
        with st.expander(f"🚀 Calibre > Qdrant ({len(selected_books)} selected)", expanded=should_expand_ingestion):
            # Display stored ingestion results if they exist (from previous rerun)
            if "last_ingestion_results" in st.session_state:
                results_data = st.session_state["last_ingestion_results"]
                # Show success message and dismiss button
                st.success(f"✅ {results_data['message']}")
                # Put dismiss button right below the message for better visibility
                if st.button("🗑️ Dismiss notification", key="dismiss_ingestion_results", type="secondary"):
                    del st.session_state["last_ingestion_results"]
                    # Clear diagnostic log when dismissing
                    if "diagnostic_log" in st.session_state:
                        del st.session_state["diagnostic_log"]
                    # Set flag to prevent manifest diagnostics from reappearing after dismiss
                    # This flag will be cleared on next ingestion
                    st.session_state["diagnostics_dismissed"] = True
                    st.rerun()
                st.markdown("---")

            # Display diagnostic log if it exists (from previous ingestion with diagnostics enabled)
            if "diagnostic_log" in st.session_state and st.session_state["diagnostic_log"]:
                # Check if this is ingestion diagnostics or manifest loading diagnostics
                log_entries = st.session_state["diagnostic_log"]
                is_ingestion_log = any("INGESTION STARTED" in entry for entry in log_entries)

                expander_title = "🔍 Ingestion Diagnostics" if is_ingestion_log else "🔍 Manifest Loading Debug"
                with st.expander(expander_title, expanded=is_ingestion_log):  # Auto-expand if ingestion log
                    # Display all log entries
                    log_text = "\n".join(log_entries)
                    st.code(log_text, language=None)
                st.markdown("---")

            # Configuration section
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

            # Display selection summary and ingest button
            if selected_books:
                st.info(f"📊 **Selected:** {len(selected_books)} book(s) ready for ingestion")

                if st.button("🚀 Start Ingestion", type="primary", use_container_width=True):
                    st.session_state["ingest_in_progress"] = True
                    # Clear any previous ingestion results and diagnostic log
                    if "last_ingestion_results" in st.session_state:
                        del st.session_state["last_ingestion_results"]
                    if "diagnostic_log" in st.session_state:
                        del st.session_state["diagnostic_log"]
                    # Clear all diagnostic flags to allow fresh diagnostics
                    keys_to_delete = [k for k in st.session_state.keys() if k.startswith("manifest_diagnostics_loaded_")]
                    for key in keys_to_delete:
                        del st.session_state[key]
                    # Clear dismiss flag to allow new diagnostic output
                    if "diagnostics_dismissed" in st.session_state:
                        del st.session_state["diagnostics_dismissed"]

                    # Initialize diagnostic log header for this ingestion
                    if get_app_state().show_ingestion_diagnostics:
                        st.session_state["diagnostic_log"] = [
                            f"🚀 **INGESTION STARTED** ({len(selected_books)} books selected)",
                            f"   Collection: {calibre_collection}",
                            f"   Domain: {calibre_domain}",
                            f"   Qdrant: {qdrant_host}:{qdrant_port}",
                            ""
                        ]
                    # Show configuration being used
                    st.write(f"🔄 Starting ingestion with {len(selected_books)} books...")
                    st.info(f"ℹ️ Ingesting to: {qdrant_host}:{qdrant_port} | Collection: {calibre_collection} | Domain: {calibre_domain}")

                    # Progress tracking
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    try:
                        # Define extraction function for Calibre books with format selection and file discovery
                        def extract_calibre_book(book):
                            """Extract filepath and metadata from Calibre book object."""
                            # Determine which format to use
                            format_to_use = None
                            if preferred_format in book.formats:
                                format_to_use = preferred_format
                            else:
                                # Fallback to first available format
                                format_to_use = book.formats[0] if book.formats else None

                            if not format_to_use:
                                raise ValueError(f"No supported format available for {book.title}")

                            # Construct absolute file path
                            active_library_path = Path(library_dir)
                            book_dir = active_library_path / book.path

                            if app_state.show_ingestion_diagnostics:
                                st.write(f"🔍 Book '{book.title}' has formats: {book.formats}")
                                st.write(f"🔍 Looking for format: {format_to_use}")
                                st.write(f"🔍 Searching in: {book_dir}")

                            # Find the actual file
                            matching_files = list(book_dir.glob(f"*.{format_to_use}"))
                            if app_state.show_ingestion_diagnostics:
                                st.write(f"🔍 Glob pattern: *.{format_to_use}")
                                st.write(f"🔍 Found files: {matching_files}")

                            if not matching_files:
                                raise FileNotFoundError(f"File not found at {book_dir} (looking for *.{format_to_use}, book has formats: {book.formats})")

                            file_path = matching_files[0]
                            # Simply convert to string like the old working code did
                            # str(WindowsPath) gives backslashes on Windows, which is correct
                            if app_state.show_ingestion_diagnostics:
                                st.write(f"📂 Path object: {file_path}")
                                st.write(f"📂 As string: {str(file_path)}")

                            metadata_dict = {
                                'title': book.title,
                                'author': book.author,
                                'language': book.language
                            }
                            if app_state.show_ingestion_diagnostics:
                                st.write(f"📋 Metadata from Calibre book object: author='{book.author}'")
                                st.write(f"📋 Calibre book ID: {book.id}, Title: {book.title}")

                            return (
                                file_path,  # Return Path object, ingest_items_batch will convert to str
                                metadata_dict
                            )

                        # Use DRY helper function for batch ingestion
                        results = ingest_items_batch(
                            items=selected_books,
                            extract_item_fn=extract_calibre_book,
                            domain=calibre_domain,
                            collection_name=calibre_collection,
                            qdrant_host=qdrant_host,
                            qdrant_port=qdrant_port,
                            move_files=False,  # Calibre doesn't move files
                            progress_callback=lambda p: progress_bar.progress(p),
                            status_callback=lambda s: status_text.text(s)
                        )

                        # Final status
                        progress_bar.progress(1.0)
                        status_text.text("✅ Ingestion complete!")

                        # Verify ingestion by checking collection
                        try:
                            from qdrant_client import QdrantClient
                            client = QdrantClient(host=qdrant_host, port=qdrant_port)
                            collection_info = client.get_collection(calibre_collection)
                            st.info(f"🔍 Collection '{calibre_collection}' now has {collection_info.points_count:,} total points")
                        except Exception as e:
                            st.warning(f"⚠️ Could not verify collection: {e}")

                        # Build results message
                        results_msg = f"Ingestion complete: {results['success_count']} successful, {results['error_count']} failed out of {results['total']} total"

                        if results['error_count'] > 0:
                            results_msg += f"\n\nErrors:\n" + "\n".join([f"• {e}" for e in results['errors']])

                        # Store ingestion results in session state to display after rerun
                        st.session_state["last_ingestion_results"] = {
                            'message': results_msg,
                            'success': results['success_count'] > 0,
                            'timestamp': datetime.now().isoformat()
                        }

                        # Clear ingestion progress flag
                        st.session_state["ingest_in_progress"] = False

                        # Clear selection after successful ingestion
                        if results['success_count'] > 0:
                            app_state.calibre_selected_books = set()
                            st.session_state.app_state.calibre_selected_books = set()  # Ensure persistence
                            st.rerun()  # Refresh UI to show cleared checkboxes and updated Qdrant tab
                        else:
                            # Show results immediately if no books were successfully ingested
                            st.success(f"✅ {results_msg}")

                    except Exception as e:
                        import traceback
                        error_trace = traceback.format_exc()
                        st.error(f"❌ Ingestion failed: {str(e)}")
                        with st.expander("Show error details"):
                            st.code(error_trace)
                        st.session_state["ingest_in_progress"] = False

            else:
                st.info("👆 Select books using the filters above, then use the checkboxes to select specific titles for ingestion")

        # Show ingestion status if in progress (displayed OUTSIDE fragment so it persists)
        if st.session_state.get("ingest_in_progress"):
            st.warning("⏳ Ingestion in progress... Please wait for completion message.")
            if st.session_state.get("ingest_error"):
                st.error(f"❌ {st.session_state['ingest_error']}")
                st.session_state["ingest_in_progress"] = False
            if st.session_state.get("ingest_success"):
                st.success(f"✅ {st.session_state['ingest_success']}")
                st.session_state["ingest_in_progress"] = False

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

                # Call isolated fragment for filters and table
                render_ingested_books_filters_and_table(books, collection_data, selected_collection)
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
                    points_count = collection_info.points_count or 0
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
                # Resolve script path for imports
                import sys
                scripts_path = Path(__file__).parent / 'scripts'
                if str(scripts_path) not in sys.path:
                    sys.path.insert(0, str(scripts_path))
                
                # PREVIEW MODE (now always active)
                from scripts.ingest_books import extract_metadata_only
                
                st.info("🔍 Scanning files for metadata...")
                metadata_list = []
                
                progress_bar = st.progress(0)
                for idx, file_path in enumerate(selected_files):
                    meta = extract_metadata_only(file_path)
                    if 'error' not in meta:
                                                    metadata_list.append({
                                                        "Title": meta.get('title', 'Unknown'),
                                                        "Author": meta.get('author', 'Unknown'),
                                                        "Language": meta.get('language', 'unknown'),
                                                        "Format": meta.get('format', 'Unknown').lower(), # Added Format, now lowercase
                                                        "Path": file_path # Hidden key
                                                    })
                    progress_bar.progress((idx + 1) / len(selected_files))
                
                if metadata_list:
                    st.session_state['ingest_metadata_preview'] = metadata_list
                    st.session_state['ingest_ready_to_confirm'] = True
                    st.rerun() # Rerun to show editor
                else:
                    st.error("❌ Failed to extract metadata from selected files.")

        # REVIEW CONFIRMATION UI (Outside the button logic)
        if st.session_state.get('ingest_ready_to_confirm', False):
            st.markdown("### 📝 Review & Edit Metadata")
            st.info("Edit the Title and Author fields below. What you see is what will be ingested.")
            
            preview_data = st.session_state['ingest_metadata_preview']
            df = pd.DataFrame(preview_data)
            
            edited_df = st.data_editor(
                df,
                use_container_width=True,
                                        disabled=["Path"],
                                        column_config={
                                            "Path": None # Hide full path
                                        },                key="metadata_editor"
            )
            
            col_confirm, col_cancel = st.columns([1, 1])
            with col_confirm:
                if st.button("✅ Confirm & Ingest All", type="primary"):
                    # Process edited dataframe using DRY helper function
                    st.info(f"🚀 Starting ingestion for {len(edited_df)} books with corrected metadata...")

                    # Resolve ingest_dir for moving
                    app_root = Path(__file__).parent
                    ingest_path_base = Path(ingest_dir) if Path(ingest_dir).is_absolute() else app_root / ingest_dir
                    ingested_dir = ingest_path_base.parent / 'ingested'
                    ingested_dir.mkdir(exist_ok=True)

                    # Setup progress tracking UI
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    # Define extraction function for dataframe rows (namedtuple from itertuples)
                    def extract_row(row):
                        """Extract filepath and metadata from dataframe row (namedtuple)"""
                        return (
                            row.Path,  # filepath (namedtuple attribute)
                            {
                                'title': row.Title,
                                'author': row.Author,
                                'language': row.Language
                            }
                        )

                    # Use DRY helper function for batch ingestion (consolidates common loop logic)
                    results = ingest_items_batch(
                        items=edited_df.itertuples(index=False),
                        extract_item_fn=lambda row: extract_row(row),
                        domain=domain,
                        collection_name=collection_name,
                        qdrant_host=qdrant_host,
                        qdrant_port=qdrant_port,
                        move_files=move_files,
                        ingested_dir=ingested_dir,
                        progress_callback=lambda p: progress_bar.progress(p),
                        status_callback=lambda s: status_text.text(s)
                    )

                    # Display results
                    if results['success_count'] > 0:
                        st.success(f"🎉 Batch complete! Successfully ingested {results['success_count']} books.")

                    if results['error_count'] > 0:
                        st.error(f"❌ Failed to ingest {results['error_count']} books")
                        with st.expander("Show errors"):
                            for error in results['errors']:
                                st.text(f"• {error}")

                    # Cleanup session state
                    del st.session_state['ingest_metadata_preview']
                    del st.session_state['ingest_ready_to_confirm']
                    st.button("🔄 Start New Batch") # Button to trigger rerun effectively

            with col_cancel:
                if st.button("❌ Cancel"):
                    del st.session_state['ingest_metadata_preview']
                    del st.session_state['ingest_ready_to_confirm']
                    st.rerun()

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
# TAB 3: Restore deleted
# ============================================
if tab_restore:
    with tab_restore:
        st.markdown('<div class="section-header">🗄️ Restore deleted</div>', unsafe_allow_html=True)
        st.info("Restore books from a deleted collection's manifest back into a new or existing collection.")

        archive_files = list(archive_dir.glob('*_manifest_*.json'))
        if not archive_files:
            st.warning("No deleted manifests found.")
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
                "Select a deleted manifest to restore from",
                options=list(archive_options.keys())
            )

            if selected_archive_display_name:
                selected_archive_path = archive_options[selected_archive_display_name]
                delete_archive_key = f"confirm_delete_archive_{selected_archive_path.name}"
                if delete_archive_key not in st.session_state:
                    st.session_state[delete_archive_key] = False
                
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
                            file_type = book.get('file_type')
                            if not file_type:
                                file_name = book.get('file_name') or book.get('file_path', '')
                                file_type = Path(file_name).suffix.upper().replace('.', '')
                            icon = {'EPUB': '📕', 'PDF': '📄', 'TXT': '📝', 'MD': '📝', 'MOBI': '📱'}.get(file_type, '📄')
                            df_data.append({
                                'Select': False,
                                '': icon,
                                'Title': book.get('book_title', 'N/A'),
                                'Author': book.get('author', 'N/A'),
                                'Domain': book.get('domain', 'N/A'),
                                'Type': file_type or 'N/A',
                                'File Path': book.get('file_path', 'N/A'),
                                'Language': book.get('language', 'unknown'),
                                'Chunks': book.get('chunks_count', 0),
                            })
                        
                        df = pd.DataFrame(df_data)

                        delete_archive_col1, delete_archive_col2 = st.columns([2, 3])
                        with delete_archive_col1:
                            if st.session_state[delete_archive_key]:
                                st.error(
                                    "**Confirm delete:** This will permanently remove the archived manifest file."
                                )
                                confirm_delete_col1, confirm_delete_col2 = st.columns(2)
                                with confirm_delete_col1:
                                    if st.button(
                                        "🗑️ Delete archive file",
                                        type="primary",
                                        use_container_width=True,
                                        key=f"delete_archive_{selected_archive_path.name}"
                                    ):
                                        try:
                                            selected_archive_path.unlink()
                                            st.success("✅ Archive file deleted.")
                                            st.session_state[delete_archive_key] = False
                                            st.info("Refreshing view...")
                                            time.sleep(1)
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"⚠️ Failed to delete archive file: {e}")
                                with confirm_delete_col2:
                                    if st.button(
                                        "Cancel",
                                        use_container_width=True,
                                        key=f"cancel_delete_archive_{selected_archive_path.name}"
                                    ):
                                        st.session_state[delete_archive_key] = False
                                        st.rerun()
                            else:
                                if st.button(
                                    "🗑️ Delete archive file",
                                    use_container_width=True,
                                    key=f"request_delete_archive_{selected_archive_path.name}"
                                ):
                                    st.session_state[delete_archive_key] = True
                                    st.rerun()
                        with delete_archive_col2:
                            st.caption("Delete the entire archived manifest file if you no longer need it.")
                        
                        st.markdown("##### 1. Select books to restore")
                        edited_df = st.data_editor(
                            df,
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "Select": st.column_config.CheckboxColumn(required=True),
                                "File Path": None,  # Hide file path from user
                                "Language": None
                            },
                            disabled=df.columns.drop("Select")
                        )
                        
                        selected_rows = edited_df[edited_df['Select']]

                        remove_col1, remove_col2 = st.columns([2, 3])
                        with remove_col1:
                            if st.button(
                                "🧹 Remove selected from archive",
                                use_container_width=True,
                                disabled=selected_rows.empty
                            ):
                                try:
                                    with open(selected_archive_path, 'r', encoding='utf-8') as f:
                                        archive_data = json.load(f)

                                    original_collection_name = selected_archive_path.stem.split('_manifest_')[0]
                                    selected_paths = set(selected_rows["File Path"].tolist())

                                    if original_collection_name in archive_data.get('collections', {}):
                                        original_books = archive_data['collections'][original_collection_name].get('books', [])
                                        updated_books = [
                                            book for book in original_books
                                            if book.get('file_path') not in selected_paths
                                        ]
                                        removed_count = len(original_books) - len(updated_books)
                                        archive_data['collections'][original_collection_name]['books'] = updated_books

                                        with open(selected_archive_path, 'w', encoding='utf-8') as f:
                                            json.dump(archive_data, f, indent=2, ensure_ascii=False)

                                        st.success(f"✅ Removed {removed_count} book(s) from the archive manifest.")
                                        st.info("Refreshing view...")
                                        time.sleep(1)
                                        st.rerun()
                                except Exception as e:
                                    st.error(f"⚠️ Failed to update archive manifest: {e}")
                        with remove_col2:
                            st.caption("Remove selected rows if you no longer want to restore them.")

                        restore_all = st.checkbox(
                            "Restore ALL books from this manifest",
                            value=False,
                            help="Ignores manual selection and restores every book in the deleted manifest."
                        )

                        if selected_rows.empty and not restore_all:
                            st.info("👆 Select books using the checkboxes above to begin the restore process, or enable Restore ALL.")
                        else:
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
                                default_domain = selected_rows.iloc[0]['Domain'] if not selected_rows.empty else df.iloc[0]['Domain']
                                restore_domain = st.selectbox(
                                    "Set new domain for all",
                                    options=load_domains(),
                                    index=load_domains().index(default_domain) if default_domain in load_domains() else 0,
                                    help="Select a new domain for all selected books for the restored collection."
                                )
                            
                            target_count = len(df) if restore_all else len(selected_rows)
                            st.info(f"You are about to ingest **{target_count}** book(s) into the **`{restore_collection_name}`** collection.")

                            if st.button("🚀 Restore Selected Books", type="primary", use_container_width=True):
                                progress_bar = st.progress(0)
                                status_text = st.empty()
                                success_count = 0
                                error_count = 0
                                errors = []
                                successfully_restored_paths = []

                                if restore_all:
                                    rows_to_restore = df
                                else:
                                    rows_to_restore = selected_rows

                                missing_paths = []
                                total_rows = len(rows_to_restore)

                                for idx, (_, row) in enumerate(rows_to_restore.iterrows(), start=1):
                                    progress = idx / max(total_rows, 1)
                                    progress_bar.progress(progress)
                                    status_text.text(f"Restoring {idx}/{total_rows}: {row['Title']}")
                                    
                                    file_path_to_ingest = row["File Path"]
                                    
                                    # Check if the file still exists
                                    if not Path(file_path_to_ingest).exists():
                                        missing_paths.append(file_path_to_ingest)
                                        errors.append(f"{row['Title']}: File not found at {file_path_to_ingest}")
                                        error_count += 1
                                        continue

                                    try:
                                        result = ingest_book(
                                            filepath=file_path_to_ingest,
                                            domain=restore_domain,
                                            collection_name=restore_collection_name,
                                            qdrant_host=qdrant_host,
                                            qdrant_port=qdrant_port,
                                            language_override=row.get('Language')
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
                                
                                if missing_paths:
                                    st.warning(
                                        f"⚠️ {len(missing_paths)} book file(s) were missing on disk and were skipped."
                                    )
                                    with st.expander("Missing file paths"):
                                        for missing in missing_paths:
                                            st.write(f"- {missing}")

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
                        


                except Exception as e:
                    st.error(f"Failed to read or parse the archive file: {selected_archive_path.name}")
                    st.error(str(e))

# ============================================
# TAB 4: Query
# ============================================
with tab_query:
    render_query_tab()

# Footer
st.markdown("---")
st.markdown(
    '<div style="text-align: center; color: #666; font-style: italic;">'
    '𝔸𝕝𝕖𝕩𝕒𝕟𝕕𝕣𝕚𝕒 𝕠𝕗 𝕋𝕖𝕞𝕖𝕟𝕠𝕤 • '
    'Built with ❤️ by 137 Team • 2026'
    '</div>',
    unsafe_allow_html=True
)
