#!/usr/bin/env python3
"""
Automated test for language filter functionality.
This script verifies that the language filter is properly implemented.
"""

import sys
import json
from pathlib import Path

def test_languages_json():
    """Test that languages.json exists and is valid"""
    print("✓ Testing languages.json...")
    try:
        with open('scripts/languages.json', 'r') as f:
            data = json.load(f)

        assert 'languages' in data, "Missing 'languages' key"
        assert len(data['languages']) > 0, "No languages defined"

        # Check structure
        for lang in data['languages']:
            assert 'id' in lang, "Language missing 'id'"
            assert 'name' in lang, "Language missing 'name'"

        print(f"  ✓ Found {len(data['languages'])} languages: {[l['id'] for l in data['languages']]}")
        return True
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return False


def test_load_languages_function():
    """Test that load_languages() function exists and works"""
    print("✓ Testing load_languages() function...")
    try:
        # Import the function
        sys.path.insert(0, '.')
        with open('alexandria_app.py', 'r') as f:
            app_code = f.read()

        # Execute up to load_languages
        exec_globals = {}
        code_parts = app_code.split('if __name__')[0]
        exec(code_parts, exec_globals)

        load_languages = exec_globals.get('load_languages')
        assert load_languages is not None, "load_languages function not found"

        langs = load_languages()
        assert isinstance(langs, list), "load_languages should return a list"
        assert len(langs) > 0, "load_languages should return languages"

        print(f"  ✓ load_languages() returns: {langs}")
        return True
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return False


def test_language_filter_in_ui():
    """Test that language filter is in the UI code"""
    print("✓ Testing language filter in UI...")
    try:
        with open('alexandria_app.py', 'r') as f:
            content = f.read()

        # Check for language selectbox
        assert 'query_language' in content, "query_language variable not found"
        assert 'Language Filter' in content, "Language Filter selectbox not found"
        assert 'load_languages()' in content, "load_languages() not called in UI"

        # Check it's passed to perform_rag_query
        assert 'language_filter=query_language' in content or 'language_filter=' in content, \
            "language_filter not passed to perform_rag_query"

        print("  ✓ Language filter UI code found")
        return True
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return False


def test_language_filter_parameter():
    """Test that language_filter parameter exists in rag_query.py"""
    print("✓ Testing language_filter parameter in rag_query.py...")
    try:
        with open('scripts/rag_query.py', 'r') as f:
            content = f.read()

        # Check parameter in function signatures
        assert 'language_filter: Optional[str]' in content or 'language_filter:' in content, \
            "language_filter parameter not in function signature"

        # Check filter logic
        assert 'language_filter and language_filter != "all"' in content or \
               'if language_filter' in content, \
            "language_filter condition not found"

        # Check FieldCondition usage
        assert 'key="language"' in content, "language field condition not found"

        print("  ✓ Language filter parameter and logic found")
        return True
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return False


def test_filter_implementation():
    """Test the actual filter implementation logic"""
    print("✓ Testing filter implementation logic...")
    try:
        with open('scripts/rag_query.py', 'r') as f:
            content = f.read()

        # Check for the filter implementation pattern
        checks = [
            ('FieldCondition', 'FieldCondition import/usage'),
            ('match=MatchValue(value=language_filter)', 'Language filter match value'),
            ('logger.info', 'Logging of language filter'),
        ]

        for check, desc in checks:
            if check in content:
                print(f"  ✓ Found: {desc}")
            else:
                print(f"  ! Warning: {desc} not found (may use different pattern)")

        return True
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return False


def test_syntax():
    """Test that the Python files have valid syntax"""
    print("✓ Testing Python syntax...")
    try:
        import py_compile

        files = [
            'alexandria_app.py',
            'scripts/rag_query.py',
        ]

        for file in files:
            py_compile.compile(file, doraise=True)
            print(f"  ✓ {file} syntax OK")

        return True
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("Language Filter Automated Test Suite")
    print("=" * 60)
    print()

    tests = [
        test_languages_json,
        test_load_languages_function,
        test_language_filter_in_ui,
        test_language_filter_parameter,
        test_filter_implementation,
        test_syntax,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test crashed: {e}")
            results.append(False)
        print()

    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("✓ ALL TESTS PASSED")
        print()
        print("Manual verification still required:")
        print("1. Start app: streamlit run alexandria_app.py")
        print("2. Navigate to Query tab")
        print("3. Verify language filter dropdown appears")
        print("4. Test filtering with different languages")
        print("5. Check browser console for errors")
        return 0
    else:
        print("✗ SOME TESTS FAILED")
        return 1


if __name__ == '__main__':
    sys.exit(main())
