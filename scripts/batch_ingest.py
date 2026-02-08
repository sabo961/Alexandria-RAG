#!/usr/bin/env python3
"""
Alexandria Batch Ingestion
===========================

Scan directory (Calibre library or custom folder) and ingest all books.

Usage:
    # Ingest from Calibre library (uses CALIBRE_LIBRARY_PATH from config)
    python batch_ingest.py

    # Ingest from custom directory
    python batch_ingest.py --directory "C:/My Books"

    # Dry run to see what would be ingested
    python batch_ingest.py --dry-run
"""

import argparse
import logging
from pathlib import Path
from typing import List
import time

from config import (
    CALIBRE_LIBRARY_PATH,
    QDRANT_HOST,
    QDRANT_PORT,
    DEFAULT_EMBEDDING_MODEL,
)
from ingest_books import ingest_book

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Supported book formats
BOOK_FORMATS = {'.epub', '.pdf', '.txt', '.md', '.html', '.htm'}


def find_books(directory: str) -> List[Path]:
    """
    Recursively find all supported book files in directory.

    Args:
        directory: Root directory to scan

    Returns:
        List of Path objects for found books
    """
    directory_path = Path(directory)

    if not directory_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    books = []
    for file_path in directory_path.rglob('*'):
        if file_path.is_file() and file_path.suffix.lower() in BOOK_FORMATS:
            books.append(file_path)

    return sorted(books)


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


def batch_ingest(
    directory: str,
    collection_name: str = 'alexandria',
    qdrant_host: str = QDRANT_HOST,
    qdrant_port: int = QDRANT_PORT,
    model_id: str = None,
    dry_run: bool = False
):
    """
    Batch ingest all books from directory.

    Args:
        directory: Directory to scan for books
        collection_name: Qdrant collection name
        qdrant_host: Qdrant server host
        qdrant_port: Qdrant server port
        model_id: Embedding model identifier
        dry_run: If True, only show what would be done
    """
    model_id = model_id or DEFAULT_EMBEDDING_MODEL

    print(f"\n{'='*70}")
    print(f"Alexandria Batch Ingestion")
    print(f"{'='*70}")
    print(f"Directory:   {directory}")
    print(f"Collection:  {collection_name}")
    print(f"Model:       {model_id}")
    print(f"Qdrant:      {qdrant_host}:{qdrant_port}")
    if dry_run:
        print(f"Mode:        DRY-RUN (no changes)")
    print(f"{'='*70}\n")

    # Find all books
    print("Scanning for books...")
    books = find_books(directory)

    if not books:
        print(f"[WARN] No books found in {directory}")
        return

    total = len(books)
    print(f"Found {total} book(s) to ingest\n")

    if dry_run:
        print("DRY-RUN - would ingest:")
        for i, book_path in enumerate(books, 1):
            print(f"  [{i}/{total}] {book_path.name}")
        print(f"\nTotal: {total} books")
        return

    # Ingest each book
    success_count = 0
    failed_count = 0
    failed_books = []
    start_time = time.time()
    book_times = []

    for i, book_path in enumerate(books, 1):
        book_start = time.time()

        # Calculate ETA
        if book_times:
            avg_time = sum(book_times) / len(book_times)
            remaining = (total - i + 1) * avg_time
            eta_str = f" (ETA: {format_duration(remaining)})"
        else:
            eta_str = ""

        print(f"\n[{i}/{total}] Processing: {book_path.name}{eta_str}")

        try:
            result = ingest_book(
                filepath=str(book_path),
                collection_name=collection_name,
                qdrant_host=qdrant_host,
                qdrant_port=qdrant_port,
                model_id=model_id,
                hierarchical=True,
                force_reingest=False  # Don't delete existing - we're building new collection
            )

            if result.get('success'):
                book_duration = time.time() - book_start
                book_times.append(book_duration)
                chunks = result.get('chunks', 0)
                print(f"  [OK] {result['title']} - {chunks} chunks ({format_duration(book_duration)})")
                success_count += 1
            else:
                error = result.get('error', 'Unknown error')
                print(f"  [FAIL] {error}")
                failed_count += 1
                failed_books.append({
                    'path': str(book_path),
                    'error': error
                })

        except Exception as e:
            print(f"  [FAIL] Exception: {str(e)}")
            failed_count += 1
            failed_books.append({
                'path': str(book_path),
                'error': str(e)
            })

    # Print summary
    total_duration = time.time() - start_time

    print(f"\n{'='*70}")
    print(f"BATCH INGESTION SUMMARY")
    print(f"{'='*70}")
    print(f"Total books:   {total}")
    print(f"Succeeded:     {success_count}")
    print(f"Failed:        {failed_count}")
    print(f"Duration:      {format_duration(total_duration)}")

    if failed_books:
        print(f"\nFAILED BOOKS:")
        print(f"-" * 70)
        for failure in failed_books:
            print(f"  - {Path(failure['path']).name}")
            print(f"    Error: {failure['error']}")

    print(f"{'='*70}\n")


def main():
    parser = argparse.ArgumentParser(description='Batch ingest books from directory')
    parser.add_argument(
        '--directory', '-d',
        default=CALIBRE_LIBRARY_PATH,
        help=f'Directory to scan (default: {CALIBRE_LIBRARY_PATH})'
    )
    parser.add_argument(
        '--collection', '-c',
        default='alexandria',
        help='Qdrant collection name (default: alexandria)'
    )
    parser.add_argument(
        '--model', '-m',
        default=None,
        help=f'Embedding model (default: {DEFAULT_EMBEDDING_MODEL})'
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
        '--dry-run', '-n',
        action='store_true',
        help='Show what would be done without making changes'
    )

    args = parser.parse_args()

    try:
        batch_ingest(
            directory=args.directory,
            collection_name=args.collection,
            qdrant_host=args.host,
            qdrant_port=args.port,
            model_id=args.model,
            dry_run=args.dry_run
        )
    except Exception as e:
        logger.error(f"Batch ingestion failed: {e}")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
