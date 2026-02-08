#!/usr/bin/env python3
"""
Project Gutenberg Connector for Alexandria
===========================================

Search and download public domain books from Project Gutenberg.
Perfect for classics in original languages (German, Greek, Latin, Russian, etc.)

API: https://gutendex.com (unofficial but excellent)

Usage:
    # Search for Kant in German
    python gutenberg_connector.py --search "Kant" --language de

    # Search for Dostoevsky in Russian
    python gutenberg_connector.py --search "Dostoevsky" --language ru

    # Download book by ID
    python gutenberg_connector.py --download 1497 --format epub

    # Search and download first match
    python gutenberg_connector.py --search "Critique of Pure Reason" --language de --auto-download
"""

import requests
import argparse
import json
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urlencode

# Gutendex API base URL
GUTENDEX_API = "https://gutendex.com/books"

# Language codes mapping
LANGUAGE_NAMES = {
    'en': 'English',
    'de': 'German',
    'fr': 'French',
    'ru': 'Russian',
    'el': 'Ancient Greek',
    'la': 'Latin',
    'hr': 'Croatian',
    'es': 'Spanish',
    'it': 'Italian',
    'pt': 'Portuguese',
    'nl': 'Dutch',
    'pl': 'Polish',
    'cs': 'Czech',
    'zh': 'Chinese',
    'ja': 'Japanese',
    'sa': 'Sanskrit',
    'ar': 'Arabic',
}


def search_books(
    query: Optional[str] = None,
    author: Optional[str] = None,
    title: Optional[str] = None,
    language: Optional[str] = None,
    topic: Optional[str] = None,
    limit: int = 20
) -> List[Dict]:
    """
    Search Project Gutenberg catalog.

    Args:
        query: General search query
        author: Author name
        title: Book title
        language: Language code (en, de, ru, el, la, etc.)
        topic: Subject/topic
        limit: Max results to return

    Returns:
        List of book dictionaries
    """
    params = {}

    if query:
        params['search'] = query
    if author:
        params['search'] = author  # Gutendex uses generic search
    if title:
        params['search'] = title
    if language:
        params['languages'] = language
    if topic:
        params['topic'] = topic

    print(f"Searching Gutenberg: {params}")

    try:
        response = requests.get(GUTENDEX_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        books = data.get('results', [])[:limit]
        print(f"Found {len(books)} books (total available: {data.get('count', 0)})")

        return books

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to search Gutenberg: {e}")
        return []


def get_book_details(book_id: int) -> Optional[Dict]:
    """Get detailed information about a specific book."""
    url = f"{GUTENDEX_API}/{book_id}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to get book details: {e}")
        return None


def get_download_url(book: Dict, format: str = 'epub') -> Optional[str]:
    """
    Extract download URL for specified format.

    Args:
        book: Book dictionary from API
        format: Desired format (epub, html, txt, pdf)

    Returns:
        Download URL or None
    """
    formats = book.get('formats', {})

    # Try to find format (Gutenberg uses MIME types as keys)
    format_map = {
        'epub': ['application/epub+zip', 'application/epub'],
        'html': ['text/html', 'text/html; charset=utf-8'],
        'txt': ['text/plain', 'text/plain; charset=utf-8', 'text/plain; charset=us-ascii'],
        'pdf': ['application/pdf'],
    }

    for mime_type in format_map.get(format, []):
        if mime_type in formats:
            return formats[mime_type]

    # Fallback: return any available format
    if formats:
        return list(formats.values())[0]

    return None


def download_book(book_id: int, format: str = 'epub', output_dir: str = './downloads') -> Optional[str]:
    """
    Download book from Project Gutenberg.

    Args:
        book_id: Gutenberg book ID
        format: Format to download (epub, html, txt, pdf)
        output_dir: Directory to save downloaded file

    Returns:
        Path to downloaded file or None
    """
    book = get_book_details(book_id)

    if not book:
        print(f"[ERROR] Could not find book {book_id}")
        return None

    download_url = get_download_url(book, format)

    if not download_url:
        print(f"[ERROR] Format '{format}' not available for book {book_id}")
        print(f"Available formats: {list(book.get('formats', {}).keys())}")
        return None

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Build filename (sanitize illegal characters for Windows: / : * ? " < > |)
    def sanitize_filename(name):
        for char in ['/', ':', '*', '?', '"', '<', '>', '|']:
            name = name.replace(char, '-')
        return name

    title = sanitize_filename(book.get('title', 'Unknown'))[:100]
    authors = book.get('authors', [])
    author_name = authors[0]['name'] if authors else 'Unknown'
    author_name = sanitize_filename(author_name)[:50]

    filename = f"{title} - {author_name}.{format}"
    file_path = output_path / filename

    print(f"\n[DOWNLOAD] {title}")
    print(f"           by {author_name}")
    print(f"           URL: {download_url}")
    print(f"           Saving to: {file_path}")

    try:
        response = requests.get(download_url, timeout=30, stream=True)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))

        with open(file_path, 'wb') as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        print(f"\r           Progress: {progress:.1f}%", end='', flush=True)

        print(f"\n[OK] Downloaded: {file_path}")
        return str(file_path)

    except requests.exceptions.RequestException as e:
        print(f"\n[ERROR] Download failed: {e}")
        return None


