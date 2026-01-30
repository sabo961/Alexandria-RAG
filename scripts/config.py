#!/usr/bin/env python3
"""
Alexandria Configuration
========================

Central configuration for all Alexandria scripts.
Reads from environment variables with sensible defaults.

Priority:
1. Environment variables (highest)
2. .env file in project root
3. Hardcoded defaults (lowest)

Usage:
    from config import QDRANT_HOST, CALIBRE_LIBRARY_PATH, ...
"""

import os
from pathlib import Path

# Find project root (where .env should be)
SCRIPTS_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPTS_DIR.parent

# Load .env file if it exists
ENV_FILE = PROJECT_ROOT / '.env'
if ENV_FILE.exists():
    with open(ENV_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                # Only set if not already in environment
                if key not in os.environ:
                    os.environ[key] = value

# =============================================================================
# QDRANT CONFIGURATION
# =============================================================================

QDRANT_HOST = os.environ.get('QDRANT_HOST', '192.168.0.151')
QDRANT_PORT = int(os.environ.get('QDRANT_PORT', '6333'))
QDRANT_COLLECTION = os.environ.get('QDRANT_COLLECTION', 'alexandria')

# =============================================================================
# CALIBRE CONFIGURATION
# =============================================================================

CALIBRE_LIBRARY_PATH = os.environ.get('CALIBRE_LIBRARY_PATH', r'G:\My Drive\alexandria')

# =============================================================================
# LOCAL FILE INGESTION
# =============================================================================

LOCAL_INGEST_PATH = os.environ.get('LOCAL_INGEST_PATH', str(Path.home() / 'Downloads'))

# =============================================================================
# OPENROUTER (OPTIONAL - for CLI testing)
# =============================================================================

OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY', '')

# Try to load from .streamlit/secrets.toml if not in env
if not OPENROUTER_API_KEY:
    secrets_file = PROJECT_ROOT / '.streamlit' / 'secrets.toml'
    if secrets_file.exists():
        try:
            import tomllib
            with open(secrets_file, 'rb') as f:
                secrets = tomllib.load(f)
            OPENROUTER_API_KEY = secrets.get('OPENROUTER_API_KEY', '')
        except Exception:
            pass

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_qdrant_url() -> str:
    """Get full Qdrant URL."""
    return f"http://{QDRANT_HOST}:{QDRANT_PORT}"


def print_config():
    """Print current configuration (for debugging)."""
    print("Alexandria Configuration")
    print("=" * 40)
    print(f"QDRANT_HOST:          {QDRANT_HOST}")
    print(f"QDRANT_PORT:          {QDRANT_PORT}")
    print(f"QDRANT_COLLECTION:    {QDRANT_COLLECTION}")
    print(f"CALIBRE_LIBRARY_PATH: {CALIBRE_LIBRARY_PATH}")
    print(f"LOCAL_INGEST_PATH:    {LOCAL_INGEST_PATH}")
    print(f"OPENROUTER_API_KEY:   {'***' + OPENROUTER_API_KEY[-4:] if OPENROUTER_API_KEY else '(not set)'}")
    print(f"ENV_FILE:             {ENV_FILE} ({'exists' if ENV_FILE.exists() else 'not found'})")
    print("=" * 40)


if __name__ == "__main__":
    print_config()
