#!/usr/bin/env python3
"""
Alexandria CWA (Calibre-Web-Automated) Pipeline
================================================

Simplified pipeline for Calibre-Web-Automated:
1. Download from Gutenberg/Archive
2. Copy to CWA ingest folder
3. [AUTO] CWA imports to Calibre
4. [AUTO] Alexandria ingests from Calibre to Qdrant

Usage:
    # Configure CWA ingest path first
    python cwa_ingest_pipeline.py --configure

    # Download and auto-ingest
    python cwa_ingest_pipeline.py --gutenberg-id 7205

    # Search and select
    python cwa_ingest_pipeline.py --search "Nietzsche" --language de

Environment Variables:
    CWA_INGEST_PATH - Path to CWA book ingest folder
                      Examples:
                      - Windows SMB: \\192.168.0.xxx\alexandria\cwa-book-ingest
                      - Linux mount: /mnt/nas/cwa-book-ingest
                      - SSH: user@nas:/docker/volumes/cwa-book-ingest
"""

import os
import argparse
import sys
from pathlib import Path
from typing import Optional
import shutil

# Import connectors
try:
    from gutenberg_connector import search_books, download_book, print_book_info
except ImportError:
    print("[ERROR] Cannot import gutenberg_connector")
    sys.exit(1)

# CWA ingest path - import from central config, fallback to env
try:
    from config import CWA_INGEST_PATH
except ImportError:
    CWA_INGEST_PATH = os.environ.get('CWA_INGEST_PATH', '')


def configure_ingest_path(path: str):
    """Save CWA ingest path to config."""
    config_file = Path(__file__).parent / '.cwa_config'

    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(f"CWA_INGEST_PATH={path}\n")

    print(f"[OK] Configured CWA ingest path: {path}")
    print(f"     Saved to: {config_file}")


def load_ingest_path() -> str:
    """Load CWA ingest path from config."""
    config_file = Path(__file__).parent / '.cwa_config'

    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('CWA_INGEST_PATH='):
                    return line.split('=', 1)[1].strip()

    return CWA_INGEST_PATH


def copy_to_cwa_ingest(file_path: str, ingest_path: str) -> bool:
    """
    Copy downloaded book to CWA ingest folder.

    Supports:
    - Local path (direct copy)
    - SMB share (Windows network path)
    - SSH (requires scp command)
    """
    file_path = Path(file_path)

    if not file_path.exists():
        print(f"[ERROR] File not found: {file_path}")
        return False

    print(f"\n[COPY] Copying to CWA ingest folder...")
    print(f"       From: {file_path}")
    print(f"       To:   {ingest_path}")

    try:
        # Check if ingest_path is SSH format (user@host:/path)
        if '@' in ingest_path and ':' in ingest_path:
            # Use SCP
            import subprocess
            cmd = ['scp', str(file_path), ingest_path]
            print(f"       Using SCP: {' '.join(cmd)}")

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                print(f"[OK] Copied via SCP")
                return True
            else:
                print(f"[ERROR] SCP failed: {result.stderr}")
                return False

        else:
            # Local or SMB path - use regular copy
            dest_path = Path(ingest_path)

            # Create directory if needed
            if not dest_path.exists():
                dest_path.mkdir(parents=True, exist_ok=True)

            # Copy file
            dest_file = dest_path / file_path.name
            shutil.copy2(file_path, dest_file)

            print(f"[OK] Copied to: {dest_file}")
            return True

    except Exception as e:
        print(f"[ERROR] Copy failed: {e}")
        return False


