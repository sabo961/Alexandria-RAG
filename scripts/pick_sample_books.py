#!/usr/bin/env python3
"""
Pick sample books from Calibre library for testing.

Creates a sample_books.txt file with paths to selected books
for batch ingestion testing.

Selection criteria:
- Mix of EPUB and PDF formats
- Multiple languages (eng, hrv, deu, etc.)
- Different domains (technical, philosophy, literature)
- Total ~15 books for quick testing
"""

import sys
import random
from pathlib import Path

from calibre_db import CalibreDB
from config import CALIBRE_LIBRARY_PATH

def pick_sample_books(
    total_books: int = 15,
    pdf_ratio: float = 0.5,
    multilingual_count: int = 5
):
    """
    Pick sample books from Calibre library.

    Args:
        total_books: Total number of books to pick
        pdf_ratio: Ratio of PDF books (0.0-1.0)
        multilingual_count: Number of non-English books to include
    """
    db = CalibreDB()

    # Get all books
    all_books = db.get_all_books()

    print(f"Total books in library: {len(all_books)}")

    # Categorize books
    epub_books = [b for b in all_books if 'epub' in b.formats]
    pdf_books = [b for b in all_books if 'pdf' in b.formats]
    multilingual = [b for b in all_books if b.language not in ['eng', 'unknown']]

    print(f"EPUB books: {len(epub_books)}")
    print(f"PDF books: {len(pdf_books)}")
    print(f"Multilingual books: {len(multilingual)}")

    # Select books
    selected = []

    # Pick multilingual books first
    if multilingual:
        sample_multilingual = random.sample(
            multilingual,
            min(multilingual_count, len(multilingual))
        )
        selected.extend(sample_multilingual)
        print(f"\nSelected {len(sample_multilingual)} multilingual books")

    # Calculate remaining slots
    remaining = total_books - len(selected)
    pdf_count = int(remaining * pdf_ratio)
    epub_count = remaining - pdf_count

    # Pick PDFs (excluding already selected)
    available_pdfs = [b for b in pdf_books if b not in selected]
    if available_pdfs:
        sample_pdfs = random.sample(
            available_pdfs,
            min(pdf_count, len(available_pdfs))
        )
        selected.extend(sample_pdfs)
        print(f"Selected {len(sample_pdfs)} PDF books")

    # Pick EPUBs (excluding already selected)
    available_epubs = [b for b in epub_books if b not in selected]
    if available_epubs:
        sample_epubs = random.sample(
            available_epubs,
            min(epub_count, len(available_epubs))
        )
        selected.extend(sample_epubs)
        print(f"Selected {len(sample_epubs)} EPUB books")

    # Write to file with UTF-8 encoding
    output_file = Path(__file__).parent / 'sample_books.txt'
    library_path = Path(CALIBRE_LIBRARY_PATH)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Sample books for Alexandria testing\n")
        f.write(f"# Total: {len(selected)} books\n")
        f.write(f"# Generated from: {CALIBRE_LIBRARY_PATH}\n\n")

        for book in selected:
            # Get first available format
            format_ext = book.formats[0] if book.formats else 'epub'

            # Get full file path
            file_path = db.get_book_file_path(book.id, format_ext)

            if file_path:
                f.write(f"{file_path}\n")
                f.write(f"# Title: {book.title}\n")
                f.write(f"# Author: {book.author}\n")
                f.write(f"# Language: {book.language}\n")
                f.write(f"# Format: {format_ext}\n\n")

    print(f"\n{output_file} created with {len(selected)} books")

    # Print summary
    print("\n=== Sample Summary ===")
    lang_dist = {}
    format_dist = {}

    for book in selected:
        # Language distribution
        lang = book.language
        lang_dist[lang] = lang_dist.get(lang, 0) + 1

        # Format distribution
        for fmt in book.formats:
            format_dist[fmt] = format_dist.get(fmt, 0) + 1

    print("\nLanguages:")
    for lang, count in sorted(lang_dist.items()):
        print(f"  {lang}: {count}")

    print("\nFormats:")
    for fmt, count in sorted(format_dist.items()):
        print(f"  {fmt}: {count}")

    return output_file


if __name__ == '__main__':
    # Set seed for reproducibility
    random.seed(42)

    sample_file = pick_sample_books(
        total_books=15,
        pdf_ratio=0.5,
        multilingual_count=5
    )

    print(f"\nNext step:")
    print(f"  python batch_ingest_from_file.py --file {sample_file}")
