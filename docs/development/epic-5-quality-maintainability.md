---
epic: 5
title: "Quality & Maintainability"
status: pending
priority: P2
estimated_stories: 3
---

# Epic 5: Quality & Maintainability

Address technical debt and improve test coverage for long-term maintainability.

**User Outcome:** Codebase is well-tested, configurable, and maintainable for future development.

**FRs Covered:** FR-002 (configurable chunking), FR-003 (configurable paths), NFR-004 (maintainability)

**ADR References:** ADR-0003 (Single Source of Truth), project-context.md (testing rules)

**Current State (Technical Debt):**
- ❌ Interactive chunking GUI lost (needs recreation)
- ❌ Universal chunking parameters hardcoded (need Settings sidebar)
- ❌ Calibre library path hardcoded (regression - was configurable)
- ✅ tqdm replaced with callbacks (will be fixed in Epic 4)
- ❌ Qdrant server location hardcoded (needs Settings)
- ❌ Test coverage ~4% (target: >80%)

**Target State:**
- All 6 technical debt items resolved
- Test coverage >80% (pytest unit tests + Playwright UI tests)
- Configuration via Settings sidebar (no hardcoded paths)
- Interactive chunking GUI recreated

---

## Stories

### Story 5.1: Configuration & Technical Debt Fixes

**Status:** ⏳ PENDING

As a **system maintainer**,
I want **all hardcoded configuration moved to Settings sidebar**,
So that **Alexandria is configurable without editing code**.

**Acceptance Criteria:**

**Given** I open Alexandria Settings
**When** I view configuration options
**Then** I can configure:
  - Calibre library path
  - Qdrant server location (host, port)
  - Universal chunking parameters (threshold, min/max chunk size)
  - Embedding model selection
  - Default collection name

**Technical Tasks:**

- [ ] Fix TD-001: Recreate interactive chunking GUI
  - Streamlit sidebar with threshold slider, min/max chunk size inputs
  - Live preview with sample text
- [ ] Fix TD-002: Make universal chunking configurable
  - Settings: threshold (0.3-0.7), min_chunk_size (100-500), max_chunk_size (1000-2000)
  - Default values from config
- [ ] Fix TD-003: Restore Calibre library path configuration
  - Settings: text input with path validation
  - Save to .env or config file
- [ ] Fix TD-005: Make Qdrant server location configurable
  - Settings: host, port inputs
  - Connection test button
- [ ] Create Settings sidebar in `alexandria_app.py`
- [ ] Persist settings to `.streamlit/config.toml` or `.env`

**Files Modified:**
- `alexandria_app.py` (add Settings sidebar)
- `scripts/config.py` (load settings from file)

**Definition of Done:**
- All settings configurable via UI
- Settings persisted across restarts
- No hardcoded paths or parameters in code

---

### Story 5.2: Comprehensive Test Coverage

**Status:** ⏳ PENDING

As a **QA engineer**,
I want **test coverage >80%**,
So that **regressions are caught automatically**.

**Acceptance Criteria:**

**Given** I run `pytest tests/`
**When** tests execute
**Then** coverage report shows >80% for core modules:
  - `scripts/ingest_books.py` (>90%)
  - `scripts/rag_query.py` (>90%)
  - `scripts/universal_chunking.py` (>95%)
  - `scripts/chapter_detection.py` (>85%)
  - `scripts/collection_manifest.py` (>85%)

**Technical Tasks:**

- [ ] Create unit tests:
  - `tests/test_ingest.py` - ingestion pipeline
  - `tests/test_chunking.py` - semantic chunking
  - `tests/test_query.py` - RAG query
  - `tests/test_chapter_detection.py` - chapter detection
  - `tests/test_collection.py` - collection management
- [ ] Create integration tests:
  - `tests/integration/test_end_to_end.py` - full ingest + query flow
- [ ] Add Playwright UI tests (if GUI exists):
  - `tests/ui/test_streamlit_app.py`
- [ ] Add CI/CD test automation (GitHub Actions or similar)
- [ ] Generate coverage report: `pytest --cov=scripts --cov-report=html`

**Files Modified:**
- `tests/` directory (new test files)
- `.github/workflows/tests.yml` (new CI/CD)

**Definition of Done:**
- Test coverage >80% overall
- All core modules >85% coverage
- Tests run in CI/CD
- Coverage report generated

---

### Story 5.3: XSS Prevention & Input Sanitization

**Status:** 🟢 IN PROGRESS (Security foundations complete)

