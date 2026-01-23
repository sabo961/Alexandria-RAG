"""
Alexandria Book Ingestion Script

Unified ingestion pipeline for EPUB, PDF, MOBI, and TXT files.
Supports domain-specific chunking strategies and uploads to Qdrant.

Usage:
    python ingest_books.py --file "path/to/book.epub" --domain technical
    python ingest_books.py --file "path/to/book.pdf" --domain psychology --collection alexandria_test
"""

import os
import argparse
import uuid
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import logging

# Book parsing libraries
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import fitz  # PyMuPDF

# NLP & Embeddings
from sentence_transformers import SentenceTransformer

# Qdrant
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# Philosophical chunking
from philosophical_chunking import argument_prechunk, should_use_argument_chunking

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# TEXT EXTRACTION
# ============================================================================

def normalize_file_path(filepath: str) -> Tuple[str, str, bool, int]:
    """
    Normalize paths for cross-platform file access.

    Returns:
        path_for_open: Path safe for os.open/fitz/etc.
        display_path: Readable absolute path for logs/UI
        used_long_path: Whether Windows long-path prefix was applied
    """
    expanded = os.path.expanduser(filepath)
    abs_path = os.path.abspath(expanded)
    path_for_open = abs_path
    used_long_path = False

    if os.name == "nt" and not abs_path.startswith("\\\\?\\"):
        # Windows long-path support (>= 248 chars for files)
        if len(abs_path) >= 248:
            if abs_path.startswith("\\\\"):
                # UNC path
                path_for_open = "\\\\?\\UNC\\" + abs_path.lstrip("\\")
            else:
                path_for_open = "\\\\?\\" + abs_path
            used_long_path = True

    return path_for_open, abs_path, used_long_path, len(abs_path)


def validate_file_access(path_for_open: str, display_path: str) -> Tuple[bool, Optional[str]]:
    """
    Validate file exists and is readable. Returns (ok, error_message).
    """
    if not os.path.exists(path_for_open):
        return False, (
            f"File not found: {display_path}. "
            "If this is a cloud-synced file, ensure it is available offline."
        )

    try:
        os.stat(path_for_open)
        with open(path_for_open, 'rb') as f:
            f.read(1)
        return True, None
    except OSError as e:
        hint_parts = []
        if os.name == "nt" and getattr(e, "errno", None) == 22:
            hint_parts.append(
                "Windows path may be too long. Try moving the file to a shorter path "
                "or enable long paths in Windows policy/registry."
            )
        hint_parts.append(
            "If using Google Drive/OneDrive, ensure the file is fully downloaded."
        )
        hint = " ".join(hint_parts)
        return False, f"{e.__class__.__name__}: {e}. {hint}"


def _describe_path_diagnostics(
    original_path: str,
    display_path: str,
    path_for_open: str,
    path_length: int
) -> Dict:
    """Log diagnostic details for troubleshooting Windows file access errors."""
    try:
        logger.info(f"Path length: {path_length} chars")
        logger.info(f"Path for open: {path_for_open}")
        logger.info(f"Original path repr: {repr(original_path)}")

        # Detect non-printable or null characters
        non_printable = [ch for ch in display_path if ord(ch) < 32 or ord(ch) == 127]
        if non_printable:
            logger.warning(f"⚠️ Non-printable characters detected: {non_printable}")

        null_positions = [idx for idx, ch in enumerate(display_path) if ch == '\x00']
        if null_positions:
            logger.warning(f"⚠️ Null byte(s) detected at positions: {null_positions}")

        return {
            "display_path": display_path,
            "path_for_open": path_for_open,
            "original_path": original_path,
            "path_length": path_length,
            "non_printable": non_printable,
            "null_positions": null_positions,
        }
    except Exception as diag_error:
        logger.warning(f"⚠️ Diagnostics error: {diag_error}")
        return {
            "display_path": display_path,
            "path_for_open": path_for_open,
            "original_path": original_path,
            "path_length": path_length,
            "non_printable": [],
            "null_positions": [],
            "error": str(diag_error)
        }

