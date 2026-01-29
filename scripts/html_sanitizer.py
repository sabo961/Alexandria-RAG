"""
Alexandria HTML Sanitizer

Utility functions for sanitizing HTML content to prevent XSS attacks.
Provides validation and cleaning of HTML content before rendering.

Usage:
    from scripts.html_sanitizer import sanitize_html, is_safe_html

    # Clean user-provided content
    clean_text = sanitize_html("<script>alert('xss')</script>Hello")
    # Returns: "&lt;script&gt;alert('xss')&lt;/script&gt;Hello"

    # Check if content is safe
    if is_safe_html(user_input):
        display(user_input)
    else:
        display(sanitize_html(user_input))
"""

import html
import re
import logging
from typing import List, Optional, Pattern

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# XSS ATTACK PATTERNS
# ============================================================================

# Dangerous HTML tags that can execute scripts
DANGEROUS_TAGS: List[str] = [
    'script',
    'iframe',
    'object',
    'embed',
    'applet',
    'meta',
    'link',
    'style',
    'base',
    'form',
]

# Dangerous HTML attributes that can execute scripts
DANGEROUS_ATTRIBUTES: List[str] = [
    'onclick',
    'onload',
    'onerror',
    'onmouseover',
    'onmouseout',
    'onmousemove',
    'onmousedown',
    'onmouseup',
    'onfocus',
    'onblur',
    'onchange',
    'onsubmit',
    'onkeydown',
    'onkeyup',
    'onkeypress',
]

# Dangerous URL schemes that can execute scripts
DANGEROUS_SCHEMES: List[str] = [
    'javascript:',
    'data:',
    'vbscript:',
    'file:',
]


def _compile_patterns() -> List[Pattern]:
    """
    Compile regex patterns for detecting XSS attack vectors.

    Returns:
        List of compiled regex patterns
    """
    patterns = []

    # Dangerous tags: <script>, <iframe>, etc.
    for tag in DANGEROUS_TAGS:
        # Match opening and closing tags
        patterns.append(re.compile(
            rf'<{tag}[^>]*?>.*?</{tag}>',
            re.IGNORECASE | re.DOTALL
        ))
        # Match self-closing tags
        patterns.append(re.compile(
            rf'<{tag}[^>]*?/>',
            re.IGNORECASE
        ))

    # Dangerous attributes: onclick="...", onerror="...", etc.
    for attr in DANGEROUS_ATTRIBUTES:
        patterns.append(re.compile(
            rf'{attr}\s*=',
            re.IGNORECASE
        ))

    # Dangerous URL schemes: javascript:, data:, etc.
    for scheme in DANGEROUS_SCHEMES:
        patterns.append(re.compile(
            rf'{re.escape(scheme)}',
            re.IGNORECASE
        ))

    return patterns


# Compile patterns once at module load time
XSS_PATTERNS: List[Pattern] = _compile_patterns()


# ============================================================================
# HTML SANITIZATION FUNCTIONS
# ============================================================================

def sanitize_html(content: str, preserve_newlines: bool = True) -> str:
    """
    Sanitize HTML content by escaping all HTML entities.

    This function uses html.escape() to convert dangerous HTML characters
    into their safe HTML entity equivalents:
    - < becomes &lt;
    - > becomes &gt;
    - & becomes &amp;
    - " becomes &quot;
    - ' becomes &#x27;

    Args:
        content: The HTML string to sanitize
        preserve_newlines: If True, preserve newline characters (default: True)

    Returns:
        Sanitized string safe for HTML rendering

    Examples:
        >>> sanitize_html("<script>alert('xss')</script>")
        "&lt;script&gt;alert('xss')&lt;/script&gt;"

        >>> sanitize_html('Click <a href="javascript:alert()">here</a>')
        'Click &lt;a href=&quot;javascript:alert()&quot;&gt;here&lt;/a&gt;'
    """
    if not content:
        return ""

    if not isinstance(content, str):
        logger.warning(f"sanitize_html received non-string input: {type(content)}")
        content = str(content)

    # Escape all HTML entities
    sanitized = html.escape(content, quote=True)

    # Optionally preserve newlines for formatting
    if preserve_newlines:
        # Newlines are already preserved by html.escape
        pass

    return sanitized


