# Unsafe HTML Rendering Audit

**Date:** 2026-01-29
**Auditor:** Auto-Claude
**Scope:** All instances of `unsafe_allow_html=True` in the Alexandria codebase

## Executive Summary

This document audits all 16 instances of `unsafe_allow_html=True` usage in the Alexandria application. Each instance has been analyzed for XSS risk, categorized by risk level, and documented with remediation recommendations.

**Summary Statistics:**
- **Total Instances:** 16
- **High Risk:** 1
- **Medium Risk:** 2
- **Low Risk:** 13

## Risk Classification

- **HIGH:** User-controlled content rendered without proper sanitization
- **MEDIUM:** Dynamic content with sanitization, but still uses unsafe_allow_html
- **LOW:** Static HTML only, no user input

---

## Instance Analysis

### Instance #1: CSS Injection
**File:** `alexandria_app.py`
**Line:** 103
**Risk Level:** 🟡 **MEDIUM**

```python
st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
```

**Context:** Loads CSS from `assets/style.css` file

**Analysis:**
- Reads CSS from local file system
- File content is controlled by application developers
- However, if file permissions are misconfigured or file is compromised, malicious CSS could be injected
- CSS injection can lead to data exfiltration and UI manipulation

**Recommended Action:**
- Migrate to `st.set_page_config()` with custom theme configuration
- Or use Streamlit's `st.html()` component (if available in version)
- Add file integrity checks (checksums) before loading CSS

---

### Instance #2: Main Title (with logo)
**File:** `alexandria_app.py`
**Line:** 593
**Risk Level:** 🟢 **LOW**

```python
st.markdown('<div class="main-title">ALEXANDRIA OF TEMENOS</div>', unsafe_allow_html=True)
```

**Context:** Static header displayed when logo is present

**Analysis:**
- Completely static HTML content
- No user input or dynamic content
- No XSS risk

**Recommended Action:**
- Replace with `st.html()` component
- Or use custom Streamlit component for headers

---

### Instance #3: Main Title Fallback
**File:** `alexandria_app.py`
**Line:** 596
**Risk Level:** 🟢 **LOW**

```python
st.markdown('<div class="main-title">ALEXANDRIA OF TEMENOS</div>', unsafe_allow_html=True)
```

**Context:** Static header fallback when logo asset is missing

**Analysis:**
- Completely static HTML content
- No user input or dynamic content
- No XSS risk

**Recommended Action:**
- Replace with `st.html()` component
- Consolidate with Instance #2 to avoid duplication

---

### Instance #4: Subtitle
**File:** `alexandria_app.py`
**Line:** 597
**Risk Level:** 🟢 **LOW**

```python
st.markdown('<div class="subtitle">The Great Library Reborn</div>', unsafe_allow_html=True)
```

**Context:** Static subtitle displayed below main title

**Analysis:**
- Completely static HTML content
- No user input or dynamic content
- No XSS risk

**Recommended Action:**
- Replace with `st.html()` component

---

### Instance #5: Query Interface Section Header
**File:** `alexandria_app.py`
**Line:** 901
**Risk Level:** 🟢 **LOW**

```python
st.markdown('<div class="section-header">🔍 Query Interface</div>', unsafe_allow_html=True)
```

**Context:** Static section header for RAG query interface

**Analysis:**
- Completely static HTML content
- No user input or dynamic content
- No XSS risk

**Recommended Action:**
- Replace with `st.html()` component
- Consider creating a reusable `section_header()` helper function

---

### Instance #6: Skeleton Loading HTML
**File:** `alexandria_app.py`
**Line:** 1454
**Risk Level:** 🔴 **HIGH**

```python
st.markdown(skeleton_html, unsafe_allow_html=True)
```

**Context:** Displays loading skeleton for book browsing table

**Analysis:**
- `skeleton_html` variable is constructed dynamically (lines 1409-1453)
- Contains hardcoded CSS animations and placeholder content
- While currently using only static content, the pattern of building HTML strings is dangerous
- If future modifications add dynamic data, XSS vulnerability could be introduced
- Large HTML string construction indicates this should use a proper templating approach

**Recommended Action:**
- **PRIORITY: Refactor to use Streamlit components or st.html()**
- Move skeleton template to separate file
- Add security review process for any changes to this section
- Consider using CSS-only skeleton loaders that don't require HTML injection

---

### Instance #7: Top Pagination Info (Sanitized)
**File:** `alexandria_app.py`
**Line:** 1706
**Risk Level:** 🟡 **MEDIUM**