def extract_text_from_epub(filepath: str) -> Tuple[List[Dict], Dict]:
    """
    Extract text from EPUB file, preserving chapter structure.

    Returns:
        chapters: List of dicts with 'chapter_name', 'text', 'order'
        metadata: Dict with 'title', 'author', 'language', etc.
    """
    logger.info(f"Extracting text from EPUB: {filepath}")

    book = epub.read_epub(filepath)
    chapters = []

    for idx, item in enumerate(book.get_items()):
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            # Parse HTML content
            content = item.get_content().decode('utf-8', errors='ignore')
            soup = BeautifulSoup(content, 'html.parser')

            # Extract text
            text = soup.get_text(separator='\n', strip=True)

            if text.strip():  # Skip empty chapters
                chapters.append({
                    'chapter_name': item.get_name(),
                    'text': text,
                    'order': idx,
                    'word_count': len(text.split())
                })

    # Extract metadata
    metadata = {
        'title': _get_epub_metadata(book, 'title'),
        'author': _get_epub_metadata(book, 'creator'),
        'language': _get_epub_metadata(book, 'language'),
        'publisher': _get_epub_metadata(book, 'publisher'),
    }

    logger.info(f"Extracted {len(chapters)} chapters from EPUB")
    return chapters, metadata


def _get_epub_metadata(book, key: str) -> str:
    """Helper to safely extract EPUB metadata"""
    try:
        result = book.get_metadata('DC', key)
        if result:
            return result[0][0]
    except:
        pass
    return "Unknown"


def extract_text_from_pdf(filepath: str) -> Tuple[List[Dict], Dict]:
    """
    Extract text from PDF file, preserving page structure.

    Returns:
        pages: List of dicts with 'page_number', 'text'
        metadata: Dict with 'title', 'author', 'page_count', etc.
    """
    logger.info(f"Extracting text from PDF: {filepath}")

    doc = fitz.open(filepath)
    pages = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()

        if text.strip():  # Skip empty pages
            pages.append({
                'page_number': page_num + 1,
                'text': text,
                'word_count': len(text.split())
            })

    # Extract metadata
    metadata = {
        'title': doc.metadata.get('title', 'Unknown'),
        'author': doc.metadata.get('author', 'Unknown'),
        'page_count': len(doc),
        'format': 'PDF'
    }

    doc.close()

    logger.info(f"Extracted {len(pages)} pages from PDF")
    return pages, metadata


def extract_text_from_txt(filepath: str) -> Tuple[List[Dict], Dict]:
    """
    Extract text from plain TXT file.

    Returns:
        sections: List with single dict containing full text
        metadata: Dict with filename as title
    """
    logger.info(f"Extracting text from TXT: {filepath}")

    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read()

    sections = [{
        'section_name': 'full_text',
        'text': text,
        'word_count': len(text.split())
    }]

    metadata = {
        'title': Path(filepath).stem,
        'author': 'Unknown',
        'format': 'TXT'
    }

    logger.info(f"Extracted TXT file ({len(text.split())} words)")
    return sections, metadata


def extract_text(filepath: str) -> Tuple[List[Dict], Dict]:
    """
    Unified text extraction dispatcher.
    Automatically detects format and calls appropriate extractor.
    """
    ext = Path(filepath).suffix.lower()

    if ext == '.epub':
        return extract_text_from_epub(filepath)
    elif ext == '.pdf':
        return extract_text_from_pdf(filepath)
    elif ext in ['.txt', '.md']:
        return extract_text_from_txt(filepath)
    elif ext == '.mobi':
        # MOBI support: convert to EPUB first (requires mobi library or Calibre)
        raise NotImplementedError("MOBI support not yet implemented. Convert to EPUB first.")
    else:
        raise ValueError(f"Unsupported file format: {ext}")


# ============================================================================
# CHUNKING STRATEGIES
# ============================================================================

DOMAIN_CHUNK_SIZES = {
    'technical': {'min': 1500, 'max': 2000, 'overlap': 200},
    'psychology': {'min': 1000, 'max': 1500, 'overlap': 150},
    'philosophy': {'min': 1200, 'max': 1800, 'overlap': 180},
    'history': {'min': 1500, 'max': 2000, 'overlap': 200},
    'default': {'min': 1000, 'max': 1500, 'overlap': 150}
}


