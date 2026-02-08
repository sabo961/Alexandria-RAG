#!/usr/bin/env python3
"""
Alexandria Public Domain Pipeline
==================================

Complete workflow: Search → Download → Quality Check → Calibre → Qdrant

Supports both Project Gutenberg and Internet Archive as sources.
Supports both CWA ingest folder and Calibre-Web API for library management.

Usage:
    # Search Internet Archive for Dostoevsky in Russian
    python public_domain_pipeline.py --source archive --search "Dostoevsky" --language rus

    # Search Gutenberg for Kant in German
    python public_domain_pipeline.py --search "Kant Kritik" --language de

    # Download from Archive + copy to CWA (no Qdrant ingest)
    python public_domain_pipeline.py --archive-id "crimeandpunishme00dostuoft" --format epub --cwa --auto

    # Full pipeline: Archive → CWA → Qdrant (with CUDA)
    python public_domain_pipeline.py --archive-id "crimeandpunishme00dostuoft" --cwa --ingest --auto

    # Gutenberg → Calibre-Web API → Qdrant
    python public_domain_pipeline.py --gutenberg-id 7205 --calibre-user admin --calibre-pass xxx --ingest --auto
"""

import argparse
import shutil
import sys
from pathlib import Path
from typing import Optional, Dict

# Import connectors
try:
    from gutenberg_connector import (
        search_books as gutenberg_search,
        download_book as gutenberg_download,
        print_book_info as gutenberg_print_info,
    )
    from archive_connector import (
        search_books as archive_search,
        download_book as archive_download,
        print_book_info as archive_print_info,
        validate_book_quality,
        print_quality_report,
    )
    from calibre_web_connector import CalibreWebClient
    from calibre_db import CalibreDB
    from ingest_books import ingest_book
    from config import (
        QDRANT_HOST, QDRANT_PORT, QDRANT_COLLECTION, DEFAULT_EMBEDDING_MODEL,
        CWA_INGEST_PATH, CALIBRE_WEB_URL, CALIBRE_LIBRARY_PATH,
    )
except ImportError as e:
    print(f"[ERROR] Failed to import connectors: {e}")
    print("Make sure you're running from the scripts directory.")
    sys.exit(1)


def check_already_exists(
    source: str,
    source_id: str,
    book_title: str = '',
    collection_name: str = QDRANT_COLLECTION,
    qdrant_host: str = QDRANT_HOST,
    qdrant_port: int = QDRANT_PORT,
) -> Dict:
    """
    Check if a book already exists in Qdrant and/or local downloads.

    Checks by source+source_id first (exact match), then falls back to title.
    This allows different translations of the same work (e.g., Crime and Punishment
    in English and Russian) while preventing re-ingestion of the exact same edition.

    Returns:
        Dict with 'in_qdrant' (bool), 'chunks' (int), 'in_downloads' (bool)
    """
    result = {'in_qdrant': False, 'chunks': 0, 'in_downloads': False, 'download_path': None}

    # Check local downloads folder
    downloads_dir = Path(__file__).parent / 'public_domain_downloads'
    if downloads_dir.exists():
        search_term = book_title.lower() if book_title else source_id.lower()
        for f in downloads_dir.iterdir():
            if search_term in f.stem.lower():
                result['in_downloads'] = True
                result['download_path'] = str(f)
                break

    # Check Qdrant by source+source_id (precise duplicate detection)
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        from qdrant_utils import check_qdrant_connection

        is_connected, _ = check_qdrant_connection(qdrant_host, qdrant_port)
        if not is_connected:
            return result

        client = QdrantClient(host=qdrant_host, port=qdrant_port, timeout=5)
        collections = [c.name for c in client.get_collections().collections]

        if collection_name not in collections:
            return result

        # Primary check: source + source_id (exact edition match)
        count_result = client.count(
            collection_name=collection_name,
            count_filter=Filter(
                must=[
                    FieldCondition(key="source", match=MatchValue(value=source)),
                    FieldCondition(key="source_id", match=MatchValue(value=str(source_id))),
                ]
            )
        )

        if count_result.count > 0:
            result['in_qdrant'] = True
            result['chunks'] = count_result.count
            return result

        # Fallback: check by title (for books ingested before source tracking)
        if book_title:
            count_result = client.count(
                collection_name=collection_name,
                count_filter=Filter(
                    must=[
                        FieldCondition(
                            key="book_title",
                            match=MatchValue(value=book_title.lower())
                        )
                    ]
                )
            )

            if count_result.count > 0:
                result['in_qdrant'] = True
                result['chunks'] = count_result.count

    except Exception:
        pass  # Non-critical - proceed with pipeline if check fails

    return result


