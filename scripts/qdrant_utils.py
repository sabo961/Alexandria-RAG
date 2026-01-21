"""
Alexandria Qdrant Utilities

Utility functions for managing Qdrant collections during experimentation.

Usage:
    python qdrant_utils.py list
    python qdrant_utils.py stats alexandria
    python qdrant_utils.py copy alexandria_v1 alexandria_v2
    python qdrant_utils.py delete alexandria_test
    python qdrant_utils.py alias alexandria alexandria_prod
    python qdrant_utils.py search alexandria "database normalization" --limit 5
"""

import argparse
import logging
from typing import List, Dict, Optional
from datetime import datetime

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# COLLECTION MANAGEMENT
# ============================================================================

def list_collections(host: str = 'localhost', port: int = 6333):
    """List all Qdrant collections with basic stats"""
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
    host: str = 'localhost',
    port: int = 6333
):
    """Get detailed statistics for a collection"""
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
    host: str = 'localhost',
    port: int = 6333,
    filter_domain: Optional[str] = None
):
    """
    Copy collection to a new collection.
    Optionally filter by domain.
    """
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


def delete_collection(
    collection_name: str,
    host: str = 'localhost',
    port: int = 6333,
    confirm: bool = False
):
    """Delete a collection (with confirmation)"""
    client = QdrantClient(host=host, port=port)

    if not confirm:
        logger.warning(f"⚠️  This will DELETE collection '{collection_name}'")
        response = input("Type collection name to confirm: ")
        if response != collection_name:
            logger.info("Deletion cancelled")
            return

    try:
        client.delete_collection(collection_name)
        logger.info(f"✅ Deleted collection: {collection_name}")
    except Exception as e:
        logger.error(f"Failed to delete collection: {e}")


def create_alias(
    collection_name: str,
    alias_name: str,
    host: str = 'localhost',
    port: int = 6333
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
    host: str = 'localhost',
    port: int = 6333
):
    """Delete points from collection based on filter"""
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
    host: str = 'localhost',
    port: int = 6333
):
    """Search collection using semantic similarity"""
    client = QdrantClient(host=host, port=port)

    # Generate query embedding
    logger.info(f"Searching for: '{query}'")
    model = SentenceTransformer('all-MiniLM-L6-v2')
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
        default='192.168.0.151',
        help='Qdrant host'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=6333,
        help='Qdrant port'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=10,
        help='Search result limit'
    )
    parser.add_argument(
        '--domain',
        help='Filter by domain'
    )
    parser.add_argument(
        '--book',
        help='Filter by book title'
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
            logger.error("Usage: qdrant_utils.py copy <source> <target> [--domain <domain>]")
            return
        copy_collection(args.args[0], args.args[1], args.host, args.port, args.domain)

    elif args.command == 'delete':
        if len(args.args) < 1:
            logger.error("Usage: qdrant_utils.py delete <collection_name>")
            return
        delete_collection(args.args[0], args.host, args.port, args.confirm)

    elif args.command == 'alias':
        if len(args.args) < 2:
            logger.error("Usage: qdrant_utils.py alias <collection_name> <alias_name>")
            return
        create_alias(args.args[0], args.args[1], args.host, args.port)

    elif args.command == 'search':
        if len(args.args) < 2:
            logger.error("Usage: qdrant_utils.py search <collection_name> <query> [--limit 10] [--domain <domain>]")
            return
        search_collection(args.args[0], args.args[1], args.limit, args.domain, args.host, args.port)

    elif args.command == 'delete-points':
        if len(args.args) < 1:
            logger.error("Usage: qdrant_utils.py delete-points <collection_name> --domain <domain> [--book <title>]")
            return
        delete_points_by_filter(args.args[0], args.domain, args.book, args.host, args.port)


if __name__ == '__main__':
    main()