```python
st.markdown(f"<div style='text-align: center; padding-top: 8px;'>Page {sanitize_html(str(current_page))} of {sanitize_html(str(total_pages))} ({sanitize_html(f'{total_books:,}')} total)</div>", unsafe_allow_html=True)
```

**Context:** Displays pagination information at top of book list

**Analysis:**
- Uses `sanitize_html()` function to escape dynamic values
- Values are numeric (page numbers, counts) which are lower risk
- Sanitization is properly applied to all dynamic values
- However, still uses `unsafe_allow_html=True` which defeats the purpose of sanitization
- If sanitization function has bugs, XSS is possible

**Recommended Action:**
- **Replace with safe Streamlit components that don't require unsafe_allow_html**
- Use `st.text()` or `st.write()` with plain text formatting
- If styling is required, use st.html() with pre-sanitized content

---

### Instance #8: Pagination Spacer
**File:** `alexandria_app.py`
**Line:** 1847
**Risk Level:** 🟢 **LOW**

```python
st.markdown("<div style='margin: 10px 0;'></div>", unsafe_allow_html=True)
```

**Context:** Adds vertical spacing before bottom pagination controls

**Analysis:**
- Completely static HTML content
- No user input or dynamic content
- No XSS risk

**Recommended Action:**
- Replace with `st.write("")` or multiple `st.write("")` calls for spacing
- Or use st.html() component

---

### Instance #9: Pagination Nav Opening Div
**File:** `alexandria_app.py`
**Line:** 1848
**Risk Level:** 🟢 **LOW**

```python
st.markdown('<div class="pagination-nav">', unsafe_allow_html=True)
```

**Context:** Opens div container for pagination navigation styling

**Analysis:**
- Completely static HTML content
- No user input or dynamic content
- No XSS risk
- Note: Relies on corresponding closing tag at line 1878

**Recommended Action:**
- Replace with `st.container()` or custom Streamlit component
- Refactor to avoid manual div tag management

---

### Instance #10: Bottom Pagination Info (Sanitized)
**File:** `alexandria_app.py`
**Line:** 1868
**Risk Level:** 🟡 **MEDIUM**

```python
st.markdown(
    f"<div style='text-align: center; padding-top: 8px; color: #666; font-size: 13px;'>"
    f"Rows {sanitize_html(str(start_idx + 1))}–{sanitize_html(str(end_idx))} of {sanitize_html(f'{total_books:,}')} &nbsp;|&nbsp; Page {sanitize_html(str(current_page))} of {sanitize_html(str(total_pages))}"
    f"</div>",
    unsafe_allow_html=True
)
```

**Context:** Displays detailed pagination information at bottom of book list

**Analysis:**
- Uses `sanitize_html()` function to escape dynamic values
- Values are numeric (indices, page numbers, counts) which are lower risk
- Sanitization is properly applied to all dynamic values
- However, still uses `unsafe_allow_html=True` which defeats the purpose
- Similar issue to Instance #7

**Recommended Action:**
- **Replace with safe Streamlit components**
- Use `st.text()` or `st.write()` with plain text formatting
- Consolidate with Instance #7 to create a reusable safe pagination component

---

### Instance #11: Pagination Nav Closing Div
**File:** `alexandria_app.py`
**Line:** 1878
**Risk Level:** 🟢 **LOW**

```python
st.markdown('</div>', unsafe_allow_html=True)
```

**Context:** Closes div container opened at line 1848

**Analysis:**
- Completely static HTML content
- No user input or dynamic content
- No XSS risk
- Paired with Instance #9

**Recommended Action:**
- Eliminate when refactoring Instance #9 to use Streamlit containers

---

### Instance #12: Calibre Library Section Header
**File:** `alexandria_app.py`
**Line:** 1946
**Risk Level:** 🟢 **LOW**

```python
st.markdown('<div class="section-header">📚 Calibre Library</div>', unsafe_allow_html=True)
```

**Context:** Static section header for Calibre library tab

**Analysis:**
- Completely static HTML content
- No user input or dynamic content
- No XSS risk

