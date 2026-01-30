#!/usr/bin/env python3
"""
Count file types in Alexandria library directory.

Usage:
    python count_file_types.py --directory "G:\My Drive\alexandria"
"""

import argparse
import logging
from pathlib import Path
from collections import Counter
from typing import Dict, List, Tuple

from config import CALIBRE_LIBRARY_PATH

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


def count_file_types(directory: str, recursive: bool = True) -> Dict[str, int]:
    """
    Count file types in directory.

    Args:
        directory: Path to directory
        recursive: Whether to search subdirectories

    Returns:
        Dictionary mapping file extension to count
    """
    directory_path = Path(directory)

    if not directory_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    if not directory_path.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory}")

    # Collect all files
    if recursive:
        files = directory_path.rglob('*')
    else:
        files = directory_path.glob('*')

    # Count extensions
    extensions = Counter()
    total_size_by_ext = Counter()
    files_by_ext = {}

    for file_path in files:
        if file_path.is_file():
            ext = file_path.suffix.lower()
            if not ext:
                ext = '(no extension)'

            extensions[ext] += 1
            total_size_by_ext[ext] += file_path.stat().st_size

            # Keep example files
            if ext not in files_by_ext:
                files_by_ext[ext] = []
            if len(files_by_ext[ext]) < 3:  # Keep first 3 examples
                files_by_ext[ext].append(file_path.name)

    return extensions, total_size_by_ext, files_by_ext


def format_size(size_bytes: int) -> str:
    """Format bytes to human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def print_results(
    extensions: Counter,
    total_size_by_ext: Counter,
    files_by_ext: Dict[str, List[str]],
    directory: str
):
    """Print formatted results."""

    total_files = sum(extensions.values())
    total_size = sum(total_size_by_ext.values())

    print("\n" + "="*80)
    print("Alexandria Library - File Type Analysis")
    print("="*80)
    print(f"Directory: {directory}")
    print(f"Total Files: {total_files:,}")
    print(f"Total Size: {format_size(total_size)}")
    print("="*80)

    # Sort by count (descending)
    sorted_exts = extensions.most_common()

    print(f"\n{'Extension':<15} {'Count':<10} {'%':<8} {'Total Size':<15} {'Avg Size':<15} {'Examples'}")
    print("-"*100)

    for ext, count in sorted_exts:
        percentage = (count / total_files) * 100
        total_ext_size = total_size_by_ext[ext]
        avg_size = total_ext_size / count
        examples = ', '.join(files_by_ext[ext][:2])  # Show first 2 examples

        print(
            f"{ext:<15} "
            f"{count:<10,} "
            f"{percentage:<7.1f}% "
            f"{format_size(total_ext_size):<15} "
            f"{format_size(avg_size):<15} "
            f"{examples[:50]}{'...' if len(examples) > 50 else ''}"
        )

    print("-"*100)
    print(f"{'TOTAL':<15} {total_files:<10,} {'100.0%':<8} {format_size(total_size):<15}")
    print()


def print_book_formats_summary(extensions: Counter):
    """Print summary of book formats specifically."""

    book_formats = {
        '.epub': 'EPUB (Digital book)',
        '.pdf': 'PDF (Portable Document)',
        '.mobi': 'MOBI (Kindle)',
        '.azw': 'AZW (Kindle)',
        '.azw3': 'AZW3 (Kindle)',
        '.txt': 'Plain Text',
        '.md': 'Markdown',
        '.doc': 'Word Document (old)',
        '.docx': 'Word Document',
        '.djvu': 'DjVu',
        '.chm': 'Compiled HTML Help'
    }

    print("\n" + "="*80)
    print("Book Format Summary")
    print("="*80)

    total_books = 0
    for ext in book_formats.keys():
        count = extensions.get(ext, 0)
        if count > 0:
            total_books += count
            desc = book_formats[ext]
            print(f"{ext:<10} {count:>6,} files  - {desc}")

    print("-"*80)
    print(f"{'TOTAL':<10} {total_books:>6,} book files")
    print()

    # Ingestion support status
    print("Ingestion Support:")
    print("  [OK] Supported:  .epub, .pdf, .txt, .md")
    print("  [!]  Possible:   .mobi (needs conversion)")
    print("  [X]  Not Yet:    .doc, .docx, .azw, .azw3, .djvu, .chm")
    print()


def main():
    parser = argparse.ArgumentParser(
        description='Count file types in Alexandria library directory'
    )
    parser.add_argument(
        '--directory',
        type=str,
        default=CALIBRE_LIBRARY_PATH,
        help=f'Directory to scan (default: {CALIBRE_LIBRARY_PATH})'
    )
    parser.add_argument(
        '--no-recursive',
        action='store_true',
        help='Do not scan subdirectories'
    )

    args = parser.parse_args()

    try:
        logger.info(f"Scanning directory: {args.directory}")

        extensions, total_size_by_ext, files_by_ext = count_file_types(
            args.directory,
            recursive=not args.no_recursive
        )

        print_results(extensions, total_size_by_ext, files_by_ext, args.directory)
        print_book_formats_summary(extensions)

    except Exception as e:
        logger.error(f"Error: {e}")
        raise


if __name__ == '__main__':
    main()
