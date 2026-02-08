"""
Alexandria Qdrant Utilities

Utility functions for managing Qdrant collections during experimentation.

Usage:
    # Note: For deletion with artifacts, use the --with-artifacts flag
    python qdrant_utils.py list
    python qdrant_utils.py stats alexandria
    python qdrant_utils.py copy alexandria_v1 alexandria_v2
    python qdrant_utils.py delete alexandria_test
    python qdrant_utils.py alias alexandria alexandria_prod
    python qdrant_utils.py search alexandria "database normalization" --limit 5
"""

import argparse
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, Filter, FieldCondition, MatchValue
import requests.exceptions

from config import QDRANT_HOST, QDRANT_PORT

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# CONNECTION HELPERS
# ============================================================================

def check_qdrant_connection(host: str, port: int, timeout: int = 5) -> Tuple[bool, Optional[str]]:
    """
    Check if Qdrant server is reachable.

    Args:
        host: Qdrant server hostname or IP address
        port: Qdrant server port
        timeout: Connection timeout in seconds (default: 5)

    Returns:
        Tuple of (is_connected, error_message):
            - (True, None) if connection successful
            - (False, error_msg) if connection failed with helpful debugging hints
    """
    try:
        client = QdrantClient(host=host, port=port, timeout=timeout)
        client.get_collections()  # Simple operation to test connectivity
        return True, None
    except (ConnectionError, TimeoutError, requests.exceptions.ConnectionError) as e:
        error_msg = f"""
❌ Cannot connect to Qdrant server at {host}:{port}

Possible causes:
  1. VPN not connected - Verify VPN connection if server is remote
  2. Firewall blocking port {port} - Check firewall rules
  3. Qdrant server not running - Verify server status at http://{host}:{port}/dashboard
  4. Network timeout ({timeout}s) - Server may be slow or unreachable

Connection error: {str(e)}
"""
        return False, error_msg
    except Exception as e:
        error_msg = f"Unexpected error connecting to Qdrant at {host}:{port}: {str(e)}"
        return False, error_msg


# ============================================================================
# COLLECTION MANAGEMENT
# ============================================================================

def list_collections(host: str = QDRANT_HOST, port: int = QDRANT_PORT):
    """List all Qdrant collections with basic stats"""
    # Check connection first
    is_connected, error_msg = check_qdrant_connection(host, port)
    if not is_connected:
        logger.error(error_msg)
        return

    client = QdrantClient(host=host, port=port)

    collections = client.get_collections().collections

    if not collections:
        logger.info("No collections found")
        return

    logger.info(f"Found {len(collections)} collections:")
    logger.info("-" * 80)

    for coll in collections:
        info = client.get_collection(coll.name)
        logger.info(f"📚 {coll.name}")
        logger.info(f"   Points: {info.points_count}")
        logger.info(f"   Vector size: {info.config.params.vectors.size}")
        logger.info(f"   Distance: {info.config.params.vectors.distance}")
        logger.info("")


def get_collection_stats(
    collection_name: str,
    host: str = QDRANT_HOST,
    port: int = QDRANT_PORT
):
    """Get detailed statistics for a collection"""
    # Check connection first
    is_connected, error_msg = check_qdrant_connection(host, port)
    if not is_connected:
        logger.error(error_msg)
        return

    client = QdrantClient(host=host, port=port)

    try:
        info = client.get_collection(collection_name)
    except Exception as e:
        logger.error(f"Collection '{collection_name}' not found: {e}")
        return

    logger.info(f"📊 Statistics for collection: {collection_name}")
    logger.info("-" * 80)
    logger.info(f"Total points: {info.points_count}")
    logger.info(f"Vector size: {info.config.params.vectors.size}")
    logger.info(f"Distance metric: {info.config.params.vectors.distance}")
    logger.info(f"Status: {info.status}")
    logger.info("")

    # Sample some points to analyze metadata
    if info.points_count > 0:
        logger.info("Sampling metadata from first 10 points...")
        points = client.scroll(
            collection_name=collection_name,
            limit=10,
            with_payload=True,
            with_vectors=False
        )

        # Analyze domains
        domains = {}
        authors = {}
        books = {}

        for point in points[0]:
            payload = point.payload
            domain = payload.get('domain', 'unknown')
            author = payload.get('author', 'unknown')
            book = payload.get('book_title', 'unknown')

            domains[domain] = domains.get(domain, 0) + 1
            authors[author] = authors.get(author, 0) + 1
            books[book] = books.get(book, 0) + 1

        logger.info(f"\nDomains: {domains}")
        logger.info(f"Authors: {list(authors.keys())}")
        logger.info(f"Books: {list(books.keys())}")


