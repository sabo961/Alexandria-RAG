#!/usr/bin/env python3
"""
Alexandria MCP Server
=====================

Model Context Protocol server for the Alexandria RAG system.
Provides access to ~9,000 books in the knowledge base via MCP tools.

TOOLS
-----
- alexandria_query: Semantic search with optional RAG answer generation
- alexandria_search: Search Calibre library by metadata
- alexandria_book: Get detailed metadata for a specific book
- alexandria_stats: Get collection and library statistics
- alexandria_ingest_preview: Preview books available for ingestion
- alexandria_ingest: Ingest a book from Calibre into Qdrant
- alexandria_test_chunking: Test chunking parameters without uploading

USAGE
-----
This server is designed to be used with Claude Code via stdio transport.

Configuration in .mcp.json:
{
  "mcpServers": {
    "alexandria": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/Alexandria", "python", "scripts/mcp_server.py"],
      "env": {
        "QDRANT_HOST": "192.168.0.151",
        "QDRANT_PORT": "6333",
        "CALIBRE_LIBRARY_PATH": "G:\\My Drive\\alexandria"
      }
    }
  }
}

For local testing:
    python scripts/mcp_server.py

ENVIRONMENT VARIABLES
--------------------
Required:
    QDRANT_HOST          - Qdrant server hostname (default: 192.168.0.151)
    QDRANT_PORT          - Qdrant server port (default: 6333)
    CALIBRE_LIBRARY_PATH - Path to Calibre library (default: G:\\My Drive\\alexandria)
    QDRANT_COLLECTION    - Qdrant collection name (default: alexandria)
"""

import os
import sys
import logging
from typing import Optional, List

from mcp.server.fastmcp import FastMCP

# Add scripts directory to path for local imports
scripts_dir = os.path.dirname(os.path.abspath(__file__))
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from rag_query import perform_rag_query, RAGResult
from calibre_db import CalibreDB, CalibreBook
from qdrant_utils import check_qdrant_connection
from ingest_books import ingest_book, test_chunking, extract_text
from collection_manifest import CollectionManifest

# Configure logging - reduce verbosity for MCP server
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

# Import from central config (loads .env automatically)
from config import (
    QDRANT_HOST,
    QDRANT_PORT,
    QDRANT_COLLECTION,
    CALIBRE_LIBRARY_PATH,
    LOCAL_INGEST_PATH,
    OPENROUTER_API_KEY,
)
COLLECTION_NAME = QDRANT_COLLECTION  # Alias for compatibility

# ============================================================================
# MCP SERVER
# ============================================================================

mcp = FastMCP(
    name="alexandria",
    instructions="Alexandria RAG system - access knowledge from ~9,000 books. Use alexandria_query for semantic search, alexandria_search for metadata search, alexandria_book for book details, alexandria_stats for statistics. For ingestion: use alexandria_ingest_preview to find books, alexandria_test_chunking to test parameters, and alexandria_ingest to upload to Qdrant."
)


# ============================================================================
# TOOL: alexandria_query
# ============================================================================

