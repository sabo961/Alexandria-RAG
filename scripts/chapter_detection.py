#!/usr/bin/env python3
"""
Alexandria Chapter Detection Module
====================================

Detects chapter/section boundaries in books for hierarchical chunking.

Detection strategies (in priority order):
1. EPUB NCX/TOC navigation (most reliable)
2. EPUB NAV document (EPUB 3.0)
3. HTML heading tags (h1, h2)
4. Token-based fallback (every 5000 tokens)

Usage:
    from chapter_detection import detect_chapters

    chapters = detect_chapters(filepath, text, metadata)
    # Returns: [{"title": "Chapter 1", "text": "...", "index": 0}, ...]
"""

import logging
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

# EPUB parsing
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup, NavigableString

# PDF parsing
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


@dataclass
class Chapter:
    """Represents a detected chapter/section."""
    title: str
    text: str
    index: int
    start_position: int = 0  # Character position in original text
    detection_method: str = "unknown"


# =============================================================================
# MAIN API
# =============================================================================

def detect_chapters(
    filepath: str,
    text: str,
    metadata: Dict,
    fallback_tokens: int = 5000,
    min_chapter_tokens: int = 500
) -> List[Dict]:
    """
    Detect chapter boundaries in a book.

    Args:
        filepath: Path to the book file
        text: Full extracted text (for fallback)
        metadata: Book metadata including 'format'
        fallback_tokens: Tokens per chapter in fallback mode
        min_chapter_tokens: Minimum chapter size (skip tiny chapters)

    Returns:
        List of chapter dicts: [{"title": "...", "text": "...", "index": 0}, ...]
    """
    ext = Path(filepath).suffix.lower()

    chapters = []
    detection_method = "fallback"

    try:
        if ext == '.epub':
            chapters, detection_method = detect_epub_chapters(filepath, min_chapter_tokens)
        elif ext == '.pdf':
            chapters, detection_method = detect_pdf_chapters(filepath, min_chapter_tokens)
        # TXT, MD, HTML use fallback
    except Exception as e:
        logger.warning(f"Chapter detection failed for {filepath}: {e}")

    # Fallback if no chapters detected
    if not chapters:
        chapters = fallback_token_split(text, fallback_tokens, min_chapter_tokens)
        detection_method = "fallback_tokens"

    logger.info(f"Chapter detection: {detection_method}, found {len(chapters)} chapters")

    # Convert to dict format
    return [
        {
            "title": ch.title if isinstance(ch, Chapter) else ch.get("title", f"Section {i+1}"),
            "text": ch.text if isinstance(ch, Chapter) else ch.get("text", ""),
            "index": i,
            "detection_method": detection_method
        }
        for i, ch in enumerate(chapters)
    ]


# =============================================================================
# EPUB CHAPTER DETECTION
# =============================================================================

def detect_epub_chapters(
    filepath: str,
    min_tokens: int = 500
) -> Tuple[List[Chapter], str]:
    """
    Detect chapters from EPUB using NCX/NAV structure.

    Returns:
        (chapters, detection_method)
    """
    book = epub.read_epub(filepath)

    # Strategy 1: Try NCX (EPUB 2.0)
    chapters = extract_from_ncx(book)
    if chapters:
        return filter_small_chapters(chapters, min_tokens), "epub_ncx"

    # Strategy 2: Try NAV (EPUB 3.0)
    chapters = extract_from_nav(book)
    if chapters:
        return filter_small_chapters(chapters, min_tokens), "epub_nav"

    # Strategy 3: Use document items as chapters
    chapters = extract_from_items(book)
    if chapters:
        return filter_small_chapters(chapters, min_tokens), "epub_items"

    return [], "none"