def copy_collection(
    source: str,
    target: str,
    host: str = QDRANT_HOST,
    port: int = QDRANT_PORT,
    filter_domain: Optional[str] = None
):
    """
    Copy collection to a new collection.
    Optionally filter by domain.
    """
    # Check connection first
    is_connected, error_msg = check_qdrant_connection(host, port)
    if not is_connected:
        logger.error(error_msg)
        return

    client = QdrantClient(host=host, port=port)

    # Get source collection info
    try:
        source_info = client.get_collection(source)
    except Exception as e:
        logger.error(f"Source collection '{source}' not found: {e}")
        return

    # Create target collection
    logger.info(f"Creating target collection: {target}")
    client.create_collection(
        collection_name=target,
        vectors_config=VectorParams(
            size=source_info.config.params.vectors.size,
            distance=source_info.config.params.vectors.distance
        )
    )

    # Scroll through source collection
    logger.info(f"Copying data from {source} to {target}...")

    scroll_filter = None
    if filter_domain:
        scroll_filter = Filter(
            must=[
                FieldCondition(
                    key="domain",
                    match=MatchValue(value=filter_domain)
                )
            ]
        )

    offset = None
    batch_count = 0
    total_copied = 0

    while True:
        points, next_offset = client.scroll(
            collection_name=source,
            scroll_filter=scroll_filter,
            limit=100,
            with_payload=True,
            with_vectors=True,
            offset=offset
        )

        if not points:
            break

        # Upload to target
        client.upsert(
            collection_name=target,
            points=points
        )

        batch_count += 1
        total_copied += len(points)
        logger.info(f"Copied batch {batch_count} ({total_copied} points so far)")

        offset = next_offset
        if offset is None:
            break

    logger.info(f"✅ Copied {total_copied} points from {source} to {target}")


def delete_collection_and_artifacts(collection_name: str, host: str, port: int) -> dict:
    """
    Deletes a Qdrant collection and permanently removes its manifest and progress files.
    This function is non-interactive and designed for programmatic use.

    Args:
        collection_name: The name of the collection to delete.
        host: Qdrant host.
        port: Qdrant port.

    Returns:
        A dictionary with the results of the deletion operations.
    """
    results = {'qdrant': False, 'manifest': False, 'csv': False, 'progress': False, 'errors': []}

    # Check connection first
    is_connected, error_msg = check_qdrant_connection(host, port)
    if not is_connected:
        logger.error(error_msg)
        results['errors'].append(f"Connection failed: {error_msg}")
        return results

    client = QdrantClient(host=host, port=port)

    # 1. Delete Qdrant collection
    try:
        collections = [c.name for c in client.get_collections().collections]
        if collection_name in collections:
            client.delete_collection(collection_name=collection_name)
        results['qdrant'] = True
    except Exception as e:
        if "Not found" in str(e) or "doesn't exist" in str(e):
            results['qdrant'] = True  # Treat as success if it's already gone
        else:
            results['errors'].append(f"Qdrant deletion failed: {e}")

    # 2. Permanently delete manifest, progress, and CSV files
    scripts_dir = Path(__file__).parent
    app_root = scripts_dir.parent

    files_to_delete = [
        app_root / 'logs' / f'{collection_name}_manifest.json',
        app_root / 'logs' / f'{collection_name}_manifest.csv',
        scripts_dir / f'batch_ingest_progress_{collection_name}.json'
    ]

    for file_path in files_to_delete:
        try:
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted {file_path.name}")

            if 'manifest.json' in str(file_path):
                results['manifest'] = True
            if 'manifest.csv' in str(file_path):
                results['csv'] = True
            if 'progress' in str(file_path):
                results['progress'] = True
        except Exception as e:
            results['errors'].append(f"Failed to delete {file_path.name}: {e}")

    return results