def get_token_count(text: str) -> int:
    """
    Estimate token count from text.
    Uses simple word count * 1.3 approximation.
    For production, use tiktoken for accurate counting.
    """
    return int(len(text.split()) * 1.3)


def calculate_optimal_chunk_params(sections: List[Dict], domain: str = 'technical') -> Dict:
    """
    Calculate optimal chunking parameters based on content analysis.

    Analyzes total content size and calculates target chunk size to achieve
    optimal chunk count (balancing context size vs chunk count).

    Args:
        sections: List of sections/chapters/pages with 'text' field
        domain: Domain category for base strategy

    Returns:
        Dict with 'max_tokens', 'overlap', 'target_chunks' keys
    """
    # Count total words and sections
    total_words = sum(len(section['text'].split()) for section in sections)
    total_sections = len(sections)
    avg_words_per_section = total_words / total_sections if total_sections > 0 else 0

    # Get domain base strategy
    strategy = DOMAIN_CHUNK_SIZES.get(domain, DOMAIN_CHUNK_SIZES['default'])

    # Calculate estimated tokens
    estimated_tokens = int(total_words * 1.3)

    # Target chunk count based on content size
    # Small books (< 50k tokens): aim for 20-40 chunks
    # Medium books (50k-150k): aim for 40-100 chunks
    # Large books (> 150k): aim for 100-200 chunks
    if estimated_tokens < 50000:
        target_chunks = 30
    elif estimated_tokens < 150000:
        target_chunks = 70
    else:
        target_chunks = 150

    # Calculate optimal max tokens
    optimal_max = int(estimated_tokens / target_chunks)

    # Clamp to reasonable range (500-3000 tokens)
    optimal_max = max(500, min(3000, optimal_max))

    # Use domain overlap ratio
    overlap_ratio = strategy['overlap'] / strategy['max']
    optimal_overlap = int(optimal_max * overlap_ratio)

    logger.info("📊 Content Analysis:")
    logger.info(f"   Total words: {total_words:,}")
    logger.info(f"   Estimated tokens: {estimated_tokens:,}")
    logger.info(f"   Sections: {total_sections}")
    logger.info(f"   Avg words/section: {avg_words_per_section:.0f}")
    logger.info("📐 Optimal Chunking:")
    logger.info(f"   Target chunks: ~{target_chunks}")
    logger.info(f"   Max tokens: {optimal_max}")
    logger.info(f"   Overlap: {optimal_overlap}")

    return {
        'max_tokens': optimal_max,
        'overlap': optimal_overlap,
        'target_chunks': target_chunks,
        'estimated_tokens': estimated_tokens
    }


def chunk_text(
    text: str,
    domain: str = 'technical',
    max_tokens: Optional[int] = None,
    overlap: Optional[int] = None,
    section_name: str = '',
    book_title: str = '',
    author: str = ''
) -> List[Dict]:
    """
    Chunk text according to domain-specific strategy.

    Uses token-based chunking with overlap to preserve context.

    Args:
        text: Full text to chunk
        domain: Domain category (technical/psychology/philosophy/history)
        max_tokens: Maximum chunk size (overrides domain default)
        overlap: Token overlap between chunks (overrides domain default)
        section_name: Section/chapter/page name for metadata
        book_title: Book title for metadata
        author: Author name for metadata

    Returns:
        List of chunk dicts with 'text', 'chunk_id', 'token_count', metadata
    """
    strategy = DOMAIN_CHUNK_SIZES.get(domain, DOMAIN_CHUNK_SIZES['default'])
    chunk_max = max_tokens if max_tokens is not None else strategy['max']
    chunk_overlap = overlap if overlap is not None else strategy['overlap']

    # Simple word-based chunking (tokens ≈ words * 1.3 for English)
    words = text.split()
    target_words = int(chunk_max / 1.3)
    overlap_words = int(chunk_overlap / 1.3)

    # Skip empty text
    if len(words) == 0:
        return []

    chunks = []
    start_idx = 0
    chunk_id = 0

    while start_idx < len(words):
        end_idx = min(start_idx + target_words, len(words))
        chunk_words = words[start_idx:end_idx]
        chunk_text = ' '.join(chunk_words)

        if chunk_text.strip():
            chunks.append({
                'text': chunk_text,
                'chunk_id': chunk_id,
                'token_count': len(chunk_words),
                'start_word': start_idx,
                'end_word': end_idx,
                'section_name': section_name,
                'book_title': book_title,
                'author': author
            })
            chunk_id += 1

        # Move start index forward (subtract overlap to create overlap between chunks)
        start_idx += target_words - overlap_words

        # Prevent infinite loop - ensure we're making progress
        if start_idx <= (chunks[-1]['start_word'] if chunks else 0):
            start_idx = end_idx

        # Break if we've processed all words
        if end_idx >= len(words):
            break

    if chunks:
        avg_tokens = sum(c['token_count'] for c in chunks) / len(chunks)
        logger.info(f"Created {len(chunks)} chunks (domain: {domain}, avg {avg_tokens:.0f} tokens/chunk)")

    return chunks


