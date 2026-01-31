# Security Documentation - Alexandria

**Last Updated:** 2026-01-29
**Version:** 1.0
**Maintainer:** Auto-Claude

---

## Table of Contents

1. [Overview](#overview)
2. [XSS Prevention Strategy](#xss-prevention-strategy)
3. [HTML Sanitization Utilities](#html-sanitization-utilities)
4. [Safe Coding Guidelines](#safe-coding-guidelines)
5. [Security Testing](#security-testing)
6. [Audit & Remediation](#audit--remediation)
7. [Incident Response](#incident-response)

---

## Overview

Alexandria is a semantic RAG library application that renders dynamic content from multiple sources:
- AI-generated answers from OpenRouter LLM
- Book metadata from Calibre database
- User search queries
- File uploads and ingestion results

This documentation describes the security measures in place to protect against **Cross-Site Scripting (XSS)** attacks when rendering HTML content in the Streamlit application.

### Threat Model

**Attack Vectors:**
1. **AI-Generated Content:** Malicious LLM responses containing `<script>` tags or JavaScript
2. **Book Metadata:** Compromised Calibre database with XSS payloads in titles/authors
3. **Search Queries:** User input rendered in search results or error messages
4. **File Names:** Malicious filenames during batch ingestion
5. **URL Parameters:** Manipulated pagination or filter parameters

**Impact of XSS:**
- Session hijacking (steal cookies/tokens)
- Phishing attacks (fake login forms)
- Malware distribution
- Data exfiltration from browser

---

## XSS Prevention Strategy

Alexandria employs a **defense-in-depth** approach to XSS prevention:

### 1. HTML Sanitization (Primary Defense)

All user-controlled and dynamic content is sanitized using `sanitize_html()` before rendering:

```python
from scripts.html_sanitizer import sanitize_html

# Sanitize AI-generated content
clean_answer = sanitize_html(llm_response)
st.markdown(clean_answer, unsafe_allow_html=True)

# Sanitize book metadata
clean_title = sanitize_html(book.title)
st.markdown(f"<h3>{clean_title}</h3>", unsafe_allow_html=True)
```

### 2. Pattern Detection (Secondary Defense)

The `is_safe_html()` function detects 39 XSS attack patterns:

**Dangerous Tags (10):**
- `<script>`, `<iframe>`, `<object>`, `<embed>`, `<applet>`
- `<meta>`, `<link>`, `<style>`, `<base>`, `<form>`

**Event Handlers (16):**
- `onclick`, `onerror`, `onload`, `onmouseover`, `onfocus`, etc.

**Dangerous URL Schemes (4):**
- `javascript:`, `data:`, `vbscript:`, `file:`

### 3. Static HTML Isolation

Static HTML content (headers, footers, styling) is isolated into helper functions to prevent mixing with dynamic content:

```python
def render_section_header(text: str) -> None:
    """Render a section header (static HTML only)."""
    st.markdown(f'<div class="section-header">{text}</div>', unsafe_allow_html=True)
```

### 4. Minimal unsafe_allow_html Usage

The codebase has been refactored to minimize `unsafe_allow_html=True` usage:
- **Before:** 16 instances (mostly inline)
- **After:** 11 instances (consolidated into 4 helper functions)

---

## HTML Sanitization Utilities

### Module: `scripts/html_sanitizer.py`

#### `sanitize_html(content: str, preserve_newlines: bool = True) -> str`

**Purpose:** Escape all HTML entities to prevent script execution

**How it works:**
```python
# Input:  <script>alert('xss')</script>Hello
# Output: &lt;script&gt;alert('xss')&lt;/script&gt;Hello
```

**Use cases:**
- AI-generated answers
- Book titles, authors, metadata
- Search queries
- Error messages
- File names

**Example:**
```python
from scripts.html_sanitizer import sanitize_html

user_input = request.get('search_query')
clean_query = sanitize_html(user_input)
st.markdown(f"Results for: {clean_query}", unsafe_allow_html=True)
```

---

#### `is_safe_html(content: str, strict: bool = True) -> bool`

**Purpose:** Validate content for XSS patterns before rendering

**How it works:**
```python
# Returns False for dangerous content
is_safe_html("<script>alert(1)</script>")  # False
is_safe_html('<img onerror="alert(1)">')    # False
is_safe_html("Hello, World!")               # True
```

**Use cases:**
- Pre-validation before expensive sanitization
- Logging security warnings
- Debugging suspicious content

**Example:**
```python
from scripts.html_sanitizer import is_safe_html, sanitize_html

if not is_safe_html(llm_response):
    logger.warning(f"Detected XSS in LLM response: {llm_response[:100]}")
    llm_response = sanitize_html(llm_response)
```

---

#### `sanitize_for_markdown(content: str) -> str`

**Purpose:** Convenience wrapper for Streamlit markdown rendering

**Example:**
```python
from scripts.html_sanitizer import sanitize_for_markdown

st.markdown(sanitize_for_markdown(book_title), unsafe_allow_html=True)
```

---

#### `get_dangerous_patterns_info() -> dict`

**Purpose:** Get information about detected XSS patterns (for debugging)

**Returns:**
```python
{
    'tags': ['script', 'iframe', 'object', ...],
    'attributes': ['onclick', 'onerror', ...],
    'schemes': ['javascript:', 'data:', ...],
    'pattern_count': 39
}
```

---

## Safe Coding Guidelines

### ✅ DO: Sanitize All Dynamic Content

```python
# Good: Always sanitize user-controlled content
from scripts.html_sanitizer import sanitize_html

book_title = sanitize_html(book.title)
author_name = sanitize_html(book.author)
ai_answer = sanitize_html(llm_response)

st.markdown(f"**{book_title}** by {author_name}", unsafe_allow_html=True)
```

### ❌ DON'T: Mix User Input with Static HTML

```python
# Bad: Never concatenate user input directly
user_query = st.text_input("Search")
st.markdown(f"<h2>Results for: {user_query}</h2>", unsafe_allow_html=True)  # XSS!

# Good: Always sanitize first
user_query = st.text_input("Search")
clean_query = sanitize_html(user_query)
st.markdown(f"<h2>Results for: {clean_query}</h2>", unsafe_allow_html=True)
```

### ✅ DO: Use Helper Functions for Static HTML

```python
# Good: Centralized, reusable, auditable
render_section_header("Query Interface")
render_main_title()
render_footer()

# Bad: Inline HTML scattered throughout code
st.markdown('<div class="section-header">Query Interface</div>', unsafe_allow_html=True)
```

### ✅ DO: Sanitize Numeric Variables in HTML

```python
# Good: Even numeric values should be sanitized in f-strings
current_page = sanitize_html(str(st.session_state.page))
total_pages = sanitize_html(str(total))
st.markdown(f"<div>Page {current_page} of {total_pages}</div>", unsafe_allow_html=True)

# Why: URL parameters could be manipulated to inject HTML
# Example: ?page=1<script>alert(1)</script>
```

### ❌ DON'T: Trust External Data Sources

```python
# Bad: Calibre database could be compromised
book_title = calibre_db.get_title(book_id)
st.markdown(f"<h3>{book_title}</h3>", unsafe_allow_html=True)  # XSS!

# Good: Always sanitize data from external sources
book_title = sanitize_html(calibre_db.get_title(book_id))
st.markdown(f"<h3>{book_title}</h3>", unsafe_allow_html=True)
```

### ✅ DO: Prefer Streamlit Native Components

```python
# Good: Use Streamlit native components when possible
st.header("Query Interface")
st.subheader("Search Results")
st.write(f"Found {count} books")

# Avoid: Custom HTML unless absolutely necessary
st.markdown('<div class="header">Query Interface</div>', unsafe_allow_html=True)
```

---

## Security Testing

### Unit Tests: HTML Sanitizer

**Location:** `tests/test_html_sanitizer.py`
**Coverage:** 53 test cases

**Test Categories:**
1. **Basic Functionality** (6 tests): Plain text, newlines, empty input, type conversion
2. **XSS Attack Vectors** (18 tests): Script tags, iframes, event handlers, URL schemes
3. **Safe Content Validation** (4 tests): HTTP links, markdown, special characters, Unicode
4. **Edge Cases** (9 tests): Long input, nested HTML, mixed content
5. **Real-World Scenarios** (4 tests): Book titles, search queries, AI content
6. **Performance** (2 tests): Sanitization speed (< 1 second for 100 iterations)

**Run tests:**
```bash
pytest tests/test_html_sanitizer.py -v
# Expected: 53 passed in ~0.2s
```

---

### Integration Tests: XSS Prevention

**Location:** `tests/test_xss_prevention.py`
**Coverage:** 58 test cases

**Test Categories:**
1. **AI-Generated Content**: Malicious LLM responses with script tags
2. **Book Metadata**: Titles/authors with XSS payloads
3. **Pagination Displays**: Manipulated page numbers
4. **Search Results**: Query injection attempts
5. **Real-World Attack Scenarios**: OWASP Top 10 XSS patterns

**Run tests:**
```bash
pytest tests/test_xss_prevention.py -v
# Expected: All XSS attack vectors blocked
```

---

### Manual Security Testing

**Test Plan:**

1. **AI Query Injection:**
   ```
   Query: "Tell me about <script>alert('xss')</script> in books"
   Expected: Script tag is escaped, no alert dialog
   ```

2. **Book Title XSS:**
   ```
   Create book with title: <img src=x onerror=alert(1)>
   Expected: Title displays as plain text, no script execution
   ```

3. **Pagination Manipulation:**
   ```
   Manually edit URL: ?page=1<script>alert(1)</script>
   Expected: Page number sanitized, no script execution
   ```

4. **Browser Console:**
   ```
   Open DevTools → Console
   Expected: No JavaScript errors or warnings
   ```

---

## Audit & Remediation

### Current Status (2026-01-29)

**Audit Document:** `docs/unsafe_html_audit.md`

**Summary:**
- **Total unsafe_allow_html instances:** 11 (down from 16)
- **High Risk:** 1 instance (skeleton HTML construction)
- **Medium Risk:** 2 instances (CSS injection, sanitized pagination)
- **Low Risk:** 8 instances (static HTML in helper functions)

### Remediation Roadmap

#### Short-Term (1-2 weeks)
- [ ] Refactor skeleton HTML loading (Instance #6 in audit)
- [ ] Add CSS file integrity checks
- [ ] Implement ESLint-style security linting for Python

#### Medium-Term (1-3 months)
- [ ] Migrate CSS to Streamlit theme configuration (`st.set_page_config`)
- [ ] Create safe component library (headers, footers, cards)
- [ ] Replace all helper functions with Streamlit native components

#### Long-Term (3-6 months)
- [ ] Eliminate all `unsafe_allow_html=True` usage
- [ ] Implement Content Security Policy (CSP) headers
- [ ] Add automated security scanning to CI/CD pipeline
- [ ] Establish security review process for new features

---

## Incident Response

### If XSS Vulnerability is Discovered

1. **Immediate Actions:**
   - Document the vulnerability (vector, impact, affected versions)
   - Apply sanitization to affected code path
   - Create regression test to prevent recurrence

2. **Verification:**
   ```bash
   # Run full security test suite
   pytest tests/test_html_sanitizer.py tests/test_xss_prevention.py -v

   # Manual verification
   streamlit run alexandria_app.py
   # Test the specific attack vector
   ```

3. **Deployment:**
   - Create hotfix branch
   - Apply fix + tests
   - Deploy to production immediately
   - Notify users if necessary

4. **Post-Incident:**
   - Update `docs/unsafe_html_audit.md` with findings
   - Add new test cases to prevent similar issues
   - Review all similar code patterns

---

## Security Contact

**For security issues:**
- **Internal:** Contact project maintainer (Sabo)
- **External:** Create GitHub issue with `[SECURITY]` prefix (do not disclose details publicly)

**Responsible Disclosure:**
- Report vulnerabilities privately before public disclosure
- Allow 90 days for patching before public disclosure
- Credit will be given in CHANGELOG.md

---

## References

### Internal Documentation
- [Unsafe HTML Audit](./unsafe_html_audit.md) - Detailed audit of all unsafe_allow_html usage
- [Architecture Overview](./architecture/README.md) - System architecture and security controls
- [CHANGELOG.md](../CHANGELOG.md) - Security fixes and updates

### External Resources
- [OWASP XSS Prevention Cheat Sheet](https://cheats.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)
- [Streamlit Security Best Practices](https://docs.streamlit.io/library/advanced-features/security)
- [HTML Escaping Reference](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference)

### Security Standards
- OWASP Top 10: A03:2021 - Injection
- CWE-79: Improper Neutralization of Input During Web Page Generation
- NIST SP 800-53: SI-10 (Information Input Validation)

---

**Document Version:** 1.0
**Last Review:** 2026-01-29
**Next Review:** 2026-04-29 (quarterly)