def delete_collection_preserve_artifacts(collection_name: str, host: str, port: int) -> dict:
    """
    Deletes a Qdrant collection and preserves its manifest and progress files by moving
    them into logs/deleted with a timestamp suffix.
    """
    results = {'qdrant': False, 'manifest': False, 'csv': False, 'progress': False, 'errors': []}

    # Check connection first
    is_connected, error_msg = check_qdrant_connection(host, port)
    if not is_connected:
        logger.error(error_msg)
        results['errors'].append(f"Connection failed: {error_msg}")
        return results

    client = QdrantClient(host=host, port=port)

    # 1. Delete Qdrant collection
    try:
        collections = [c.name for c in client.get_collections().collections]
        if collection_name in collections:
            client.delete_collection(collection_name=collection_name)
        results['qdrant'] = True
    except Exception as e:
        if "Not found" in str(e) or "doesn't exist" in str(e):
            results['qdrant'] = True
        else:
            results['errors'].append(f"Qdrant deletion failed: {e}")

    # 2. Move manifest, progress, and CSV files to deleted folder
    scripts_dir = Path(__file__).parent
    app_root = scripts_dir.parent
    deleted_dir = app_root / 'logs' / 'deleted'
    deleted_dir.mkdir(exist_ok=True)

    files_to_archive = [
        app_root / 'logs' / f'{collection_name}_manifest.json',
        app_root / 'logs' / f'{collection_name}_manifest.csv',
        scripts_dir / f'batch_ingest_progress_{collection_name}.json'
    ]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for file_path in files_to_archive:
        try:
            if file_path.exists():
                archive_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
                archive_path = deleted_dir / archive_name
                file_path.rename(archive_path)
                logger.info(f"Moved {file_path.name} to deleted/{archive_path.name}")

            if 'manifest.json' in str(file_path):
                results['manifest'] = True
            if 'manifest.csv' in str(file_path):
                results['csv'] = True
            if 'progress' in str(file_path):
                results['progress'] = True
        except Exception as e:
            results['errors'].append(f"Failed to archive {file_path.name}: {e}")

    return results


def delete_collection(
    collection_name: str,
    host: str = QDRANT_HOST,
    port: int = QDRANT_PORT,
    confirm: bool = False,
    with_artifacts: bool = False
):
    """Delete a collection (with confirmation)"""
    # Check connection first
    is_connected, error_msg = check_qdrant_connection(host, port)
    if not is_connected:
        logger.error(error_msg)
        return

    if not confirm:
        logger.warning(f"⚠️  This will DELETE collection '{collection_name}'")
        if with_artifacts:
            logger.warning("   ...and its associated manifest and progress files!")
        response = input("Type collection name to confirm: ")
        if response != collection_name:
            logger.info("Deletion cancelled")
            return

    if with_artifacts:
        results = delete_collection_and_artifacts(collection_name, host, port)
        if not results['errors']:
            logger.info(f"✅ Deleted collection '{collection_name}' and permanently removed all artifacts.")
        else:
            logger.error(f"❌ Encountered errors during deletion for '{collection_name}':")
            for error in results['errors']:
                logger.error(f"  - {error}")
    else:
        results = delete_collection_preserve_artifacts(collection_name, host, port)
        if not results['errors']:
            logger.info(f"✅ Deleted collection '{collection_name}' and preserved artifacts in logs/deleted.")
        else:
            logger.error(f"❌ Encountered errors during deletion for '{collection_name}':")
            for error in results['errors']:
                logger.error(f"  - {error}")


def create_alias(
    collection_name: str,
    alias_name: str,
    host: str = QDRANT_HOST,
    port: int = QDRANT_PORT
):
    """Create an alias for a collection"""
    client = QdrantClient(host=host, port=port)

    try:
        client.update_collection_aliases(
            change_aliases_operations=[
                {
                    "create_alias": {
                        "collection_name": collection_name,
                        "alias_name": alias_name
                    }
                }
            ]
        )
        logger.info(f"✅ Created alias '{alias_name}' -> '{collection_name}'")
    except Exception as e:
        logger.error(f"Failed to create alias: {e}")


def delete_points_by_filter(
    collection_name: str,
    domain: Optional[str] = None,
    book_title: Optional[str] = None,
    host: str = QDRANT_HOST,
    port: int = QDRANT_PORT
):
    """Delete points from collection based on filter"""
    # Check connection first
    is_connected, error_msg = check_qdrant_connection(host, port)
    if not is_connected:
        logger.error(error_msg)
        return

    client = QdrantClient(host=host, port=port)

    conditions = []
    if domain:
        conditions.append(
            FieldCondition(key="domain", match=MatchValue(value=domain))
        )
    if book_title:
        conditions.append(
            FieldCondition(key="book_title", match=MatchValue(value=book_title))
        )

    if not conditions:
        logger.error("No filter specified. Use --domain or --book")
        return

    logger.info(f"Deleting points from {collection_name} with filters:")
    if domain:
        logger.info(f"  - domain: {domain}")
    if book_title:
        logger.info(f"  - book_title: {book_title}")

    try:
        client.delete(
            collection_name=collection_name,
            points_selector=Filter(must=conditions)
        )
        logger.info("✅ Points deleted successfully")
    except Exception as e:
        logger.error(f"Failed to delete points: {e}")


# ============================================================================
# SEARCH / QUERY
# ============================================================================

