"""Tests for guardian_personas module — file-based loading from .md frontmatter."""

import os
import sys
import pytest
import tempfile
from pathlib import Path

# Add scripts directory to path
scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts')
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from guardian_personas import (
    GuardianPersona,
    get_guardian,
    list_guardians,
    get_default_guardian_id,
    compose_instruction,
    compose_system_prompt,
    reload_guardians,
    _parse_frontmatter,
    _load_guardian_from_file,
)


# ============================================================================
# get_guardian (loads from real guardian .md files)
# ============================================================================

def test_get_guardian_valid():
    """get_guardian returns GuardianPersona for valid ID."""
    guardian = get_guardian("zec")
    assert guardian is not None
    assert isinstance(guardian, GuardianPersona)
    assert guardian.id == "zec"
    assert guardian.name == "Zec"


def test_get_guardian_all_five():
    """All five guardians are retrievable by ID."""
    ids = ["zec", "vault_e", "ariadne", "hipatija", "klepac"]
    for gid in ids:
        guardian = get_guardian(gid)
        assert guardian is not None, f"Guardian '{gid}' not found"
        assert guardian.id == gid


def test_get_guardian_invalid():
    """get_guardian returns None for unknown ID."""
    assert get_guardian("nonexistent") is None
    assert get_guardian("") is None


def test_guardian_has_source_file():
    """Loaded guardians track their source .md file."""
    guardian = get_guardian("zec")
    assert guardian.source_file
    assert guardian.source_file.endswith('.md')


# ============================================================================
# list_guardians
# ============================================================================

def test_list_guardians_returns_at_least_five():
    """list_guardians returns at least the 5 core guardians."""
    guardians = list_guardians()
    assert len(guardians) >= 5


def test_list_guardians_has_required_fields():
    """Each guardian summary dict has required fields."""
    required_fields = {"id", "name", "title", "emoji", "role", "specialties", "greeting"}
    for g in list_guardians():
        missing = required_fields - set(g.keys())
        assert not missing, f"Guardian '{g.get('id', '?')}' missing fields: {missing}"


def test_list_guardians_returns_dicts():
    """list_guardians returns list of dicts, not GuardianPersona objects."""
    for g in list_guardians():
        assert isinstance(g, dict)


# ============================================================================
# get_default_guardian_id
# ============================================================================

def test_default_guardian_is_zec():
    """Default guardian ID is 'zec'."""
    assert get_default_guardian_id() == "zec"


def test_default_guardian_exists():
    """Default guardian ID resolves to an actual guardian."""
    default_id = get_default_guardian_id()
    assert get_guardian(default_id) is not None


# ============================================================================
# compose_instruction
# ============================================================================

def test_compose_instruction_guardian_only():
    """compose_instruction with guardian only returns personality prompt."""
    instruction = compose_instruction("zec")
    guardian = get_guardian("zec")
    assert guardian.personality_prompt in instruction


def test_compose_instruction_with_pattern():
    """compose_instruction with both includes guardian + pattern."""
    pattern = "Extract 3-5 key principles from the sources."
    instruction = compose_instruction("hipatija", pattern_template=pattern)
    guardian = get_guardian("hipatija")
    assert guardian.personality_prompt in instruction
    assert pattern in instruction


def test_compose_instruction_pattern_none():
    """compose_instruction with pattern_template=None works fine."""
    instruction = compose_instruction("ariadne", pattern_template=None)
    guardian = get_guardian("ariadne")
    assert guardian.personality_prompt in instruction


def test_compose_instruction_unknown_raises():
    """compose_instruction raises ValueError for unknown guardian."""
    with pytest.raises(ValueError, match="Unknown guardian"):
        compose_instruction("nonexistent")


# ============================================================================
# compose_system_prompt
# ============================================================================

def test_compose_system_prompt_includes_base_context():
    """compose_system_prompt includes knowledge base context."""
    prompt = compose_system_prompt("vault_e")
    assert "Alexandrije" in prompt or "Alexandria" in prompt
    assert "knjiga" in prompt
    assert "Vault-E" in prompt


def test_compose_system_prompt_includes_guardian_personality():
    """compose_system_prompt includes the guardian's personality prompt."""
    prompt = compose_system_prompt("klepac")
    guardian = get_guardian("klepac")
    assert guardian.personality_prompt in prompt


def test_compose_system_prompt_with_pattern():
    """compose_system_prompt appends pattern template."""
    pattern = "Summarize key insights in 2-3 sentences."
    prompt = compose_system_prompt("zec", pattern_template=pattern)
    assert pattern in prompt


def test_compose_system_prompt_unknown_raises():
    """compose_system_prompt raises ValueError for unknown guardian."""
    with pytest.raises(ValueError, match="Unknown guardian"):
        compose_system_prompt("nonexistent")


# ============================================================================
# GuardianPersona quality checks
# ============================================================================

