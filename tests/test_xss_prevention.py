"""
Security tests for XSS prevention in Alexandria App

Tests verify that XSS attack vectors are blocked in real-world application
scenarios including AI-generated content, book metadata, search results,
and pagination displays.
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.html_sanitizer import sanitize_html, is_safe_html


class TestXSSPreventionInAIContent:
    """Test suite for XSS prevention in AI-generated content"""

    def test_script_tag_in_ai_answer(self):
        """Test that script tags in AI answers are sanitized"""
        malicious_answer = "The answer is: <script>alert('xss')</script> helpful!"

        # Simulate AI answer sanitization (line 1185 in alexandria_app.py)
        sanitized = sanitize_html(malicious_answer)

        # Verify script tag is escaped, not executed
        assert "<script>" not in sanitized
        assert "&lt;script&gt;" in sanitized
        assert is_safe_html(malicious_answer) is False

    def test_event_handler_in_ai_answer(self):
        """Test that event handlers in AI answers are sanitized"""
        malicious_answer = 'Click <img src="x" onerror="alert(1)"> here'

        sanitized = sanitize_html(malicious_answer)

        # Verify HTML tag is escaped (making event handler safe)
        assert '&lt;img' in sanitized  # Tag is escaped
        assert '<img' not in sanitized  # Raw tag removed

    def test_javascript_url_in_ai_answer(self):
        """Test that javascript: URLs in AI answers are sanitized"""
        malicious_answer = '<a href="javascript:alert(\'xss\')">Click me</a>'

        sanitized = sanitize_html(malicious_answer)

        # Verify HTML tag is escaped (making javascript: URL safe)
        assert '&lt;a' in sanitized  # Tag is escaped
        assert '<a href=' not in sanitized  # Raw tag removed

    def test_iframe_in_ai_answer(self):
        """Test that iframe tags in AI answers are sanitized"""
        malicious_answer = 'Check this: <iframe src="evil.com"></iframe>'

        sanitized = sanitize_html(malicious_answer)

        # Verify iframe is escaped
        assert "<iframe>" not in sanitized
        assert "&lt;iframe" in sanitized

    def test_data_url_in_ai_answer(self):
        """Test that data: URLs in AI answers are sanitized"""
        malicious_answer = '<img src="data:text/html,<script>alert(1)</script>">'

        sanitized = sanitize_html(malicious_answer)

        # Verify data: URL is escaped
        assert "data:text/html" not in sanitized or "&lt;" in sanitized
        assert "<img" not in sanitized

    def test_safe_ai_answer(self):
        """Test that safe AI answers pass through correctly"""
        safe_answer = "The answer is 42. This is helpful information."

        sanitized = sanitize_html(safe_answer)

        # Verify safe content is unchanged
        assert sanitized == safe_answer
        assert is_safe_html(safe_answer) is True


class TestXSSPreventionInBookMetadata:
    """Test suite for XSS prevention in book titles and metadata"""

    def test_script_tag_in_book_title(self):
        """Test that script tags in book titles are sanitized"""
        # Simulate malicious book title (line 1198 in alexandria_app.py)
        malicious_title = "My Book <script>steal()</script>"

        sanitized = sanitize_html(malicious_title)

        assert "<script>" not in sanitized
        assert "&lt;script&gt;" in sanitized

    def test_event_handler_in_author_name(self):
        """Test that event handlers in author names are sanitized"""
        # Simulate malicious author name (line 1200 in alexandria_app.py)
        malicious_author = 'John <img onerror="alert(1)" src="x"> Doe'

        sanitized = sanitize_html(malicious_author)

        # HTML should be escaped, making the event handler safe
        assert '<img' not in sanitized or '&lt;img' in sanitized
        assert '&quot;' in sanitized  # Quotes are escaped

    def test_javascript_url_in_domain(self):
        """Test that javascript: URLs in domains are sanitized"""
        # Simulate malicious domain (line 1201 in alexandria_app.py)
        malicious_domain = '<a href="javascript:hack()">Domain</a>'

        sanitized = sanitize_html(malicious_domain)

        # HTML should be escaped, making javascript: URL safe
        assert '<a href=' not in sanitized or '&lt;a' in sanitized
        assert '&quot;' in sanitized  # Quotes are escaped

    def test_iframe_in_section_name(self):
        """Test that iframe tags in section names are sanitized"""
        # Simulate malicious section name (line 1202 in alexandria_app.py)
        malicious_section = 'Chapter 1<iframe src="evil.com"></iframe>'

        sanitized = sanitize_html(malicious_section)

        assert "<iframe>" not in sanitized
        assert "&lt;iframe" in sanitized

    def test_safe_book_metadata(self):
        """Test that safe book metadata passes through correctly"""
        safe_title = "Clean Code: A Handbook of Agile Software Craftsmanship"
        safe_author = "Robert C. Martin"
        safe_domain = "Software Engineering"
        safe_section = "Chapter 1: Clean Code"

        assert sanitize_html(safe_title) == safe_title
        assert sanitize_html(safe_author) == safe_author
        assert sanitize_html(safe_domain) == safe_domain
        assert sanitize_html(safe_section) == safe_section

        assert is_safe_html(safe_title) is True
        assert is_safe_html(safe_author) is True
        assert is_safe_html(safe_domain) is True
        assert is_safe_html(safe_section) is True


class TestXSSPreventionInPagination:
    """Test suite for XSS prevention in pagination displays"""

    def test_script_in_page_number(self):
        """Test that script tags in page numbers are sanitized"""
        # Simulate malicious page number (line 1764 in alexandria_app.py)
        malicious_page = "<script>alert(1)</script>1"

        sanitized = sanitize_html(malicious_page)

        assert "<script>" not in sanitized
        assert "&lt;script&gt;" in sanitized

    def test_event_handler_in_total_pages(self):
        """Test that event handlers in total pages are sanitized"""
        malicious_total = '<img src="x" onerror="steal()">10'

        sanitized = sanitize_html(malicious_total)

        # Verify HTML tag is escaped (making event handler safe)
        assert '&lt;img' in sanitized  # Tag is escaped
        assert '<img' not in sanitized  # Raw tag removed

    def test_javascript_url_in_total_books(self):
        """Test that javascript: URLs in total books are sanitized"""
        malicious_total_books = '<a href="javascript:hack()">487</a>'

        sanitized = sanitize_html(malicious_total_books)

        # Verify HTML tag is escaped (making javascript: URL safe)
        assert '&lt;a' in sanitized  # Tag is escaped
        assert '<a href=' not in sanitized  # Raw tag removed

    def test_numeric_pagination_values(self):
        """Test that numeric pagination values are sanitized safely"""
        # Simulate numeric values being sanitized (lines 1764, 1924)
        # In real usage, numbers are ALWAYS converted to strings first
        current_page = 2
        total_pages = 10
        total_books = 487
        start_idx = 50
        end_idx = 100

        # These should convert to string safely
        assert sanitize_html(str(current_page)) == "2"
        assert sanitize_html(str(total_pages)) == "10"
        assert sanitize_html(f'{total_books:,}') == "487"
        assert sanitize_html(str(start_idx + 1)) == "51"
        assert sanitize_html(str(end_idx)) == "100"

    def test_safe_pagination_display(self):
        """Test that safe pagination text is unchanged"""
        safe_page_info = "Page 2 of 10 (487 total)"

        sanitized = sanitize_html(safe_page_info)

        assert sanitized == safe_page_info
        assert is_safe_html(safe_page_info) is True


class TestXSSPreventionInSearchResults:
    """Test suite for XSS prevention in search results and expanders"""

    def test_script_in_search_result_expander(self):
        """Test that script tags in search result expanders are sanitized"""
        # Simulate malicious book title in expander (line 1198)
        malicious_source = {
            'book_title': '<script>alert("xss")</script>Malicious Book',
            'score': 0.95
        }

        sanitized_title = sanitize_html(malicious_source['book_title'])

        assert "<script>" not in sanitized_title
        assert "&lt;script&gt;" in sanitized_title

    def test_event_handler_in_search_metadata(self):
        """Test that event handlers in search metadata are sanitized"""
        malicious_source = {
            'book_title': 'Normal Book',
            'author': '<img onerror="hack()" src="x">Evil Author',
            'domain': 'Safe Domain',
            'section_name': 'Chapter 1',
            'score': 0.85
        }

        sanitized_author = sanitize_html(malicious_source['author'])

        # HTML should be escaped
        assert '<img' not in sanitized_author or '&lt;img' in sanitized_author
        assert '&quot;' in sanitized_author

    def test_multiple_xss_vectors_in_single_source(self):
        """Test that multiple XSS vectors in one source are all sanitized"""
        malicious_source = {
            'book_title': '<script>alert(1)</script>Book',
            'author': '<img onerror="alert(2)" src="x">Author',
            'domain': '<iframe src="evil.com"></iframe>Domain',
            'section_name': '<a href="javascript:alert(3)">Section</a>',
            'score': 0.90
        }

        sanitized_title = sanitize_html(malicious_source['book_title'])
        sanitized_author = sanitize_html(malicious_source['author'])
        sanitized_domain = sanitize_html(malicious_source['domain'])
        sanitized_section = sanitize_html(malicious_source['section_name'])

        # Verify all are sanitized (HTML tags escaped)
        assert "<script>" not in sanitized_title
        assert '<img' not in sanitized_author or '&lt;img' in sanitized_author
        assert "<iframe>" not in sanitized_domain
        assert '<a href=' not in sanitized_section or '&lt;a' in sanitized_section

    def test_safe_search_results(self):
        """Test that safe search results pass through correctly"""
        safe_source = {
            'book_title': 'The Pragmatic Programmer',
            'author': 'Andrew Hunt and David Thomas',  # No & to avoid HTML escaping
            'domain': 'Software Development',
            'section_name': 'Chapter 2: A Pragmatic Approach',
            'score': 0.92
        }

        assert sanitize_html(safe_source['book_title']) == safe_source['book_title']
        assert sanitize_html(safe_source['author']) == safe_source['author']
        assert sanitize_html(safe_source['domain']) == safe_source['domain']
        assert sanitize_html(safe_source['section_name']) == safe_source['section_name']


class TestXSSPreventionEdgeCases:
    """Test suite for edge cases and complex attack vectors"""

    def test_nested_tags(self):
        """Test that nested malicious tags are sanitized"""
        nested_attack = '<div><script><iframe>alert(1)</iframe></script></div>'

        sanitized = sanitize_html(nested_attack)

        assert "<div>" not in sanitized
        assert "<script>" not in sanitized
        assert "<iframe>" not in sanitized
        assert "&lt;" in sanitized

    def test_case_variation_attacks(self):
        """Test that case variations are sanitized"""
        case_attacks = [
            '<ScRiPt>alert(1)</ScRiPt>',
            '<IFRAME SRC="evil.com"></IFRAME>',
            '<IMG oNeRrOr="alert(1)" src="x">',
        ]

        for attack in case_attacks:
            sanitized = sanitize_html(attack)
            assert "&lt;" in sanitized
            assert "&gt;" in sanitized

    def test_whitespace_obfuscation(self):
        """Test that whitespace-obfuscated attacks are sanitized"""
        whitespace_attacks = [
            '<script >alert(1)</script>',
            '<script\n>alert(1)</script>',
            '<script\t>alert(1)</script>',
        ]

        for attack in whitespace_attacks:
            sanitized = sanitize_html(attack)
            assert "<script" not in sanitized
            assert "&lt;script" in sanitized

    def test_unicode_and_special_chars(self):
        """Test that unicode and special characters are handled safely"""
        special_content = [
            "Book with émojis 🎉 and ünïcödé",
            "Title with &nbsp; entities",
            "Content with 中文字符",
        ]

        for content in special_content:
            sanitized = sanitize_html(content)
            # Should handle unicode safely without breaking
            assert isinstance(sanitized, str)

    def test_long_attack_payloads(self):
        """Test that long attack payloads are sanitized"""
        long_attack = '<script>' + 'a' * 10000 + '</script>'

        sanitized = sanitize_html(long_attack)

        assert "<script>" not in sanitized
        assert "&lt;script&gt;" in sanitized
        assert len(sanitized) > len(long_attack)  # Escaped version is longer

    def test_empty_and_none_inputs(self):
        """Test that empty and None inputs are handled safely"""
        assert sanitize_html("") == ""
        assert sanitize_html(None) == ""
        assert is_safe_html("") is True
        assert is_safe_html(None) is True

    def test_numeric_inputs(self):
        """Test that numeric inputs are converted safely"""
        # In real usage, numbers are converted to strings first (see alexandria_app.py)
        numeric_inputs = [0, 1, 42, -1, 3.14, 999999]

        for num in numeric_inputs:
            sanitized = sanitize_html(str(num))
            assert sanitized == str(num)


class TestXSSPreventionRealWorldScenarios:
    """Test suite for real-world Alexandria attack scenarios"""

    def test_malicious_book_title_from_calibre(self):
        """Test XSS prevention for malicious book title from Calibre DB"""
        # Scenario: Attacker adds book with malicious title to Calibre library
        malicious_book = {
            'title': 'Hacking Guide <script>sendData(document.cookie)</script>',
            'author': 'Normal Author',
            'path': 'books/hack_guide'
        }

        sanitized_title = sanitize_html(malicious_book['title'])

        # Verify XSS is blocked (HTML is escaped)
        assert "<script>" not in sanitized_title
        assert "&lt;script&gt;" in sanitized_title

    def test_crafted_search_query_with_xss(self):
        """Test XSS prevention in search query results"""
        # Scenario: Attacker crafts search query with XSS payload
        malicious_query = '<img src=x onerror="alert(document.domain)">'

        sanitized_query = sanitize_html(malicious_query)

        # Verify HTML tag is escaped (making event handler safe)
        assert '&lt;img' in sanitized_query  # Tag is escaped
        assert '<img' not in sanitized_query  # Raw tag removed

    def test_ai_generated_content_with_injected_html(self):
        """Test XSS prevention in AI-generated RAG answers"""
        # Scenario: RAG system retrieves content with HTML injection
        ai_answer_with_html = """
        Based on the documentation, here's the answer:
        <iframe src="javascript:alert('xss')"></iframe>
        The solution is to use proper validation.
        """

        sanitized_answer = sanitize_html(ai_answer_with_html)

        # Verify HTML tag is escaped (making iframe safe)
        assert "<iframe>" not in sanitized_answer  # Raw tag removed
        assert "&lt;iframe" in sanitized_answer  # Tag is escaped
        assert '<iframe src=' not in sanitized_answer  # Raw tag removed

    def test_metadata_injection_attack(self):
        """Test XSS prevention in book metadata fields"""
        # Scenario: Attacker injects XSS into multiple metadata fields
        malicious_metadata = {
            'title': 'Book<script>alert(1)</script>',
            'author': 'Author<img src=x onerror=alert(2)>',
            'domain': 'Domain<iframe src="evil.com">',
            'section': 'Chapter<a href="javascript:alert(3)">1</a>',
        }

        sanitized = {
            key: sanitize_html(value)
            for key, value in malicious_metadata.items()
        }

        # Verify all XSS vectors are blocked (HTML is escaped)
        assert "<script>" not in sanitized['title']
        assert '<img' not in sanitized['author'] or '&lt;img' in sanitized['author']
        assert "<iframe>" not in sanitized['domain']
        assert '<a href=' not in sanitized['section'] or '&lt;a' in sanitized['section']

    def test_pagination_parameter_manipulation(self):
        """Test XSS prevention when pagination parameters are manipulated"""
        # Scenario: Attacker manipulates URL parameters for pagination
        manipulated_params = {
            'page': '<script>alert("page")</script>1',
            'total': '<img src=x onerror=alert(1)>10',
            'limit': '<iframe>50</iframe>'
        }

        sanitized_params = {
            key: sanitize_html(value)
            for key, value in manipulated_params.items()
        }

        # Verify XSS is blocked in all parameters (HTML is escaped)
        for value in sanitized_params.values():
            assert "<script>" not in value or "&lt;script&gt;" in value
            assert '<img src=' not in value or '&lt;img' in value
            assert "<iframe>" not in value or "&lt;iframe&gt;" in value
            assert "&lt;" in value


class TestXSSPreventionPerformance:
    """Test suite for sanitization performance with large datasets"""

    def test_sanitize_large_batch_of_books(self):
        """Test that sanitizing many books is performant"""
        import time

        # Simulate sanitizing 1000 book titles
        book_titles = [f"Book Title {i}" for i in range(1000)]

        start_time = time.time()
        sanitized_titles = [sanitize_html(title) for title in book_titles]
        elapsed_time = time.time() - start_time

        # Should complete in reasonable time (< 1 second for 1000 titles)
        assert elapsed_time < 1.0
        assert len(sanitized_titles) == 1000

    def test_sanitize_large_text_content(self):
        """Test that sanitizing large text blocks is performant"""
        import time

        # Simulate large AI-generated answer
        large_text = "This is a safe answer. " * 1000  # ~24KB

        start_time = time.time()
        sanitized = sanitize_html(large_text)
        elapsed_time = time.time() - start_time

        # Should complete quickly (< 0.1 seconds)
        assert elapsed_time < 0.1
        assert len(sanitized) == len(large_text)

    def test_detect_xss_in_large_dataset(self):
        """Test that XSS detection works efficiently on large datasets"""
        import time

        # Mix of safe and malicious content
        test_data = [
            "Safe content" if i % 10 != 0 else "<script>alert(1)</script>"
            for i in range(1000)
        ]

        start_time = time.time()
        results = [is_safe_html(content) for content in test_data]
        elapsed_time = time.time() - start_time

        # Should complete in reasonable time
        assert elapsed_time < 1.0

        # Should detect 100 malicious items (every 10th)
        unsafe_count = sum(1 for r in results if not r)
        assert unsafe_count == 100


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
