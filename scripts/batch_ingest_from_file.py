#!/usr/bin/env python3
"""
Batch ingest books from a file list.

Usage:
    python batch_ingest_from_file.py --file sample_books.txt
"""

import argparse
import time
from pathlib import Path

from config import QDRANT_HOST, QDRANT_PORT, DEFAULT_EMBEDDING_MODEL
from ingest_books import ingest_book


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


def batch_ingest_from_file(
    file_path: str,
    collection_name: str = 'alexandria',
    qdrant_host: str = QDRANT_HOST,
    qdrant_port: int = QDRANT_PORT,
    model_id: str = None
):
    """
    Batch ingest books from file list.

    File format (UTF-8):
        /path/to/book1.epub
        # Comment lines ignored
        /path/to/book2.pdf
    """
    model_id = model_id or DEFAULT_EMBEDDING_MODEL

    # Read file list
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Extract book paths (skip comments and empty lines)
    book_paths = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            if Path(line).exists():
                book_paths.append(line)
            else:
                print(f"[WARN] File not found, skipping: {line}")

    if not book_paths:
        print(f"[ERROR] No valid book paths found in {file_path}")
        return

    total = len(book_paths)

    print(f"\n{'='*70}")
    print(f"Alexandria Batch Ingestion from File")
    print(f"{'='*70}")
    print(f"File:        {file_path}")
    print(f"Books:       {total}")
    print(f"Collection:  {collection_name}")
    print(f"Model:       {model_id}")
    print(f"Qdrant:      {qdrant_host}:{qdrant_port}")
    print(f"{'='*70}\n")

    # Ingest each book
    success_count = 0
    failed_count = 0
    failed_books = []
    start_time = time.time()
    book_times = []

    for i, book_path in enumerate(book_paths, 1):
        book_start = time.time()
        book_name = Path(book_path).name

        # Calculate ETA
        if book_times:
            avg_time = sum(book_times) / len(book_times)
            remaining = (total - i + 1) * avg_time
            eta_str = f" (ETA: {format_duration(remaining)})"
        else:
            eta_str = ""

        print(f"\n[{i}/{total}] Processing: {book_name}{eta_str}")

        try:
            result = ingest_book(
                filepath=book_path,
                collection_name=collection_name,
                qdrant_host=qdrant_host,
                qdrant_port=qdrant_port,
                model_id=model_id,
                hierarchical=True,
                force_reingest=False
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
                    'path': book_path,
                    'error': error
                })

        except Exception as e:
            print(f"  [FAIL] Exception: {str(e)}")
            failed_count += 1
            failed_books.append({
                'path': book_path,
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
    parser = argparse.ArgumentParser(description='Batch ingest from file list')
    parser.add_argument(
        '--file', '-f',
        required=True,
        help='File containing book paths (one per line)'
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

    args = parser.parse_args()

    batch_ingest_from_file(
        file_path=args.file,
        collection_name=args.collection,
        qdrant_host=args.host,
        qdrant_port=args.port,
        model_id=args.model
    )


if __name__ == '__main__':
    main()
