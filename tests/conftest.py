"""
Root pytest configuration for Alexandria tests.

Sets up path configuration to enable importing from scripts/ directory.
"""

import sys
import os

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
scripts_root = os.path.join(project_root, 'scripts')

if project_root not in sys.path:
    sys.path.insert(0, project_root)
if scripts_root not in sys.path:
    sys.path.insert(0, scripts_root)