def check_calibre_exists(book_title: str, author: str = '') -> bool:
    """Check if a book already exists in Calibre library by title (and optionally author)."""
    try:
        db = CalibreDB(CALIBRE_LIBRARY_PATH)
        matches = db.search_books(title=book_title)
        if matches:
            # If author provided, narrow down
            if author:
                author_lower = author.lower()
                for m in matches:
                    if author_lower in (m.author or '').lower():
                        return True
            # Title-only match is enough
            return True
    except Exception:
        pass
    return False


def copy_to_cwa(file_path: str, ingest_path: str = CWA_INGEST_PATH) -> bool:
    """Copy downloaded book to CWA ingest folder."""
    src = Path(file_path)
    if not src.exists():
        print(f"[ERROR] File not found: {src}")
        return False

    dest_dir = Path(ingest_path)
    print(f"\n[COPY] Copying to CWA ingest folder...")
    print(f"       From: {src}")
    print(f"       To:   {dest_dir}")

    try:
        if not dest_dir.exists():
            dest_dir.mkdir(parents=True, exist_ok=True)
        dest_file = dest_dir / src.name
        shutil.copy2(src, dest_file)
        print(f"[OK] Copied to: {dest_file}")
        return True
    except Exception as e:
        print(f"[ERROR] Copy failed: {e}")
        return False