def extract_from_ncx(book: epub.EpubBook) -> List[Chapter]:
    """Extract chapters from NCX navigation (EPUB 2.0)."""
    chapters = []

    try:
        # Get NCX item
        ncx_item = None
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_NAVIGATION:
                ncx_item = item
                break

        if not ncx_item:
            return []

        # Parse NCX XML
        soup = BeautifulSoup(ncx_item.get_content(), 'xml')
        nav_points = soup.find_all('navPoint')

        # Build href -> (full_content, soup) mapping
        href_data = {}
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                href = item.get_name()
                content = item.get_content().decode('utf-8', errors='ignore')
                item_soup = BeautifulSoup(content, 'html.parser')
                href_data[href] = item_soup

        # Collect navigation info with fragments
        nav_info = []
        for nav_point in nav_points:
            label = nav_point.find('navLabel')
            if not label:
                continue
            text_elem = label.find('text')
            title = text_elem.get_text(strip=True) if text_elem else None
            if not title:
                continue

            content_ref = nav_point.find('content')
            if not content_ref:
                continue

            src = content_ref.get('src', '')
            if '#' in src:
                base_href, fragment = src.split('#', 1)
            else:
                base_href, fragment = src, None

            nav_info.append({
                'title': title,
                'href': base_href,
                'fragment': fragment
            })

        if not nav_info:
            return []

        # Group nav points by base href to handle both single-file and
        # multi-file EPUBs with per-file fragment extraction.
        href_groups = {}
        for i, nav in enumerate(nav_info):
            href = nav['href']
            if href not in href_groups:
                href_groups[href] = []
            href_groups[href].append((i, nav))

        for href, nav_list in href_groups.items():
            if href not in href_data:
                continue

            file_soup = href_data[href]
            has_fragments = any(nav['fragment'] for _, nav in nav_list)

            if len(nav_list) == 1 and not has_fragments:
                # Single nav point, no fragment → full file text
                idx, nav = nav_list[0]
                chapter_text = file_soup.get_text(separator='\n', strip=True)
                if chapter_text.strip():
                    chapters.append(Chapter(
                        title=nav['title'], text=chapter_text,
                        index=idx, detection_method="epub_ncx"
                    ))
            elif not has_fragments:
                # Multiple nav points without fragments → deduplicate to one
                idx, nav = nav_list[0]
                chapter_text = file_soup.get_text(separator='\n', strip=True)
                if chapter_text.strip():
                    chapters.append(Chapter(
                        title=nav['title'], text=chapter_text,
                        index=idx, detection_method="epub_ncx"
                    ))
            else:
                # Fragment-based: extract text between anchors within this file
                # Collect fragment IDs for this file's nav points
                file_frag_ids = [nav['fragment'] for _, nav in nav_list if nav['fragment']]

                for j, (idx, nav) in enumerate(nav_list):
                    fragment_id = nav['fragment']
                    if not fragment_id:
                        continue

                    anchor = file_soup.find(id=fragment_id)
                    if not anchor:
                        continue

                    # Stop IDs: later fragments within THIS file
                    later_ids = set()
                    for k in range(j + 1, len(nav_list)):
                        fid = nav_list[k][1]['fragment']
                        if fid:
                            later_ids.add(fid)

                    # Walk document in order from anchor, collecting text nodes
                    chapter_text_parts = []
                    current = anchor
                    while current is not None:
                        if current is not anchor and later_ids:
                            eid = current.get('id') if hasattr(current, 'get') else None
                            if eid in later_ids:
                                break

                        if isinstance(current, NavigableString):
                            text = current.strip()
                            if text:
                                chapter_text_parts.append(text)

                        current = current.next_element

                    chapter_text = '\n'.join(chapter_text_parts)
                    if chapter_text.strip():
                        chapters.append(Chapter(
                            title=nav['title'], text=chapter_text,
                            index=idx, detection_method="epub_ncx_fragments"
                        ))

        # Sort by original nav index to preserve document order
        chapters.sort(key=lambda ch: ch.index)

    except Exception as e:
        logger.debug(f"NCX extraction failed: {e}")

    return chapters


