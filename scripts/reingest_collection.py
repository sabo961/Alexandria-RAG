#!/usr/bin/env python3
"""
Alexandria Collection Re-ingestion Tool

Re-ingest books in a collection with a specified embedding model.
Useful for upgrading collections to better models or creating A/B test collections.

Usage:
    # Dry-run to preview what would be re-ingested
    python reingest_collection.py --collection alexandria --model bge-large --dry-run

    # Re-ingest all books with bge-large model
    python reingest_collection.py --collection alexandria --model bge-large

    # Re-ingest with custom Qdrant host
    python reingest_collection.py --collection alexandria --model bge-large --host 192.168.0.151
"""

import argparse
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional

from qdrant_client import QdrantClient

from collection_manifest import CollectionManifest
from config import (
    QDRANT_HOST,
    QDRANT_PORT,
    EMBEDDING_MODELS,
    DEFAULT_EMBEDDING_MODEL,
)
from ingest_books import ingest_book
from qdrant_utils import check_qdrant_connection

# Setup logging
log_level_str = 'INFO'
logging.basicConfig(
    level=getattr(logging, log_level_str, logging.INFO),
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Type alias for progress callback
ProgressCallback = Callable[[int, int, str, str], None]


def default_progress_callback(current: int, total: int, book_title: str, status: str) -> None:
    """
    Default progress callback that prints to stdout.

    Args:
        current: Current book number (1-indexed)
        total: Total number of books
        book_title: Title of the current book
        status: Status message (e.g., "processing", "completed", "failed")
    """
    percent = (current / total) * 100 if total > 0 else 0
    print(f"[{current}/{total}] ({percent:.1f}%) {book_title}: {status}")


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def get_books_from_manifest(
    collection_name: str,
    qdrant_host: str = QDRANT_HOST,
    qdrant_port: int = QDRANT_PORT
) -> List[Dict]:
    """
    Get list of books from collection manifest.

    Args:
        collection_name: Name of the collection
        qdrant_host: Qdrant host for manifest verification
        qdrant_port: Qdrant port for manifest verification

    Returns:
        List of book dictionaries with 'title', 'author', 'file_path', 'chunks_count'
    """
    manifest = CollectionManifest(collection_name=collection_name)

    # Verify collection exists in Qdrant
    manifest.verify_collection_exists(collection_name, qdrant_host, qdrant_port)

    if collection_name not in manifest.manifest.get('collections', {}):
        logger.warning(f"Collection '{collection_name}' not found in manifest")
        return []

    collection_data = manifest.manifest['collections'][collection_name]
    books = collection_data.get('books', [])

    return [
        {
            'title': book.get('book_title', 'Unknown'),
            'author': book.get('author', 'Unknown'),
            'file_path': book.get('file_path', ''),
            'chunks_count': book.get('chunks_count', 0),
            'language': book.get('language', 'unknown'),
        }
        for book in books
    ]


def get_books_from_qdrant(
    collection_name: str,
    qdrant_host: str = QDRANT_HOST,
    qdrant_port: int = QDRANT_PORT
) -> List[Dict]:
    """
    Get unique books from Qdrant collection by scanning payloads.

    Falls back to this method when manifest is unavailable.
    Note: This method cannot provide file_path, so re-ingestion may not work.

    Args:
        collection_name: Name of the collection
        qdrant_host: Qdrant host
        qdrant_port: Qdrant port

    Returns:
        List of book dictionaries with 'title', 'author' (no file_path)
    """
    is_connected, error_msg = check_qdrant_connection(qdrant_host, qdrant_port)
    if not is_connected:
        logger.error(error_msg)
        return []

    client = QdrantClient(host=qdrant_host, port=qdrant_port)

    # Check if collection exists
    collections = [c.name for c in client.get_collections().collections]
    if collection_name not in collections:
        logger.error(f"Collection '{collection_name}' not found in Qdrant")
        return []

    # Sample points to get unique books
    books_dict = {}
    offset = None
    batch_count = 0
    max_batches = 100  # Safety limit

    while batch_count < max_batches:
        points, next_offset = client.scroll(
            collection_name=collection_name,
            limit=1000,
            with_payload=True,
            with_vectors=False,
            offset=offset
        )

        if not points:
            break

        for point in points:
            payload = point.payload
            book_title = payload.get('book_title', 'Unknown')
            if book_title not in books_dict:
                books_dict[book_title] = {
                    'title': book_title,
                    'author': payload.get('author', 'Unknown'),
                    'file_path': '',  # Not available from Qdrant
                    'chunks_count': 0,
                    'language': payload.get('language', 'unknown'),
                }
            books_dict[book_title]['chunks_count'] += 1

        offset = next_offset
        batch_count += 1
        if offset is None:
            break

    return list(books_dict.values())


def reingest_collection(
    collection_name: str,
    model_id: str,
    qdrant_host: str = QDRANT_HOST,
    qdrant_port: int = QDRANT_PORT,
    dry_run: bool = False,
    progress_callback: Optional[ProgressCallback] = None
) -> Dict:
    """
    Re-ingest all books in a collection with specified embedding model.

    Args:
        collection_name: Name of the collection to re-ingest
        model_id: Embedding model identifier
        qdrant_host: Qdrant server host
        qdrant_port: Qdrant server port
        dry_run: If True, only show what would be done
        progress_callback: Optional callback for progress updates

    Returns:
        Summary dict with success count, failures, etc.
    """
    if progress_callback is None:
        progress_callback = default_progress_callback

    # Validate model_id
    if model_id not in EMBEDDING_MODELS:
        return {
            'success': False,
            'error': f"Unknown model_id: {model_id}. Available: {list(EMBEDDING_MODELS.keys())}"
        }

    # Get books from manifest
    logger.info(f"Loading books from manifest for collection '{collection_name}'...")
    books = get_books_from_manifest(collection_name, qdrant_host, qdrant_port)

    if not books:
        # Fall back to Qdrant scan
        logger.info("Manifest empty or unavailable, scanning Qdrant collection...")
        books = get_books_from_qdrant(collection_name, qdrant_host, qdrant_port)

    if not books:
        return {
            'success': False,
            'error': f"No books found in collection '{collection_name}'"
        }

    total = len(books)
    logger.info(f"Found {total} books to re-ingest")

    # Track results
    success_count = 0
    failures = []
    skipped = []
    start_time = time.time()
    book_times = []

    for i, book in enumerate(books, 1):
        book_title = book['title']
        file_path = book.get('file_path', '')
        book_start = time.time()

        # Calculate ETA
        if book_times:
            avg_time = sum(book_times) / len(book_times)
            remaining = (total - i + 1) * avg_time
            eta_str = f" (ETA: {format_duration(remaining)})"
        else:
            eta_str = ""

        if dry_run:
            progress_callback(i, total, book_title, f"would re-ingest with {model_id}{eta_str}")
            success_count += 1
            continue

        if not file_path:
            progress_callback(i, total, book_title, "SKIPPED - no file path in manifest")
            skipped.append({
                'title': book_title,
                'reason': 'No file path available'
            })
            continue

        # Check if file exists
        if not Path(file_path).exists():
            progress_callback(i, total, book_title, f"SKIPPED - file not found: {file_path}")
            skipped.append({
                'title': book_title,
                'reason': f'File not found: {file_path}'
            })
            continue

        progress_callback(i, total, book_title, f"processing with {model_id}...{eta_str}")

        try:
            result = ingest_book(
                filepath=file_path,
                collection_name=collection_name,
                qdrant_host=qdrant_host,
                qdrant_port=qdrant_port,
                force_reingest=True,
                model_id=model_id
            )

            if result.get('success'):
                book_duration = time.time() - book_start
                book_times.append(book_duration)
                progress_callback(
                    i, total, book_title,
                    f"completed ({result.get('chunks', 0)} chunks, {format_duration(book_duration)})"
                )
                success_count += 1
            else:
                error = result.get('error', 'Unknown error')
                progress_callback(i, total, book_title, f"FAILED: {error}")
                failures.append({
                    'title': book_title,
                    'file_path': file_path,
                    'error': error
                })

        except Exception as e:
            progress_callback(i, total, book_title, f"FAILED: {str(e)}")
            failures.append({
                'title': book_title,
                'file_path': file_path,
                'error': str(e)
            })

    # Calculate totals
    total_duration = time.time() - start_time

    return {
        'success': True,
        'collection': collection_name,
        'model_id': model_id,
        'dry_run': dry_run,
        'total': total,
        'succeeded': success_count,
        'failed': len(failures),
        'skipped': len(skipped),
        'failures': failures,
        'skipped_books': skipped,
        'duration_seconds': total_duration,
        'duration_formatted': format_duration(total_duration)
    }


def print_summary(result: Dict) -> None:
    """Print summary report from reingest_collection result."""
    print("\n" + "=" * 70)
    print("RE-INGESTION SUMMARY")
    print("=" * 70)
    print(f"Collection:    {result.get('collection', 'N/A')}")
    print(f"Model:         {result.get('model_id', 'N/A')}")
    print(f"Mode:          {'DRY-RUN (no changes made)' if result.get('dry_run') else 'LIVE'}")
    print(f"Duration:      {result.get('duration_formatted', 'N/A')}")
    print("")
    print(f"Total books:   {result.get('total', 0)}")
    print(f"Succeeded:     {result.get('succeeded', 0)}")
    print(f"Failed:        {result.get('failed', 0)}")
    print(f"Skipped:       {result.get('skipped', 0)}")

    failures = result.get('failures', [])
    if failures:
        print("\nFAILURES:")
        print("-" * 70)
        for failure in failures:
            print(f"  - {failure['title']}")
            print(f"    Error: {failure['error']}")
            if failure.get('file_path'):
                print(f"    Path: {failure['file_path']}")

    skipped = result.get('skipped_books', [])
    if skipped:
        print("\nSKIPPED:")
        print("-" * 70)
        for skip in skipped:
            print(f"  - {skip['title']}: {skip['reason']}")

    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description='Re-ingest books in a collection with specified embedding model'
    )
    parser.add_argument(
        '--collection', '-c',
        required=True,
        help='Qdrant collection name'
    )
    parser.add_argument(
        '--model', '-m',
        required=True,
        choices=list(EMBEDDING_MODELS.keys()),
        help=f'Embedding model to use. Available: {list(EMBEDDING_MODELS.keys())}'
    )
    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help='Show what would be done without making changes'
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

    args = parser.parse_args()

    print(f"\nAlexandria Collection Re-ingestion Tool")
    print(f"Collection: {args.collection}")
    print(f"Model: {args.model} ({EMBEDDING_MODELS[args.model]['name']})")
    print(f"Qdrant: {args.host}:{args.port}")
    if args.dry_run:
        print("Mode: DRY-RUN (no changes will be made)")
    print("")

    result = reingest_collection(
        collection_name=args.collection,
        model_id=args.model,
        qdrant_host=args.host,
        qdrant_port=args.port,
        dry_run=args.dry_run
    )

    if not result.get('success'):
        print(f"\n[ERROR] {result.get('error', 'Unknown error')}")
        return 1

    print_summary(result)

    # Exit with error code if there were failures
    if result.get('failed', 0) > 0:
        return 1
    return 0


if __name__ == '__main__':
    exit(main())
