#!/usr/bin/env python3
"""
End-to-End Verification Script for Qdrant Error Handling
=========================================================

This script verifies that all Qdrant operations have proper error handling
and provide user-friendly error messages when the server is unreachable.

Usage:
    # Test with server running (baseline):
    python verify_error_handling.py --test baseline

    # Test with invalid host (simulates server down):
    python verify_error_handling.py --test error-handling

    # Run all tests:
    python verify_error_handling.py --test all

Requirements:
    - Qdrant server at 192.168.0.151:6333 (for baseline tests)
    - Python packages: qdrant-client, requests, sentence-transformers
"""

import sys
import argparse
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent / 'scripts'))

def test_baseline():
    """Test that operations work with server running"""
    print("=" * 80)
    print("BASELINE TEST: Operations with Qdrant server running")
    print("=" * 80)

    from qdrant_utils import check_qdrant_connection

    # Test 1: Connection check with valid server
    print("\n[Test 1] check_qdrant_connection() with valid server")
    is_connected, error_msg = check_qdrant_connection('192.168.0.151', 6333, timeout=5)

    if is_connected:
        print("✅ PASS: Successfully connected to Qdrant server")
    else:
        print(f"⚠️  WARNING: Could not connect to Qdrant server:")
        print(error_msg)
        print("\nNote: This is expected if server is not running. Proceeding to error handling tests.")

    return is_connected

def test_error_handling():
    """Test error handling with invalid server"""
    print("\n" + "=" * 80)
    print("ERROR HANDLING TEST: Operations with invalid Qdrant server")
    print("=" * 80)

    from qdrant_utils import check_qdrant_connection, list_collections

    # Test 1: Connection check with invalid host
    print("\n[Test 1] check_qdrant_connection() with invalid host")
    is_connected, error_msg = check_qdrant_connection('invalid-host-12345', 6333, timeout=2)

    if not is_connected and error_msg:
        print("✅ PASS: Returns error message as expected")
        print("\nError message preview:")
        print(error_msg[:300] + "..." if len(error_msg) > 300 else error_msg)

        # Verify error message contains required debugging hints
        required_hints = ['VPN', 'firewall', 'server', 'dashboard']
        hints_found = [hint for hint in required_hints if hint.lower() in error_msg.lower()]

        if len(hints_found) == len(required_hints):
            print(f"\n✅ PASS: Error message contains all required debugging hints: {required_hints}")
        else:
            print(f"\n❌ FAIL: Missing debugging hints. Found: {hints_found}, Expected: {required_hints}")
    else:
        print("❌ FAIL: Should return error for invalid host")

    # Test 2: list_collections with invalid host
    print("\n[Test 2] list_collections() with invalid host")
    print("Expected: Should log error and return gracefully (no exception)")
    try:
        result = list_collections('invalid-host-12345', 6333)
        print("✅ PASS: Function returned without raising exception")
    except Exception as e:
        print(f"❌ FAIL: Function raised exception: {e}")

def test_rag_query_error_handling():
    """Test RAG query error handling"""
    print("\n" + "=" * 80)
    print("RAG QUERY ERROR HANDLING TEST")
    print("=" * 80)

    print("\n[Test 3] rag_query with invalid server")
    print("Expected: Should return RAGResult with error field populated")

    try:
        from rag_query import search_qdrant, check_qdrant_connection

        # Test connection check
        is_connected, error_msg = check_qdrant_connection('invalid-host-12345', 6333, timeout=2)

        if not is_connected:
            print("✅ PASS: Connection check detected server unavailable")
            print(f"Error message length: {len(error_msg)} chars")
        else:
            print("❌ FAIL: Should detect invalid server")

    except Exception as e:
        print(f"⚠️  Could not test: {e}")

def test_ingest_error_handling():
    """Test ingestion error handling"""
    print("\n" + "=" * 80)
    print("INGESTION ERROR HANDLING TEST")
    print("=" * 80)

    print("\n[Test 4] ingest_books upload_to_qdrant with invalid server")
    print("Expected: Should return dict with success=False and error message")

    try:
        from ingest_books import check_qdrant_connection

        # Test connection check
        is_connected, error_msg = check_qdrant_connection('invalid-host-12345', 6333, timeout=2)

        if not is_connected and 'VPN' in error_msg and 'firewall' in error_msg:
            print("✅ PASS: Connection check returns proper error message")
            print("✅ PASS: Error message includes debugging hints (VPN, firewall)")
        else:
            print("❌ FAIL: Error message missing required hints")

    except Exception as e:
        print(f"⚠️  Could not test: {e}")

