#!/usr/bin/env python3
"""
Alexandria Public Domain Pipeline
==================================

Complete workflow: Search → Download → Upload to Calibre → Ingest to Qdrant

This is THE RIGHT WAY to add public domain books to Alexandria:
1. Find book on Gutenberg/Archive
2. Download book file
3. Upload to Calibre-Web (source of truth)
4. Ingest to Qdrant (for RAG search)

Usage:
    # Interactive mode - search and select
    python public_domain_pipeline.py --search "Nietzsche Zarathustra" --language de

    # Automated - download and process specific book
    python public_domain_pipeline.py --gutenberg-id 7205 --auto

    # Batch processing from TIER 0 classics list
    python public_domain_pipeline.py --batch tier0_classics.txt --auto

Examples:
    # Search Gutenberg for Kant in German
    python public_domain_pipeline.py --search "Kant Kritik" --language de

    # Download, upload to Calibre, and ingest
    python public_domain_pipeline.py --gutenberg-id 7205 --calibre-user admin --calibre-pass xxx --auto
"""

import argparse
import sys
from pathlib import Path
from typing import Optional, Dict, List

# Import our connectors
try:
    from gutenberg_connector import search_books, download_book, print_book_info
    from calibre_web_connector import CalibreWebClient
    from ingest_books import ingest_book
    from config import QDRANT_HOST, QDRANT_PORT, DEFAULT_EMBEDDING_MODEL
except ImportError as e:
    print(f"[ERROR] Failed to import connectors: {e}")
    print("Make sure you're running from the scripts directory.")
    sys.exit(1)

DEFAULT_CALIBRE_WEB_URL = "https://alexandria.jedai.space"


def full_pipeline(
    gutenberg_id: int,
    download_format: str = 'epub',
    calibre_web_url: str = DEFAULT_CALIBRE_WEB_URL,
    calibre_user: Optional[str] = None,
    calibre_password: Optional[str] = None,
    skip_calibre: bool = False,
    skip_qdrant: bool = False
) -> bool:
    """
    Execute full pipeline for a single book.

    Args:
        gutenberg_id: Project Gutenberg book ID
        download_format: Format to download (epub, pdf, txt)
        calibre_web_url: Calibre-Web instance URL
        calibre_user: Calibre-Web username
        calibre_password: Calibre-Web password
        skip_calibre: Skip upload to Calibre-Web
        skip_qdrant: Skip ingestion to Qdrant

    Returns:
        True if successful, False otherwise
    """
    print(f"\n{'='*70}")
    print(f"ALEXANDRIA PUBLIC DOMAIN PIPELINE")
    print(f"{'='*70}")
    print(f"Book ID: {gutenberg_id}")
    print(f"Format: {download_format}")
    print(f"Calibre-Web: {calibre_web_url}")
    print(f"{'='*70}\n")

    # Step 1: Download from Gutenberg
    print(f"[STEP 1/3] Downloading from Project Gutenberg...")
    file_path = download_book(gutenberg_id, download_format, output_dir='./public_domain_downloads')

    if not file_path:
        print(f"[ERROR] Failed to download book {gutenberg_id}")
        return False

    # Step 2: Upload to Calibre-Web (optional)
    if not skip_calibre:
        if not calibre_user or not calibre_password:
            print(f"\n[STEP 2/3] SKIPPED - No Calibre-Web credentials provided")
            print(f"           Use --calibre-user and --calibre-pass to enable upload")
        else:
            print(f"\n[STEP 2/3] Uploading to Calibre-Web...")
            client = CalibreWebClient(calibre_web_url, calibre_user, calibre_password)

            success = client.upload_book(file_path)

            if not success:
                print(f"[WARN] Upload to Calibre-Web failed, but continuing with Qdrant ingestion")
    else:
        print(f"\n[STEP 2/3] SKIPPED - Upload to Calibre-Web disabled (--skip-calibre)")

    # Step 3: Ingest to Qdrant
    if not skip_qdrant:
        print(f"\n[STEP 3/3] Ingesting to Qdrant...")

        result = ingest_book(
            filepath=file_path,
            collection_name='alexandria',
            qdrant_host=QDRANT_HOST,
            qdrant_port=QDRANT_PORT,
            model_id=DEFAULT_EMBEDDING_MODEL,
            hierarchical=True,
            force_reingest=False
        )

        if result.get('success'):
            chunks = result.get('chunks', 0)
            print(f"[OK] Ingestion complete: {result['title']} ({chunks} chunks)")
        else:
            error = result.get('error', 'Unknown error')
            print(f"[ERROR] Ingestion failed: {error}")
            return False
    else:
        print(f"\n[STEP 3/3] SKIPPED - Qdrant ingestion disabled (--skip-qdrant)")

    # Success!
    print(f"\n{'='*70}")
    print(f"[SUCCESS] Pipeline complete!")
    print(f"{'='*70}")
    print(f"Downloaded: {file_path}")
    if not skip_calibre and calibre_user:
        print(f"Uploaded:   {calibre_web_url}")
    if not skip_qdrant:
        print(f"Ingested:   alexandria collection on {QDRANT_HOST}")
    print(f"{'='*70}\n")

    return True