**Recommended Action:**
- Replace with `st.html()` component
- Consolidate with other section headers (Instances #5, #13, #14, #15)

---

### Instance #13: Ingested Books Section Header
**File:** `alexandria_app.py`
**Line:** 2270
**Risk Level:** 🟢 **LOW**

```python
st.markdown('<div class="section-header">📖 Ingested Books</div>', unsafe_allow_html=True)
```

**Context:** Static section header for Ingested Books tab

**Analysis:**
- Completely static HTML content
- No user input or dynamic content
- No XSS risk

**Recommended Action:**
- Replace with `st.html()` component
- Consolidate with other section headers

---

### Instance #14: Ingestion Pipeline Section Header
**File:** `alexandria_app.py`
**Line:** 2327
**Risk Level:** 🟢 **LOW**

```python
st.markdown('<div class="section-header">🔄 Ingestion Pipeline</div>', unsafe_allow_html=True)
```

**Context:** Static section header for Ingestion Pipeline tab

**Analysis:**
- Completely static HTML content
- No user input or dynamic content
- No XSS risk

**Recommended Action:**
- Replace with `st.html()` component
- Consolidate with other section headers

---

### Instance #15: Restore Deleted Section Header
**File:** `alexandria_app.py`
**Line:** 2709
**Risk Level:** 🟢 **LOW**

```python
st.markdown('<div class="section-header">🗄️ Restore deleted</div>', unsafe_allow_html=True)
```

**Context:** Static section header for Restore deleted tab

**Analysis:**
- Completely static HTML content
- No user input or dynamic content
- No XSS risk

**Recommended Action:**
- Replace with `st.html()` component
- Consolidate with other section headers

---

### Instance #16: Footer
**File:** `alexandria_app.py`
**Line:** 3022
**Risk Level:** 🟢 **LOW**

```python
st.markdown(
    '<div class="footer">'
    '𝔸𝕝𝕖𝕩𝕒𝕟𝕕𝕣𝕚𝕒 𝕠𝕗 𝕋𝕖𝕞𝕖𝕟𝕠𝕤 • '
    'Built with ❤️ by 137 Team • 2026'
    '</div>',
    unsafe_allow_html=True
)
```

**Context:** Static footer displayed at bottom of application

**Analysis:**
- Completely static HTML content
- No user input or dynamic content
- No XSS risk

**Recommended Action:**
- Replace with `st.html()` component

---

## Remediation Priority

### Critical (Immediate Action Required)

1. **Instance #6 - Skeleton Loading HTML (Line 1454)**
   - High risk due to complex HTML string construction
   - Refactor to use component-based approach
   - Add security review for any changes

### High Priority (Address in Next Sprint)

2. **Instance #1 - CSS Injection (Line 103)**
   - Medium risk from file-based CSS loading
   - Migrate to Streamlit theme configuration
   - Add file integrity verification

3. **Instances #7, #10 - Pagination Info (Lines 1706, 1868)**
   - Medium risk despite sanitization
   - Create safe reusable pagination component
   - Remove dependency on unsafe_allow_html

### Medium Priority (Technical Debt)

4. **All Static Content Instances (#2-5, #8-9, #11-16)**
   - Low risk but violates security best practices
   - Create helper functions for common patterns:
     - `section_header(text: str)` for section headers
     - `render_footer()` for footer
     - Use Streamlit containers instead of manual divs

## Recommendations

### Short-term (Current Sprint)
1. Address critical Instance #6 (skeleton HTML)
2. Document all unsafe_allow_html usage in code comments with justification
3. Add linting rule to flag new unsafe_allow_html usage

### Medium-term (Next Quarter)
1. Refactor CSS loading mechanism (Instance #1)
2. Create safe component library for:
   - Section headers
   - Pagination displays
   - Footer rendering
3. Replace all pagination unsafe_allow_html with safe components (Instances #7, #10)

### Long-term (Architecture)
1. Establish security review process for UI changes
2. Create custom Streamlit components for all branded UI elements
3. Eliminate all unsafe_allow_html usage from codebase
4. Add automated security scanning for XSS vulnerabilities

## Existing Mitigations

The codebase includes `scripts/html_sanitizer.py` which provides:
- `sanitize_html()`: Escapes HTML special characters
- `sanitize_for_markdown()`: Wrapper for markdown rendering

**Current Usage:**
- Instances #7 and #10 use sanitization for dynamic values
- However, using sanitization WITH `unsafe_allow_html=True` is contradictory
- The proper solution is to use safe Streamlit components instead

## Conclusion

While the current XSS risk is relatively low due to minimal user-controlled content, the widespread use of `unsafe_allow_html=True` creates technical debt and potential security vulnerabilities. The priority should be:

1. **Immediate:** Refactor skeleton HTML (Instance #6)
2. **Short-term:** Replace dynamic content with safe components (Instances #1, #7, #10)
3. **Long-term:** Eliminate all unsafe_allow_html usage through proper component architecture

This audit should be reviewed quarterly and updated as the codebase evolves.

---

**Next Review Date:** 2026-04-29
