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

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# TEXT EXTRACTION
# ============================================================================

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


def chunk_text(
    text: str,
    domain: str = 'technical',
    overlap: Optional[int] = None
) -> List[Dict]:
    """
    Chunk text according to domain-specific strategy.

    Uses token-based chunking with overlap to preserve context.

    Args:
        text: Full text to chunk
        domain: Domain category (technical/psychology/philosophy/history)
        overlap: Token overlap between chunks (overrides domain default)

    Returns:
        List of chunk dicts with 'text', 'chunk_id', 'token_count'
    """
    strategy = DOMAIN_CHUNK_SIZES.get(domain, DOMAIN_CHUNK_SIZES['default'])
    chunk_size = strategy['max']
    chunk_overlap = overlap if overlap is not None else strategy['overlap']

    # Simple word-based chunking (tokens ≈ words * 1.3 for English)
    # For production, use tiktoken or similar for accurate token counting
    words = text.split()
    target_words = int(chunk_size / 1.3)
    overlap_words = int(chunk_overlap / 1.3)

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
                'end_word': end_idx
            })
            chunk_id += 1

        # Move start index forward (with overlap)
        start_idx = end_idx - overlap_words

        # Break if we've reached the end
        if end_idx >= len(words):
            break

    logger.info(f"Created {len(chunks)} chunks (domain: {domain}, avg {sum(c['token_count'] for c in chunks) / len(chunks):.0f} tokens/chunk)")
    return chunks


def create_chunks_from_sections(
    sections: List[Dict],
    metadata: Dict,
    domain: str = 'technical'
) -> List[Dict]:
    """
    Create chunks from book sections/chapters/pages.
    Preserves section metadata in each chunk.
    """
    all_chunks = []

    for section in sections:
        section_text = section['text']
        section_name = section.get('chapter_name') or section.get('page_number') or section.get('section_name')

        # Chunk this section
        chunks = chunk_text(section_text, domain=domain)

        # Add section metadata to each chunk
        for chunk in chunks:
            chunk['section_name'] = section_name
            chunk['section_order'] = section.get('order', 0)
            chunk['book_title'] = metadata.get('title', 'Unknown')
            chunk['book_author'] = metadata.get('author', 'Unknown')

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
    client = QdrantClient(host=qdrant_host, port=qdrant_port)

    # Ensure collection exists
    setup_qdrant_collection(client, collection_name, vector_size=len(embeddings[0]))

    # Prepare points
    points = []
    for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        point = PointStruct(
            id=idx,  # Simple sequential ID (use UUID for production)
            vector=embedding,
            payload={
                # Core content
                "text": chunk['text'],
                "text_length": chunk['token_count'],

                # Book metadata
                "book_title": chunk['book_title'],
                "author": chunk['book_author'],
                "domain": domain,

                # Location metadata
                "section_name": chunk['section_name'],
                "section_order": chunk['section_order'],
                "chunk_id": chunk['chunk_id'],

                # Ingestion metadata
                "ingested_at": datetime.now().isoformat(),
                "chunk_strategy": f"{domain}-overlap",
                "embedding_model": "all-MiniLM-L6-v2",

                # Open WebUI compatibility
                "metadata": {
                    "source": chunk['book_title'],
                    "section": chunk['section_name'],
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
    logger.info(f"Starting ingestion pipeline for: {filepath}")
    logger.info(f"Domain: {domain} | Collection: {collection_name}")

    # Step 1: Extract text
    sections, metadata = extract_text(filepath)
    logger.info(f"Book: {metadata['title']} by {metadata['author']}")

    # Step 2: Chunk text
    chunks = create_chunks_from_sections(sections, metadata, domain=domain)
    logger.info(f"Total chunks created: {len(chunks)}")

    # Step 3: Generate embeddings
    embedding_gen = EmbeddingGenerator()
    texts = [chunk['text'] for chunk in chunks]
    embeddings = embedding_gen.generate_embeddings(texts)

    # Step 4: Upload to Qdrant
    upload_to_qdrant(
        chunks=chunks,
        embeddings=embeddings,
        domain=domain,
        collection_name=collection_name,
        qdrant_host=qdrant_host,
        qdrant_port=qdrant_port
    )

    logger.info(f"✅ Ingestion complete for: {metadata['title']}")


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
