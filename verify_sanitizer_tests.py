"""
Simple verification script for HTML sanitizer (without pytest dependency)
"""

import sys
from scripts.html_sanitizer import (
    sanitize_html,
    is_safe_html,
    sanitize_for_markdown,
    get_dangerous_patterns_info
)


def test_basic_functionality():
    """Test basic sanitizer functionality"""
    print("Testing basic functionality...")

    # Test 1: Plain text is safe
    assert is_safe_html("Hello, World!") is True
    print("✓ Plain text detection works")

    # Test 2: Script tags are detected
    assert is_safe_html("<script>alert('xss')</script>") is False
    print("✓ Script tag detection works")

    # Test 3: Script tags are sanitized
    result = sanitize_html("<script>alert('xss')</script>")
    assert "&lt;script&gt;" in result
    assert "<script>" not in result
    print("✓ Script tag sanitization works")

    # Test 4: Event handlers are detected
    assert is_safe_html('<div onclick="alert(1)">') is False
    print("✓ Event handler detection works")

    # Test 5: JavaScript URLs are detected
    assert is_safe_html('<a href="javascript:alert(1)">') is False
    print("✓ JavaScript URL detection works")

    # Test 6: Data URLs are detected
    assert is_safe_html('<img src="data:text/html,<script>">') is False
    print("✓ Data URL detection works")

    # Test 7: Iframe tags are detected
    assert is_safe_html('<iframe src="evil.com"></iframe>') is False
    print("✓ Iframe detection works")

    # Test 8: Safe HTTP links pass
    assert is_safe_html("Visit https://example.com") is True
    print("✓ Safe HTTP links work")

    # Test 9: Pattern info is available
    info = get_dangerous_patterns_info()
    assert 'script' in info['tags']
    assert 'onclick' in info['attributes']
    assert 'javascript:' in info['schemes']
    print("✓ Pattern info works")

    # Test 10: Sanitize for markdown
    result = sanitize_for_markdown("<b>Bold</b>")
    assert "&lt;b&gt;" in result
    print("✓ Sanitize for markdown works")

    print("\n✅ All basic tests passed!")
    return True


def test_xss_vectors():
    """Test comprehensive XSS attack vectors"""
    print("\nTesting XSS attack vectors...")

    attack_vectors = [
        ("<script>alert(1)</script>", "script tag"),
        ('<img src=x onerror="alert(1)">', "onerror handler"),
        ('<a href="javascript:alert(1)">click</a>', "javascript: URL"),
        ('<iframe src="evil.com"></iframe>', "iframe tag"),
        ('<object data="evil.swf"></object>', "object tag"),
        ('<embed src="evil.swf">', "embed tag"),
        ('<meta http-equiv="refresh" content="0;url=evil">', "meta refresh"),
        ('<link rel="stylesheet" href="evil.css">', "link tag"),
        ('<style>body{background:red}</style>', "style tag"),
        ('<form action="evil.php">', "form tag"),
        ('<div onload="alert(1)">', "onload handler"),
        ('<div onmouseover="alert(1)">', "onmouseover handler"),
        ('<a href="vbscript:alert(1)">', "vbscript: URL"),
        ('<a href="file:///etc/passwd">', "file: URL"),
    ]

    passed = 0
    failed = 0

    for vector, description in attack_vectors:
        if not is_safe_html(vector):
            sanitized = sanitize_html(vector)
            if "<" not in sanitized or "&lt;" in sanitized:
                print(f"✓ Blocked: {description}")
                passed += 1
            else:
                print(f"✗ Sanitization failed for: {description}")
                failed += 1
        else:
            print(f"✗ Failed to detect: {description}")
            failed += 1

    print(f"\n{passed} attack vectors blocked, {failed} failed")

    if failed == 0:
        print("✅ All XSS vectors blocked!")
        return True
    else:
        print(f"❌ {failed} XSS vectors not properly blocked")
        return False


def test_real_world_scenarios():
    """Test real-world Alexandria use cases"""
    print("\nTesting real-world scenarios...")

    # Book titles with XSS
    title1 = "Great Book<script>alert('xss')</script>"
    assert is_safe_html(title1) is False
    sanitized1 = sanitize_html(title1)
    assert "Great Book" in sanitized1
    assert "<script" not in sanitized1.lower()
    print("✓ Malicious book title sanitized")

    # Author names with XSS
    author = "John Doe<img src=x onerror=alert(1)>"
    assert is_safe_html(author) is False
    sanitized2 = sanitize_html(author)
    assert "John Doe" in sanitized2
    assert "<img" not in sanitized2.lower()
    print("✓ Malicious author name sanitized")

    # Search queries with XSS
    query = 'search<iframe src="evil"></iframe>'
    assert is_safe_html(query) is False
    sanitized3 = sanitize_html(query)
    assert "search" in sanitized3
    assert "<iframe" not in sanitized3.lower()
    print("✓ Malicious search query sanitized")

    # Safe content passes through
    safe_title = "Introduction to Python Programming"
    assert is_safe_html(safe_title) is True
    assert sanitize_html(safe_title) == safe_title
    print("✓ Safe content preserved")

    print("✅ All real-world scenarios passed!")
    return True


def main():
    """Run all verification tests"""
    print("=" * 70)
    print("HTML Sanitizer Verification Tests")
    print("=" * 70)

    try:
        result1 = test_basic_functionality()
        result2 = test_xss_vectors()
        result3 = test_real_world_scenarios()

        print("\n" + "=" * 70)
        if result1 and result2 and result3:
            print("✅ ALL TESTS PASSED - HTML Sanitizer is working correctly!")
            print("=" * 70)
            return 0
        else:
            print("❌ SOME TESTS FAILED - Please review the output above")
            print("=" * 70)
            return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