def create_chunks_from_sections(
    sections: List[Dict],
    metadata: Dict,
    domain: str = 'technical',
    max_tokens: Optional[int] = None,
    overlap: Optional[int] = None,
    merge_sections: bool = False
) -> List[Dict]:
    """
    Create chunks from book sections/chapters/pages.
    Preserves section metadata in each chunk.

    Args:
        sections: List of sections/chapters/pages with 'text' field
        metadata: Book metadata (title, author, etc.)
        domain: Domain category for chunking strategy
        max_tokens: Override max chunk size
        overlap: Override chunk overlap
        merge_sections: If True, merge all sections into one text before chunking (better for PDFs)

    Returns:
        List of chunks with metadata
    """
    all_chunks = []
    book_title = metadata.get('title', 'Unknown')
    author = metadata.get('author', 'Unknown')

    # Check if argument-based chunking should be used
    use_argument_chunking = should_use_argument_chunking(domain)

    if use_argument_chunking:
        logger.info(f"📚 Using argument-based pre-chunking for domain: {domain}")

    if merge_sections:
        # Merge all sections into one text and chunk it
        # This is better for PDFs where each "section" is just a page
        full_text = '\n\n'.join(section['text'] for section in sections)

        # Apply philosophical pre-chunking if enabled
        if use_argument_chunking:
            text_blocks = argument_prechunk(full_text, author=author)
            logger.info(f"   Pre-chunked into {len(text_blocks)} argument blocks")
        else:
            text_blocks = [full_text]

        # Apply token-based chunking to each pre-chunked block
        for block in text_blocks:
            chunks = chunk_text(
                text=block,
                domain=domain,
                max_tokens=max_tokens,
                overlap=overlap,
                section_name='merged',
                book_title=book_title,
                author=author
            )
            all_chunks.extend(chunks)
    else:
        # Chunk each section separately (better for EPUBs with actual chapters)
        for section in sections:
            section_text = section['text']
            section_name = str(section.get('chapter_name') or section.get('page_number') or section.get('section_name', ''))

            # Apply philosophical pre-chunking if enabled
            if use_argument_chunking:
                text_blocks = argument_prechunk(section_text, author=author)
            else:
                text_blocks = [section_text]

            # Apply token-based chunking to each pre-chunked block
            for block in text_blocks:
                chunks = chunk_text(
                    text=block,
                    domain=domain,
                    max_tokens=max_tokens,
                    overlap=overlap,
                    section_name=section_name,
                    book_title=book_title,
                    author=author
                )

                # Add section order to each chunk
                for chunk in chunks:
                    chunk['section_order'] = section.get('order', 0)

                all_chunks.extend(chunks)

    return all_chunks


# ============================================================================
# EMBEDDINGS
# ============================================================================

class EmbeddingGenerator:
    """Singleton wrapper for sentence-transformers model"""

    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_model(self, model_name: str = 'all-MiniLM-L6-v2'):
        """Lazy load the embedding model"""
        if self._model is None:
            logger.info(f"Loading embedding model: {model_name}")
            self._model = SentenceTransformer(model_name)
        return self._model

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for list of texts"""
        model = self.get_model()
        logger.info(f"Generating embeddings for {len(texts)} chunks...")
        embeddings = model.encode(texts, show_progress_bar=True)
        return embeddings.tolist()


# Convenience function for generating embeddings
def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a list of texts using sentence-transformers.

    Args:
        texts: List of text strings to embed

    Returns:
        List of embedding vectors
    """
    embedding_gen = EmbeddingGenerator()
    return embedding_gen.generate_embeddings(texts)


