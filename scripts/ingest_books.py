"""
Alexandria Book Ingestion Script

Unified ingestion pipeline for EPUB, PDF, and TXT files.
Utilizes Universal Semantic Chunking for all domains to ensure high-quality retrieval.

Usage:
    python ingest_books.py --file "path/to/book.epub" --domain technical
"""

import os
import argparse
import uuid
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import logging
from scripts.calibre_db import CalibreDB # Import CalibreDB

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

# Universal Semantic Chunking
from universal_chunking import UniversalChunker

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

CALIBRE_LIBRARY_PATH = "G:\\My Drive\\alexandria" # Calibre library path
calibre_db_instance = None # Lazy load


# ============================================================================ 
# TEXT EXTRACTION
# ============================================================================ 

def normalize_file_path(filepath: str) -> Tuple[str, str, bool, int]:
    """Normalize paths for cross-platform file access."""
    expanded = os.path.expanduser(filepath)
    abs_path = os.path.abspath(expanded)
    path_for_open = abs_path
    used_long_path = False

    if os.name == "nt" and not abs_path.startswith("\\\\?\\"):
        if len(abs_path) >= 248:
            if abs_path.startswith("\\\\"):
                path_for_open = "\\\\?\\UNC\\" + abs_path.lstrip("\\")
            else:
                path_for_open = "\\\\?\\" + abs_path
            used_long_path = True

    return path_for_open, abs_path, used_long_path, len(abs_path)


def validate_file_access(path_for_open: str, display_path: str) -> Tuple[bool, Optional[str]]:
    """Validate file exists and is readable."""
    if not os.path.exists(path_for_open):
        return False, f"File not found: {display_path}"

    try:
        os.stat(path_for_open)
        with open(path_for_open, 'rb') as f:
            f.read(1)
        return True, None
    except OSError as e:
        return False, f"{e.__class__.__name__}: {e}"


def extract_text(filepath: str) -> Tuple[str, Dict]:
    """
    Extract text from file based on extension.
    Returns: full_text, metadata
    """
    ext = Path(filepath).suffix.lower()
    
    if ext == '.epub':
        book = epub.read_epub(filepath)
        chapters = []
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                content = item.get_content().decode('utf-8', errors='ignore')
                soup = BeautifulSoup(content, 'html.parser')
                text = soup.get_text(separator='\n', strip=True)
                if text: chapters.append(text)
        
        metadata = {
            'title': _get_epub_metadata(book, 'title'),
            'author': _get_epub_metadata(book, 'creator'),
            'language': _get_epub_metadata(book, 'language'),
            'format': 'EPUB'
        }
        return "\n\n".join(chapters), metadata

    elif ext == '.pdf':
        doc = fitz.open(filepath)
        pages = [page.get_text() for page in doc]
        metadata = {
            'title': doc.metadata.get('title', 'Unknown'),
            'author': doc.metadata.get('author', 'Unknown'),
            'language': standardize_language_code(doc.metadata.get('language') or 'unknown'),
            'format': 'PDF'
        }
        doc.close()
        return "\n\n".join(pages), metadata

    elif ext in ['.txt', '.md']:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
        return text, {'title': Path(filepath).stem, 'author': 'Unknown', 'format': 'TXT'}
    
    else:
        raise ValueError(f"Unsupported format: {ext}")


def _get_epub_metadata(book, key: str) -> str:
    try:
        result = book.get_metadata('DC', key)
        if result: 
            return standardize_language_code(result[0][0])
    except: pass
    return "unknown"

def standardize_language_code(lang: str) -> str:
    """Standardizes common language codes to a consistent format (e.g., 'en', 'hr')."""
    if not lang:
        return "unknown"
    
    lang = lang.lower().strip()

    # Standardize known problematic English indicators
    if lang == 'eng': # Only 'eng' to 'en', keep 'en-us', 'en-gb'
        return 'en'
    
    # Standardize known problematic Croatian indicators
    if lang in ['hrv', 'cro']:
        return 'hr' 
    
    # Keep other specific regional variants or unexpected codes as they are
    return lang


# ============================================================================ 
# EMBEDDINGS
# ============================================================================ 

class EmbeddingGenerator:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_model(self, model_name: str = 'all-MiniLM-L6-v2'):
        if self._model is None:
            logger.info(f"Loading embedding model: {model_name}")
            self._model = SentenceTransformer(model_name)
        return self._model

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        model = self.get_model()
        embeddings = model.encode(texts, show_progress_bar=True)
        return embeddings.tolist()

def generate_embeddings(texts: List[str]) -> List[List[float]]:
    return EmbeddingGenerator().generate_embeddings(texts)


# ============================================================================ 
# QDRANT UPLOAD
# ============================================================================ 

def upload_to_qdrant(
    chunks: List[Dict],
    embeddings: List[List[float]],
    domain: str,
    collection_name: str,
    qdrant_host: str,
    qdrant_port: int
):
    if not chunks: return

    client = QdrantClient(host=qdrant_host, port=qdrant_port)
    
    # Ensure collection
    collections = [c.name for c in client.get_collections().collections]
    if collection_name not in collections:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=len(embeddings[0]), distance=Distance.COSINE)
        )

    points = []
    for chunk, embedding in zip(chunks, embeddings):
        points.append(PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={
                "text": chunk['text'],
                "book_title": chunk.get('book_title', 'Unknown'),
                "author": chunk.get('author', 'Unknown'),
                "domain": domain,
                "language": chunk.get('language', 'unknown'),
                "ingested_at": datetime.now().isoformat(),
                "strategy": "universal-semantic",
                "metadata": {
                    "source": chunk.get('book_title', 'Unknown'),
                    "domain": domain
                }
            }
        ))

    # Batch upload
    for i in range(0, len(points), 100):
        client.upsert(collection_name=collection_name, points=points[i:i+100])
    
    logger.info(f"✅ Uploaded {len(points)} semantic chunks to '{collection_name}'")