def cwa_pipeline(
    gutenberg_id: int,
    download_format: str = 'epub',
    ingest_path: Optional[str] = None
) -> bool:
    """
    Execute CWA pipeline for a book.

    Args:
        gutenberg_id: Gutenberg book ID
        download_format: Format to download
        ingest_path: CWA ingest folder path

    Returns:
        True if successful
    """
    print(f"\n{'='*70}")
    print(f"ALEXANDRIA CWA PIPELINE")
    print(f"{'='*70}")
    print(f"Book ID: {gutenberg_id}")
    print(f"Format:  {download_format}")
    print(f"{'='*70}\n")

    # Step 1: Download
    print(f"[STEP 1/2] Downloading from Gutenberg...")
    file_path = download_book(
        gutenberg_id,
        download_format,
        output_dir='./public_domain_downloads'
    )

    if not file_path:
        print(f"[ERROR] Download failed")
        return False

    # Step 2: Copy to CWA ingest
    print(f"\n[STEP 2/2] Copying to CWA ingest folder...")

    if not ingest_path:
        print(f"[ERROR] CWA ingest path not configured!")
        print(f"\nRun: python cwa_ingest_pipeline.py --configure")
        return False

    success = copy_to_cwa_ingest(file_path, ingest_path)

    if not success:
        return False

    # Done!
    print(f"\n{'='*70}")
    print(f"[SUCCESS] Pipeline complete!")
    print(f"{'='*70}")
    print(f"Downloaded:  {file_path}")
    print(f"Copied to:   {ingest_path}")
    print(f"\nNext steps:")
    print(f"  1. CWA will automatically import to Calibre")
    print(f"  2. Check https://alexandria.jedai.space for the book")
    print(f"  3. Run Qdrant ingestion from Calibre library")
    print(f"{'='*70}\n")

    return True


def interactive_search(ingest_path: str):
    """Interactive search and download."""
    query = input("Search query: ")
    language = input("Language code (or Enter for all): ").strip() or None

    books = search_books(query=query, language=language, limit=10)

    if not books:
        print("[WARN] No books found")
        return

    print(f"\n{'='*70}")
    print(f"RESULTS")
    print(f"{'='*70}")

    for i, book in enumerate(books, 1):
        print_book_info(book, index=i)

    choice = input("\nSelect book (or 'q' to quit): ")

    if choice.lower() == 'q':
        return

    try:
        index = int(choice) - 1
        if 0 <= index < len(books):
            book = books[index]
            book_id = book.get('id')

            cwa_pipeline(book_id, 'epub', ingest_path)
    except ValueError:
        print("[ERROR] Invalid input")


def main():
    parser = argparse.ArgumentParser(
        description='Alexandria CWA Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Configuration
    parser.add_argument('--configure', action='store_true',
                       help='Configure CWA ingest path')
    parser.add_argument('--ingest-path', type=str,
                       help='CWA ingest folder path')

    # Search mode
    parser.add_argument('--search', '-s', type=str,
                       help='Search Gutenberg')
    parser.add_argument('--language', '-l', type=str,
                       help='Language filter')

    # Direct mode
    parser.add_argument('--gutenberg-id', '-g', type=int,
                       help='Gutenberg book ID')
    parser.add_argument('--format', '-f', type=str, default='epub',
                       choices=['epub', 'pdf', 'txt', 'html'],
                       help='Download format')

    args = parser.parse_args()

    # Configure mode
    if args.configure:
        if args.ingest_path:
            configure_ingest_path(args.ingest_path)
        else:
            print("Enter CWA ingest path:")
            print("\nExamples:")
            print("  Windows SMB:  \\\\192.168.0.xxx\\alexandria\\cwa-book-ingest")
            print("  Linux mount:  /mnt/nas/cwa-book-ingest")
            print("  SSH:          user@nas:/docker/volumes/cwa-book-ingest")
            print()
            path = input("Path: ").strip()
            if path:
                configure_ingest_path(path)
        return

    # Load configured ingest path
    ingest_path = args.ingest_path or load_ingest_path()

    if not ingest_path:
        print("[ERROR] CWA ingest path not configured!")
        print("\nRun: python cwa_ingest_pipeline.py --configure")
        sys.exit(1)

    # Search mode
    if args.search:
        interactive_search(ingest_path)
        return

    # Direct download mode
    if args.gutenberg_id:
        success = cwa_pipeline(args.gutenberg_id, args.format, ingest_path)
        sys.exit(0 if success else 1)

    # No action
    parser.print_help()


if __name__ == '__main__':
    main()
