#!/usr/bin/env python3
"""
Calibre-Web API Connector
==========================

Upload books to Calibre-Web instance (running at alexandria.jedai.space).
This ensures books are properly managed in Calibre library before Qdrant ingestion.

Usage:
    # Upload single book
    python calibre_web_connector.py --upload book.epub --user admin --password xxx

    # Upload from Gutenberg download
    python calibre_web_connector.py --upload gutenberg_downloads/zarathustra.epub

    # Search Calibre-Web catalog
    python calibre_web_connector.py --search "Nietzsche" --user admin --password xxx
"""

import requests
import argparse
from pathlib import Path
from typing import Optional, Dict, List
import json
from urllib.parse import urljoin

# Default Calibre-Web instance
DEFAULT_CALIBRE_WEB_URL = "https://alexandria.jedai.space"


class CalibreWebClient:
    """Client for Calibre-Web REST API."""

    def __init__(self, base_url: str, username: str, password: str):
        """
        Initialize Calibre-Web client.

        Args:
            base_url: Calibre-Web instance URL
            username: Calibre-Web username
            password: Calibre-Web password
        """
        self.base_url = base_url.rstrip('/')
        self.auth = (username, password)
        self.session = requests.Session()
        self.session.auth = self.auth

    def test_connection(self) -> bool:
        """Test connection to Calibre-Web."""
        try:
            response = self.session.get(f"{self.base_url}/opds", timeout=10)
            response.raise_for_status()
            print(f"[OK] Connected to Calibre-Web: {self.base_url}")
            return True
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Failed to connect: {e}")
            return False

    def search_books(self, query: str, limit: int = 20) -> List[Dict]:
        """
        Search books in Calibre-Web catalog.

        Args:
            query: Search query
            limit: Max results

        Returns:
            List of book dictionaries
        """
        # Calibre-Web search endpoint
        url = f"{self.base_url}/opds/search"
        params = {'query': query}

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            # Parse OPDS feed (XML)
            # For simplicity, return raw response
            # TODO: Parse OPDS XML properly
            print(f"[OK] Search completed: {query}")
            return []

        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Search failed: {e}")
            return []

    def upload_book(
        self,
        file_path: str,
        title: Optional[str] = None,
        author: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """
        Upload book to Calibre-Web.

        Args:
            file_path: Path to book file (EPUB, PDF, etc.)
            title: Book title (optional, auto-detected from file)
            author: Book author (optional, auto-detected from metadata)
            tags: List of tags (optional)

        Returns:
            True if successful, False otherwise
        """
        file_path = Path(file_path)

        if not file_path.exists():
            print(f"[ERROR] File not found: {file_path}")
            return False

        # Calibre-Web upload endpoint
        # NOTE: This endpoint may vary depending on Calibre-Web version
        # Common endpoints:
        #   - /admin/book/upload (admin interface)
        #   - /upload (if enabled)
        url = f"{self.base_url}/admin/book/upload"

        print(f"\n[UPLOAD] {file_path.name}")
        print(f"         Size: {file_path.stat().st_size / 1024:.1f} KB")
        print(f"         To: {url}")

        try:
            # Prepare file upload
            with open(file_path, 'rb') as f:
                files = {
                    'btn-upload': (file_path.name, f, self._get_mime_type(file_path))
                }

                # Optional metadata
                data = {}
                if title:
                    data['book_title'] = title
                if author:
                    data['author_name'] = author
                if tags:
                    data['tags'] = ','.join(tags)

                # Upload
                response = self.session.post(
                    url,
                    files=files,
                    data=data,
                    timeout=60
                )

                # Check response
                if response.status_code == 200:
                    print(f"[OK] Upload successful!")
                    return True
                elif response.status_code == 401:
                    print(f"[ERROR] Authentication failed. Check username/password.")
                    return False
                elif response.status_code == 403:
                    print(f"[ERROR] Permission denied. User needs upload permissions.")
                    return False
                else:
                    print(f"[ERROR] Upload failed: HTTP {response.status_code}")
                    print(f"Response: {response.text[:500]}")
                    return False

        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Upload failed: {e}")
            return False

    def _get_mime_type(self, file_path: Path) -> str:
        """Get MIME type for file."""
        ext = file_path.suffix.lower()
        mime_types = {
            '.epub': 'application/epub+zip',
            '.pdf': 'application/pdf',
            '.mobi': 'application/x-mobipocket-ebook',
            '.azw3': 'application/vnd.amazon.ebook',
            '.txt': 'text/plain',
            '.html': 'text/html',
            '.htm': 'text/html',
        }
        return mime_types.get(ext, 'application/octet-stream')

    def get_recent_books(self, limit: int = 20) -> List[Dict]:
        """Get recently added books."""
        # OPDS feed for recent books
        url = f"{self.base_url}/opds"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            print(f"[OK] Retrieved recent books")
            # TODO: Parse OPDS XML
            return []

        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Failed to get recent books: {e}")
            return []


def main():
    parser = argparse.ArgumentParser(description='Calibre-Web API connector')

    # Connection
    parser.add_argument('--url', type=str, default=DEFAULT_CALIBRE_WEB_URL,
                       help=f'Calibre-Web URL (default: {DEFAULT_CALIBRE_WEB_URL})')
    parser.add_argument('--user', '-u', type=str, required=True,
                       help='Calibre-Web username')
    parser.add_argument('--password', '-p', type=str, required=True,
                       help='Calibre-Web password')

    # Actions
    parser.add_argument('--upload', type=str,
                       help='Upload book file to Calibre-Web')
    parser.add_argument('--search', '-s', type=str,
                       help='Search books in catalog')
    parser.add_argument('--test', action='store_true',
                       help='Test connection')

    # Upload metadata (optional)
    parser.add_argument('--title', type=str,
                       help='Book title (for upload)')
    parser.add_argument('--author', type=str,
                       help='Book author (for upload)')
    parser.add_argument('--tags', type=str,
                       help='Book tags, comma-separated (for upload)')

    args = parser.parse_args()

    # Create client
    client = CalibreWebClient(args.url, args.user, args.password)

    # Test connection
    if args.test or not (args.upload or args.search):
        success = client.test_connection()
        if not success:
            print("\n[HELP] Check:")
            print("  1. Is Calibre-Web running?")
            print("  2. Are credentials correct?")
            print("  3. Is user allowed to upload?")
        return

    # Upload
    if args.upload:
        tags = args.tags.split(',') if args.tags else None
        success = client.upload_book(
            args.upload,
            title=args.title,
            author=args.author,
            tags=tags
        )

        if success:
            print(f"\n[SUCCESS] Book uploaded to Calibre-Web!")
            print(f"\nNext steps:")
            print(f"  1. Book is now in Calibre library")
            print(f"  2. Calibre-Web will extract metadata automatically")
            print(f"  3. Ready to ingest to Qdrant:")
            print(f'     python ingest_books.py --file "{args.upload}"')

    # Search
    if args.search:
        results = client.search_books(args.search)
        print(f"Found {len(results)} books")


if __name__ == '__main__':
    main()
