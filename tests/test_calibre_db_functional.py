"""
Functional tests for CalibreDB get_all_books method

Tests verify that the get_all_books() method works correctly with and without
the limit parameter, respecting the specified limit and returning correct data.
"""

import pytest
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.calibre_db import CalibreDB, CalibreBook


class TestGetAllBooksFunctionality:
    """Test suite for get_all_books() functional behavior"""

    @pytest.fixture
    def mock_db_with_books(self, tmp_path):
        """Create a temporary test database with multiple books"""
        db_path = tmp_path / "metadata.db"

        # Create Calibre database structure
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create essential tables
        cursor.execute("""
            CREATE TABLE books (
                id INTEGER PRIMARY KEY,
                title TEXT,
                path TEXT,
                timestamp TEXT,
                pubdate TEXT,
                isbn TEXT,
                series_index REAL
            )
        """)

        cursor.execute("""
            CREATE TABLE authors (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE languages (
                id INTEGER PRIMARY KEY,
                lang_code TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE tags (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE series (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE publishers (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE ratings (
                id INTEGER PRIMARY KEY,
                rating INTEGER
            )
        """)

        cursor.execute("""
            CREATE TABLE data (
                id INTEGER PRIMARY KEY,
                book INTEGER,
                format TEXT,
                FOREIGN KEY(book) REFERENCES books(id)
            )
        """)

        # Create link tables
        cursor.execute("""
            CREATE TABLE books_authors_link (
                id INTEGER PRIMARY KEY,
                book INTEGER,
                author INTEGER,
                FOREIGN KEY(book) REFERENCES books(id),
                FOREIGN KEY(author) REFERENCES authors(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE books_languages_link (
                id INTEGER PRIMARY KEY,
                book INTEGER,
                lang_code INTEGER,
                FOREIGN KEY(book) REFERENCES books(id),
                FOREIGN KEY(lang_code) REFERENCES languages(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE books_tags_link (
                id INTEGER PRIMARY KEY,
                book INTEGER,
                tag INTEGER,
                FOREIGN KEY(book) REFERENCES books(id),
                FOREIGN KEY(tag) REFERENCES tags(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE books_series_link (
                id INTEGER PRIMARY KEY,
                book INTEGER,
                series INTEGER,
                FOREIGN KEY(book) REFERENCES books(id),
                FOREIGN KEY(series) REFERENCES series(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE books_publishers_link (
                id INTEGER PRIMARY KEY,
                book INTEGER,
                publisher INTEGER,
                FOREIGN KEY(book) REFERENCES books(id),
                FOREIGN KEY(publisher) REFERENCES publishers(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE books_ratings_link (
                id INTEGER PRIMARY KEY,
                book INTEGER,
                rating INTEGER,
                FOREIGN KEY(book) REFERENCES books(id),
                FOREIGN KEY(rating) REFERENCES ratings(id)
            )
        """)

        # Insert test data - create 15 books
        for i in range(1, 16):
            cursor.execute("""
                INSERT INTO books (id, title, path, timestamp, pubdate, isbn, series_index)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (i, f'Test Book {i}', f'test/path/{i}', f'2024-01-{i:02d}', f'2024-01-{i:02d}', f'ISBN{i:010d}', float(i)))

            # Add author
            cursor.execute("""
                INSERT INTO authors (id, name) VALUES (?, ?)
            """, (i, f'Author {i}'))

            # Link book to author
            cursor.execute("""
                INSERT INTO books_authors_link (book, author) VALUES (?, ?)
            """, (i, i))

            # Add language
            if i == 1:
                cursor.execute("""
                    INSERT INTO languages (id, lang_code) VALUES (1, 'eng')
                """)

            # Link book to language
            cursor.execute("""
                INSERT INTO books_languages_link (book, lang_code) VALUES (?, 1)
            """, (i,))

            # Add format
            cursor.execute("""
                INSERT INTO data (book, format) VALUES (?, ?)
            """, (i, 'EPUB'))

        conn.commit()
        conn.close()

        # Create CalibreDB instance with test database
        calibre_db = CalibreDB.__new__(CalibreDB)
        calibre_db.library_path = tmp_path
        calibre_db.db_path = db_path

        return calibre_db

    def test_get_all_books_without_limit(self, mock_db_with_books):
        """Test that get_all_books() without limit returns all books"""
        books = mock_db_with_books.get_all_books()

        assert isinstance(books, list)
        assert len(books) == 15
        assert all(isinstance(book, CalibreBook) for book in books)

    def test_get_all_books_with_limit(self, mock_db_with_books):
        """Test that get_all_books(limit=10) returns at most 10 books"""
        books = mock_db_with_books.get_all_books(limit=10)

        assert isinstance(books, list)
        assert len(books) == 10
        assert all(isinstance(book, CalibreBook) for book in books)

    def test_limit_respects_count_when_fewer_books(self, mock_db_with_books):
        """Test that limit works correctly when there are fewer books than limit"""
        # Request 20 books but only 15 exist
        books = mock_db_with_books.get_all_books(limit=20)

        assert isinstance(books, list)
        assert len(books) == 15
        assert all(isinstance(book, CalibreBook) for book in books)

    def test_limit_of_one(self, mock_db_with_books):
        """Test that limit=1 returns exactly one book"""
        books = mock_db_with_books.get_all_books(limit=1)

        assert isinstance(books, list)
        assert len(books) == 1
        assert isinstance(books[0], CalibreBook)

    def test_limit_of_five(self, mock_db_with_books):
        """Test that limit=5 returns exactly 5 books"""
        books = mock_db_with_books.get_all_books(limit=5)

        assert isinstance(books, list)
        assert len(books) == 5
        assert all(isinstance(book, CalibreBook) for book in books)

    def test_books_have_correct_structure(self, mock_db_with_books):
        """Test that returned books have all expected fields"""
        books = mock_db_with_books.get_all_books(limit=1)

        assert len(books) == 1
        book = books[0]

        # Verify all CalibreBook fields are present
        assert hasattr(book, 'id')
        assert hasattr(book, 'title')
        assert hasattr(book, 'author')
        assert hasattr(book, 'path')
        assert hasattr(book, 'language')
        assert hasattr(book, 'tags')
        assert hasattr(book, 'series')
        assert hasattr(book, 'series_index')
        assert hasattr(book, 'isbn')
        assert hasattr(book, 'publisher')
        assert hasattr(book, 'pubdate')
        assert hasattr(book, 'timestamp')
        assert hasattr(book, 'rating')
        assert hasattr(book, 'formats')

        # Verify types
        assert isinstance(book.id, int)
        assert isinstance(book.title, str)
        assert isinstance(book.author, str)
        assert isinstance(book.path, str)
        assert isinstance(book.language, str)
        assert isinstance(book.tags, list)
        assert isinstance(book.formats, list)

    def test_books_ordered_by_timestamp_desc(self, mock_db_with_books):
        """Test that books are ordered by timestamp in descending order"""
        books = mock_db_with_books.get_all_books()

        # Verify ordering (most recent first)
        # Our test data has timestamps 2024-01-01 through 2024-01-15
        # Descending order means book 15 should be first
        assert books[0].title == 'Test Book 15'
        assert books[-1].title == 'Test Book 1'

    def test_limit_with_ordering(self, mock_db_with_books):
        """Test that limit respects the timestamp ordering"""
        books = mock_db_with_books.get_all_books(limit=3)

        assert len(books) == 3
        # Should get the 3 most recent books (15, 14, 13)
        assert books[0].title == 'Test Book 15'
        assert books[1].title == 'Test Book 14'
        assert books[2].title == 'Test Book 13'

    def test_none_limit_equivalent_to_no_limit(self, mock_db_with_books):
        """Test that limit=None behaves the same as not providing limit"""
        books_no_limit = mock_db_with_books.get_all_books()
        books_none_limit = mock_db_with_books.get_all_books(limit=None)

        assert len(books_no_limit) == len(books_none_limit)
        assert len(books_none_limit) == 15


class TestGetAllBooksEdgeCases:
    """Test edge cases for get_all_books"""

    @pytest.fixture
    def empty_db(self, tmp_path):
        """Create a temporary test database with no books"""
        db_path = tmp_path / "metadata.db"

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create structure but no data
        cursor.execute("""
            CREATE TABLE books (
                id INTEGER PRIMARY KEY,
                title TEXT,
                path TEXT,
                timestamp TEXT,
                pubdate TEXT,
                isbn TEXT,
                series_index REAL
            )
        """)

        # Create all required tables
        for table in ['authors', 'languages', 'tags', 'series', 'publishers', 'ratings', 'data']:
            if table == 'data':
                cursor.execute(f"CREATE TABLE {table} (id INTEGER PRIMARY KEY, book INTEGER, format TEXT)")
            elif table == 'languages':
                cursor.execute(f"CREATE TABLE {table} (id INTEGER PRIMARY KEY, lang_code TEXT)")
            elif table == 'ratings':
                cursor.execute(f"CREATE TABLE {table} (id INTEGER PRIMARY KEY, rating INTEGER)")
            else:
                cursor.execute(f"CREATE TABLE {table} (id INTEGER PRIMARY KEY, name TEXT)")

        for link_table in ['books_authors_link', 'books_languages_link', 'books_tags_link',
                           'books_series_link', 'books_publishers_link', 'books_ratings_link']:
            cursor.execute(f"""
                CREATE TABLE {link_table} (
                    id INTEGER PRIMARY KEY,
                    book INTEGER,
                    {'author' if 'author' in link_table else 'lang_code' if 'language' in link_table else
                     'tag' if 'tag' in link_table else 'series' if 'series' in link_table else
                     'publisher' if 'publisher' in link_table else 'rating'} INTEGER
                )
            """)

        conn.commit()
        conn.close()

        calibre_db = CalibreDB.__new__(CalibreDB)
        calibre_db.library_path = tmp_path
        calibre_db.db_path = db_path

        return calibre_db

    def test_empty_database_returns_empty_list(self, empty_db):
        """Test that empty database returns empty list"""
        books = empty_db.get_all_books()

        assert isinstance(books, list)
        assert len(books) == 0

    def test_empty_database_with_limit_returns_empty_list(self, empty_db):
        """Test that empty database with limit returns empty list"""
        books = empty_db.get_all_books(limit=10)

        assert isinstance(books, list)
        assert len(books) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