def test_personality_prompt_length():
    """Each guardian personality_prompt is between 100-800 chars."""
    for g in list_guardians():
        guardian = get_guardian(g["id"])
        length = len(guardian.personality_prompt)
        assert 100 <= length <= 800, (
            f"Guardian '{guardian.id}' personality_prompt is {length} chars "
            f"(expected 100-800)"
        )


def test_all_guardians_have_emoji():
    """Every guardian has a non-empty emoji."""
    for g in list_guardians():
        assert g["emoji"], f"Guardian '{g['id']}' has no emoji"


def test_all_guardians_have_greeting():
    """Every guardian has a non-empty greeting."""
    for g in list_guardians():
        assert g["greeting"], f"Guardian '{g['id']}' has no greeting"


def test_guardian_ids_are_lowercase_snake():
    """Guardian IDs use lowercase with underscores only."""
    import re
    for g in list_guardians():
        assert re.match(r'^[a-z][a-z0-9_]*$', g["id"]), (
            f"Guardian ID '{g['id']}' is not lowercase snake_case"
        )


# ============================================================================
# Frontmatter parser
# ============================================================================

def test_parse_frontmatter_valid():
    """_parse_frontmatter extracts YAML from markdown."""
    text = "---\ntitle: Test\nalexandria:\n  id: test\n---\n# Content"
    result = _parse_frontmatter(text)
    assert result is not None
    assert result["title"] == "Test"
    assert result["alexandria"]["id"] == "test"


def test_parse_frontmatter_no_frontmatter():
    """_parse_frontmatter returns None for files without ---."""
    assert _parse_frontmatter("# Just a heading\nSome text") is None


def test_parse_frontmatter_no_closing():
    """_parse_frontmatter returns None if closing --- is missing."""
    assert _parse_frontmatter("---\ntitle: Test\n# No closing") is None


def test_parse_frontmatter_with_bom():
    """_parse_frontmatter handles BOM prefix."""
    text = "\ufeff---\ntitle: BOM Test\n---\n# Content"
    result = _parse_frontmatter(text)
    assert result is not None
    assert result["title"] == "BOM Test"


# ============================================================================
# File-based loading
# ============================================================================

def test_load_guardian_from_file_valid():
    """_load_guardian_from_file loads a guardian from a valid .md file."""
    content = """---
alexandria:
  id: test_guardian
  emoji: "🧪"
  role: "Test role"
  personality_prompt: >
    This is a test personality prompt that should be long enough
    to pass validation checks and demonstrate that the loading works
    correctly from a markdown file with proper frontmatter.
  greeting: "Hello test"
  specialties: [testing]
  quirks: [always testing]
---
# Test Guardian

**A test guardian for unit tests.**
"""
    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.md', delete=False, encoding='utf-8'
    ) as f:
        f.write(content)
        f.flush()
        filepath = Path(f.name)

    try:
        guardian = _load_guardian_from_file(filepath)
        assert guardian is not None
        assert guardian.id == "test_guardian"
        assert guardian.emoji == "🧪"
        assert guardian.name == "Test Guardian"
        assert "test personality prompt" in guardian.personality_prompt
        assert guardian.greeting == "Hello test"
    finally:
        filepath.unlink()


def test_load_guardian_from_file_no_frontmatter():
    """_load_guardian_from_file returns None for files without alexandria: block."""
    content = "# Just a Guardian\n\nNo frontmatter here."
    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.md', delete=False, encoding='utf-8'
    ) as f:
        f.write(content)
        f.flush()
        filepath = Path(f.name)

    try:
        guardian = _load_guardian_from_file(filepath)
        assert guardian is None
    finally:
        filepath.unlink()


def test_load_guardian_from_file_missing_required():
    """_load_guardian_from_file returns None if id or personality_prompt missing."""
    content = """---
alexandria:
  id: incomplete
  emoji: "❌"
---
# Incomplete Guardian
"""
    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.md', delete=False, encoding='utf-8'
    ) as f:
        f.write(content)
        f.flush()
        filepath = Path(f.name)

    try:
        guardian = _load_guardian_from_file(filepath)
        assert guardian is None
    finally:
        filepath.unlink()


def test_load_guardian_derives_name_from_heading():
    """Guardian name is derived from first # heading if not in frontmatter."""
    content = """---
alexandria:
  id: derived_name
  emoji: "📝"
  personality_prompt: "A test prompt that is sufficiently long for testing."
---
# Bro JedAI

Some content.
"""
    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.md', delete=False, encoding='utf-8'
    ) as f:
        f.write(content)
        f.flush()
        filepath = Path(f.name)

    try:
        guardian = _load_guardian_from_file(filepath)
        assert guardian is not None
        assert guardian.name == "Bro JedAI"
    finally:
        filepath.unlink()


def test_reload_guardians():
    """reload_guardians clears and reloads from disk."""
    count = reload_guardians()
    assert count >= 5
    assert get_guardian("zec") is not None