# ============================================================================
# QDRANT UPLOAD
# ============================================================================

def setup_qdrant_collection(
    client: QdrantClient,
    collection_name: str = 'alexandria',
    vector_size: int = 384,
    force_recreate: bool = False
):
    """
    Create or verify Qdrant collection exists.

    Args:
        client: QdrantClient instance
        collection_name: Name of collection
        vector_size: Embedding dimension (384 for all-MiniLM-L6-v2)
        force_recreate: If True, delete and recreate collection
    """
    collections = [c.name for c in client.get_collections().collections]

    if collection_name in collections:
        if force_recreate:
            logger.warning(f"Deleting existing collection: {collection_name}")
            client.delete_collection(collection_name)
        else:
            logger.info(f"Collection '{collection_name}' already exists")
            return

    logger.info(f"Creating collection: {collection_name}")
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=vector_size,
            distance=Distance.COSINE
        )
    )


def upload_to_qdrant(
    chunks: List[Dict],
    embeddings: List[List[float]],
    domain: str,
    collection_name: str = 'alexandria',
    qdrant_host: str = 'localhost',
    qdrant_port: int = 6333
):
    """
    Upload chunks and embeddings to Qdrant.
    Uses Open WebUI compatible format.
    """
    # Handle empty chunks/embeddings
    if not chunks or not embeddings:
        logger.warning(f"⚠️  No chunks to upload (chunks: {len(chunks)}, embeddings: {len(embeddings)})")
        return

    client = QdrantClient(host=qdrant_host, port=qdrant_port)

    # Ensure collection exists
    setup_qdrant_collection(client, collection_name, vector_size=len(embeddings[0]))

    # Prepare points
    points = []
    for chunk, embedding in zip(chunks, embeddings):
        # Generate UUID for point ID
        point_id = str(uuid.uuid4())

        point = PointStruct(
            id=point_id,
            vector=embedding,
            payload={
                # Core content
                "text": chunk['text'],
                "text_length": chunk['token_count'],

                # Book metadata
                "book_title": chunk.get('book_title', 'Unknown'),
                "author": chunk.get('author', 'Unknown'),
                "domain": domain,

                # Location metadata
                "section_name": chunk.get('section_name', ''),
                "section_order": chunk.get('section_order', 0),
                "chunk_id": chunk['chunk_id'],

                # Ingestion metadata
                "ingested_at": datetime.now().isoformat(),
                "chunk_strategy": f"{domain}-overlap",
                "embedding_model": "all-MiniLM-L6-v2",

                # Open WebUI compatibility
                "metadata": {
                    "source": chunk.get('book_title', 'Unknown'),
                    "section": chunk.get('section_name', ''),
                    "domain": domain
                }
            }
        )
        points.append(point)

    # Upload in batches
    batch_size = 100
    for i in range(0, len(points), batch_size):
        batch = points[i:i+batch_size]
        client.upsert(
            collection_name=collection_name,
            points=batch
        )
        logger.info(f"Uploaded batch {i//batch_size + 1}/{(len(points)-1)//batch_size + 1}")

    logger.info(f"✅ Successfully uploaded {len(points)} chunks to Qdrant collection '{collection_name}'")


# ============================================================================
# MAIN INGESTION PIPELINE
# ============================================================================