def _get_calibre_db() -> Optional[CalibreDB]:
    """Lazy-loads and returns a CalibreDB instance."""
    global calibre_db_instance
    if calibre_db_instance is None:
        try:
            calibre_db_instance = CalibreDB(CALIBRE_LIBRARY_PATH)
        except FileNotFoundError:
            logger.warning(f"Calibre DB not found at {CALIBRE_LIBRARY_PATH}. Metadata enrichment from Calibre will be skipped.")
            calibre_db_instance = None
        except Exception as e:
            logger.error(f"Failed to connect to Calibre DB at {CALIBRE_LIBRARY_PATH}: {e}. Metadata enrichment from Calibre will be skipped.")
            calibre_db_instance = None
    return calibre_db_instance

def _enrich_metadata_from_calibre(filepath: str, metadata: Dict) -> Dict:
    """
    Attempts to enrich metadata from Calibre DB if a match is found.
    Prioritizes Calibre data for title, author, and language if current metadata is 'Unknown' or 'unknown'.
    """
    db = _get_calibre_db()
    if not db:
        return metadata # Cannot enrich without Calibre DB

    filename = Path(filepath).name
    calibre_book = db.match_file_to_book(filename)

    if calibre_book:
        logger.info(f"Matched '{filename}' to Calibre book: '{calibre_book.title}' by '{calibre_book.author}'.")
        # Override 'Unknown' or 'unknown' fields with Calibre data
        if metadata.get('title', 'Unknown') in ['Unknown', 'unknown']:
            metadata['title'] = calibre_book.title
        # Calibre stores authors as "Author1 & Author2", but metadata expects a string.
        # CalibreBook.author field already handles this.
        if metadata.get('author', 'Unknown') in ['Unknown', 'unknown']:
            metadata['author'] = calibre_book.author

        if metadata.get('language', 'unknown') == 'unknown':
            # Use standardized language from Calibre if available and current is 'unknown'
            metadata['language'] = standardize_language_code(calibre_book.language)
        
        # Also ensure format is consistent (take first format from Calibre and uppercase it)
        if calibre_book.formats and metadata.get('format', 'unknown') == 'unknown':
             metadata['format'] = calibre_book.formats[0].upper()

    return metadata





def extract_metadata_only(filepath: str) -> Dict:
    """
    Extracts only metadata (title, author, language) from a file without processing content.
    Returns: Dict with 'title', 'author', 'language', 'format', or 'error' if unsupported/failed.
    """
    normalized_path, display_path, _, _ = normalize_file_path(filepath)

    ok, err = validate_file_access(normalized_path, display_path)
    if not ok: 
        return {'error': err, 'filepath': display_path}

    try:
        _, metadata = extract_text(normalized_path)
        metadata['filepath'] = display_path
        
        # Enrich metadata from Calibre if available
        metadata = _enrich_metadata_from_calibre(filepath, metadata)

        return metadata
    except ValueError as e:
        return {'error': str(e), 'filepath': display_path}
    except Exception as e:
        logger.error(f"Error extracting metadata from {display_path}: {e}")
        return {'error': f"Failed to extract metadata: {e}", 'filepath': display_path}


# ============================================================================ 
# MAIN PIPELINE
# ============================================================================ 

def ingest_book(
    filepath: str,
    domain: str = 'technical',
    collection_name: str = 'alexandria',
    qdrant_host: str = 'localhost',
    qdrant_port: int = 6333,
    language_override: Optional[str] = None,
    title_override: Optional[str] = None,
    author_override: Optional[str] = None
):
    normalized_path, display_path, _, _ = normalize_file_path(filepath)
    
    ok, err = validate_file_access(normalized_path, display_path)
    if not ok: return {'success': False, 'error': err}

    # 1. Extract
    text, metadata = extract_text(normalized_path)
    if language_override: metadata['language'] = language_override
    if title_override: metadata['title'] = title_override
    if author_override: metadata['author'] = author_override

    # Enrich metadata from Calibre after initial extraction but before overrides
    metadata = _enrich_metadata_from_calibre(filepath, metadata)

    # 2. Semantic Chunking
    # Adjust threshold based on domain (Philosophy needs tighter focus)
    threshold = 0.45 if domain == 'philosophy' else 0.55
    
    embedder = EmbeddingGenerator()
    chunker = UniversalChunker(
        embedder, 
        threshold=threshold, 
        min_chunk_size=200, 
        max_chunk_size=1200
    )
    
    # Calculate rough sentence count for stats
    sentence_count = len(text.split('. '))
    
    chunks = chunker.chunk(text, metadata=metadata)
    
    if not chunks:
        return {'success': False, 'error': 'No chunks created'}

    # 3. Embed & Upload
    embeddings = generate_embeddings([c['text'] for c in chunks])
    upload_to_qdrant(chunks, embeddings, domain, collection_name, qdrant_host, qdrant_port)

    return {
        'success': True,
        'title': metadata.get('title', 'Unknown'),
        'author': metadata.get('author', 'Unknown'),
        'chunks': len(chunks),
        'sentences': sentence_count,
        'strategy': 'Universal Semantic',
        'file_size_mb': os.path.getsize(normalized_path) / (1024 * 1024),
        'filepath': display_path
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', required=True)
    parser.add_argument('--domain', default='technical')
    parser.add_argument('--collection', default='alexandria')
    parser.add_argument('--host', default='192.168.0.151')
    parser.add_argument('--port', type=int, default=6333)
    args = parser.parse_args()

    ingest_book(args.file, args.domain, args.collection, args.host, args.port)

if __name__ == '__main__':
    main()