def extract_from_nav(book: epub.EpubBook) -> List[Chapter]:
    """Extract chapters from NAV document (EPUB 3.0)."""
    chapters = []

    try:
        # Find NAV item
        nav_item = None
        for item in book.get_items():
            if isinstance(item, epub.EpubNav):
                nav_item = item
                break

        if not nav_item:
            return []

        # Parse NAV HTML
        soup = BeautifulSoup(nav_item.get_content(), 'html.parser')
        toc = soup.find('nav', {'epub:type': 'toc'}) or soup.find('nav')

        if not toc:
            return []

        # Build href -> content mapping
        href_content = {}
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                href = item.get_name()
                content = item.get_content().decode('utf-8', errors='ignore')
                text = BeautifulSoup(content, 'html.parser').get_text(separator='\n', strip=True)
                href_content[href] = text

        # Extract from <a> links in TOC
        links = toc.find_all('a')
        for i, link in enumerate(links):
            title = link.get_text(strip=True)
            href = link.get('href', '').split('#')[0]

            chapter_text = href_content.get(href, '')
            if chapter_text:
                chapters.append(Chapter(
                    title=title,
                    text=chapter_text,
                    index=i,
                    detection_method="epub_nav"
                ))

    except Exception as e:
        logger.debug(f"NAV extraction failed: {e}")

    return chapters


def extract_from_items(book: epub.EpubBook) -> List[Chapter]:
    """Fallback: treat each document item as a chapter."""
    chapters = []

    for i, item in enumerate(book.get_items()):
        if item.get_type() != ebooklib.ITEM_DOCUMENT:
            continue

        content = item.get_content().decode('utf-8', errors='ignore')
        soup = BeautifulSoup(content, 'html.parser')
        text = soup.get_text(separator='\n', strip=True)

        if not text or len(text) < 100:  # Skip empty/tiny items
            continue

        # Try to get title from h1/h2
        title_tag = soup.find(['h1', 'h2'])
        title = title_tag.get_text(strip=True) if title_tag else f"Section {len(chapters)+1}"

        chapters.append(Chapter(
            title=title,
            text=text,
            index=len(chapters),
            detection_method="epub_items"
        ))

    return chapters


# =============================================================================
# PDF CHAPTER DETECTION
# =============================================================================

def detect_pdf_chapters(
    filepath: str,
    min_tokens: int = 500
) -> Tuple[List[Chapter], str]:
    """
    Detect chapters from PDF using outline/bookmarks.

    Returns:
        (chapters, detection_method)
    """
    doc = fitz.open(filepath)

    # Strategy 1: Try PDF outline/bookmarks
    chapters = extract_from_outline(doc)
    if chapters:
        doc.close()
        return filter_small_chapters(chapters, min_tokens), "pdf_outline"

    # Strategy 2: Detect heading patterns
    chapters = extract_from_headings(doc)
    if chapters:
        doc.close()
        return filter_small_chapters(chapters, min_tokens), "pdf_headings"

    doc.close()
    return [], "none"


def extract_from_outline(doc: fitz.Document) -> List[Chapter]:
    """Extract chapters from PDF outline/bookmarks."""
    chapters = []

    try:
        toc = doc.get_toc()  # [(level, title, page), ...]

        if not toc:
            return []

        # Get text for each chapter (from page to next chapter's page)
        for i, (level, title, page) in enumerate(toc):
            if level > 1:  # Skip sub-chapters for now
                continue

            # Determine page range
            start_page = page - 1  # 0-indexed
            if i + 1 < len(toc):
                end_page = toc[i + 1][2] - 1
            else:
                end_page = doc.page_count

            # Extract text from page range
            text_parts = []
            for p in range(max(0, start_page), min(end_page, doc.page_count)):
                text_parts.append(doc[p].get_text())

            chapter_text = '\n'.join(text_parts)

            if chapter_text.strip():
                chapters.append(Chapter(
                    title=title,
                    text=chapter_text,
                    index=len(chapters),
                    detection_method="pdf_outline"
                ))

    except Exception as e:
        logger.debug(f"PDF outline extraction failed: {e}")

    return chapters


