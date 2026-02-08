#!/usr/bin/env python3
"""
Internet Archive Connector for Alexandria
==========================================

Search and download public domain books from Internet Archive.
Critical for PRIORITY ZERO: Russian literature, 20th century philosophy,
rare languages not available on Gutenberg.

API: https://archive.org/services/docs/api/

Usage:
    # Search for Dostoevsky in Russian
    python archive_connector.py --search "Dostoevsky" --language rus

    # Search for Heidegger in German
    python archive_connector.py --search "Heidegger" --language ger

    # Download book by identifier
    python archive_connector.py --download "crimeandpunishme00dostuoft" --format pdf

    # Search and download first match
    python archive_connector.py --search "Crime and Punishment" --language rus --auto-download
"""

import requests
import argparse
import json
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urlencode, quote

# Internet Archive API endpoints
ARCHIVE_SEARCH_API = "https://archive.org/advancedsearch.php"
ARCHIVE_METADATA_API = "https://archive.org/metadata"
ARCHIVE_DOWNLOAD_BASE = "https://archive.org/download"

# Language codes mapping (ISO 639-2/B codes used by Archive)
LANGUAGE_CODES = {
    'en': 'eng',      # English
    'de': 'ger',      # German
    'fr': 'fre',      # French
    'ru': 'rus',      # Russian
    'el': 'gre',      # Greek
    'la': 'lat',      # Latin
    'hr': 'hrv',      # Croatian
    'sr': 'srp',      # Serbian
    'es': 'spa',      # Spanish
    'it': 'ita',      # Italian
    'pt': 'por',      # Portuguese
    'nl': 'dut',      # Dutch
    'pl': 'pol',      # Polish
    'cs': 'cze',      # Czech
    'zh': 'chi',      # Chinese
    'ja': 'jpn',      # Japanese
    'sa': 'san',      # Sanskrit
    'ar': 'ara',      # Arabic
}

LANGUAGE_NAMES = {
    'eng': 'English',
    'ger': 'German',
    'fre': 'French',
    'rus': 'Russian',
    'gre': 'Ancient Greek',
    'lat': 'Latin',
    'hrv': 'Croatian',
    'srp': 'Serbian',
    'spa': 'Spanish',
    'ita': 'Italian',
    'por': 'Portuguese',
    'dut': 'Dutch',
    'pol': 'Polish',
    'cze': 'Czech',
    'chi': 'Chinese',
    'jpn': 'Japanese',
    'san': 'Sanskrit',
    'ara': 'Arabic',
}


def search_books(
    query: Optional[str] = None,
    creator: Optional[str] = None,
    title: Optional[str] = None,
    language: Optional[str] = None,
    subject: Optional[str] = None,
    limit: int = 20,
    sort_by: str = 'downloads'
) -> List[Dict]:
    """
    Search Internet Archive for books.

    Args:
        query: General search query
        creator: Author/creator name
        title: Book title
        language: ISO 639-2 language code (eng, ger, rus, etc.)
        subject: Subject/topic
        limit: Max results to return
        sort_by: Sort field (downloads, date, relevance)

    Returns:
        List of book dictionaries
    """
    # Build search query
    search_parts = ['mediatype:texts']

    if query:
        search_parts.append(f'({query})')
    if creator:
        search_parts.append(f'creator:"{creator}"')
    if title:
        search_parts.append(f'title:"{title}"')
    if language:
        # Convert 2-letter code to 3-letter if needed
        lang_code = LANGUAGE_CODES.get(language, language)
        search_parts.append(f'language:{lang_code}')
    if subject:
        search_parts.append(f'subject:"{subject}"')

    search_query = ' AND '.join(search_parts)

    # API parameters
    params = {
        'q': search_query,
        'fl[]': ['identifier', 'title', 'creator', 'language', 'subject',
                 'downloads', 'avg_rating', 'num_reviews', 'date', 'format'],
        'rows': limit,
        'page': 1,
        'output': 'json',
        'sort[]': f'{sort_by} desc'
    }

    print(f"Searching Archive.org: {search_query}")

    try:
        response = requests.get(ARCHIVE_SEARCH_API, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        docs = data.get('response', {}).get('docs', [])
        total = data.get('response', {}).get('numFound', 0)

        print(f"Found {len(docs)} books (total available: {total:,})")

        return docs

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to search Archive.org: {e}")
        return []


def get_book_metadata(identifier: str) -> Optional[Dict]:
    """
    Get detailed metadata for a specific book.

    Args:
        identifier: Archive.org item identifier

    Returns:
        Book metadata dictionary or None
    """
    url = f"{ARCHIVE_METADATA_API}/{identifier}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to get metadata: {e}")
        return None


def get_download_url(identifier: str, format: str = 'pdf') -> Optional[str]:
    """
    Get download URL for a book file.

    Args:
        identifier: Archive.org item identifier
        format: Desired format (pdf, epub, djvu, txt, etc.)

    Returns:
        Download URL or None
    """
    # Get metadata to find available files
    metadata = get_book_metadata(identifier)

    if not metadata:
        return None

    files = metadata.get('files', [])

    # Try to find requested format
    format_lower = format.lower()

    # Prefer non-derived versions
    for file in files:
        name = file.get('name', '').lower()
        file_format = file.get('format', '').lower()

        if format_lower in name or format_lower in file_format:
            # Avoid derived/metadata files
            if 'meta.xml' not in name and 'marc.xml' not in name and '_files.xml' not in name:
                return f"{ARCHIVE_DOWNLOAD_BASE}/{identifier}/{file.get('name')}"

    # If not found, try format field
    for file in files:
        file_format = file.get('format', '').lower()
        if format_lower in file_format.replace(' ', ''):
            return f"{ARCHIVE_DOWNLOAD_BASE}/{identifier}/{file.get('name')}"

    return None


