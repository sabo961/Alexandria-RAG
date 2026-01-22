#!/usr/bin/env python3
"""
Calibre Database Interface

Direct SQLite access to Calibre's metadata.db for rich book metadata.
Provides book information: title, author, language, tags, series, ISBN, etc.

Usage:
    from calibre_db import CalibreDB

    db = CalibreDB("G:\\My Drive\\alexandria")
    books = db.get_all_books()

    # Search
    results = db.search_books(author="Mishima", language="eng")

    # Get book by path
    book = db.get_book_by_path("Mishima, Yukio/Sun and Steel")
"""

import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class CalibreBook:
    """Calibre book metadata"""
    id: int
    title: str
    author: str  # Primary author (multiple authors joined with " & ")
    path: str  # Relative path from library root
    language: str  # ISO language code (eng, hrv, jpn, etc.)
    tags: List[str]
    series: Optional[str]
    series_index: Optional[float]
    isbn: Optional[str]
    publisher: Optional[str]
    pubdate: Optional[str]
    timestamp: str  # Date added to library
    rating: Optional[int]  # 1-10 scale (Calibre uses 2-10, 0=unrated)
    formats: List[str]  # File formats available (.epub, .pdf, etc.)

    def __repr__(self):
        return f"<CalibreBook: {self.title} by {self.author}>"