def interactive_search_mode(
    query: str,
    language: Optional[str] = None,
    calibre_user: Optional[str] = None,
    calibre_password: Optional[str] = None
):
    """
    Interactive mode: search, select, and process.
    """
    print(f"\n{'='*70}")
    print(f"ALEXANDRIA PUBLIC DOMAIN SEARCH")
    print(f"{'='*70}")
    print(f"Query: {query}")
    if language:
        print(f"Language: {language}")
    print(f"{'='*70}\n")

    # Search Gutenberg
    books = search_books(query=query, language=language, limit=10)

    if not books:
        print("[WARN] No books found")
        return

    print(f"\n{'='*70}")
    print(f"SEARCH RESULTS")
    print(f"{'='*70}")

    for i, book in enumerate(books, 1):
        print_book_info(book, index=i)

    # Ask user to select
    print(f"\n{'='*70}")
    choice = input("Select book number to process (or 'q' to quit): ")

    if choice.lower() == 'q':
        print("Cancelled.")
        return

    try:
        index = int(choice) - 1
        if 0 <= index < len(books):
            selected_book = books[index]
            book_id = selected_book.get('id')

            print(f"\n[SELECTED] {selected_book.get('title')}")
            print(f"           by {selected_book.get('authors', [{}])[0].get('name', 'Unknown')}")

            # Run pipeline
            full_pipeline(
                gutenberg_id=book_id,
                download_format='epub',
                calibre_user=calibre_user,
                calibre_password=calibre_password
            )
        else:
            print("[ERROR] Invalid selection")
    except ValueError:
        print("[ERROR] Invalid input")


def main():
    parser = argparse.ArgumentParser(
        description='Alexandria Public Domain Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive search
  python public_domain_pipeline.py --search "Kant Kritik" --language de

  # Automated download + upload + ingest
  python public_domain_pipeline.py --gutenberg-id 7205 --auto --calibre-user admin --calibre-pass xxx

  # Download only (skip Calibre and Qdrant)
  python public_domain_pipeline.py --gutenberg-id 7205 --skip-calibre --skip-qdrant
        """
    )

    # Search mode
    parser.add_argument('--search', '-s', type=str,
                       help='Search query (author, title, etc.)')
    parser.add_argument('--language', '-l', type=str,
                       help='Language code (en, de, ru, el, la, etc.)')

    # Direct download mode
    parser.add_argument('--gutenberg-id', '-g', type=int,
                       help='Project Gutenberg book ID to download')
    parser.add_argument('--format', '-f', type=str, default='epub',
                       choices=['epub', 'pdf', 'txt', 'html'],
                       help='Download format (default: epub)')

    # Calibre-Web settings
    parser.add_argument('--calibre-url', type=str, default=DEFAULT_CALIBRE_WEB_URL,
                       help=f'Calibre-Web URL (default: {DEFAULT_CALIBRE_WEB_URL})')
    parser.add_argument('--calibre-user', type=str,
                       help='Calibre-Web username')
    parser.add_argument('--calibre-pass', type=str,
                       help='Calibre-Web password')

    # Pipeline control
    parser.add_argument('--auto', action='store_true',
                       help='Auto-run full pipeline without prompts')
    parser.add_argument('--skip-calibre', action='store_true',
                       help='Skip upload to Calibre-Web')
    parser.add_argument('--skip-qdrant', action='store_true',
                       help='Skip ingestion to Qdrant')

    args = parser.parse_args()

    # Search mode
    if args.search:
        interactive_search_mode(
            query=args.search,
            language=args.language,
            calibre_user=args.calibre_user,
            calibre_password=args.calibre_pass
        )
        return

    # Direct download mode
    if args.gutenberg_id:
        if not args.auto:
            confirm = input(f"Download and process book {args.gutenberg_id}? (yes/no): ")
            if confirm.lower() != 'yes':
                print("Cancelled.")
                return

        success = full_pipeline(
            gutenberg_id=args.gutenberg_id,
            download_format=args.format,
            calibre_web_url=args.calibre_url,
            calibre_user=args.calibre_user,
            calibre_password=args.calibre_pass,
            skip_calibre=args.skip_calibre,
            skip_qdrant=args.skip_qdrant
        )

        sys.exit(0 if success else 1)

    # No action specified
    parser.print_help()


if __name__ == '__main__':
    main()