def search_collection(
    collection_name: str,
    query: str,
    limit: int = 10,
    domain_filter: Optional[str] = None,
    model_id: Optional[str] = None,
    host: str = QDRANT_HOST,
    port: int = QDRANT_PORT
):
    """Search collection using semantic similarity.

    Args:
        collection_name: Qdrant collection to search
        query: Search query text
        limit: Maximum results to return
        domain_filter: Optional domain filter
        model_id: Embedding model ID (default: uses DEFAULT_EMBEDDING_MODEL)
        host: Qdrant host
        port: Qdrant port
    """
    # Check connection first
    is_connected, error_msg = check_qdrant_connection(host, port)
    if not is_connected:
        logger.error(error_msg)
        return

    client = QdrantClient(host=host, port=port)

    # Generate query embedding using EmbeddingGenerator (lazy import to avoid circular dependency)
    from ingest_books import EmbeddingGenerator
    logger.info(f"Searching for: '{query}'")
    embedder = EmbeddingGenerator()
    model = embedder.get_model(model_id)
    query_vector = model.encode(query).tolist()

    # Build filter
    query_filter = None
    if domain_filter:
        query_filter = Filter(
            must=[
                FieldCondition(key="domain", match=MatchValue(value=domain_filter))
            ]
        )

    # Search (using newer Qdrant API)
    results = client.query_points(
        collection_name=collection_name,
        query=query_vector,
        limit=limit,
        query_filter=query_filter
    ).points

    logger.info(f"\n🔍 Found {len(results)} results:")
    logger.info("=" * 80)

    for idx, result in enumerate(results, 1):
        payload = result.payload
        logger.info(f"\n{idx}. Score: {result.score:.4f}")
        logger.info(f"   Book: {payload.get('book_title', 'N/A')}")
        logger.info(f"   Author: {payload.get('author', 'N/A')}")
        logger.info(f"   Domain: {payload.get('domain', 'N/A')}")
        logger.info(f"   Section: {payload.get('section_name', 'N/A')}")
        logger.info(f"   Text preview: {payload.get('text', '')[:200]}...")
        logger.info("")


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Alexandria Qdrant Utilities'
    )
    parser.add_argument(
        'command',
        choices=['list', 'stats', 'copy', 'delete', 'alias', 'search', 'delete-points'],
        help='Command to execute'
    )
    parser.add_argument(
        'args',
        nargs='*',
        help='Command arguments'
    )
    parser.add_argument(
        '--host',
        default=QDRANT_HOST,
        help=f'Qdrant host (default: {QDRANT_HOST})'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=QDRANT_PORT,
        help=f'Qdrant port (default: {QDRANT_PORT})'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=10,
        help='Search result limit'
    )
    parser.add_argument(
        '--domain',
        help='(Deprecated) Filter by domain - no longer used'
    )
    parser.add_argument(
        '--book',
        help='Filter by book title'
    )
    parser.add_argument(
        '--with-artifacts',
        action='store_true',
        help='Also delete manifest and progress files (used with `delete` command)'
    )
    parser.add_argument(
        '--confirm',
        action='store_true',
        help='Skip confirmation prompts'
    )

    args = parser.parse_args()

    # Route commands
    if args.command == 'list':
        list_collections(args.host, args.port)

    elif args.command == 'stats':
        if len(args.args) < 1:
            logger.error("Usage: qdrant_utils.py stats <collection_name>")
            return
        get_collection_stats(args.args[0], args.host, args.port)

    elif args.command == 'copy':
        if len(args.args) < 2:
            logger.error("Usage: qdrant_utils.py copy <source> <target>")
            return
        copy_collection(args.args[0], args.args[1], args.host, args.port, args.domain)

    elif args.command == 'delete':
        if len(args.args) < 1:
            logger.error("Usage: qdrant_utils.py delete <collection_name>")
            return
        delete_collection(args.args[0], args.host, args.port, args.confirm, args.with_artifacts)

    elif args.command == 'alias':
        if len(args.args) < 2:
            logger.error("Usage: qdrant_utils.py alias <collection_name> <alias_name>")
            return
        create_alias(args.args[0], args.args[1], args.host, args.port)

    elif args.command == 'search':
        if len(args.args) < 2:
            logger.error("Usage: qdrant_utils.py search <collection_name> <query> [--limit 10]")
            return
        search_collection(args.args[0], args.args[1], args.limit, args.domain, args.host, args.port)

    elif args.command == 'delete-points':
        if len(args.args) < 1:
            logger.error("Usage: qdrant_utils.py delete-points <collection_name> --book <title>")
            return
        delete_points_by_filter(args.args[0], args.domain, args.book, args.host, args.port)


if __name__ == '__main__':
    main()
