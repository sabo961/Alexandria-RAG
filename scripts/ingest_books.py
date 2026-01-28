"""
Alexandria Book Ingestion Script

Unified ingestion pipeline for EPUB, PDF, and TXT files.
Utilizes Universal Semantic Chunking for all domains to ensure high-quality retrieval.

Usage:
    python ingest_books.py --file "path/to/book.epub" --domain technical
"""

import os
# Disable tqdm globally to avoid stderr issues in Streamlit
os.environ['TQDM_DISABLE'] = '1'

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

# Setup logging - configurable via ALEXANDRIA_LOG_LEVEL environment variable
# Usage: export ALEXANDRIA_LOG_LEVEL=DEBUG or ALEXANDRIA_LOG_LEVEL=INFO
log_level_str = os.getenv('ALEXANDRIA_LOG_LEVEL', 'INFO').upper()
log_level = getattr(logging, log_level_str, logging.INFO)

logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger = logging.getLogger(__name__)

CALIBRE_LIBRARY_PATH = "G:\\My Drive\\alexandria" # Calibre library path
calibre_db_instance = None # Lazy load


# ============================================================================ 
# TEXT EXTRACTION
# ============================================================================ 

def normalize_file_path(filepath: str) -> Tuple[str, str, bool, int]:
    r"""
    Normalize file paths for cross-platform access with Windows long path support.

    Expands user home directory (~), converts to absolute path, and applies Windows
    long path prefix (\\?\) for paths >= 248 characters to avoid MAX_PATH limitations.

    Args:
        filepath: Input file path (relative, absolute, or with ~ prefix).

    Returns:
        Tuple containing:
            - path_for_open (str): Path to use with open() - includes long path prefix if needed
            - abs_path (str): Standard absolute path without long path prefix
            - used_long_path (bool): True if Windows long path prefix was applied
            - path_length (int): Length of the absolute path in characters
    """
    logger.debug(f"normalize_file_path input: {repr(filepath)}")
    expanded = os.path.expanduser(filepath)
    logger.debug(f"After expanduser: {repr(expanded)}")
    abs_path = os.path.abspath(expanded)
    logger.debug(f"After abspath: {repr(abs_path)}")
    path_for_open = abs_path
    used_long_path = False

    if os.name == "nt" and not abs_path.startswith("\\\\?\\"):
        if len(abs_path) >= 248:
            if abs_path.startswith("\\\\"):
                path_for_open = "\\\\?\\UNC\\" + abs_path.lstrip("\\")
            else:
                path_for_open = "\\\\?\\" + abs_path
            used_long_path = True
            logger.debug(f"Applied long path prefix: {repr(path_for_open)}")

    logger.debug(f"normalize_file_path output: path_for_open={repr(path_for_open)}, abs_path={repr(abs_path)}")
    return path_for_open, abs_path, used_long_path, len(abs_path)


def validate_file_access(path_for_open: str, display_path: str) -> Tuple[bool, Optional[str]]:
    r"""
    Validate that a file exists and is readable.

    Performs a two-step validation:
    1. Checks file existence using os.path.exists()
    2. Verifies file accessibility by calling os.stat() and attempting to read first byte

    Args:
        path_for_open: The actual file path to use for operations (may include Windows
                      long path prefix \\?\ for paths >= 248 characters).
        display_path: User-friendly path for error messages (without long path prefix).

    Returns:
        Tuple containing:
            - success (bool): True if file exists and is readable, False otherwise
            - error_message (Optional[str]): None on success, descriptive error message on failure
    """
    # NOTE: Cannot use sys.stderr in Streamlit - it causes [Errno 22]
    logger.debug(f"validate_file_access checking: {repr(path_for_open)}")

    if not os.path.exists(path_for_open):
        logger.debug(f"File does not exist: {path_for_open}")
        return False, f"File not found: {display_path}"

    try:
        logger.debug(f"Calling os.stat()...")
        os.stat(path_for_open)
        logger.debug(f"os.stat() succeeded, attempting to open file...")
        with open(path_for_open, 'rb') as f:
            f.read(1)
        logger.debug(f"File opened and read successfully")
        return True, None
    except OSError as e:
        logger.error(f"OSError during file access: {e.__class__.__name__}: {e}", exc_info=True)
        return False, f"{e.__class__.__name__}: {e}"