class CalibreDB:
    """Interface to Calibre metadata.db"""

    def __init__(self, library_path: str = "G:\\My Drive\\alexandria"):
        """
        Initialize connection to Calibre library database.

        Args:
            library_path: Path to Calibre library root (contains metadata.db)
        """
        self.library_path = Path(library_path)
        self.db_path = self.library_path / "metadata.db"

        if not self.db_path.exists():
            raise FileNotFoundError(f"Calibre database not found: {self.db_path}")

        logger.info(f"Connected to Calibre DB: {self.db_path}")

    def _connect(self) -> sqlite3.Connection:
        """Create database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Access columns by name
        return conn

    def get_all_books(self, limit: Optional[int] = None) -> List[CalibreBook]:
        """
        Get all books from Calibre library with full metadata.

        Args:
            limit: Optional limit on number of books to return

        Returns:
            List of CalibreBook objects
        """
        conn = self._connect()
        cursor = conn.cursor()

        # Main query with joins for authors, languages, tags, series
        # Note: GROUP_CONCAT with DISTINCT not supported with custom separator in SQLite
        query = """
        SELECT
            b.id,
            b.title,
            b.path,
            b.timestamp,
            b.pubdate,
            b.isbn,
            b.series_index,
            GROUP_CONCAT(a.name, ' & ') as authors,
            GROUP_CONCAT(l.lang_code, ', ') as languages,
            GROUP_CONCAT(t.name, ', ') as tags,
            s.name as series_name,
            p.name as publisher,
            r.rating
        FROM books b
        LEFT JOIN books_authors_link bal ON b.id = bal.book
        LEFT JOIN authors a ON bal.author = a.id
        LEFT JOIN books_languages_link bll ON b.id = bll.book
        LEFT JOIN languages l ON bll.lang_code = l.id
        LEFT JOIN books_tags_link btl ON b.id = btl.book
        LEFT JOIN tags t ON btl.tag = t.id
        LEFT JOIN books_series_link bsl ON b.id = bsl.book
        LEFT JOIN series s ON bsl.series = s.id
        LEFT JOIN books_publishers_link bpl ON b.id = bpl.book
        LEFT JOIN publishers p ON bpl.publisher = p.id
        LEFT JOIN books_ratings_link brl ON b.id = brl.book
        LEFT JOIN ratings r ON brl.rating = r.id
        GROUP BY b.id
        ORDER BY b.timestamp DESC
        """

        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query)
        rows = cursor.fetchall()

        books = []
        for row in rows:
            # Get available formats for this book
            formats = self._get_book_formats(cursor, row['id'])

            # Parse data
            books.append(CalibreBook(
                id=row['id'],
                title=row['title'] or 'Unknown',
                author=row['authors'] or 'Unknown',
                path=row['path'] or '',
                language=row['languages'].split(',')[0].strip() if row['languages'] else 'unknown',
                tags=row['tags'].split(', ') if row['tags'] else [],
                series=row['series_name'],
                series_index=row['series_index'],
                isbn=row['isbn'],
                publisher=row['publisher'],
                pubdate=row['pubdate'],
                timestamp=row['timestamp'],
                rating=row['rating'],
                formats=formats
            ))

        conn.close()
        logger.info(f"Retrieved {len(books)} books from Calibre DB")
        return books

    def _get_book_formats(self, cursor: sqlite3.Cursor, book_id: int) -> List[str]:
        """Get available file formats for a book"""
        cursor.execute("""
            SELECT format FROM data WHERE book = ?
        """, (book_id,))

        formats = [row['format'].lower() for row in cursor.fetchall()]
        return formats

    def search_books(
        self,
        author: Optional[str] = None,
        title: Optional[str] = None,
        language: Optional[str] = None,
        tags: Optional[List[str]] = None,
        series: Optional[str] = None,
        format: Optional[str] = None
    ) -> List[CalibreBook]:
        """
        Search Calibre library with filters.

        Args:
            author: Author name (partial match, case-insensitive)
            title: Book title (partial match, case-insensitive)
            language: ISO language code (eng, hrv, jpn, etc.)
            tags: List of tag names (must have ALL tags)
            series: Series name (partial match)
            format: File format (epub, pdf, etc.)

        Returns:
            List of matching CalibreBook objects
        """
        # Start with all books
        books = self.get_all_books()

        # Apply filters
        if author:
            author_lower = author.lower()
            books = [b for b in books if author_lower in b.author.lower()]

        if title:
            title_lower = title.lower()
            books = [b for b in books if title_lower in b.title.lower()]

        if language:
            books = [b for b in books if b.language.lower() == language.lower()]

        if tags:
            # Must have ALL specified tags
            for tag in tags:
                tag_lower = tag.lower()
                books = [b for b in books if any(tag_lower in t.lower() for t in b.tags)]

        if series:
            series_lower = series.lower()
            books = [b for b in books if b.series and series_lower in b.series.lower()]

        if format:
            format_lower = format.lower().replace('.', '')
            books = [b for b in books if format_lower in b.formats]

        logger.info(f"Search returned {len(books)} books")
        return books

    def get_book_by_path(self, relative_path: str) -> Optional[CalibreBook]:
        """
        Get book by its relative path in Calibre library.

        Args:
            relative_path: Path relative to library root
                          e.g., "Mishima, Yukio/Sun and Steel (123)"

        Returns:
            CalibreBook object or None if not found
        """
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM books WHERE path = ?", (relative_path,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        # Get full book details
        books = self.get_all_books()
        for book in books:
            if book.id == row['id']:
                return book

        return None

    def get_book_by_id(self, book_id: int) -> Optional[CalibreBook]:
        """Get book by Calibre database ID"""
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM books WHERE id = ?", (book_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        # Get full book details (inefficient but simple - can optimize later)
        books = self.get_all_books()
        for book in books:
            if book.id == book_id:
                return book

        return None

    def match_file_to_book(self, filename: str) -> Optional[CalibreBook]:
        """
        Try to match an ingested file to a Calibre book entry.

        Args:
            filename: Filename like "Sun and Steel - Yukio Mishima.epub"

        Returns:
            Best matching CalibreBook or None

        Strategy:
        1. Extract title and author from filename
        2. Search for fuzzy match in Calibre DB
        3. Return best match or None
        """
        # Simple heuristic: "Title - Author.ext" format
        name = Path(filename).stem  # Remove extension

        if ' - ' in name:
            parts = name.split(' - ', 1)
            title_part = parts[0].strip()
            author_part = parts[1].strip()

            # Search by both title and author
            results = self.search_books(title=title_part, author=author_part)

            if results:
                # Return first match (could improve with fuzzy matching)
                logger.info(f"Matched '{filename}' to Calibre book: {results[0].title}")
                return results[0]

        # Fallback: search by title only
        title_part = name
        results = self.search_books(title=title_part)

        if results:
            logger.info(f"Fuzzy matched '{filename}' to: {results[0].title}")
            return results[0]

        logger.warning(f"Could not match '{filename}' to any Calibre book")
        return None

    def get_available_languages(self) -> List[str]:
        """Get list of all language codes in library"""
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT l.lang_code
            FROM languages l
            JOIN books_languages_link bll ON l.id = bll.lang_code
            ORDER BY l.lang_code
        """)

        languages = [row['lang_code'] for row in cursor.fetchall()]
        conn.close()

        return languages

    def get_available_tags(self) -> List[str]:
        """Get list of all tags in library"""
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT t.name
            FROM tags t
            JOIN books_tags_link btl ON t.id = btl.tag
            ORDER BY t.name
        """)

        tags = [row['name'] for row in cursor.fetchall()]
        conn.close()

        return tags

    def get_available_series(self) -> List[str]:
        """Get list of all series in library"""
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT s.name
            FROM series s
            JOIN books_series_link bsl ON s.id = bsl.series
            ORDER BY s.name
        """)

        series = [row['name'] for row in cursor.fetchall()]
        conn.close()

        return series

    def get_stats(self) -> Dict:
        """Get library statistics"""
        conn = self._connect()
        cursor = conn.cursor()

        # Total books
        cursor.execute("SELECT COUNT(*) as count FROM books")
        total_books = cursor.fetchone()['count']

        # Total authors
        cursor.execute("SELECT COUNT(DISTINCT id) as count FROM authors")
        total_authors = cursor.fetchone()['count']

        # Format distribution
        cursor.execute("""
            SELECT format, COUNT(*) as count
            FROM data
            GROUP BY format
            ORDER BY count DESC
        """)
        format_dist = {row['format']: row['count'] for row in cursor.fetchall()}

        # Language distribution
        cursor.execute("""
            SELECT l.lang_code, COUNT(*) as count
            FROM languages l
            JOIN books_languages_link bll ON l.id = bll.lang_code
            GROUP BY l.lang_code
            ORDER BY count DESC
        """)
        language_dist = {row['lang_code']: row['count'] for row in cursor.fetchall()}

        conn.close()

        return {
            'total_books': total_books,
            'total_authors': total_authors,
            'formats': format_dist,
            'languages': language_dist
        }


# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    """CLI for testing Calibre DB queries"""
    import argparse

    parser = argparse.ArgumentParser(description='Query Calibre database')
    parser.add_argument(
        '--library',
        type=str,
        default='G:\\My Drive\\alexandria',
        help='Path to Calibre library'
    )
    parser.add_argument(
        '--action',
        type=str,
        choices=['stats', 'list', 'search', 'languages', 'tags', 'series'],
        default='stats',
        help='Action to perform'
    )
    parser.add_argument(
        '--author',
        type=str,
        help='Search by author'
    )
    parser.add_argument(
        '--title',
        type=str,
        help='Search by title'
    )
    parser.add_argument(
        '--language',
        type=str,
        help='Filter by language code (eng, hrv, jpn, etc.)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=20,
        help='Limit results (default: 20)'
    )

    args = parser.parse_args()

    # Connect to DB
    db = CalibreDB(args.library)

    if args.action == 'stats':
        stats = db.get_stats()
        print("\n=== Calibre Library Statistics ===")
        print(f"Total Books: {stats['total_books']:,}")
        print(f"Total Authors: {stats['total_authors']:,}")
        print(f"\nFormat Distribution:")
        for fmt, count in sorted(stats['formats'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {fmt:<10} {count:>6,}")
        print(f"\nLanguage Distribution:")
        for lang, count in sorted(stats['languages'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {lang:<5} {count:>6,}")

    elif args.action == 'list':
        books = db.get_all_books(limit=args.limit)
        print(f"\n=== First {len(books)} Books ===")
        for book in books:
            formats = ', '.join(book.formats)
            print(f"\n{book.title}")
            print(f"  Author: {book.author}")
            print(f"  Language: {book.language}")
            print(f"  Formats: {formats}")
            if book.series:
                print(f"  Series: {book.series} #{book.series_index}")

    elif args.action == 'search':
        results = db.search_books(
            author=args.author,
            title=args.title,
            language=args.language
        )
        print(f"\n=== Search Results ({len(results)} books) ===")
        for book in results[:args.limit]:
            print(f"\n{book.title}")
            print(f"  Author: {book.author}")
            print(f"  Language: {book.language}")
            print(f"  Formats: {', '.join(book.formats)}")

    elif args.action == 'languages':
        languages = db.get_available_languages()
        print(f"\n=== Available Languages ({len(languages)}) ===")
        for lang in languages:
            print(f"  {lang}")

    elif args.action == 'tags':
        tags = db.get_available_tags()
        print(f"\n=== Available Tags ({len(tags)}) ===")
        for tag in tags[:args.limit]:
            print(f"  {tag}")

    elif args.action == 'series':
        series = db.get_available_series()
        print(f"\n=== Available Series ({len(series)}) ===")
        for s in series[:args.limit]:
            print(f"  {s}")


if __name__ == '__main__':
    main()