As a **security engineer**,
I want **comprehensive XSS protection and input sanitization**,
So that **Alexandria is secure against injection attacks**.

**Acceptance Criteria:**

**Given** I render dynamic content from AI, user input, or external sources
**When** content is displayed in the UI
**Then**:
  - All HTML entities are properly escaped
  - No script execution from untrusted content
  - XSS attack patterns are blocked
  - Unsafe HTML usage is minimized

**Technical Tasks:**

**✅ COMPLETED:**
- [x] HTML sanitization utilities (`scripts/html_sanitizer.py`)
  - `sanitize_html()` - Escape all HTML entities
  - `is_safe_html()` - Detect 39 XSS patterns
  - `sanitize_for_markdown()` - Streamlit markdown wrapper
- [x] XSS attack pattern detection (10 dangerous tags, 16 event handlers, 4 URL schemes)
- [x] Unit tests (`tests/test_html_sanitizer.py`) - 53 test cases
- [x] Integration tests (`tests/test_xss_prevention.py`) - 58 test cases
- [x] Unsafe HTML audit (`docs/development/security/unsafe_html_audit.md`)
  - 16 instances audited, categorized by risk level
  - 1 high risk, 2 medium risk, 13 low risk
- [x] Security documentation (`docs/development/security/SECURITY.md`)

**⏳ PENDING - Short-term (1-2 weeks):**
- [ ] Refactor skeleton HTML loading (Instance #6 - HIGH RISK)
  - Move skeleton template to separate file
  - Use Streamlit components or st.html()
  - Add security review process for UI changes
- [ ] Add CSS file integrity checks
  - Checksum validation before loading `assets/style.css`
  - Prevent CSS injection attacks
- [ ] Implement ESLint-style security linting for Python
  - Pre-commit hook to flag new `unsafe_allow_html` usage
  - Automated XSS pattern detection

**⏳ PENDING - Medium-term (1-3 months):**
- [ ] Migrate CSS to Streamlit theme configuration (`st.set_page_config`)
  - Eliminate CSS file loading via `unsafe_allow_html`
- [ ] Create safe component library (headers, footers, cards)
  - Replace 13 low-risk static HTML instances
  - Consolidate section headers into reusable functions
- [ ] Replace pagination displays with safe components (Instances #7, #10)
  - Remove dependency on `unsafe_allow_html` for numeric values
  - Use `st.text()` or `st.write()` with plain text formatting

**⏳ PENDING - Long-term (3-6 months):**
- [ ] Eliminate all `unsafe_allow_html=True` usage (target: 0 instances)
- [ ] Implement Content Security Policy (CSP) headers
  - Prevent inline script execution
  - Whitelist safe content sources
- [ ] Add automated security scanning to CI/CD pipeline
  - Bandit for Python security linting
  - OWASP dependency check
- [ ] Establish security review process for new features
  - Mandatory review for any `unsafe_allow_html` addition
  - XSS testing checklist for UI changes

**Files Modified:**
- ✅ `scripts/html_sanitizer.py` (created)
- ✅ `tests/test_html_sanitizer.py` (created)
- ✅ `tests/test_xss_prevention.py` (created)
- ⏳ `alexandria_app.py` (refactor skeleton HTML, pagination, CSS loading)
- ⏳ `.pre-commit-config.yaml` (add security linting)
- ⏳ `.github/workflows/security.yml` (CI/CD security scanning)

**Security Standards Compliance:**
- OWASP Top 10: A03:2021 - Injection (XSS)
- CWE-79: Improper Neutralization of Input During Web Page Generation
- NIST SP 800-53: SI-10 (Information Input Validation)

**Definition of Done:**
- All high-risk instances refactored
- CSS file integrity checks in place
- Pre-commit security linting active
- Zero new `unsafe_allow_html` instances without review
- Security documentation maintained quarterly

---

## Epic Summary

**Total Stories:** 3
**Status:** 🟢 IN PROGRESS (Story 5.3 security foundations complete)

**Technical Debt Items:**
1. ✅ TD-004: tqdm → callbacks (Epic 4)
2. ⏳ TD-001: Recreate interactive chunking GUI
3. ⏳ TD-002: Configurable universal chunking parameters
4. ⏳ TD-003: Restore Calibre path configuration
5. ⏳ TD-005: Configurable Qdrant server location
6. ⏳ TD-006: Increase test coverage to >80%

**Success Metrics:**
- All 6 technical debt items resolved
- Test coverage >80%
- Configuration via Settings (no code editing)
