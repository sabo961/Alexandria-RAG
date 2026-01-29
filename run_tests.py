#!/usr/bin/env python
"""Wrapper script to run pytest with user site-packages"""
import sys
import os

# Add user site-packages to path
user_site = r'C:\Users\goran\AppData\Roaming\Python\Python314\site-packages'
if user_site not in sys.path:
    sys.path.insert(0, user_site)

# Now import and run pytest
import pytest

if __name__ == '__main__':
    sys.exit(pytest.main(['-v', 'tests/']))
