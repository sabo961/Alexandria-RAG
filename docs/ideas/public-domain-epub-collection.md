# Idea: Public Domain EPUB Collection

**Status:** Idea
**Created:** 2026-01-30
**Effort:** Low-Medium (ongoing)

---

## Concept

Replace PDF-only books with public domain EPUB versions where available. EPUB provides cleaner text extraction and better structure for hierarchical chunking.

## Why

- **Better chunking** - EPUB has proper chapter structure (NCX/NAV)
- **Cleaner text** - No PDF extraction artifacts
- **Smaller files** - EPUB typically smaller than PDF
- **Hierarchical support** - TOC maps directly to parent chunks

## Sources for Public Domain EPUBs

| Source | Collection | API |
|--------|-----------|-----|
| **Project Gutenberg** | 60,000+ books | gutendex.com (unofficial REST API) |
| **Standard Ebooks** | 800+ curated | OPDS feed + GitHub repo |
| **Internet Archive** | Vast, variable quality | archive.org/advancedsearch.php |
| **Open Library** | 4M+ books | openlibrary.org/developers/api |

All searchable by title/author, direct EPUB download links.

## Implementation

1. **Identify PDF-only books** in Calibre that are public domain (pre-1928 US, or author 70+ years dead)
2. **Search sources** for EPUB version
3. **Download and add** to Calibre (replaces or supplements PDF)
4. **Re-ingest** to Qdrant with hierarchical chunking

## Calibre Integration

Calibre can:
- Store multiple formats per book (PDF + EPUB)
- Prefer EPUB for reading/export
- Track which format was used for ingestion

## Automation Potential

**Use Claude Haiku for matching:**
- Input: Book title + author from Calibre
- Task: Search Gutenberg/Archive for matching EPUB
- Output: Download URL or "not found"

## Priority Candidates

Focus on books where PDF extraction is problematic:
- Scanned PDFs (OCR quality issues)
- Multi-column layouts
- Books with many footnotes
- Philosophy/classics (often available on Gutenberg)

---

## References

- Project Gutenberg: https://www.gutenberg.org/
- Standard Ebooks: https://standardebooks.org/
- Internet Archive: https://archive.org/details/texts