def extract_from_headings(doc: fitz.Document) -> List[Chapter]:
    """
    Detect chapters by looking for heading patterns in text.

    Looks for:
    - "Chapter N" / "CHAPTER N"
    - "Part N" / "PART N"
    - Numbered sections like "1." "2."
    """
    chapters = []

    # Patterns that indicate chapter start
    chapter_patterns = [
        r'^CHAPTER\s+\d+',
        r'^Chapter\s+\d+',
        r'^PART\s+[IVX\d]+',
        r'^Part\s+[IVX\d]+',
        r'^\d+\.\s+[A-Z]',  # "1. Title"
    ]
    combined_pattern = '|'.join(f'({p})' for p in chapter_patterns)

    current_title = "Introduction"
    current_text = []

    for page in doc:
        page_text = page.get_text()
        lines = page_text.split('\n')

        for line in lines:
            line_stripped = line.strip()

            # Check if this line starts a new chapter
            if re.match(combined_pattern, line_stripped):
                # Save previous chapter
                if current_text:
                    chapters.append(Chapter(
                        title=current_title,
                        text='\n'.join(current_text),
                        index=len(chapters),
                        detection_method="pdf_headings"
                    ))

                current_title = line_stripped
                current_text = []
            else:
                current_text.append(line)

    # Don't forget last chapter
    if current_text:
        chapters.append(Chapter(
            title=current_title,
            text='\n'.join(current_text),
            index=len(chapters),
            detection_method="pdf_headings"
        ))

    return chapters


# =============================================================================
# FALLBACK & UTILITIES
# =============================================================================

def fallback_token_split(
    text: str,
    tokens_per_chunk: int = 5000,
    min_tokens: int = 500
) -> List[Chapter]:
    """
    Split text into chapters by token count.

    Uses ~1.3 tokens per word as rough estimate.
    """
    words = text.split()
    words_per_chunk = int(tokens_per_chunk / 1.3)

    chapters = []
    for i in range(0, len(words), words_per_chunk):
        chunk_words = words[i:i + words_per_chunk]
        chunk_text = ' '.join(chunk_words)

        # Skip tiny chunks
        if len(chunk_words) < min_tokens / 1.3:
            continue

        chapters.append(Chapter(
            title=f"Section {len(chapters) + 1}",
            text=chunk_text,
            index=len(chapters),
            detection_method="fallback_tokens"
        ))

    return chapters


def filter_small_chapters(
    chapters: List[Chapter],
    min_tokens: int = 500
) -> List[Chapter]:
    """Remove chapters below minimum token threshold."""
    min_words = int(min_tokens / 1.3)
    return [
        ch for ch in chapters
        if len(ch.text.split()) >= min_words
    ]


def estimate_token_count(text: str) -> int:
    """Rough token count estimate (~1.3 tokens per word)."""
    return int(len(text.split()) * 1.3)


# =============================================================================
# CLI TESTING
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test chapter detection")
    parser.add_argument("filepath", help="Path to book file")
    parser.add_argument("--min-tokens", type=int, default=500, help="Minimum chapter size")
    parser.add_argument("--fallback-tokens", type=int, default=5000, help="Tokens per fallback chapter")

    args = parser.parse_args()

    # Read file to get text
    from ingest_books import extract_text
    text, metadata = extract_text(args.filepath)

    # Detect chapters
    chapters = detect_chapters(
        args.filepath,
        text,
        metadata,
        fallback_tokens=args.fallback_tokens,
        min_chapter_tokens=args.min_tokens
    )

    print(f"\n{'='*70}")
    print(f"Chapter Detection Results: {Path(args.filepath).name}")
    print(f"{'='*70}")
    print(f"Total chapters: {len(chapters)}")
    print(f"Detection method: {chapters[0]['detection_method'] if chapters else 'none'}")
    print()

    for ch in chapters:
        word_count = len(ch['text'].split())
        print(f"[{ch['index']:2d}] {ch['title'][:50]:<50} ({word_count:,} words)")

    print(f"\n{'='*70}\n")