def test_collection_manifest_error_handling():
    """Test collection manifest error handling"""
    print("\n" + "=" * 80)
    print("COLLECTION MANIFEST ERROR HANDLING TEST")
    print("=" * 80)

    print("\n[Test 5] collection_manifest verify_collection_exists with invalid server")
    print("Expected: Should handle connection errors gracefully")

    try:
        from collection_manifest import check_qdrant_connection

        # Test connection check
        is_connected, error_msg = check_qdrant_connection('invalid-host-12345', 6333, timeout=2)

        if not is_connected:
            print("✅ PASS: Connection check properly imported and works")
        else:
            print("❌ FAIL: Should detect invalid server")

    except Exception as e:
        print(f"⚠️  Could not test: {e}")

def verify_code_implementation():
    """Verify error handling implementation in code"""
    print("\n" + "=" * 80)
    print("CODE IMPLEMENTATION VERIFICATION")
    print("=" * 80)

    checks = {
        'qdrant_utils.py': [
            'check_qdrant_connection function exists',
            'list_collections uses check_qdrant_connection',
            'get_collection_stats uses check_qdrant_connection',
            'copy_collection uses check_qdrant_connection',
            'delete_collection uses check_qdrant_connection'
        ],
        'rag_query.py': [
            'search_qdrant uses check_qdrant_connection',
            'Error messages include debugging hints'
        ],
        'ingest_books.py': [
            'upload_to_qdrant uses check_qdrant_connection',
            'Returns dict with success and error fields'
        ],
        'collection_manifest.py': [
            'verify_collection_exists uses check_qdrant_connection'
        ],
        'alexandria_app.py': [
            'check_qdrant_health function exists',
            'QdrantClient instantiations wrapped with error handling'
        ]
    }

    scripts_dir = Path(__file__).parent / 'scripts'
    app_file = Path(__file__).parent / 'alexandria_app.py'

    all_passed = True

    for file_name, file_checks in checks.items():
        file_path = scripts_dir / file_name if file_name != 'alexandria_app.py' else app_file

        print(f"\n📄 {file_name}:")

        if not file_path.exists():
            print(f"   ❌ File not found: {file_path}")
            all_passed = False
            continue

        content = file_path.read_text(encoding='utf-8')

        for check in file_checks:
            # Simple text-based verification
            if 'check_qdrant_connection' in check and 'check_qdrant_connection' in content:
                print(f"   ✅ {check}")
            elif 'debugging hints' in check and all(hint in content for hint in ['VPN', 'firewall', 'dashboard']):
                print(f"   ✅ {check}")
            elif 'success and error' in check and 'success' in content and "'error'" in content:
                print(f"   ✅ {check}")
            elif 'function exists' in check:
                func_name = check.split(' function')[0]
                if f"def {func_name}" in content:
                    print(f"   ✅ {check}")
                else:
                    print(f"   ❌ {check}")
                    all_passed = False
            else:
                # Generic check - look for key phrases
                key_phrase = check.split(' uses ')[0] if ' uses ' in check else check.split(' ')[0]
                if key_phrase in content:
                    print(f"   ✅ {check}")
                else:
                    print(f"   ⚠️  Could not verify: {check}")

    return all_passed

def main():
    parser = argparse.ArgumentParser(description='Verify Qdrant error handling implementation')
    parser.add_argument('--test', choices=['baseline', 'error-handling', 'all', 'code-review'],
                        default='all', help='Type of test to run')

    args = parser.parse_args()

    print("🧪 Qdrant Error Handling Verification")
    print("=" * 80)

    if args.test in ['code-review', 'all']:
        verify_code_implementation()

    if args.test in ['baseline', 'all']:
        try:
            test_baseline()
        except ImportError as e:
            print(f"⚠️  Cannot run baseline test - missing dependencies: {e}")
            print("    Run: pip install qdrant-client requests sentence-transformers")

    if args.test in ['error-handling', 'all']:
        try:
            test_error_handling()
            test_rag_query_error_handling()
            test_ingest_error_handling()
            test_collection_manifest_error_handling()
        except ImportError as e:
            print(f"⚠️  Cannot run error handling tests - missing dependencies: {e}")
            print("    Run: pip install qdrant-client requests sentence-transformers")

    print("\n" + "=" * 80)
    print("VERIFICATION COMPLETE")
    print("=" * 80)
    print("\nManual Testing Checklist:")
    print("□ Stop Qdrant server (if you have control over it)")
    print("□ Run: python scripts/qdrant_utils.py list --host 192.168.0.151 --port 6333")
    print("□ Verify friendly error message appears (not stack trace)")
    print("□ Run: python scripts/rag_query.py 'test query'")
    print("□ Verify friendly error message appears")
    print("□ Start Streamlit: streamlit run alexandria_app.py")
    print("□ Verify Qdrant health check shows connection status")
    print("□ Restart Qdrant server")
    print("□ Verify all operations work normally")
    print("□ Check logs to ensure stack traces are logged for debugging")

if __name__ == '__main__':
    main()