def full_pipeline(
    source: str = 'gutenberg',
    gutenberg_id: Optional[int] = None,
    archive_id: Optional[str] = None,
    download_format: str = 'epub',
    use_cwa: bool = False,
    calibre_web_url: str = CALIBRE_WEB_URL,
    calibre_user: Optional[str] = None,
    calibre_password: Optional[str] = None,
    do_ingest: bool = False,
    skip_quality_check: bool = False,
    force: bool = False,
) -> bool:
    """
    Execute full pipeline for a single book.

    Args:
        source: 'gutenberg' or 'archive'
        gutenberg_id: Gutenberg book ID (for source=gutenberg)
        archive_id: Archive.org identifier (for source=archive)
        download_format: Format to download (epub, pdf, txt)
        use_cwa: If True, copy to CWA ingest folder instead of Calibre-Web API
        calibre_web_url: Calibre-Web instance URL
        calibre_user: Calibre-Web username
        calibre_password: Calibre-Web password
        do_ingest: If True, ingest to Qdrant after Calibre step
        skip_quality_check: Skip quality validation

    Returns:
        True if successful, False otherwise
    """
    # Determine step count
    total_steps = 2  # download + calibre
    if not skip_quality_check:
        total_steps += 1
    if do_ingest:
        total_steps += 1
    step = 0

    book_label = archive_id if source == 'archive' else str(gutenberg_id)
    print(f"\n{'='*70}")
    print(f"ALEXANDRIA PUBLIC DOMAIN PIPELINE")
    print(f"{'='*70}")
    print(f"Source:  {source.upper()}")
    print(f"Book:    {book_label}")
    print(f"Format:  {download_format}")
    print(f"Calibre: {'CWA folder' if use_cwa else 'Calibre-Web API'}")
    print(f"Ingest:  {'Yes (Qdrant)' if do_ingest else 'No'}")
    print(f"{'='*70}\n")

    # Pre-flight: check if book already exists in Qdrant or downloads
    check_source_id = archive_id if source == 'archive' else str(gutenberg_id)
    pre_check_title = ''
    try:
        if source == 'gutenberg' and gutenberg_id:
            results = gutenberg_search(query=str(gutenberg_id), limit=1)
            for r in results:
                if r.get('id') == gutenberg_id:
                    pre_check_title = r.get('title', '')
                    break
    except Exception:
        pass

    exists = check_already_exists(
        source=source, source_id=check_source_id, book_title=pre_check_title
    )
    if exists['in_qdrant']:
        print(f"[WARN] Book already in Qdrant! ({exists['chunks']} chunks)")
        print(f"       Source: {source}:{check_source_id}")
        if not force:
            print(f"       Use --force to re-download and re-ingest.")
            return False
        print(f"       --force specified, continuing anyway...")
    if exists['in_downloads']:
        print(f"[INFO] Book already downloaded: {exists['download_path']}")

    # Step 1: Download
    step += 1
    if source == 'archive':
        print(f"[STEP {step}/{total_steps}] Downloading from Internet Archive...")
        file_path = archive_download(archive_id, download_format, output_dir='./public_domain_downloads')
    else:
        print(f"[STEP {step}/{total_steps}] Downloading from Project Gutenberg...")
        file_path = gutenberg_download(gutenberg_id, download_format, output_dir='./public_domain_downloads')

    if not file_path:
        print(f"[ERROR] Failed to download book {book_label}")
        return False

    # Step 2: Quality check
    if not skip_quality_check:
        step += 1
        print(f"\n[STEP {step}/{total_steps}] Running quality check...")
        quality = validate_book_quality(file_path)
        print_quality_report(quality)

        if not quality['passed']:
            print(f"\n[ABORT] Quality check failed. File saved at: {file_path}")
            print(f"        Use --skip-quality-check to bypass.")
            return False

    # Step 3: Calibre (CWA folder or Calibre-Web API)
    step += 1

    # Extract title from filename for Calibre duplicate check
    file_stem = Path(file_path).stem  # "Title - Author"
    calibre_check_title = file_stem.split(' - ')[0].strip() if ' - ' in file_stem else file_stem
    calibre_check_author = file_stem.split(' - ')[1].strip() if ' - ' in file_stem else ''

    if check_calibre_exists(calibre_check_title, calibre_check_author):
        print(f"\n[STEP {step}/{total_steps}] SKIPPED - already in Calibre: {calibre_check_title}")
        if not force:
            print(f"         Use --force to re-send to Calibre.")
    elif use_cwa:
        print(f"\n[STEP {step}/{total_steps}] Copying to CWA ingest folder...")
        success = copy_to_cwa(file_path)
        if not success:
            print(f"[WARN] CWA copy failed, but file is saved at: {file_path}")
    else:
        if calibre_user and calibre_password:
            print(f"\n[STEP {step}/{total_steps}] Uploading to Calibre-Web...")
            client = CalibreWebClient(calibre_web_url, calibre_user, calibre_password)
            success = client.upload_book(file_path)
            if not success:
                print(f"[WARN] Calibre-Web upload failed, but file is saved at: {file_path}")
        else:
            print(f"\n[STEP {step}/{total_steps}] SKIPPED Calibre-Web - no credentials provided")
            print(f"         Use --calibre-user and --calibre-pass, or --cwa for folder copy")

    # Step 4: Qdrant ingest (only if --ingest)
    if do_ingest:
        step += 1
        print(f"\n[STEP {step}/{total_steps}] Ingesting to Qdrant (CUDA)...")

        # Build source metadata for tracking
        source_id = archive_id if source == 'archive' else str(gutenberg_id)
        src_meta = {'source': source, 'source_id': source_id}

        result = ingest_book(
            filepath=file_path,
            collection_name='alexandria',
            qdrant_host=QDRANT_HOST,
            qdrant_port=QDRANT_PORT,
            model_id=DEFAULT_EMBEDDING_MODEL,
            hierarchical=True,
            force_reingest=force,
            source_meta=src_meta,
        )

        if result.get('success'):
            chunks = result.get('chunks', 0)
            print(f"[OK] Ingestion complete: {result['title']} ({chunks} chunks)")
        else:
            error = result.get('error', 'Unknown error')
            print(f"[ERROR] Ingestion failed: {error}")
            return False

    # Summary
    print(f"\n{'='*70}")
    print(f"[SUCCESS] Pipeline complete!")
    print(f"{'='*70}")
    print(f"Downloaded: {file_path}")
    if use_cwa:
        print(f"CWA folder: {CWA_INGEST_PATH}")
    if do_ingest:
        print(f"Ingested:   alexandria collection on {QDRANT_HOST}")
    if not do_ingest:
        print(f"\nTo ingest to Qdrant later, run:")
        print(f'  python ingest_books.py --file "{file_path}"')
    print(f"{'='*70}\n")

    return True