def print_book_info(book: Dict, index: int = None):
    """Pretty print book information."""
    title = book.get('title', 'Unknown')
    authors = book.get('authors', [])
    author_names = ', '.join(a['name'] for a in authors) if authors else 'Unknown'
    languages = ', '.join(book.get('languages', []))
    subjects = book.get('subjects', [])[:3]  # First 3 subjects
    book_id = book.get('id', 'Unknown')
    download_count = book.get('download_count', 0)

    prefix = f"[{index}] " if index is not None else ""

    print(f"\n{prefix}ID: {book_id}")
    print(f"    Title: {title}")
    print(f"    Author: {author_names}")
    print(f"    Language: {languages} ({LANGUAGE_NAMES.get(languages, 'Unknown')})")
    print(f"    Downloads: {download_count:,}")
    if subjects:
        print(f"    Subjects: {', '.join(subjects)}")

    # Show available formats
    formats = book.get('formats', {})
    available = []
    if any('epub' in k.lower() for k in formats.keys()):
        available.append('EPUB')
    if any('html' in k.lower() for k in formats.keys()):
        available.append('HTML')
    if any('txt' in k.lower() or 'plain' in k.lower() for k in formats.keys()):
        available.append('TXT')
    if any('pdf' in k.lower() for k in formats.keys()):
        available.append('PDF')

    if available:
        print(f"    Formats: {', '.join(available)}")


def main():
    parser = argparse.ArgumentParser(description='Project Gutenberg connector for Alexandria')

    # Search parameters
    parser.add_argument('--search', '-s', type=str, help='Search query (author, title, etc.)')
    parser.add_argument('--author', '-a', type=str, help='Search by author name')
    parser.add_argument('--title', '-t', type=str, help='Search by title')
    parser.add_argument('--language', '-l', type=str, help='Language code (en, de, ru, el, la, etc.)')
    parser.add_argument('--topic', type=str, help='Subject/topic')
    parser.add_argument('--limit', type=int, default=20, help='Max results (default: 20)')

    # Download parameters
    parser.add_argument('--download', '-d', type=int, help='Download book by ID')
    parser.add_argument('--format', '-f', type=str, default='epub',
                       choices=['epub', 'html', 'txt', 'pdf'],
                       help='Download format (default: epub)')
    parser.add_argument('--output', '-o', type=str, default='./downloads',
                       help='Output directory (default: ./downloads)')

    # Convenience
    parser.add_argument('--auto-download', action='store_true',
                       help='Auto-download first search result')

    args = parser.parse_args()

    # Download mode
    if args.download:
        file_path = download_book(args.download, args.format, args.output)
        if file_path:
            print(f"\n[SUCCESS] Ready to ingest: {file_path}")
            print(f"\nNext step:")
            print(f'  python ingest_books.py --file "{file_path}"')
        return

    # Search mode
    if args.search or args.author or args.title:
        books = search_books(
            query=args.search,
            author=args.author,
            title=args.title,
            language=args.language,
            topic=args.topic,
            limit=args.limit
        )

        if not books:
            print("[WARN] No books found")
            return

        print(f"\n{'='*70}")
        print(f"SEARCH RESULTS")
        print(f"{'='*70}")

        for i, book in enumerate(books, 1):
            print_book_info(book, index=i)

        # Auto-download first result
        if args.auto_download and books:
            print(f"\n{'='*70}")
            print(f"AUTO-DOWNLOADING FIRST RESULT")
            print(f"{'='*70}")

            first_book = books[0]
            book_id = first_book.get('id')

            if book_id:
                file_path = download_book(book_id, args.format, args.output)
                if file_path:
                    print(f"\n[SUCCESS] Ready to ingest: {file_path}")
                    print(f"\nNext step:")
                    print(f'  python ingest_books.py --file "{file_path}"')

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