def is_safe_html(content: str, strict: bool = True) -> bool:
    """
    Check if HTML content is safe (no XSS attack vectors).

    This function checks for common XSS attack patterns:
    - Dangerous tags: <script>, <iframe>, <object>, <embed>, etc.
    - Event handlers: onclick, onerror, onload, etc.
    - Dangerous URL schemes: javascript:, data:, vbscript:, etc.

    Args:
        content: The HTML string to validate
        strict: If True, reject any potential XSS patterns (default: True)
               If False, only reject obvious attack vectors

    Returns:
        True if content is safe, False if potentially dangerous

    Examples:
        >>> is_safe_html("Hello, World!")
        True

        >>> is_safe_html("<script>alert('xss')</script>")
        False

        >>> is_safe_html('<a href="javascript:alert()">Click</a>')
        False
    """
    if not content:
        return True

    if not isinstance(content, str):
        logger.warning(f"is_safe_html received non-string input: {type(content)}")
        content = str(content)

    # Check against all XSS patterns
    for pattern in XSS_PATTERNS:
        if pattern.search(content):
            if strict:
                logger.warning(f"Detected potential XSS pattern: {pattern.pattern}")
                return False

    return True


def sanitize_for_markdown(content: str) -> str:
    """
    Sanitize content for use in Streamlit markdown with unsafe_allow_html=True.

    This is a convenience wrapper around sanitize_html() for use specifically
    with Streamlit's markdown rendering.

    Args:
        content: The string to sanitize for markdown rendering

    Returns:
        Sanitized string safe for st.markdown(..., unsafe_allow_html=True)

    Examples:
        >>> sanitize_for_markdown("<b>Bold</b> and <script>alert()</script>")
        "&lt;b&gt;Bold&lt;/b&gt; and &lt;script&gt;alert()&lt;/script&gt;"
    """
    return sanitize_html(content, preserve_newlines=True)


def get_dangerous_patterns_info() -> dict:
    """
    Get information about dangerous patterns detected by this module.

    Returns:
        Dictionary with lists of dangerous tags, attributes, and URL schemes

    Examples:
        >>> info = get_dangerous_patterns_info()
        >>> 'script' in info['tags']
        True
        >>> 'onclick' in info['attributes']
        True
    """
    return {
        'tags': DANGEROUS_TAGS,
        'attributes': DANGEROUS_ATTRIBUTES,
        'schemes': DANGEROUS_SCHEMES,
        'pattern_count': len(XSS_PATTERNS)
    }


# ============================================================================
# MODULE INITIALIZATION
# ============================================================================

if __name__ == '__main__':
    # Simple test when run as script
    test_cases = [
        ("Plain text", "Hello, World!"),
        ("Script tag", "<script>alert('xss')</script>"),
        ("Event handler", '<img src="x" onerror="alert(1)">'),
        ("JavaScript URL", '<a href="javascript:alert()">Click</a>'),
        ("Data URL", '<img src="data:text/html,<script>alert(1)</script>">'),
        ("Iframe", '<iframe src="evil.com"></iframe>'),
    ]

    logger.info("Testing HTML Sanitizer")
    logger.info("=" * 80)

    for name, test_input in test_cases:
        is_safe = is_safe_html(test_input)
        sanitized = sanitize_html(test_input)

        logger.info(f"\nTest: {name}")
        logger.info(f"Input:     {test_input}")
        logger.info(f"Is Safe:   {is_safe}")
        logger.info(f"Sanitized: {sanitized}")

    logger.info("\n" + "=" * 80)
    logger.info("Pattern Information:")
    info = get_dangerous_patterns_info()
    logger.info(f"Dangerous tags:       {len(info['tags'])}")
    logger.info(f"Dangerous attributes: {len(info['attributes'])}")
    logger.info(f"Dangerous schemes:    {len(info['schemes'])}")
    logger.info(f"Total XSS patterns:   {info['pattern_count']}")
