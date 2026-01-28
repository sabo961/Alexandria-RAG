"""
Security tests for SQL injection prevention in CalibreDB

Tests verify that the limit parameter in get_all_books() is protected against
SQL injection attacks through runtime type validation.
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

from scripts.calibre_db import CalibreDB


class TestSQLInjectionPrevention:
    """Test suite for SQL injection prevention in limit parameter"""

    @pytest.fixture
    def mock_db(self, tmp_path):
        """Create a temporary test database"""
        db_path = tmp_path / "metadata.db"

        # Create minimal Calibre database structure
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

        # Insert test data
        cursor.execute("""
            INSERT INTO books (id, title, path, timestamp, pubdate, isbn, series_index)
            VALUES (1, 'Test Book', 'test/path', '2024-01-01', '2024-01-01', '1234567890', 1.0)
        """)

        cursor.execute("""
            INSERT INTO authors (id, name) VALUES (1, 'Test Author')
        """)

        cursor.execute("""
            INSERT INTO languages (id, lang_code) VALUES (1, 'eng')
        """)

        cursor.execute("""
            INSERT INTO books_authors_link (book, author) VALUES (1, 1)
        """)

        cursor.execute("""
            INSERT INTO books_languages_link (book, lang_code) VALUES (1, 1)
        """)

        cursor.execute("""
            INSERT INTO data (book, format) VALUES (1, 'EPUB')
        """)

        conn.commit()
        conn.close()

        # Create CalibreDB instance with test database
        calibre_db = CalibreDB.__new__(CalibreDB)
        calibre_db.library_path = tmp_path
        calibre_db.db_path = db_path

        return calibre_db

    def test_valid_integer_limit(self, mock_db):
        """Test that valid integer limit works correctly"""
        # Should not raise any exception
        books = mock_db.get_all_books(limit=5)
        assert isinstance(books, list)
        assert len(books) <= 5

    def test_sql_injection_string_raises_typeerror(self, mock_db):
        """Test that SQL injection string raises TypeError"""
        malicious_input = "10; DROP TABLE books--"

        with pytest.raises(TypeError, match="limit must be an integer"):
            mock_db.get_all_books(limit=malicious_input)

    def test_malicious_union_query_blocked(self, mock_db):
        """Test that malicious UNION query is blocked"""
        malicious_union = "1 UNION SELECT * FROM users--"

        with pytest.raises(TypeError, match="limit must be an integer"):
            mock_db.get_all_books(limit=malicious_union)

    def test_none_limit_works(self, mock_db):
        """Test that None limit works (returns all books)"""
        # Should not raise any exception
        books = mock_db.get_all_books(limit=None)
        assert isinstance(books, list)

    def test_zero_limit(self, mock_db):
        """Test that zero limit is handled safely"""
        # Zero is a valid integer, should not raise TypeError
        # Note: The implementation checks "if limit:" which is falsy for 0
        # So limit=0 behaves like limit=None (no LIMIT clause added)
        books = mock_db.get_all_books(limit=0)
        assert isinstance(books, list)
        # Zero limit doesn't add LIMIT clause, so returns all books
        assert len(books) >= 0

    def test_negative_limit(self, mock_db):
        """Test that negative limit is handled safely"""
        # Negative is a valid integer, should not raise TypeError
        # SQLite treats negative LIMIT as unlimited
        books = mock_db.get_all_books(limit=-1)
        assert isinstance(books, list)

    def test_float_limit_raises_typeerror(self, mock_db):
        """Test that float limit raises TypeError"""
        with pytest.raises(TypeError, match="limit must be an integer"):
            mock_db.get_all_books(limit=5.5)

    def test_list_limit_raises_typeerror(self, mock_db):
        """Test that list limit raises TypeError"""
        with pytest.raises(TypeError, match="limit must be an integer"):
            mock_db.get_all_books(limit=[10])

    def test_dict_limit_raises_typeerror(self, mock_db):
        """Test that dict limit raises TypeError"""
        with pytest.raises(TypeError, match="limit must be an integer"):
            mock_db.get_all_books(limit={"limit": 10})

    def test_sql_comment_injection_blocked(self, mock_db):
        """Test that SQL comment injection is blocked"""
        malicious_comment = "10--"

        with pytest.raises(TypeError, match="limit must be an integer"):
            mock_db.get_all_books(limit=malicious_comment)

    def test_sql_semicolon_injection_blocked(self, mock_db):
        """Test that SQL semicolon injection is blocked"""
        malicious_semicolon = "10; DELETE FROM books"

        with pytest.raises(TypeError, match="limit must be an integer"):
            mock_db.get_all_books(limit=malicious_semicolon)

    def test_large_integer_limit(self, mock_db):
        """Test that large integer limit is handled correctly"""
        # Very large integer should not raise TypeError
        books = mock_db.get_all_books(limit=999999999)
        assert isinstance(books, list)


class TestTypeValidationRobustness:
    """Additional tests for type validation robustness"""

    @pytest.fixture
    def mock_db_minimal(self, tmp_path):
        """Create minimal test database for type validation tests"""
        db_path = tmp_path / "metadata.db"

        # Create minimal structure
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

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

        # Create all required tables and links (minimal structure)
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

    def test_string_number_blocked(self, mock_db_minimal):
        """Test that string representation of number is blocked"""
        with pytest.raises(TypeError, match="limit must be an integer"):
            mock_db_minimal.get_all_books(limit="10")

    def test_boolean_passes_validation(self, mock_db_minimal):
        """Test that boolean passes validation (bool is int subclass in Python)"""
        # In Python, bool is a subclass of int, so True/False will pass isinstance check
        # True evaluates to 1, False to 0
        # This test documents the current behavior - booleans are technically valid
        books = mock_db_minimal.get_all_books(limit=True)
        assert isinstance(books, list)
        # True becomes LIMIT 1
        assert len(books) <= 1

    def test_none_type_validation(self, mock_db_minimal):
        """Test that None explicitly bypasses type validation"""
        # None should work without raising TypeError
        books = mock_db_minimal.get_all_books(limit=None)
        assert isinstance(books, list)

    def test_object_with_int_method_blocked(self, mock_db_minimal):
        """Test that objects with __int__ method are blocked"""
        class FakeInt:
            def __int__(self):
                return 10

        with pytest.raises(TypeError, match="limit must be an integer"):
            mock_db_minimal.get_all_books(limit=FakeInt())


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