def _load_response_patterns() -> dict:
    """Load response patterns from patterns.json."""
    import json
    patterns_file = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'patterns.json')
    try:
        with open(patterns_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def _get_pattern_template(pattern_name: str) -> Optional[str]:
    """Get template for a pattern by category or id."""
    patterns = _load_response_patterns()

    # Search by category (e.g., "direct", "synthesis") - returns first in category
    if pattern_name in patterns:
        items = patterns[pattern_name]
        if items:
            return items[0].get('template')

    # Search by id across all categories (e.g., "cross_perspective", "tldr")
    for category, items in patterns.items():
        for p in items:
            if p.get('id') == pattern_name:
                return p.get('template')

    return None


@mcp.tool()
def alexandria_query(
    query: str,
    limit: int = 5,
    threshold: float = 0.5,
    context_mode: str = "precise",
    response_pattern: str = "free"
) -> dict:
    """
    Search Alexandria knowledge base using semantic similarity.

    Returns relevant chunks from books - Claude reads these directly
    and generates answers (no external LLM needed).

    Args:
        query: Natural language question or search query
        limit: Number of results to return (default: 5, max: 20)
        threshold: Similarity threshold 0.0-1.0 (default: 0.5)
        context_mode: How much context to include (default: "precise")
            - "precise": Only matched chunks (fastest, default)
            - "contextual": Include parent chapter context for each match
            - "comprehensive": Include parent + sibling chunks (most context)
        response_pattern: How to format the response (default: "free")
            - "free": No constraints, answer naturally
            - "direct": Use ONLY retrieved sources, cite explicitly
            - "synthesis": Cross-perspective analysis, use multiple sources
            - "extraction": Structured extraction with citations
            - "critical": Find contradictions, analyze assumptions
            - Or specific pattern id: "tldr", "cross_perspective", etc.

    Returns:
        dict with:
            - query: Original query
            - results: List of matching chunks with score, book_title, author,
                      section_name, and text
            - result_count: Number of results returned
            - context_mode: The context mode used
            - response_instruction: How to format response (if pattern specified)
            - parent_chunks: Parent chapter context (if context_mode != "precise")
            - hierarchy_stats: Stats about hierarchical retrieval
            - error: Error message if any

    Examples:
        alexandria_query("database normalization")
        alexandria_query("What is the shipment pattern?", limit=10)
        alexandria_query("loss aversion", context_mode="contextual")
        alexandria_query("cognitive biases", response_pattern="direct")
        alexandria_query("data modeling approaches", response_pattern="synthesis")
    """
    # Validate inputs
    limit = min(max(1, limit), 20)  # Clamp to 1-20
    threshold = min(max(0.0, threshold), 1.0)  # Clamp to 0.0-1.0

    # Validate context_mode
    valid_modes = ("precise", "contextual", "comprehensive")
    if context_mode not in valid_modes:
        context_mode = "precise"

    try:
        result: RAGResult = perform_rag_query(
            query=query,
            collection_name=COLLECTION_NAME,
            limit=limit,
            threshold=threshold,
            generate_llm_answer=False,
            host=QDRANT_HOST,
            port=QDRANT_PORT,
            context_mode=context_mode
        )

        response = {
            "query": result.query,
            "results": result.results,
            "result_count": len(result.results),
            "context_mode": result.context_mode,
            "error": result.error
        }

        # Include response instruction if pattern specified (not "free")
        if response_pattern and response_pattern != "free":
            template = _get_pattern_template(response_pattern)
            if template:
                response["response_instruction"] = template
                response["response_pattern"] = response_pattern
            else:
                response["response_instruction"] = None
                response["response_pattern_error"] = f"Unknown pattern: {response_pattern}"

        # Include hierarchical data if not in precise mode
        if context_mode != "precise":
            response["parent_chunks"] = result.parent_chunks
            response["hierarchy_stats"] = result.hierarchy_stats

        return response

    except Exception as e:
        logger.error(f"Query failed: {e}")
        return {
            "query": query,
            "results": [],
            "result_count": 0,
            "context_mode": context_mode,
            "error": str(e)
        }


# ============================================================================
# TOOL: alexandria_search
# ============================================================================

@mcp.tool()
def alexandria_search(
    author: Optional[str] = None,
    title: Optional[str] = None,
    language: Optional[str] = None,
    tags: Optional[str] = None,
    limit: int = 20
) -> dict:
    """
    Search Calibre library by metadata (author, title, language, tags).

    This is a metadata search, not semantic search. Use for finding books
    by known attributes rather than content-based queries.

    Args:
        author: Author name (partial match, case-insensitive)
        title: Book title (partial match, case-insensitive)
        language: ISO language code (e.g., 'eng', 'hrv', 'jpn')
        tags: Comma-separated tag names (books must have ALL tags)
        limit: Maximum results to return (default: 20, max: 100)

    Returns:
        dict with:
            - books: List of matching books with id, title, author, language,
                    tags, series, formats
            - count: Number of results
            - error: Error message if any

    Examples:
        # Search by author
        alexandria_search(author="Silverston")

        # Search by language
        alexandria_search(language="hrv")

        # Combined search
        alexandria_search(author="Mishima", language="eng")
    """
    limit = min(max(1, limit), 100)  # Clamp to 1-100

    try:
        db = CalibreDB(CALIBRE_LIBRARY_PATH)

        # Parse tags if provided
        tags_list = None
        if tags:
            tags_list = [t.strip() for t in tags.split(',')]

        books = db.search_books(
            author=author,
            title=title,
            language=language,
            tags=tags_list
        )

        # Limit results
        books = books[:limit]

        # Convert to serializable format
        results = []
        for book in books:
            results.append({
                "id": book.id,
                "title": book.title,
                "author": book.author,
                "language": book.language,
                "tags": book.tags,
                "series": book.series,
                "series_index": book.series_index,
                "formats": book.formats
            })

        return {
            "books": results,
            "count": len(results),
            "error": None
        }

    except FileNotFoundError as e:
        return {
            "books": [],
            "count": 0,
            "error": f"Calibre library not found: {e}"
        }
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return {
            "books": [],
            "count": 0,
            "error": str(e)
        }


# ============================================================================
# TOOL: alexandria_book
# ============================================================================

@mcp.tool()
def alexandria_book(book_id: int) -> dict:
    """
    Get detailed metadata for a specific book by Calibre ID.

    Args:
        book_id: Calibre database ID for the book

    Returns:
        dict with book metadata:
            - id, title, author, language, tags, series, series_index,
              isbn, publisher, pubdate, rating, formats
            - error: Error message if book not found

    Example:
        alexandria_book(123)
    """
    try:
        db = CalibreDB(CALIBRE_LIBRARY_PATH)
        book = db.get_book_by_id(book_id)

        if not book:
            return {
                "book": None,
                "error": f"Book with ID {book_id} not found"
            }

        return {
            "book": {
                "id": book.id,
                "title": book.title,
                "author": book.author,
                "language": book.language,
                "tags": book.tags,
                "series": book.series,
                "series_index": book.series_index,
                "isbn": book.isbn,
                "publisher": book.publisher,
                "pubdate": book.pubdate,
                "rating": book.rating,
                "formats": book.formats
            },
            "error": None
        }

    except FileNotFoundError as e:
        return {
            "book": None,
            "error": f"Calibre library not found: {e}"
        }
    except Exception as e:
        logger.error(f"Book lookup failed: {e}")
        return {
            "book": None,
            "error": str(e)
        }


# ============================================================================
# TOOL: alexandria_stats
# ============================================================================

@mcp.tool()
def alexandria_stats() -> dict:
    """
    Get Alexandria collection and Calibre library statistics.

    Returns statistics about the knowledge base including total books,
    authors, format distribution, language distribution, and vector
    collection status.

    Returns:
        dict with:
            - calibre: Calibre library stats (total_books, total_authors,
                      formats, languages)
            - qdrant: Vector collection stats (connected, collection_name,
                     points_count, vector_size)
            - error: Error message if any
    """
    result = {
        "calibre": None,
        "qdrant": None,
        "error": None
    }

    # Get Calibre stats
    try:
        db = CalibreDB(CALIBRE_LIBRARY_PATH)
        calibre_stats = db.get_stats()
        result["calibre"] = calibre_stats
    except FileNotFoundError as e:
        result["error"] = f"Calibre library not found: {e}"
    except Exception as e:
        result["error"] = f"Calibre stats failed: {e}"

    # Get Qdrant stats
    try:
        from qdrant_client import QdrantClient

        is_connected, error_msg = check_qdrant_connection(QDRANT_HOST, QDRANT_PORT)

        if is_connected:
            client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

            try:
                info = client.get_collection(COLLECTION_NAME)
                result["qdrant"] = {
                    "connected": True,
                    "collection_name": COLLECTION_NAME,
                    "points_count": info.points_count,
                    "vector_size": info.config.params.vectors.size,
                    "status": str(info.status)
                }
            except Exception as e:
                result["qdrant"] = {
                    "connected": True,
                    "collection_name": COLLECTION_NAME,
                    "error": f"Collection '{COLLECTION_NAME}' not found: {e}"
                }
        else:
            result["qdrant"] = {
                "connected": False,
                "error": "Cannot connect to Qdrant server"
            }

    except Exception as e:
        result["qdrant"] = {
            "connected": False,
            "error": str(e)
        }

    return result


# ============================================================================
# TOOL: alexandria_ingest_preview
# ============================================================================

@mcp.tool()
def alexandria_ingest_preview(
    author: Optional[str] = None,
    title: Optional[str] = None,
    language: Optional[str] = None,
    format_filter: str = "epub",
    limit: int = 20
) -> dict:
    """
    Preview books available for ingestion from Calibre library.

    Shows books matching criteria WITH their file paths and formats.
    Use this to see what's available before calling alexandria_ingest.

    Args:
        author: Filter by author name (partial match)
        title: Filter by book title (partial match)
        language: Filter by language code (e.g., 'en', 'hr')
        format_filter: Preferred format - 'epub', 'pdf', 'any' (default: epub)
        limit: Maximum results (default: 20, max: 50)

    Returns:
        dict with:
            - books: List of books with id, title, author, formats, file_path
            - count: Number of matching books
            - error: Error message if any

    Example:
        # Find EPUB books by a specific author
        alexandria_ingest_preview(author="Fowler", format_filter="epub")
    """
    limit = min(max(1, limit), 50)

    try:
        db = CalibreDB(CALIBRE_LIBRARY_PATH)

        books = db.search_books(
            author=author,
            title=title,
            language=language
        )

        results = []
        for book in books:
            # Filter by format
            available_formats = [f.lower() for f in book.formats]

            if format_filter.lower() == "any":
                selected_format = book.formats[0] if book.formats else None
            elif format_filter.lower() in available_formats:
                selected_format = format_filter.upper()
            else:
                continue  # Skip books without requested format

            if not selected_format:
                continue

            # Get file path
            file_path = db.get_book_file_path(book.id, selected_format)

            results.append({
                "id": book.id,
                "title": book.title,
                "author": book.author,
                "language": book.language,
                "formats": book.formats,
                "selected_format": selected_format,
                "file_path": file_path
            })

            if len(results) >= limit:
                break

        return {
            "books": results,
            "count": len(results),
            "format_filter": format_filter,
            "error": None
        }

    except FileNotFoundError as e:
        return {"books": [], "count": 0, "error": f"Calibre library not found: {e}"}
    except Exception as e:
        logger.error(f"Ingest preview failed: {e}")
        return {"books": [], "count": 0, "error": str(e)}


# ============================================================================
# TOOL: alexandria_ingest
# ============================================================================

@mcp.tool()
def alexandria_ingest(
    book_id: int,
    collection: Optional[str] = None,
    format_preference: str = "epub",
    hierarchical: bool = True,
    threshold: float = 0.55,
    min_chunk_size: int = 200,
    max_chunk_size: int = 1200
) -> dict:
    """
    Ingest a book from Calibre library into Qdrant vector database.

    Extracts text, chunks semantically, generates embeddings, and uploads.
    Use alexandria_ingest_preview first to find book IDs.

    Args:
        book_id: Calibre book ID (from alexandria_ingest_preview or alexandria_search)
        collection: Target Qdrant collection (default: uses QDRANT_COLLECTION env var)
        format_preference: Preferred format - 'epub' or 'pdf' (default: epub)
        hierarchical: Use two-level chunking - parent (chapter) + child (semantic) (default: True)
                      Set to False for flat chunking (legacy mode)
        threshold: Similarity threshold for chunking (0.0-1.0, default: 0.55)
                   Lower = fewer breaks (larger chunks), Higher = more breaks (smaller chunks)
        min_chunk_size: Minimum words per chunk (default: 200)
        max_chunk_size: Maximum words per chunk (default: 1200)

    Returns:
        dict with:
            - success: Whether ingestion completed
            - title: Book title
            - author: Book author
            - chunks: Number of chunks created
            - hierarchical: Whether hierarchical chunking was used
            - collection: Target collection name
            - progress: Visual progress indicator and steps completed
            - error: Error message if failed

    Example:
        alexandria_ingest(book_id=123)
        alexandria_ingest(book_id=123, hierarchical=False)  # flat mode
    """
    target_collection = collection or COLLECTION_NAME

    # Progress tracking
    steps = []
    total_steps = 6

    def progress_bar(current: int) -> str:
        """Generate visual progress bar."""
        filled = '█' * current
        empty = '░' * (total_steps - current)
        pct = int((current / total_steps) * 100)
        return f"[{filled}{empty}] {pct}%"

    try:
        # Step 1: Lookup book
        steps.append("📖 Looking up book in Calibre...")
        db = CalibreDB(CALIBRE_LIBRARY_PATH)
        book = db.get_book_by_id(book_id)

        if not book:
            return {
                "success": False,
                "progress": progress_bar(1),
                "steps": steps,
                "error": f"Book with ID {book_id} not found in Calibre"
            }

        steps[-1] = f"📖 Found: '{book.title}' by {book.author}"

        # Step 2: Select format
        steps.append(f"📁 Selecting format for '{book.title}'...")
        available_formats = [f.lower() for f in book.formats]
        if format_preference.lower() in available_formats:
            selected_format = format_preference.upper()
        elif available_formats:
            selected_format = book.formats[0]
        else:
            return {
                "success": False,
                "title": book.title,
                "author": book.author,
                "progress": progress_bar(2),
                "steps": steps,
                "error": f"No readable formats available for '{book.title}'"
            }
        steps[-1] = f"📁 Using {selected_format} format"

        # Step 3: Get file path
        steps.append(f"🔍 Locating file...")
        file_path = db.get_book_file_path(book_id, selected_format)
        if not file_path:
            return {
                "success": False,
                "title": book.title,
                "author": book.author,
                "progress": progress_bar(3),
                "steps": steps,
                "error": f"Could not locate {selected_format} file for '{book.title}'"
            }
        steps[-1] = f"🔍 File located"

        # Step 4: Check manifest
        steps.append(f"📋 Checking if already ingested...")
        manifest = CollectionManifest(collection_name=target_collection)
        for coll_name, coll_data in manifest.manifest.get('collections', {}).items():
            for ingested_book in coll_data.get('books', []):
                if ingested_book.get('file_path') == file_path:
                    return {
                        "success": False,
                        "title": book.title,
                        "author": book.author,
                        "progress": progress_bar(4),
                        "steps": steps + [f"⚠️ Already ingested in '{coll_name}'"],
                        "error": f"'{book.title}' already ingested in collection '{coll_name}'"
                    }
        steps[-1] = f"📋 Not previously ingested"

        # Step 5: Perform ingestion (extract, chunk, embed, upload)
        chunk_mode = "hierarchical" if hierarchical else "flat"
        steps.append(f"⚙️ Ingesting '{book.title}' ({chunk_mode} mode, threshold={threshold})...")
        result = ingest_book(
            filepath=file_path,
            collection_name=target_collection,
            qdrant_host=QDRANT_HOST,
            qdrant_port=QDRANT_PORT,
            title_override=book.title,
            author_override=book.author,
            language_override=book.language,
            hierarchical=hierarchical,
            threshold=threshold,
            min_chunk_size=min_chunk_size,
            max_chunk_size=max_chunk_size
        )

        if not result.get('success'):
            return {
                "success": False,
                "title": book.title,
                "author": book.author,
                "progress": progress_bar(5),
                "steps": steps + [f"❌ Ingestion failed"],
                "error": result.get('error', 'Unknown error during ingestion')
            }

        chunks_count = result.get('chunks', 0)
        steps[-1] = f"⚙️ Created {chunks_count} chunks"

        # Step 6: Update manifest
        steps.append(f"💾 Updating manifest...")
        import os
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        manifest.add_book(
            collection_name=target_collection,
            book_path=file_path,
            book_title=book.title,
            author=book.author,
            chunks_count=chunks_count,
            file_size_mb=file_size_mb,
            file_type=selected_format,
            language=book.language
        )
        steps[-1] = f"💾 Manifest updated"

        # Final success
        steps.append(f"✅ Successfully ingested '{book.title}'!")

        return {
            "success": True,
            "title": book.title,
            "author": book.author,
            "language": book.language,
            "chunks": chunks_count,
            "hierarchical": hierarchical,
            "chunking_params": {
                "threshold": threshold,
                "min_chunk_size": min_chunk_size,
                "max_chunk_size": max_chunk_size
            },
            "file_size_mb": round(file_size_mb, 2),
            "collection": target_collection,
            "format": selected_format,
            "progress": progress_bar(total_steps),
            "steps": steps,
            "error": None
        }

    except FileNotFoundError as e:
        return {
            "success": False,
            "progress": progress_bar(0),
            "steps": steps + [f"❌ Calibre library not found"],
            "error": f"Calibre library not found: {e}"
        }
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        return {
            "success": False,
            "progress": progress_bar(len(steps)),
            "steps": steps + [f"❌ Error: {str(e)}"],
            "error": str(e)
        }


# ============================================================================
# TOOL: alexandria_batch_ingest
# ============================================================================

@mcp.tool()
def alexandria_batch_ingest(
    book_ids: Optional[List[int]] = None,
    author: Optional[str] = None,
    title: Optional[str] = None,
    language: Optional[str] = None,
    limit: int = 10,
    collection: Optional[str] = None,
    format_preference: str = "epub",
    hierarchical: bool = True,
    threshold: float = 0.55,
    min_chunk_size: int = 200,
    max_chunk_size: int = 1200
) -> dict:
    """
    Batch ingest multiple books from Calibre library into Qdrant.

    Provide either book_ids OR search criteria (author/title/language).
    Books already in manifest are skipped.

    Args:
        book_ids: List of Calibre book IDs to ingest (e.g., [123, 456, 789])
        author: Search by author name (partial match) - alternative to book_ids
        title: Search by title (partial match) - alternative to book_ids
        language: Filter by language code (e.g., 'eng', 'hrv')
        limit: Maximum books to ingest (default: 10, max: 50)
        collection: Target Qdrant collection (default: env QDRANT_COLLECTION)
        format_preference: Preferred format - 'epub' or 'pdf' (default: epub)
        hierarchical: Use hierarchical chunking (default: True)
        threshold: Similarity threshold for chunking (default: 0.55)
        min_chunk_size: Minimum words per chunk (default: 200)
        max_chunk_size: Maximum words per chunk (default: 1200)

    Returns:
        dict with:
            - total: Number of books attempted
            - succeeded: Number successfully ingested
            - skipped: Number skipped (already ingested or no format)
            - failed: Number that failed
            - results: List of per-book results
            - summary: Human-readable summary

    Examples:
        # By IDs
        alexandria_batch_ingest(book_ids=[123, 456, 789])

        # By author (up to 10 books)
        alexandria_batch_ingest(author="Nietzsche", limit=10)

        # By author and language
        alexandria_batch_ingest(author="Mishima", language="eng", limit=5)
    """
    target_collection = collection or COLLECTION_NAME
    limit = min(max(1, limit), 50)  # Clamp to 1-50

    # Must provide either book_ids or search criteria
    if not book_ids and not any([author, title, language]):
        return {
            "total": 0,
            "succeeded": 0,
            "skipped": 0,
            "failed": 0,
            "results": [],
            "summary": "❌ Must provide either book_ids or search criteria (author/title/language)",
            "error": "No books specified"
        }

    try:
        db = CalibreDB(CALIBRE_LIBRARY_PATH)
        manifest = CollectionManifest(collection_name=target_collection)

        # Get list of books to process
        books_to_process = []

        if book_ids:
            # Lookup each book by ID
            for bid in book_ids[:limit]:
                book = db.get_book_by_id(bid)
                if book:
                    books_to_process.append(book)
        else:
            # Search by criteria
            found_books = db.search_books(
                author=author,
                title=title,
                language=language
            )
            books_to_process = found_books[:limit]

        if not books_to_process:
            return {
                "total": 0,
                "succeeded": 0,
                "skipped": 0,
                "failed": 0,
                "results": [],
                "summary": "⚠️ No books found matching criteria",
                "error": None
            }

        # Process each book
        results = []
        succeeded = 0
        skipped = 0
        failed = 0

        for i, book in enumerate(books_to_process):
            book_result = {
                "id": book.id,
                "title": book.title,
                "author": book.author,
                "status": None,
                "chunks": 0,
                "error": None
            }

            # Check format availability
            available_formats = [f.lower() for f in book.formats]
            if format_preference.lower() in available_formats:
                selected_format = format_preference.upper()
            elif available_formats:
                selected_format = book.formats[0]
            else:
                book_result["status"] = "skipped"
                book_result["error"] = "No readable format"
                skipped += 1
                results.append(book_result)
                continue

            # Get file path
            file_path = db.get_book_file_path(book.id, selected_format)
            if not file_path:
                book_result["status"] = "skipped"
                book_result["error"] = "File not found"
                skipped += 1
                results.append(book_result)
                continue

            # Check if already ingested
            already_ingested = False
            for coll_name, coll_data in manifest.manifest.get('collections', {}).items():
                for ingested_book in coll_data.get('books', []):
                    if ingested_book.get('file_path') == file_path:
                        already_ingested = True
                        break
                if already_ingested:
                    break

            if already_ingested:
                book_result["status"] = "skipped"
                book_result["error"] = "Already ingested"
                skipped += 1
                results.append(book_result)
                continue

            # Perform ingestion
            try:
                ingest_result = ingest_book(
                    filepath=file_path,
                    collection_name=target_collection,
                    qdrant_host=QDRANT_HOST,
                    qdrant_port=QDRANT_PORT,
                    title_override=book.title,
                    author_override=book.author,
                    language_override=book.language,
                    hierarchical=hierarchical,
                    threshold=threshold,
                    min_chunk_size=min_chunk_size,
                    max_chunk_size=max_chunk_size
                )

                if ingest_result.get('success'):
                    # Update manifest
                    import os
                    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
                    manifest.add_book(
                        collection_name=target_collection,
                        book_path=file_path,
                        book_title=book.title,
                        author=book.author,
                        chunks_count=ingest_result.get('chunks', 0),
                        file_size_mb=file_size_mb,
                        file_type=selected_format,
                        language=book.language
                    )

                    book_result["status"] = "success"
                    book_result["chunks"] = ingest_result.get('chunks', 0)
                    succeeded += 1
                else:
                    book_result["status"] = "failed"
                    book_result["error"] = ingest_result.get('error', 'Unknown error')
                    failed += 1

            except Exception as e:
                book_result["status"] = "failed"
                book_result["error"] = str(e)
                failed += 1

            results.append(book_result)

        # Build summary
        total = len(books_to_process)
        summary_parts = [f"📚 Batch ingest complete: {succeeded}/{total} succeeded"]
        if skipped > 0:
            summary_parts.append(f"{skipped} skipped")
        if failed > 0:
            summary_parts.append(f"{failed} failed")

        return {
            "total": total,
            "succeeded": succeeded,
            "skipped": skipped,
            "failed": failed,
            "results": results,
            "summary": ", ".join(summary_parts),
            "error": None
        }

    except FileNotFoundError as e:
        return {
            "total": 0,
            "succeeded": 0,
            "skipped": 0,
            "failed": 0,
            "results": [],
            "summary": f"❌ Calibre library not found",
            "error": str(e)
        }
    except Exception as e:
        logger.error(f"Batch ingestion failed: {e}")
        return {
            "total": 0,
            "succeeded": 0,
            "skipped": 0,
            "failed": 0,
            "results": [],
            "summary": f"❌ Error: {str(e)}",
            "error": str(e)
        }


# ============================================================================
# TOOL: alexandria_browse_local
# ============================================================================

@mcp.tool()
def alexandria_browse_local(
    path: Optional[str] = None,
    recursive: bool = False
) -> dict:
    """
    Browse local files available for ingestion.

    Lists EPUB, PDF, TXT, MD, and HTML files in a directory. Use this to find files
    before calling alexandria_ingest_file.

    Args:
        path: Directory to browse (default: LOCAL_INGEST_PATH env var or ~/Downloads)
        recursive: Search subdirectories (default: False)

    Returns:
        dict with:
            - path: Directory browsed
            - files: List of files with name, size_mb, format, full_path
            - count: Number of files found
            - error: Error message if any

    Examples:
        # Browse default location (~/Downloads)
        alexandria_browse_local()

        # Browse specific directory
        alexandria_browse_local(path="C:/Books")

        # Include subdirectories
        alexandria_browse_local(path="C:/Books", recursive=True)
    """
    import os
    from pathlib import Path

    browse_path = path or LOCAL_INGEST_PATH

    try:
        if not os.path.isdir(browse_path):
            return {
                "path": browse_path,
                "files": [],
                "count": 0,
                "error": f"Directory not found: {browse_path}"
            }

        supported_extensions = {'.epub', '.pdf', '.txt', '.md', '.html', '.htm'}
        files = []

        if recursive:
            for root, _, filenames in os.walk(browse_path):
                for filename in filenames:
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in supported_extensions:
                        full_path = os.path.join(root, filename)
                        size_mb = os.path.getsize(full_path) / (1024 * 1024)
                        files.append({
                            "name": filename,
                            "size_mb": round(size_mb, 2),
                            "format": ext[1:].upper(),
                            "full_path": full_path
                        })
        else:
            for filename in os.listdir(browse_path):
                ext = os.path.splitext(filename)[1].lower()
                if ext in supported_extensions:
                    full_path = os.path.join(browse_path, filename)
                    if os.path.isfile(full_path):
                        size_mb = os.path.getsize(full_path) / (1024 * 1024)
                        files.append({
                            "name": filename,
                            "size_mb": round(size_mb, 2),
                            "format": ext[1:].upper(),
                            "full_path": full_path
                        })

        # Sort by name
        files.sort(key=lambda x: x['name'].lower())

        return {
            "path": browse_path,
            "files": files,
            "count": len(files),
            "error": None
        }

    except PermissionError:
        return {
            "path": browse_path,
            "files": [],
            "count": 0,
            "error": f"Permission denied: {browse_path}"
        }
    except Exception as e:
        return {
            "path": browse_path,
            "files": [],
            "count": 0,
            "error": str(e)
        }


# ============================================================================
# TOOL: alexandria_ingest_file
# ============================================================================

@mcp.tool()
def alexandria_ingest_file(
    file_path: str,
    title: Optional[str] = None,
    author: Optional[str] = None,
    language: Optional[str] = None,
    collection: Optional[str] = None,
    hierarchical: bool = True,
    threshold: float = 0.55,
    min_chunk_size: int = 200,
    max_chunk_size: int = 1200
) -> dict:
    """
    Ingest a local book file into Qdrant (no Calibre required).

    Supports EPUB, PDF, TXT, MD, and HTML files. Metadata is extracted from the file
    first - if title or author is missing/unknown, returns asking for them.

    Args:
        file_path: Absolute path to the book file (EPUB, PDF, TXT, MD, HTML)
        title: Book title (required if not in file metadata)
        author: Book author (required if not in file metadata)
        language: Language code e.g. 'eng', 'hrv' (optional)
        collection: Target Qdrant collection (default: env QDRANT_COLLECTION)
        hierarchical: Use two-level chunking - parent (chapter) + child (semantic) (default: True)
        threshold: Similarity threshold for chunking (0.0-1.0, default: 0.55)
                   Lower = fewer breaks (larger chunks), Higher = more breaks (smaller chunks)
        min_chunk_size: Minimum words per chunk (default: 200)
        max_chunk_size: Maximum words per chunk (default: 1200)

    Returns:
        On success:
            - success: True
            - title, author, language, chunks, collection, format
            - progress: Visual progress indicator
            - steps: Steps completed

        If metadata missing (needs_metadata=True):
            - success: False
            - needs_metadata: True
            - file_path, file_name, format, file_size_mb
            - extracted: What was found in file
            - missing_fields: ['title'] and/or ['author']
            - error: Instructions to provide missing data

    Examples:
        # First attempt - may ask for metadata
        alexandria_ingest_file(file_path="/path/to/book.pdf")
        # Response: needs_metadata=True, missing_fields=['title', 'author']

        # Second attempt with metadata
        alexandria_ingest_file(
            file_path="/path/to/book.pdf",
            title="My Book",
            author="John Doe"
        )
    """
    import os
    target_collection = collection or COLLECTION_NAME

    # Progress tracking
    steps = []
    total_steps = 6  # validate, manifest, metadata, ingest, manifest update, done

    def progress_bar(current: int) -> str:
        filled = '█' * current
        empty = '░' * (total_steps - current)
        pct = int((current / total_steps) * 100)
        return f"[{filled}{empty}] {pct}%"

    try:
        # Step 1: Validate file
        steps.append(f"📁 Validating file path...")

        if not os.path.isabs(file_path):
            return {
                "success": False,
                "progress": progress_bar(1),
                "steps": steps + ["❌ Path must be absolute"],
                "error": f"File path must be absolute, got: {file_path}"
            }

        if not os.path.exists(file_path):
            return {
                "success": False,
                "progress": progress_bar(1),
                "steps": steps + ["❌ File not found"],
                "error": f"File not found: {file_path}"
            }

        # Check file extension
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in ['.epub', '.pdf', '.txt', '.md', '.html', '.htm']:
            return {
                "success": False,
                "progress": progress_bar(1),
                "steps": steps + [f"❌ Unsupported format: {ext}"],
                "error": f"Unsupported file format: {ext}. Supported: .epub, .pdf, .txt, .md, .html"
            }

        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        file_name = os.path.basename(file_path)
        steps[-1] = f"📁 Found: {file_name} ({file_size_mb:.1f} MB)"

        # Step 2: Check manifest
        steps.append(f"📋 Checking if already ingested...")
        manifest = CollectionManifest(collection_name=target_collection)
        for coll_name, coll_data in manifest.manifest.get('collections', {}).items():
            for ingested_book in coll_data.get('books', []):
                if ingested_book.get('file_path') == file_path:
                    book_title = ingested_book.get('title', file_name)
                    return {
                        "success": False,
                        "title": book_title,
                        "progress": progress_bar(2),
                        "steps": steps + [f"⚠️ Already ingested in '{coll_name}'"],
                        "error": f"'{book_title}' already ingested in collection '{coll_name}'"
                    }
        steps[-1] = f"📋 Not previously ingested"

        # Step 3: Extract and validate metadata
        steps.append(f"🔍 Extracting metadata from file...")

        try:
            _, file_metadata = extract_text(file_path)
        except Exception as e:
            return {
                "success": False,
                "progress": progress_bar(3),
                "steps": steps + [f"❌ Failed to extract: {str(e)}"],
                "error": f"Failed to extract text/metadata: {str(e)}"
            }

        # Determine final metadata (override > extracted)
        extracted_title = file_metadata.get('title', '')
        extracted_author = file_metadata.get('author', '')
        extracted_language = file_metadata.get('language', '')

        final_title = title or extracted_title
        final_author = author or extracted_author
        final_language = language or extracted_language

        # Check for missing/unknown values
        def is_missing(val: str) -> bool:
            if not val:
                return True
            return val.lower() in ['unknown', 'unknown author', '']

        missing_fields = []
        if is_missing(final_title):
            missing_fields.append('title')
        if is_missing(final_author):
            missing_fields.append('author')

        # If metadata is missing, return asking for it
        if missing_fields:
            steps[-1] = f"⚠️ Missing metadata: {', '.join(missing_fields)}"

            return {
                "success": False,
                "needs_metadata": True,
                "file_path": file_path,
                "file_name": file_name,
                "file_size_mb": round(file_size_mb, 2),
                "format": ext[1:].upper(),
                "extracted": {
                    "title": extracted_title if not is_missing(extracted_title) else None,
                    "author": extracted_author if not is_missing(extracted_author) else None,
                    "language": extracted_language if not is_missing(extracted_language) else None
                },
                "missing_fields": missing_fields,
                "progress": progress_bar(3),
                "steps": steps,
                "error": f"Missing required metadata: {', '.join(missing_fields)}. Please provide: alexandria_ingest_file(file_path=\"{file_path}\", {', '.join(f'{f}=\"...\"' for f in missing_fields)})"
            }

        steps[-1] = f"🔍 Metadata: '{final_title}' by {final_author}"

        # Step 4: Ingest (chunk, embed, upload)
        chunk_mode = "hierarchical" if hierarchical else "flat"
        steps.append(f"⚙️ Ingesting ({chunk_mode} mode, threshold={threshold})...")

        result = ingest_book(
            filepath=file_path,
            collection_name=target_collection,
            qdrant_host=QDRANT_HOST,
            qdrant_port=QDRANT_PORT,
            title_override=final_title,
            author_override=final_author,
            language_override=final_language,
            hierarchical=hierarchical,
            threshold=threshold,
            min_chunk_size=min_chunk_size,
            max_chunk_size=max_chunk_size
        )

        if not result.get('success'):
            return {
                "success": False,
                "title": final_title,
                "author": final_author,
                "progress": progress_bar(4),
                "steps": steps + ["❌ Ingestion failed"],
                "error": result.get('error', 'Unknown error during ingestion')
            }

        actual_title = final_title
        actual_author = final_author
        actual_language = final_language or 'unknown'
        chunks_count = result.get('chunks', 0)

        steps[-1] = f"⚙️ Created {chunks_count} chunks"

        # Step 4: Update manifest
        steps.append(f"💾 Updating manifest...")
        manifest.add_book(
            collection_name=target_collection,
            book_path=file_path,
            book_title=actual_title,
            author=actual_author,
            chunks_count=chunks_count,
            file_size_mb=file_size_mb,
            file_type=ext[1:].upper(),  # Remove dot
            language=actual_language
        )
        steps[-1] = f"💾 Manifest updated"

        # Final success
        steps.append(f"✅ Successfully ingested '{actual_title}'!")

        return {
            "success": True,
            "title": actual_title,
            "author": actual_author,
            "language": actual_language,
            "chunks": chunks_count,
            "hierarchical": hierarchical,
            "chunking_params": {
                "threshold": threshold,
                "min_chunk_size": min_chunk_size,
                "max_chunk_size": max_chunk_size
            },
            "file_size_mb": round(file_size_mb, 2),
            "collection": target_collection,
            "format": ext[1:].upper(),
            "progress": progress_bar(total_steps),
            "steps": steps,
            "error": None
        }

    except Exception as e:
        logger.error(f"File ingestion failed: {e}")
        return {
            "success": False,
            "progress": progress_bar(len(steps)),
            "steps": steps + [f"❌ Error: {str(e)}"],
            "error": str(e)
        }


# ============================================================================
# TOOL: alexandria_test_chunking
# ============================================================================

@mcp.tool()
def alexandria_test_chunking(
    book_id: int,
    threshold: float = 0.55,
    min_chunk_size: int = 200,
    max_chunk_size: int = 1200,
    format_preference: str = "epub"
) -> dict:
    """
    Test chunking parameters on a book WITHOUT uploading to Qdrant.

    Use this to experiment with chunking settings before ingestion.

    Args:
        book_id: Calibre book ID
        threshold: Similarity threshold 0.0-1.0 (default: 0.55)
                   Lower = fewer breaks (larger chunks)
                   Higher = more breaks (smaller chunks)
        min_chunk_size: Minimum words per chunk (default: 200)
        max_chunk_size: Maximum words per chunk (default: 1200)
        format_preference: Preferred format - 'epub' or 'pdf' (default: epub)

    Returns:
        dict with:
            - success: Whether test completed
            - title: Book title
            - parameters: Chunking parameters used
            - stats: Chunk statistics (total, avg/min/max words)
            - samples: Sample chunks for review
            - error: Error message if failed

    Example:
        # Test with more aggressive chunking
        alexandria_test_chunking(book_id=123, threshold=0.7, max_chunk_size=800)
    """
    try:
        db = CalibreDB(CALIBRE_LIBRARY_PATH)
        book = db.get_book_by_id(book_id)

        if not book:
            return {"success": False, "error": f"Book with ID {book_id} not found"}

        # Select format
        available_formats = [f.lower() for f in book.formats]
        if format_preference.lower() in available_formats:
            selected_format = format_preference.upper()
        elif available_formats:
            selected_format = book.formats[0]
        else:
            return {"success": False, "error": f"No readable formats for '{book.title}'"}

        file_path = db.get_book_file_path(book_id, selected_format)
        if not file_path:
            return {"success": False, "error": f"Could not locate file for '{book.title}'"}

        # Run chunking test
        result = test_chunking(
            filepath=file_path,
            threshold=threshold,
            min_chunk_size=min_chunk_size,
            max_chunk_size=max_chunk_size,
            show_samples=3
        )

        return result

    except Exception as e:
        logger.error(f"Chunking test failed: {e}")
        return {"success": False, "error": str(e)}


# ============================================================================
# TOOL: alexandria_test_chunking_file
# ============================================================================

@mcp.tool()
def alexandria_test_chunking_file(
    file_path: str,
    threshold: float = 0.55,
    min_chunk_size: int = 200,
    max_chunk_size: int = 1200
) -> dict:
    """
    Test chunking parameters on a local file WITHOUT uploading to Qdrant.

    No Calibre required. Use this to experiment with chunking settings
    before ingestion.

    Args:
        file_path: Absolute path to the book file (EPUB, PDF, TXT, MD, HTML)
        threshold: Similarity threshold 0.0-1.0 (default: 0.55)
                   Lower = fewer breaks (larger chunks)
                   Higher = more breaks (smaller chunks)
        min_chunk_size: Minimum words per chunk (default: 200)
        max_chunk_size: Maximum words per chunk (default: 1200)

    Returns:
        dict with:
            - success: Whether test completed
            - title: Book title (extracted from file)
            - parameters: Chunking parameters used
            - stats: Chunk statistics (total, avg/min/max words)
            - samples: Sample chunks for review
            - error: Error message if failed

    Example:
        alexandria_test_chunking_file(
            file_path="/path/to/book.epub",
            threshold=0.7,
            max_chunk_size=800
        )
    """
    import os

    try:
        # Validate file
        if not os.path.isabs(file_path):
            return {"success": False, "error": f"File path must be absolute: {file_path}"}

        if not os.path.exists(file_path):
            return {"success": False, "error": f"File not found: {file_path}"}

        ext = os.path.splitext(file_path)[1].lower()
        if ext not in ['.epub', '.pdf', '.txt', '.md', '.html', '.htm']:
            return {"success": False, "error": f"Unsupported format: {ext}"}

        # Run chunking test
        result = test_chunking(
            filepath=file_path,
            threshold=threshold,
            min_chunk_size=min_chunk_size,
            max_chunk_size=max_chunk_size,
            show_samples=3
        )

        return result

    except Exception as e:
        logger.error(f"Chunking test failed: {e}")
        return {"success": False, "error": str(e)}


# ============================================================================
# MAIN
# ============================================================================

def print_help():
    """Print help information about the MCP server."""
    help_text = """
Alexandria MCP Server
=====================

Model Context Protocol server for the Alexandria RAG system.
Provides access to ~9,000 books in the knowledge base.

QUERY TOOLS
-----------
  alexandria_query        Semantic search with context modes (precise/contextual/comprehensive)
  alexandria_search       Search Calibre library by metadata (author, title, tags)
  alexandria_book         Get detailed metadata for a specific book by ID
  alexandria_stats        Get collection and library statistics

INGEST TOOLS (Calibre)
----------------------
  alexandria_ingest_preview  Preview books available for ingestion
  alexandria_ingest          Ingest a book from Calibre into Qdrant
  alexandria_batch_ingest    Ingest multiple books by criteria
  alexandria_test_chunking   Test chunking parameters without uploading

INGEST TOOLS (Local Files)
--------------------------
  alexandria_browse_local       Browse local files for ingestion
  alexandria_ingest_file        Ingest local file (no Calibre)
  alexandria_test_chunking_file Test chunking on local file

ENVIRONMENT VARIABLES
---------------------
  QDRANT_HOST           Qdrant server hostname (default: 192.168.0.151)
  QDRANT_PORT           Qdrant server port (default: 6333)
  CALIBRE_LIBRARY_PATH  Path to Calibre library
  QDRANT_COLLECTION     Collection name (default: alexandria)
  LOCAL_INGEST_PATH     Default path for local file browsing

CONFIGURATION
-------------
Add to .mcp.json:

  {
    "mcpServers": {
      "alexandria": {
        "command": "uv",
        "args": ["run", "--directory", "/path/to/Alexandria", "python", "scripts/mcp_server.py"],
        "env": {
          "QDRANT_HOST": "192.168.0.151",
          "CALIBRE_LIBRARY_PATH": "G:\\\\My Drive\\\\alexandria"
        }
      }
    }
  }

DOCUMENTATION
-------------
  Full docs: docs/reference/mcp-server.md
  Workflows: docs/how-to-guides/common-workflows.md

ANSWER GENERATION
-----------------
  Default:  Claude Code synthesizes answers from returned chunks
  Optional: Use CLI with --answer for OpenRouter LLM testing
            python rag_query.py "question" --answer --model meta-llama/llama-3-8b-instruct
"""
    print(help_text)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Alexandria MCP Server - RAG knowledge base for Claude Code",
        add_help=False  # We handle --help ourselves for nicer output
    )
    parser.add_argument('-h', '--help', action='store_true', help='Show this help message')
    parser.add_argument('--list-tools', action='store_true', help='List available MCP tools')

    args, unknown = parser.parse_known_args()

    if args.help:
        print_help()
        sys.exit(0)

    if args.list_tools:
        tools = [
            "alexandria_query", "alexandria_search", "alexandria_book", "alexandria_stats",
            "alexandria_ingest_preview", "alexandria_ingest", "alexandria_batch_ingest",
            "alexandria_test_chunking", "alexandria_browse_local", "alexandria_ingest_file",
            "alexandria_test_chunking_file"
        ]
        print("Available MCP tools:")
        for t in tools:
            print(f"  - {t}")
        sys.exit(0)

    # Run the MCP server using stdio transport
    mcp.run()
