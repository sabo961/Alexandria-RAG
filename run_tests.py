#!/usr/bin/env python
"""Test runner script for HTML sanitizer tests"""
import sys
import os

# Add user site-packages to path
sys.path.insert(0, os.path.expanduser(r'~\AppData\Roaming\Python\Python314\site-packages'))

try:
    import pytest
    sys.exit(pytest.main(['tests/test_html_sanitizer.py', '-v']))
except ImportError:
    print("pytest not found, falling back to verification script")
    import subprocess
    sys.exit(subprocess.call([sys.executable, 'verify_sanitizer_tests.py']))