def ingest_book(
    filepath: str,
    domain: str = 'technical',
    collection_name: str = 'alexandria',
    qdrant_host: str = 'localhost',
    qdrant_port: int = 6333
):
    """
    Main ingestion pipeline: Extract → Chunk → Embed → Upload

    Args:
        filepath: Path to book file (EPUB/PDF/TXT)
        domain: Domain category for chunking strategy
        collection_name: Qdrant collection name
        qdrant_host: Qdrant server host
        qdrant_port: Qdrant server port
    """
    normalized_path, display_path, used_long_path, path_length = normalize_file_path(filepath)
    logger.info(f"Starting ingestion pipeline for: {display_path}")
    logger.info(f"Path repr: {repr(display_path)}")
    if used_long_path:
        logger.info("⚙️ Windows long-path prefix applied for file access")

    diagnostics = _describe_path_diagnostics(filepath, display_path, normalized_path, path_length)

    ok, error_message = validate_file_access(normalized_path, display_path)
    if not ok:
        logger.error(f"❌ File access check failed: {error_message}")
        return {'success': False, 'error': error_message, 'diagnostics': diagnostics}

    logger.info(f"Domain: {domain} | Collection: {collection_name}")

    # Step 1: Extract text
    sections, metadata = extract_text(normalized_path)
    logger.info(f"Book: {metadata['title']} by {metadata['author']}")

    # Check if any content was extracted
    if not sections or all(not section.get('text', '').strip() for section in sections):
        logger.error(f"❌ No content extracted from {filepath}")
        logger.error("   The file may be encrypted, corrupted, or in an unsupported format")
        return {'success': False, 'error': 'No content extracted'}

    # Step 2: Calculate optimal chunking parameters
    optimal_params = calculate_optimal_chunk_params(sections, domain=domain)

    # Step 3: Chunk text
    # For PDFs, merge all pages before chunking (better chunk sizes)
    # For EPUBs, keep chapters separate (preserve structure)
    file_format = metadata.get('format', '')
    merge_sections = (file_format == 'PDF')

    chunks = create_chunks_from_sections(
        sections,
        metadata,
        domain=domain,
        max_tokens=optimal_params['max_tokens'],
        overlap=optimal_params['overlap'],
        merge_sections=merge_sections
    )

    actual_chunks = len(chunks)
    target_chunks = optimal_params['target_chunks']
    efficiency = (target_chunks / actual_chunks * 100) if actual_chunks > 0 else 0

    logger.info(f"Total chunks created: {actual_chunks} (target: ~{target_chunks}, efficiency: {efficiency:.0f}%)")

    # Step 4: Generate embeddings
    embedding_gen = EmbeddingGenerator()
    texts = [chunk['text'] for chunk in chunks]
    embeddings = embedding_gen.generate_embeddings(texts)

    # Step 5: Upload to Qdrant
    upload_to_qdrant(
        chunks=chunks,
        embeddings=embeddings,
        domain=domain,
        collection_name=collection_name,
        qdrant_host=qdrant_host,
        qdrant_port=qdrant_port
    )

    logger.info(f"✅ Ingestion complete for: {metadata['title']}")

    # Return success status and metadata for manifest logging
    return {
        'success': True,
        'title': metadata.get('title', 'Unknown'),
        'author': metadata.get('author', 'Unknown'),
        'chunks': len(chunks),
        'file_size_mb': os.path.getsize(normalized_path) / (1024 * 1024),
        'filepath': display_path,
        'diagnostics': diagnostics
    }


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Alexandria Book Ingestion Pipeline'
    )
    parser.add_argument(
        '--file',
        type=str,
        required=True,
        help='Path to book file (EPUB/PDF/TXT)'
    )
    parser.add_argument(
        '--domain',
        type=str,
        default='technical',
        choices=['technical', 'psychology', 'philosophy', 'history'],
        help='Domain category for chunking strategy'
    )
    parser.add_argument(
        '--collection',
        type=str,
        default='alexandria',
        help='Qdrant collection name'
    )
    parser.add_argument(
        '--host',
        type=str,
        default='192.168.0.151',
        help='Qdrant server host'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=6333,
        help='Qdrant server port'
    )

    args = parser.parse_args()

    # Validate file exists
    if not os.path.exists(args.file):
        logger.error(f"File not found: {args.file}")
        return

    # Run ingestion
    try:
        ingest_book(
            filepath=args.file,
            domain=args.domain,
            collection_name=args.collection,
            qdrant_host=args.host,
            qdrant_port=args.port
        )
    except Exception as e:
        logger.error(f"Ingestion failed: {str(e)}", exc_info=True)


if __name__ == '__main__':
    main()