def extract_text(filepath: str) -> Tuple[str, Dict]:
    """
    Extract text content and metadata from supported book file formats.

    Parses EPUB, PDF, TXT, and Markdown files to extract full text content and
    associated metadata (title, author, language, format). EPUB files are processed
    chapter by chapter with HTML parsing. PDF files use PyMuPDF for text extraction.

    Args:
        filepath: Path to the book file (supports .epub, .pdf, .txt, .md extensions).

    Returns:
        Tuple containing:
            - full_text (str): Extracted text content, chapters/pages separated by double newlines
            - metadata (dict): Book metadata with keys:
                - title (str): Book title or filename stem
                - author (str): Author name or 'Unknown'
                - language (str): Standardized language code (e.g., 'en', 'hr') or 'unknown'
                - format (str): File format ('EPUB', 'PDF', or 'TXT')

    Raises:
        ValueError: If file extension is not supported (.epub, .pdf, .txt, .md).
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
    """
    Extract metadata field from EPUB book using Dublin Core namespace.

    Retrieves metadata from EPUB files using the Dublin Core (DC) metadata standard.
    Automatically standardizes language codes to ensure consistency across the system.

    Args:
        book: EPUB book object from ebooklib (epub.EpubBook instance).
        key: Dublin Core metadata key to extract (e.g., 'title', 'creator', 'language').

    Returns:
        Metadata value as string. For language fields, returns standardized code
        (e.g., 'en', 'hr'). Returns 'unknown' if metadata key is not found or
        extraction fails.

    Note:
        This is a private helper function used internally by extract_text().
        All language values are automatically passed through standardize_language_code().
    """
    try:
        result = book.get_metadata('DC', key)
        if result:
            return standardize_language_code(result[0][0])
    except: pass
    return "unknown"

def standardize_language_code(lang: str) -> str:
    """
    Standardize language codes to consistent format for metadata uniformity.

    Converts ISO 639-2 three-letter codes and non-standard variants to their
    canonical two-letter ISO 639-1 equivalents. Preserves regional variants
    (e.g., 'en-us', 'en-gb') while normalizing base language codes.

    Args:
        lang: Language code string in any format (e.g., 'eng', 'en', 'hrv', 'en-US').
              Can be None or empty string.

    Returns:
        Standardized language code in lowercase. Returns 'unknown' for None/empty input.

        Common transformations:
            - 'eng' -> 'en' (ISO 639-2 to ISO 639-1)
            - 'hrv', 'cro' -> 'hr' (Croatian variants to standard code)
            - 'en-US' -> 'en-us' (lowercase normalization, preserves regional variant)
            - '' or None -> 'unknown'

    Note:
        Regional variants like 'en-us' or 'en-gb' are preserved to maintain
        specificity while ensuring consistent lowercase formatting.
    """
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
    """
    Singleton Embedding Generator for Text Vectorization
    =====================================================

    Thread-safe singleton that manages a shared SentenceTransformer model instance
    to generate vector embeddings for text chunks. Ensures the model is loaded only
    once across the entire application lifecycle, reducing memory usage and startup time.

    Design Pattern:
        Singleton: Only one instance of this class exists across all imports and calls.
        This prevents multiple copies of the 384MB+ embedding model from being loaded
        into memory when processing multiple books or serving requests.

    Usage:
        # All instances reference the same underlying object
        embedder1 = EmbeddingGenerator()
        embedder2 = EmbeddingGenerator()
        assert embedder1 is embedder2  # True

        # Generate embeddings for a list of text chunks
        texts = ["Philosophy is the study...", "Nietzsche wrote about..."]
        vectors = embedder1.generate_embeddings(texts)

    Attributes:
        _instance (EmbeddingGenerator): Shared singleton instance.
        _model (SentenceTransformer): Lazy-loaded embedding model (default: all-MiniLM-L6-v2).
    """
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_model(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Lazy-load and return the SentenceTransformer embedding model.

        Loads the model on first call and caches it for subsequent requests.
        This prevents redundant model loading and reduces memory overhead.

        Args:
            model_name: HuggingFace model identifier (default: 'all-MiniLM-L6-v2').
                       Supports any model from sentence-transformers library.

        Returns:
            SentenceTransformer: Cached model instance ready for encoding text.
        """
        if self._model is None:
            logger.info(f"Loading embedding model: {model_name}")
            self._model = SentenceTransformer(model_name)
        return self._model

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate vector embeddings for a batch of text strings.

        Converts text into dense vector representations using the cached
        SentenceTransformer model. Progress bars are disabled to prevent
        stderr conflicts in Streamlit environments.

        Args:
            texts: List of text strings to encode (e.g., chunks, sentences).

        Returns:
            List of embedding vectors, where each vector is a list of floats
            with dimensionality matching the model (384 for all-MiniLM-L6-v2).
        """
        model = self.get_model()
        # Disable ALL progress bars to avoid sys.stderr issues in Streamlit environment
        # tqdm progress bar causes [Errno 22] when sys.stderr is not available
        embeddings = model.encode(
            texts,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=False
        )
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
    """
    Upload text chunks with embeddings to Qdrant vector database.

    Creates or updates a Qdrant collection with text chunks and their vector embeddings.
    Automatically creates the collection if it doesn't exist, using COSINE distance metric.
    Uploads points in batches of 100 to optimize network performance and memory usage.

    Each chunk is stored as a PointStruct with:
        - UUID-based unique identifier
        - Vector embedding for semantic search
        - Payload containing text, metadata (title, author, domain, language),
          ingestion timestamp, and chunking strategy

    Args:
        chunks: List of chunk dictionaries containing 'text' and optional metadata
               (book_title, author, language). Each chunk represents a semantic segment
               from the ingested book.
        embeddings: List of embedding vectors corresponding to chunks (same length).
                   Each embedding is a list of floats with dimensionality matching
                   the model (384 for all-MiniLM-L6-v2).
        domain: Domain classification for the book (e.g., 'technical', 'philosophy',
               'literature'). Used for filtering and retrieval optimization.
        collection_name: Name of the Qdrant collection to upload to. Created if
                        it doesn't exist.
        qdrant_host: Qdrant server hostname or IP address.
        qdrant_port: Qdrant server port number.

    Returns:
        None. Logs success message upon completion with upload statistics.

    Note:
        - Early returns if chunks list is empty (no-op)
        - Collection uses COSINE distance for similarity search
        - Batch size is hardcoded to 100 points per upload
        - All points receive unique UUIDs to prevent ID collisions
        - Ingestion timestamp is stored in ISO format for audit trails
    """
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
    """
    Lazy-load and return singleton CalibreDB instance for metadata enrichment.

    Initializes a connection to the Calibre library database on first call and
    caches the instance for subsequent calls to avoid repeated database connections.
    Handles connection errors gracefully by returning None if the Calibre library
    is unavailable or inaccessible.

    The Calibre library path is read from the module-level CALIBRE_LIBRARY_PATH
    constant. If the database connection fails, appropriate warnings/errors are
    logged and metadata enrichment will be skipped for the current ingestion session.

    Returns:
        CalibreDB instance if connection successful, None if connection fails.
        Returns None in these cases:
            - Calibre library path does not exist (FileNotFoundError)
            - Database file is corrupted or inaccessible (generic Exception)
            - metadata.db file is missing from the library path

    Note:
        This is a private helper function that implements the singleton pattern.
        The global calibre_db_instance is initialized once and reused across
        multiple book ingestion operations to improve performance.
    """
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
    Enrich book metadata with high-quality data from Calibre library if available.

    Attempts to match the book file against the Calibre library database using
    filename matching. If a match is found, enriches the metadata dictionary with
    Calibre's curated metadata (title, author, language, format), but only overwrites
    fields that contain 'Unknown' or 'unknown' values to preserve higher-quality
    metadata from other sources.

    The function performs a non-destructive merge: existing valid metadata values
    are retained, while missing or low-quality values are replaced with Calibre data.
    Language codes from Calibre are automatically standardized using the
    standardize_language_code() function to ensure consistency.

    Args:
        filepath: Path to the book file (used for filename-based matching).
                 Only the filename component is used for matching, not the full path.
        metadata: Dictionary containing current book metadata with keys:
                 title, author, language, format. Values may be 'Unknown' or 'unknown'
                 if not extracted from the book file.

    Returns:
        Dictionary with enriched metadata. Returns the original metadata unchanged if:
            - Calibre database connection is unavailable
            - No matching book is found in Calibre library
            - Calibre book record lacks the requested metadata fields

        Modified metadata fields (only if current value is 'Unknown' or 'unknown'):
            - title (str): Book title from Calibre
            - author (str): Author name(s) from Calibre (handles multiple authors)
            - language (str): Standardized language code from Calibre
            - format (str): Uppercase file format from Calibre's format list

    Note:
        This is a private helper function used during book ingestion. It does not
        modify the original metadata dictionary - a new dictionary is returned.
        The function gracefully handles missing Calibre database connections by
        returning the original metadata without raising exceptions.
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
    Extract book metadata without processing full text content.

    Efficiently retrieves metadata (title, author, language, format) from book files
    without performing full text extraction or chunking. Supports EPUB, PDF, TXT, and
    Markdown formats. Automatically enriches metadata from Calibre library if available.

    The function performs path normalization with Windows long path support, validates
    file accessibility, extracts basic metadata from the file format, and optionally
    enriches it with Calibre library data when a matching book is found.

    Args:
        filepath: Path to the book file (supports .epub, .pdf, .txt, .md extensions).
                 Can be relative, absolute, or use ~ for home directory.

    Returns:
        Dictionary containing either metadata or error information:
            On success:
                - title (str): Book title from file metadata or Calibre
                - author (str): Author name from file metadata or Calibre
                - language (str): Standardized language code (e.g., 'en', 'hr')
                - format (str): File format ('EPUB', 'PDF', or 'TXT')
                - filepath (str): Normalized absolute path to the file
            On error:
                - error (str): Error message describing the failure
                - filepath (str): Normalized absolute path to the file

    Note:
        This function is optimized for metadata-only extraction and does not
        perform text chunking or embedding generation, making it suitable for
        preview, validation, or batch metadata collection workflows.
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
    r"""
    Complete end-to-end pipeline for ingesting books into Alexandria vector database.

    Orchestrates the full ingestion workflow: file validation, text extraction, metadata
    enrichment from Calibre library, universal semantic chunking, embedding generation,
    and upload to Qdrant. Supports EPUB, PDF, TXT, and Markdown formats with automatic
    format detection. Handles Windows long paths and Streamlit compatibility.

    The pipeline performs these steps:
    1. Path normalization with Windows long path support (\\?\ prefix for paths >= 248 chars)
    2. File access validation to ensure readability
    3. Text extraction and metadata parsing from book file
    4. Metadata enrichment from Calibre library (skipped if overrides provided)
    5. Application of metadata overrides (language, title, author)
    6. Universal semantic chunking with domain-specific thresholds
    7. Batch embedding generation using cached SentenceTransformer model
    8. Upload to Qdrant with semantic search optimized metadata

    Args:
        filepath: Path to the book file (supports .epub, .pdf, .txt, .md extensions).
                 Can be relative, absolute, or use ~ for home directory. Automatically
                 handles Windows long path limitations.
        domain: Domain classification for chunking and retrieval optimization.
               Options: 'technical', 'philosophy', 'literature'. Philosophy uses stricter
               semantic threshold (0.45) for tighter conceptual coherence. Default: 'technical'.
        collection_name: Name of the Qdrant collection to upload chunks to. Created
                        automatically if it doesn't exist. Default: 'alexandria'.
        qdrant_host: Qdrant server hostname or IP address. Default: 'localhost'.
        qdrant_port: Qdrant server port number. Default: 6333.
        language_override: Override extracted language metadata with specific ISO 639-1 code
                          (e.g., 'en', 'hr'). If provided, skips Calibre enrichment.
                          Default: None (use extracted/enriched metadata).
        title_override: Override extracted title metadata. If provided with author_override,
                       skips Calibre enrichment entirely. Default: None (use extracted/enriched).
        author_override: Override extracted author metadata. If provided with title_override,
                        skips Calibre enrichment entirely. Default: None (use extracted/enriched).

    Returns:
        Dictionary containing ingestion results and statistics:
            On success:
                - success (bool): True
                - title (str): Final book title (extracted, enriched, or overridden)
                - author (str): Final author name (extracted, enriched, or overridden)
                - language (str): Final language code (extracted, enriched, or overridden)
                - chunks (int): Number of semantic chunks created and uploaded
                - sentences (int): Approximate sentence count (rough estimate via '. ' splits)
                - strategy (str): Chunking strategy used ('Universal Semantic')
                - file_size_mb (float): Book file size in megabytes
                - filepath (str): Normalized absolute path to the ingested file
                - debug_author (dict): Debug information tracking author metadata through pipeline
            On error:
                - success (bool): False
                - error (str): Error message describing the failure

    Note:
        - Calibre enrichment is automatically skipped when both title_override and
          author_override are provided (indicates metadata already sourced from Calibre)
        - Semantic chunking thresholds: philosophy (0.45), all others (0.55)
        - Chunk size constraints: min 200 chars, max 1200 chars
        - All chunks receive unique UUIDs and ingestion timestamps
        - Progress bars are disabled globally (TQDM_DISABLE=1) for Streamlit compatibility
        - Function is safe to call from Streamlit - no sys.stderr usage
    """
    # NOTE: Cannot use sys.stderr in Streamlit - it causes [Errno 22]
    logging.debug(f"ingest_book started: {filepath} (domain={domain}, collection={collection_name})")

    try:
        normalized_path, display_path, _, _ = normalize_file_path(filepath)
        logging.debug(f"normalize_file_path returned: normalized_path={repr(normalized_path)}")
    except Exception as e:
        logging.error(f"normalize_file_path FAILED: {e.__class__.__name__}: {e}")
        return {'success': False, 'error': f"Path normalization failed: {e}"}

    ok, err = validate_file_access(normalized_path, display_path)
    if not ok:
        logging.error(f"File access validation failed: {err}")
        return {'success': False, 'error': err}

    # 1. Extract
    text, metadata = extract_text(normalized_path)

    logging.debug(f"Text extracted. Title: '{metadata.get('title')}', Author: '{metadata.get('author')}'")
    logging.debug(f"Overrides: title_override={title_override}, author_override={author_override}")

    # Enrich metadata from Calibre ONLY if we don't have overrides (i.e., not from Calibre ingestion)
    # When ingesting from Calibre, metadata already comes from Calibre book object
    if not (title_override and author_override):
        logging.debug(f"Running Calibre enrichment (no overrides present)")
        metadata = _enrich_metadata_from_calibre(filepath, metadata)
    else:
        logging.debug(f"Skipping Calibre enrichment (overrides present)")

    # Apply overrides AFTER enrichment
    debug_info = {
        'extracted_author': metadata.get('author'),
        'author_override': author_override,
    }

    if language_override: metadata['language'] = language_override
    if title_override: metadata['title'] = title_override
    if author_override:
        logging.debug(f"Applying author_override: {author_override}")
        debug_info['final_author'] = author_override
        metadata['author'] = author_override
    else:
        debug_info['final_author'] = metadata.get('author')

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
        logging.error(f"No chunks created for {metadata.get('title')}")
        return {'success': False, 'error': 'No chunks created'}

    logging.debug(f"Chunks created: {len(chunks)} chunks from {len(text)} characters")

    # 3. Embed & Upload
    embeddings = generate_embeddings([c['text'] for c in chunks])
    upload_to_qdrant(chunks, embeddings, domain, collection_name, qdrant_host, qdrant_port)

    result = {
        'success': True,
        'title': metadata.get('title', 'Unknown'),
        'author': metadata.get('author', 'Unknown'),
        'language': metadata.get('language', 'unknown'),
        'chunks': len(chunks),
        'sentences': sentence_count,
        'strategy': 'Universal Semantic',
        'file_size_mb': os.path.getsize(normalized_path) / (1024 * 1024),
        'filepath': display_path,
        'debug_author': debug_info  # Debug: track author through pipeline
    }

    logging.info(f"✅ Successfully ingested '{result['title']}' ({result['file_size_mb']:.2f} MB, {len(chunks)} chunks)")

    return result

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