def download_book(
    identifier: str,
    format: str = 'pdf',
    output_dir: str = './archive_downloads'
) -> Optional[str]:
    """
    Download book from Internet Archive.

    Args:
        identifier: Archive.org item identifier
        format: Format to download (pdf, epub, djvu, txt)
        output_dir: Directory to save downloaded file

    Returns:
        Path to downloaded file or None
    """
    # Get metadata first
    metadata = get_book_metadata(identifier)

    if not metadata:
        print(f"[ERROR] Could not get metadata for {identifier}")
        return None

    # Extract book info
    meta = metadata.get('metadata', {})
    title = meta.get('title', 'Unknown')
    if isinstance(title, list):
        title = title[0]
    title = str(title).replace('/', '-')[:100]

    creator = meta.get('creator', 'Unknown')
    if isinstance(creator, list):
        creator = creator[0] if creator else 'Unknown'
    creator = str(creator).replace('/', '-')[:50]

    # Get download URL
    download_url = get_download_url(identifier, format)

    if not download_url:
        print(f"[ERROR] Format '{format}' not available for {identifier}")
        available_formats = set()
        for file in metadata.get('files', []):
            fmt = file.get('format', '')
            if fmt and 'meta' not in fmt.lower():
                available_formats.add(fmt)
        print(f"Available formats: {', '.join(sorted(available_formats))}")
        return None

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Build filename
    # Extract extension from download URL
    file_ext = Path(download_url).suffix or f'.{format}'
    filename = f"{title} - {creator}{file_ext}"
    file_path = output_path / filename

    print(f"\n[DOWNLOAD] {title}")
    print(f"           by {creator}")
    print(f"           URL: {download_url}")
    print(f"           Saving to: {file_path}")

    try:
        response = requests.get(download_url, timeout=60, stream=True)
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
    identifier = book.get('identifier', 'Unknown')
    title = book.get('title', 'Unknown')

    # Handle creator (can be string or list)
    creator = book.get('creator', 'Unknown')
    if isinstance(creator, list):
        creator = ', '.join(creator)

    # Handle language (can be string or list)
    language = book.get('language', ['unknown'])
    if isinstance(language, str):
        language = [language]
    language_str = ', '.join(language)
    language_name = LANGUAGE_NAMES.get(language[0], 'Unknown') if language else 'Unknown'

    downloads = book.get('downloads', 0)
    avg_rating = book.get('avg_rating', 0)
    num_reviews = book.get('num_reviews', 0)

    # Handle subject (can be string or list)
    subject = book.get('subject', [])
    if isinstance(subject, str):
        subject = [subject]
    subjects = subject[:3] if isinstance(subject, list) else []

    # Handle format (can be string or list)
    formats = book.get('format', [])
    if isinstance(formats, str):
        formats = [formats]

    prefix = f"[{index}] " if index is not None else ""

    # Safe print function that handles encoding errors
    def safe_print(text):
        try:
            print(text)
        except UnicodeEncodeError:
            # Fallback: encode to ASCII with replacement
            safe_text = text.encode('ascii', errors='replace').decode('ascii')
            print(safe_text)

    safe_print(f"\n{prefix}ID: {identifier}")
    safe_print(f"    Title: {title}")
    safe_print(f"    Creator: {creator}")
    safe_print(f"    Language: {language_str} ({language_name})")
    safe_print(f"    Downloads: {downloads:,}")

    if avg_rating:
        safe_print(f"    Rating: {avg_rating:.1f}/5.0 ({num_reviews} reviews)")

    if subjects:
        safe_print(f"    Subjects: {', '.join(subjects)}")

    # Show available formats
    if formats:
        # Filter out metadata formats
        book_formats = [f for f in formats if 'meta' not in f.lower() and 'marc' not in f.lower()]
        if book_formats:
            safe_print(f"    Formats: {', '.join(book_formats[:5])}")


def main():
    parser = argparse.ArgumentParser(
        description='Internet Archive connector for Alexandria',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Search parameters
    parser.add_argument('--search', '-s', type=str,
                       help='Search query (author, title, etc.)')
    parser.add_argument('--creator', '-c', type=str,
                       help='Search by creator/author name')
    parser.add_argument('--title', '-t', type=str,
                       help='Search by title')
    parser.add_argument('--language', '-l', type=str,
                       help='Language code (en, de, ru, el, la, etc.) or ISO 639-2 (eng, ger, rus)')
    parser.add_argument('--subject', type=str,
                       help='Subject/topic')
    parser.add_argument('--limit', type=int, default=20,
                       help='Max results (default: 20)')
    parser.add_argument('--sort', type=str, default='downloads',
                       choices=['downloads', 'date', 'relevance'],
                       help='Sort by (default: downloads)')

    # Download parameters
    parser.add_argument('--download', '-d', type=str,
                       help='Download book by identifier')
    parser.add_argument('--format', '-f', type=str, default='pdf',
                       help='Download format (pdf, epub, djvu, txt) (default: pdf)')
    parser.add_argument('--output', '-o', type=str, default='./archive_downloads',
                       help='Output directory (default: ./archive_downloads)')

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
    if args.search or args.creator or args.title:
        books = search_books(
            query=args.search,
            creator=args.creator,
            title=args.title,
            language=args.language,
            subject=args.subject,
            limit=args.limit,
            sort_by=args.sort
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
            identifier = first_book.get('identifier')

            if identifier:
                file_path = download_book(identifier, args.format, args.output)
                if file_path:
                    print(f"\n[SUCCESS] Ready to ingest: {file_path}")
                    print(f"\nNext step:")
                    print(f'  python ingest_books.py --file "{file_path}"')

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
