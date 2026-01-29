# Manual Testing Results

Date: 2026-01-29
Tester: QA Fix Agent
Status: PENDING MANUAL VERIFICATION

## Browser Tests

### Prerequisites
- [ ] Qdrant is running: `docker ps | grep qdrant`
- [ ] Collection has ingested books: `python scripts/collection_manifest.py show alexandria`
- [ ] Streamlit started: `streamlit run alexandria_app.py`

### Test Cases

- [ ] **TC1: Book dropdown appears** - PASS/FAIL
  - Navigate to RAG Query tab
  - Verify book filter dropdown exists in column 3
  - Verify label is "Book"
  - Screenshot: _[attach here]_

- [ ] **TC2: Book dropdown populates** - PASS/FAIL
  - Verify "all" is first option
  - Verify book titles appear
  - Verify alphabetical sorting
  - Verify no duplicates
  - Screenshot: _[attach here]_

- [ ] **TC3: Book filter works** - PASS/FAIL
  - Select specific book (e.g., "Design Patterns")
  - Enter query: "factory pattern"
  - Click "Run Query"
  - Verify ALL results show selected book in "Book:" field
  - Verify NO results from other books
  - Screenshot: _[attach here]_

- [ ] **TC4: "all" option works** - PASS/FAIL
  - Select "all" from dropdown
  - Enter query that spans books
  - Verify results from multiple books appear
  - Screenshot: _[attach here]_

- [ ] **TC5: Combined filters work** - PASS/FAIL
  - Select domain: "technical"
  - Select book: "Clean Code"
  - Enter query: "refactoring"
  - Verify results match BOTH filters
  - No results outside technical domain
  - No results from other books
  - Screenshot: _[attach here]_

- [ ] **TC6: Console clean** - PASS/FAIL
  - Open browser DevTools (F12) → Console
  - Perform above tests
  - Verify NO JavaScript errors (red messages)
  - Verify NO failed network requests
  - Screenshot: _[attach here]_

- [ ] **TC7: State persistence** - PASS/FAIL
  - Select a book
  - Run query
  - Navigate to "Ingest Books" tab
  - Return to "RAG Query" tab
  - Verify book selection preserved

## CLI Tests

### Test Commands

- [ ] **TC8: --book in help** - PASS/FAIL
  ```bash
  python scripts/rag_query.py --help | grep -i book
  ```
  Expected: Shows --book flag and description
  Output: _[paste here]_

- [ ] **TC9: Book filter works** - PASS/FAIL
  ```bash
  python scripts/rag_query.py "design patterns" --book "Design Patterns" --limit 3
  ```
  Expected: Results only from "Design Patterns" book
  Expected: Log shows "📖 Filtering by book: Design Patterns"
  Output: _[paste here]_

- [ ] **TC10: Combined filters** - PASS/FAIL
  ```bash
  python scripts/rag_query.py "database normalization" --domain technical --book "Database System Concepts" --limit 3
  ```
  Expected: Results match both domain AND book
  Expected: Logs show both filters applied
  Output: _[paste here]_

- [ ] **TC11: Backward compatibility** - PASS/FAIL
  ```bash
  python scripts/rag_query.py "query" --limit 3
  ```
  Expected: Works normally, results from all books
  Output: _[paste here]_

## Issues Found

_List any issues discovered during testing:_

1. [Issue 1 if any]
2. [Issue 2 if any]

## Conclusion

**Overall Status**: PASS / FAIL

**Summary**: _[Brief summary of testing results]_

**Notes**:
- All test cases must pass before QA approval
- Screenshots required for browser tests
- CLI output samples required for CLI tests
- Any failures must be fixed before resubmission
