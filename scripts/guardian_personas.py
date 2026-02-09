#!/usr/bin/env python3
"""
Guardian Personas for Alexandria
================================

Character personas from the Temenos Čuvari (Guardians) that give voice
to Alexandria's responses. Loaded from .md files with ``alexandria:``
frontmatter — different servers can point to different guardian
directories for completely different library personalities.

Guardian = WHO speaks (personality, voice, quirks)
Pattern  = HOW to structure (synthesis, extraction, critical, etc.)
These two dimensions are orthogonal and compose at runtime.

Usage:
    from guardian_personas import get_guardian, list_guardians, compose_instruction

    # MCP path: instruction for Claude to follow
    instruction = compose_instruction("zec", pattern_template="...")

    # GUI path: system prompt for OpenRouter LLM
    prompt = compose_system_prompt("vault_e")
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DEFAULT_GUARDIAN_ID = "zec"


@dataclass
class GuardianPersona:
    """A guardian character persona for Alexandria responses."""

    id: str
    name: str
    title: str
    emoji: str
    role: str
    personality_prompt: str
    specialties: List[str] = field(default_factory=list)
    greeting: str = ""
    quirks: List[str] = field(default_factory=list)
    source_file: str = ""

    def to_summary(self) -> Dict[str, Any]:
        """Return summary dict for MCP tool responses."""
        return {
            "id": self.id,
            "name": self.name,
            "title": self.title,
            "emoji": self.emoji,
            "role": self.role,
            "specialties": self.specialties,
            "greeting": self.greeting,
        }


# ============================================================================
# FRONTMATTER PARSER
# ============================================================================

def _parse_frontmatter(text: str) -> Optional[dict]:
    """
    Extract YAML frontmatter from markdown text.

    Looks for content between opening and closing ``---`` delimiters.

    Returns:
        Parsed YAML dict, or None if no valid frontmatter found.
    """
    import yaml

    text = text.lstrip('\ufeff')  # Strip BOM if present
    if not text.startswith('---'):
        return None

    end = text.find('---', 3)
    if end == -1:
        return None

    yaml_text = text[3:end]
    try:
        return yaml.safe_load(yaml_text)
    except yaml.YAMLError as e:
        logger.warning(f"⚠️ Failed to parse YAML frontmatter: {e}")
        return None


def _extract_name_from_heading(text: str) -> str:
    """Extract guardian name from first markdown heading."""
    for line in text.split('\n'):
        line = line.strip()
        if line.startswith('# '):
            # Strip emoji and formatting from heading
            name = line.lstrip('# ').strip()
            # Remove common emoji prefixes
            for prefix in ['🤖 ', '🐇 ', '🧵 ', '⚔️ ', '🎨 ']:
                if name.startswith(prefix):
                    name = name[len(prefix):]
            # Take first part before colon (e.g., "Vault-E: Arhivator" → "Vault-E")
            if ':' in name:
                name = name.split(':')[0].strip()
            return name
    return ""


def _extract_title_from_content(text: str) -> str:
    """Extract title from first bold line after heading."""
    for line in text.split('\n'):
        line = line.strip()
        if line.startswith('**') and line.endswith('**'):
            return line.strip('*').strip()
        if line.startswith('**') and '**' in line[2:]:
            # Extract bold text: **some text** rest
            end = line.index('**', 2)
            return line[2:end].strip()
    return ""


# ============================================================================
# GUARDIAN LOADER
# ============================================================================

_GUARDIANS: Dict[str, GuardianPersona] = {}
_LOADED = False


def _load_guardian_from_file(filepath: Path) -> Optional[GuardianPersona]:
    """
    Load a single guardian from a markdown file with alexandria: frontmatter.

    Args:
        filepath: Path to the .md file

    Returns:
        GuardianPersona if file has valid alexandria: frontmatter, None otherwise
    """
    try:
        text = filepath.read_text(encoding='utf-8')
    except Exception as e:
        logger.warning(f"⚠️ Cannot read {filepath.name}: {e}")
        return None

    frontmatter = _parse_frontmatter(text)
    if not frontmatter or 'alexandria' not in frontmatter:
        return None

    alex = frontmatter['alexandria']

    # Required fields
    guardian_id = alex.get('id')
    personality_prompt = alex.get('personality_prompt', '').strip()
    if not guardian_id or not personality_prompt:
        logger.warning(
            f"⚠️ {filepath.name}: alexandria frontmatter missing 'id' or 'personality_prompt'"
        )
        return None

    # Derive name from heading if not in frontmatter
    name = alex.get('name') or _extract_name_from_heading(text)
    if not name:
        name = guardian_id.replace('_', '-').title()

    # Derive title from content if not in frontmatter
    title = alex.get('title') or _extract_title_from_content(text)

    return GuardianPersona(
        id=guardian_id,
        name=name,
        title=title,
        emoji=alex.get('emoji', ''),
        role=alex.get('role', ''),
        personality_prompt=personality_prompt,
        specialties=alex.get('specialties', []),
        greeting=alex.get('greeting', ''),
        quirks=alex.get('quirks', []),
        source_file=str(filepath),
    )


def _load_guardians() -> None:
    """
    Scan guardians directory and load all .md files with alexandria: frontmatter.

    Uses GUARDIANS_DIR from config.py. Skips files without frontmatter silently.
    """
    global _LOADED
    if _LOADED:
        return

    from config import GUARDIANS_DIR

    guardians_path = Path(GUARDIANS_DIR)
    if not guardians_path.exists():
        logger.warning(f"⚠️ Guardians directory not found: {guardians_path}")
        _LOADED = True
        return

    count = 0
    for md_file in sorted(guardians_path.glob('*.md')):
        guardian = _load_guardian_from_file(md_file)
        if guardian:
            _GUARDIANS[guardian.id] = guardian
            count += 1

    if count > 0:
        logger.info(f"✅ Loaded {count} guardian(s) from {guardians_path}")
    else:
        logger.warning(f"⚠️ No guardians with alexandria: frontmatter found in {guardians_path}")

    _LOADED = True


def reload_guardians() -> int:
    """
    Force reload guardians from disk.

    Returns:
        Number of guardians loaded.
    """
    global _LOADED
    _GUARDIANS.clear()
    _LOADED = False
    _load_guardians()
    return len(_GUARDIANS)


# ============================================================================
# PUBLIC API
# ============================================================================

def get_guardian(guardian_id: str) -> Optional[GuardianPersona]:
    """
    Get a guardian persona by ID.

    Args:
        guardian_id: Guardian identifier (e.g., "zec", "vault_e")

    Returns:
        GuardianPersona if found, None otherwise
    """
    _load_guardians()
    return _GUARDIANS.get(guardian_id)


def list_guardians() -> List[Dict[str, Any]]:
    """
    List all available guardians with summary info.

    Returns:
        List of guardian summary dicts with id, name, emoji, role, etc.
    """
    _load_guardians()
    return [g.to_summary() for g in _GUARDIANS.values()]


def get_default_guardian_id() -> str:
    """Return the default guardian ID."""
    return DEFAULT_GUARDIAN_ID


def compose_instruction(
    guardian_id: str,
    pattern_template: Optional[str] = None
) -> str:
    """
    Compose a unified instruction from guardian personality + pattern template.

    Used by MCP path: returned as response_instruction for Claude to follow.

    Guardian personality always comes first (WHO speaks).
    Pattern template appended if present (HOW to structure).

    Args:
        guardian_id: Guardian identifier
        pattern_template: Optional response pattern template text

    Returns:
        Composed instruction string

    Raises:
        ValueError: If guardian_id is not found
    """
    guardian = get_guardian(guardian_id)
    if not guardian:
        raise ValueError(f"Unknown guardian: {guardian_id}")

    parts = [guardian.personality_prompt]

    if pattern_template:
        parts.append(f"\n---\nStruktura odgovora: {pattern_template}")

    return "\n".join(parts)


def compose_system_prompt(
    guardian_id: str,
    pattern_template: Optional[str] = None
) -> str:
    """
    Compose a system prompt for GUI/OpenRouter path.

    Wraps guardian personality with base Alexandria context
    (knowledge base access, source citation requirement).

    Args:
        guardian_id: Guardian identifier
        pattern_template: Optional response pattern template text

    Returns:
        Composed system prompt string

    Raises:
        ValueError: If guardian_id is not found
    """
    guardian = get_guardian(guardian_id)
    if not guardian:
        raise ValueError(f"Unknown guardian: {guardian_id}")

    base = (
        f"Ti si {guardian.name} ({guardian.emoji}), čuvar/ica Alexandrije — "
        f"baze znanja s preko 9.000 knjiga. {guardian.personality_prompt} "
        "Odgovaraj na temelju dostavljenog konteksta iz baze znanja. "
        "Ako kontekst ne sadrži dovoljno informacija, reci to. "
        "Uvijek citiraj izvore navodeći naslov knjige i autora."
    )

    if pattern_template:
        base += f"\n\n---\nStruktura odgovora: {pattern_template}"

    return base
