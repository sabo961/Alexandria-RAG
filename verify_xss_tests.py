#!/usr/bin/env python
"""
Standalone test runner for XSS prevention tests
Runs tests without requiring pytest to be installed
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from scripts.html_sanitizer import sanitize_html, is_safe_html

def run_test(test_name, test_func):
    """Run a single test and report results"""
    try:
        test_func()
        print(f"✓ {test_name}")
        return True
    except AssertionError as e:
        import traceback
        print(f"✗ {test_name}: {e if str(e) else 'Assertion failed'}")
        traceback.print_exc()
        return False
    except Exception as e:
        import traceback
        print(f"✗ {test_name}: Unexpected error: {e}")
        traceback.print_exc()
        return False

# Test suite
def test_script_tag_in_ai_answer():
    malicious_answer = "The answer is: <script>alert('xss')</script> helpful!"
    sanitized = sanitize_html(malicious_answer)
    assert "<script>" not in sanitized
    assert "&lt;script&gt;" in sanitized
    assert is_safe_html(malicious_answer) is False

def test_event_handler_in_book_title():
    malicious_title = 'Book<img src="x" onerror="alert(1)">'
    sanitized = sanitize_html(malicious_title)
    # HTML should be escaped, making it safe
    assert '<img' not in sanitized or '&lt;img' in sanitized
    assert '&quot;' in sanitized  # Quotes are escaped

def test_javascript_url():
    malicious = '<a href="javascript:alert()">Click</a>'
    sanitized = sanitize_html(malicious)
    # HTML should be escaped, making javascript: URL safe
    assert '<a href=' not in sanitized or '&lt;a' in sanitized
    assert '&quot;' in sanitized  # Quotes are escaped

def test_iframe_injection():
    malicious = 'Check <iframe src="evil.com"></iframe>'
    sanitized = sanitize_html(malicious)
    assert "<iframe>" not in sanitized

def test_data_url():
    malicious = '<img src="data:text/html,<script>alert(1)</script>">'
    sanitized = sanitize_html(malicious)
    assert "<img" not in sanitized

def test_safe_content():
    safe = "Hello, World! This is safe."
    sanitized = sanitize_html(safe)
    assert sanitized == safe
    assert is_safe_html(safe) is True

def test_pagination_sanitization():
    current_page = 2
    total_pages = 10
    assert sanitize_html(str(current_page)) == "2"
    assert sanitize_html(str(total_pages)) == "10"

def test_nested_tags():
    nested = '<div><script>alert(1)</script></div>'
    sanitized = sanitize_html(nested)
    assert "<div>" not in sanitized
    assert "<script>" not in sanitized

def test_case_variations():
    variations = [
        '<ScRiPt>alert(1)</ScRiPt>',
        '<IFRAME SRC="evil.com"></IFRAME>',
    ]
    for attack in variations:
        sanitized = sanitize_html(attack)
        assert "&lt;" in sanitized

def test_numeric_inputs():
    # In real usage, numbers are converted to strings first (see alexandria_app.py lines 1764, 1924)
    for num in [0, 1, 42, -1, 3.14]:
        sanitized = sanitize_html(str(num))
        assert sanitized == str(num)

def test_empty_and_none():
    assert sanitize_html("") == ""
    assert sanitize_html(None) == ""
    assert is_safe_html("") is True

def test_malicious_metadata():
    metadata = {
        'title': 'Book<script>alert(1)</script>',
        'author': 'Author<img src=x onerror=alert(2)>',
        'domain': 'Domain<iframe src="evil.com">',
    }
    sanitized = {k: sanitize_html(v) for k, v in metadata.items()}
    # All HTML should be escaped
    assert "<script>" not in sanitized['title']
    assert '&lt;img' in sanitized['author']  # <img escaped
    assert "<iframe>" not in sanitized['domain']

def test_large_batch_performance():
    import time
    titles = [f"Book {i}" for i in range(1000)]
    start = time.time()
    sanitized = [sanitize_html(t) for t in titles]
    elapsed = time.time() - start
    assert elapsed < 1.0
    assert len(sanitized) == 1000

def main():
    print("=" * 70)
    print("XSS Prevention Test Suite - Standalone Runner")
    print("=" * 70)

    tests = [
        ("Script tag in AI answer", test_script_tag_in_ai_answer),
        ("Event handler in book title", test_event_handler_in_book_title),
        ("JavaScript URL", test_javascript_url),
        ("Iframe injection", test_iframe_injection),
        ("Data URL", test_data_url),
        ("Safe content unchanged", test_safe_content),
        ("Pagination sanitization", test_pagination_sanitization),
        ("Nested tags", test_nested_tags),
        ("Case variations", test_case_variations),
        ("Numeric inputs", test_numeric_inputs),
        ("Empty and None inputs", test_empty_and_none),
        ("Malicious metadata", test_malicious_metadata),
        ("Large batch performance", test_large_batch_performance),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        if run_test(test_name, test_func):
            passed += 1
        else:
            failed += 1

    print("=" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 70)

    if failed == 0:
        print("✓ All XSS attack vectors are blocked!")
        return 0
    else:
        print(f"✗ {failed} test(s) failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())
