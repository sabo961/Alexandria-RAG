#!/usr/bin/env python3
"""
Generate book inventory from Calibre library structure.

Calibre structure: Author Folder (FirstName LastName) / Book Folder / Files

Usage:
    python generate_book_inventory.py --directory "G:\My Drive\alexandria" --output ../docs/book-inventory.txt
"""

import argparse
import logging
from pathlib import Path
from typing import List, Dict
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


# Book formats to include
BOOK_FORMATS = {
    '.epub', '.pdf', '.mobi', '.txt', '.md',
    '.doc', '.docx', '.djvu', '.chm', '.azw3',
    '.azw', '.lit', '.rtf', '.fb2'
}


def scan_calibre_library(directory: str) -> List[Dict]:
    """
    Scan Calibre library and extract book information.

    Calibre structure:
        Author Folder (FirstName LastName)/
            Book Folder/
                book.epub
                book.pdf
                cover.jpg
                metadata.opf

    Args:
        directory: Path to Calibre library root

    Returns:
        List of book dictionaries with author, title, formats, path
    """
    directory_path = Path(directory)

    if not directory_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    books = []

    # Iterate through author folders (level 1)
    for author_folder in sorted(directory_path.iterdir()):
        if not author_folder.is_dir():
            continue

        # Skip folders starting with underscore
        if author_folder.name.startswith('_'):
            logger.debug(f"Skipping folder: {author_folder.name}")
            continue

        author_name = author_folder.name

        # Iterate through book folders (level 2)
        for book_folder in sorted(author_folder.iterdir()):
            if not book_folder.is_dir():
                continue

            # Skip folders starting with underscore
            if book_folder.name.startswith('_'):
                logger.debug(f"Skipping folder: {book_folder.name}")
                continue

            book_title = book_folder.name

            # Find book files in this folder
            book_files = []
            for file_path in book_folder.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in BOOK_FORMATS:
                    book_files.append({
                        'format': file_path.suffix.lower(),
                        'size_mb': file_path.stat().st_size / (1024 * 1024),
                        'path': str(file_path.relative_to(directory_path))
                    })

            if book_files:
                books.append({
                    'author': author_name,
                    'title': book_title,
                    'files': book_files,
                    'folder_path': str(book_folder.relative_to(directory_path))
                })

    return books


def write_inventory(books: List[Dict], output_file: str):
    """Write book inventory to text file."""

    output_path = Path(output_file)

    with open(output_path, 'w', encoding='utf-8') as f:
        # Header
        f.write("="*80 + "\n")
        f.write("Alexandria Library - Book Inventory\n")
        f.write("="*80 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Books: {len(books):,}\n")
        f.write("="*80 + "\n\n")

        # Count formats
        format_counts = {}
        for book in books:
            for file_info in book['files']:
                fmt = file_info['format']
                format_counts[fmt] = format_counts.get(fmt, 0) + 1

        f.write("Format Distribution:\n")
        for fmt, count in sorted(format_counts.items(), key=lambda x: x[1], reverse=True):
            f.write(f"  {fmt:<10} {count:>6,} files\n")
        f.write("\n" + "="*80 + "\n\n")

        # Book list
        f.write("Book List (Author / Title / Formats):\n")
        f.write("-"*80 + "\n\n")

        current_author = None
        for book in sorted(books, key=lambda x: (x['author'], x['title'])):
            # Print author header if changed
            if book['author'] != current_author:
                current_author = book['author']
                f.write(f"\n[{current_author}]\n")
                f.write("-"*80 + "\n")

            # Book title
            f.write(f"  {book['title']}\n")

            # Formats
            formats = ', '.join([f"{fi['format']} ({fi['size_mb']:.1f} MB)"
                                for fi in book['files']])
            f.write(f"    Formats: {formats}\n")

            # Path
            f.write(f"    Path: {book['folder_path']}\n")
            f.write("\n")

    logger.info(f"Inventory written to: {output_path}")
    logger.info(f"Total books: {len(books):,}")


def main():
    parser = argparse.ArgumentParser(
        description='Generate book inventory from Calibre library'
    )
    parser.add_argument(
        '--directory',
        type=str,
        default='G:\\My Drive\\alexandria',
        help='Calibre library directory (default: G:\\My Drive\\alexandria)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='../docs/book-inventory.txt',
        help='Output inventory file (default: ../docs/book-inventory.txt)'
    )

    args = parser.parse_args()

    try:
        logger.info(f"Scanning Calibre library: {args.directory}")

        books = scan_calibre_library(args.directory)

        logger.info(f"Found {len(books):,} books")

        write_inventory(books, args.output)

    except Exception as e:
        logger.error(f"Error: {e}")
        raise


if __name__ == '__main__':
    main()