def interactive_search_mode(
    query: str,
    source: str = 'gutenberg',
    language: Optional[str] = None,
    use_cwa: bool = False,
    calibre_user: Optional[str] = None,
    calibre_password: Optional[str] = None,
    do_ingest: bool = False,
    download_format: str = 'epub',
):
    """Interactive mode: search, select, and process."""
    print(f"\n{'='*70}")
    print(f"ALEXANDRIA PUBLIC DOMAIN SEARCH ({source.upper()})")
    print(f"{'='*70}")
    print(f"Query: {query}")
    if language:
        print(f"Language: {language}")
    print(f"{'='*70}\n")

    # Search
    if source == 'archive':
        books = archive_search(query=query, language=language, limit=10)
    else:
        books = gutenberg_search(query=query, language=language, limit=10)

    if not books:
        print("[WARN] No books found")
        return

    print(f"\n{'='*70}")
    print(f"SEARCH RESULTS")
    print(f"{'='*70}")

    print_fn = archive_print_info if source == 'archive' else gutenberg_print_info
    for i, book in enumerate(books, 1):
        print_fn(book, index=i)

    # Ask user to select
    print(f"\n{'='*70}")
    choice = input("Select book number to process (or 'q' to quit): ")

    if choice.lower() == 'q':
        print("Cancelled.")
        return

    try:
        index = int(choice) - 1
        if 0 <= index < len(books):
            selected = books[index]

            if source == 'archive':
                identifier = selected.get('identifier')
                title = selected.get('title', 'Unknown')
                creator = selected.get('creator', 'Unknown')
                if isinstance(creator, list):
                    creator = creator[0]
                print(f"\n[SELECTED] {title}")
                print(f"           by {creator}")

                full_pipeline(
                    source='archive',
                    archive_id=identifier,
                    download_format=download_format,
                    use_cwa=use_cwa,
                    calibre_user=calibre_user,
                    calibre_password=calibre_password,
                    do_ingest=do_ingest,
                )
            else:
                book_id = selected.get('id')
                title = selected.get('title', 'Unknown')
                authors = selected.get('authors', [{}])
                author = authors[0].get('name', 'Unknown') if authors else 'Unknown'
                print(f"\n[SELECTED] {title}")
                print(f"           by {author}")

                full_pipeline(
                    source='gutenberg',
                    gutenberg_id=book_id,
                    download_format=download_format,
                    use_cwa=use_cwa,
                    calibre_user=calibre_user,
                    calibre_password=calibre_password,
                    do_ingest=do_ingest,
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
  # Search Archive for Dostoevsky in Russian
  python public_domain_pipeline.py --source archive --search "Dostoevsky" --language rus

  # Search Gutenberg for Kant in German
  python public_domain_pipeline.py --search "Kant Kritik" --language de

  # Download from Archive + CWA (no ingest)
  python public_domain_pipeline.py --archive-id "crimeandpunishme00dostuoft" --format epub --cwa --auto

  # Full pipeline: Archive -> CWA -> Qdrant
  python public_domain_pipeline.py --archive-id "crimeandpunishme00dostuoft" --cwa --ingest --auto

  # Gutenberg -> Calibre-Web API -> Qdrant
  python public_domain_pipeline.py --gutenberg-id 7205 --calibre-user admin --calibre-pass xxx --ingest --auto
        """
    )

    # Source selection
    parser.add_argument('--source', type=str, default='gutenberg',
                       choices=['gutenberg', 'archive'],
                       help='Book source (default: gutenberg)')

    # Search mode
    parser.add_argument('--search', '-s', type=str,
                       help='Search query (author, title, etc.)')
    parser.add_argument('--language', '-l', type=str,
                       help='Language code (en, de, ru, el, la, etc.)')

    # Direct download mode
    parser.add_argument('--gutenberg-id', '-g', type=int,
                       help='Project Gutenberg book ID')
    parser.add_argument('--archive-id', '-a', type=str,
                       help='Internet Archive identifier')
    parser.add_argument('--format', '-f', type=str, default='epub',
                       help='Download format (default: epub)')

    # Calibre destination
    parser.add_argument('--cwa', action='store_true',
                       help=f'Copy to CWA ingest folder ({CWA_INGEST_PATH})')
    parser.add_argument('--calibre-url', type=str, default=CALIBRE_WEB_URL,
                       help=f'Calibre-Web URL (default: {CALIBRE_WEB_URL})')
    parser.add_argument('--calibre-user', type=str,
                       help='Calibre-Web username')
    parser.add_argument('--calibre-pass', type=str,
                       help='Calibre-Web password')

    # Pipeline control
    parser.add_argument('--ingest', action='store_true',
                       help='Ingest to Qdrant after Calibre step (default: no)')
    parser.add_argument('--auto', action='store_true',
                       help='Auto-run without prompts')
    parser.add_argument('--skip-quality-check', action='store_true',
                       help='Skip quality validation after download')
    parser.add_argument('--force', action='store_true',
                       help='Force download even if book already exists in Qdrant')

    args = parser.parse_args()

    # If --archive-id is given, auto-set source to archive
    if args.archive_id:
        args.source = 'archive'

    # Search mode
    if args.search:
        interactive_search_mode(
            query=args.search,
            source=args.source,
            language=args.language,
            use_cwa=args.cwa,
            calibre_user=args.calibre_user,
            calibre_password=args.calibre_pass,
            do_ingest=args.ingest,
            download_format=args.format,
        )
        return

    # Direct download mode (Gutenberg)
    if args.gutenberg_id:
        if not args.auto:
            confirm = input(f"Download and process Gutenberg book {args.gutenberg_id}? (yes/no): ")
            if confirm.lower() != 'yes':
                print("Cancelled.")
                return

        success = full_pipeline(
            source='gutenberg',
            gutenberg_id=args.gutenberg_id,
            download_format=args.format,
            use_cwa=args.cwa,
            calibre_web_url=args.calibre_url,
            calibre_user=args.calibre_user,
            calibre_password=args.calibre_pass,
            do_ingest=args.ingest,
            skip_quality_check=args.skip_quality_check,
            force=args.force,
        )
        sys.exit(0 if success else 1)

    # Direct download mode (Archive)
    if args.archive_id:
        if not args.auto:
            confirm = input(f"Download and process Archive book '{args.archive_id}'? (yes/no): ")
            if confirm.lower() != 'yes':
                print("Cancelled.")
                return

        success = full_pipeline(
            source='archive',
            archive_id=args.archive_id,
            download_format=args.format,
            use_cwa=args.cwa,
            calibre_web_url=args.calibre_url,
            calibre_user=args.calibre_user,
            calibre_password=args.calibre_pass,
            do_ingest=args.ingest,
            skip_quality_check=args.skip_quality_check,
            force=args.force,
        )
        sys.exit(0 if success else 1)

    # No action specified
    parser.print_help()


if __name__ == '__main__':
    main()
