"""
Alexandria Batch Ingestion Script

Batch processing script for ingesting multiple books from a directory.
Useful for processing entire library collections efficiently.

Usage:
    # Ingest all books from ingest folder
    python batch_ingest.py --directory ../ingest --domain technical

    # Ingest with custom collection and specific formats
    python batch_ingest.py --directory ../ingest --formats epub,pdf --collection alexandria_v2

    # Resume from failure (skip already processed books)
    python batch_ingest.py --directory ../ingest --resume
"""

import argparse
import logging
import os
import json
import shutil
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import traceback

from ingest_books import (
    extract_text_from_epub,
    extract_text_from_pdf,
    extract_text_from_txt,
    chunk_text,
    generate_embeddings,
    upload_to_qdrant,
    get_token_count
)
from collection_manifest import CollectionManifest
from calibre_db import CalibreDB
from config import QDRANT_HOST, QDRANT_PORT, QDRANT_COLLECTION, CALIBRE_LIBRARY_PATH

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BatchIngestionTracker:
    """Track batch ingestion progress to support resume functionality"""

    def __init__(self, tracker_file: str = 'batch_ingest_progress.json'):
        self.tracker_file = tracker_file
        self.progress = self._load_progress()

    def _load_progress(self) -> Dict:
        """Load progress from tracker file"""
        if os.path.exists(self.tracker_file):
            with open(self.tracker_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'started_at': datetime.now().isoformat(),
            'processed_files': [],
            'failed_files': [],
            'stats': {
                'total_books': 0,
                'total_chunks': 0,
                'total_errors': 0
            }
        }

    def save_progress(self):
        """Save progress to tracker file"""
        with open(self.tracker_file, 'w', encoding='utf-8') as f:
            json.dump(self.progress, f, indent=2, ensure_ascii=False)

    def mark_processed(self, filepath: str, chunks_count: int):
        """Mark file as successfully processed"""
        self.progress['processed_files'].append({
            'filepath': filepath,
            'chunks': chunks_count,
            'processed_at': datetime.now().isoformat()
        })
        self.progress['stats']['total_books'] += 1
        self.progress['stats']['total_chunks'] += chunks_count
        self.save_progress()

    def mark_failed(self, filepath: str, error: str):
        """Mark file as failed"""
        self.progress['failed_files'].append({
            'filepath': filepath,
            'error': error,
            'failed_at': datetime.now().isoformat()
        })
        self.progress['stats']['total_errors'] += 1
        self.save_progress()

    def is_processed(self, filepath: str) -> bool:
        """Check if file was already processed"""
        return any(
            f['filepath'] == filepath
            for f in self.progress['processed_files']
        )


def find_books(
    directory: str,
    formats: List[str] = ['epub', 'pdf', 'txt', 'md']
) -> List[Path]:
    """
    Find all book files in directory with specified formats.

    Args:
        directory: Directory to search
        formats: List of file extensions to include

    Returns:
        List of Path objects for matching files
    """
    books = []
    directory_path = Path(directory)

    for ext in formats:
        books.extend(directory_path.glob(f'**/*.{ext}'))
        books.extend(directory_path.glob(f'**/*.{ext.upper()}'))

    # Sort by filename for consistent processing order
    books.sort(key=lambda x: x.name)

    return books


def ingest_book(
    filepath: Path,
    domain: str,
    collection_name: str,
    host: str,
    port: int,
    manifest: Optional[CollectionManifest] = None,
    calibre_db: Optional[CalibreDB] = None
) -> int:
    """
    Ingest a single book file.

    Args:
        filepath: Path to book file
        domain: Domain category
        collection_name: Qdrant collection name
        host: Qdrant host
        port: Qdrant port
        manifest: Optional manifest tracker
        calibre_db: Optional Calibre DB for metadata lookup

    Returns:
        Number of chunks created

    Raises:
        Exception: If ingestion fails
    """
    logger.info(f"📖 Processing: {filepath.name}")

    # Extract text based on file format
    ext = filepath.suffix.lower()

    if ext == '.epub':
        chapters, metadata = extract_text_from_epub(str(filepath))
        book_title = metadata.get('title', filepath.stem)
        author = metadata.get('author', 'Unknown')
    elif ext == '.pdf':
        pages, metadata = extract_text_from_pdf(str(filepath))
        chapters = pages  # PDFs return pages, not chapters
        book_title = metadata.get('title', filepath.stem)
        author = metadata.get('author', 'Unknown')
    elif ext in ['.txt', '.md']:
        text, metadata = extract_text_from_txt(str(filepath))
        chapters = [{'text': text, 'name': filepath.stem}]
        book_title = filepath.stem
        author = 'Unknown'
    else:
        raise ValueError(f"Unsupported format: {ext}")

    logger.info(f"   Book: {book_title} by {author}")
    logger.info(f"   Sections: {len(chapters)}")

    # Chunk all chapters
    language = metadata.get('language', 'unknown') or 'unknown'
    all_chunks = []
    for chapter in chapters:
        chunks = chunk_text(
            text=chapter['text'],
            domain=domain,
            section_name=chapter['name'],
            book_title=book_title,
            author=author,
            language=language
        )
        all_chunks.extend(chunks)

    logger.info(f"   Total chunks: {len(all_chunks)}")

    # Calculate average chunk size
    avg_tokens = sum(get_token_count(c['text']) for c in all_chunks) / len(all_chunks)
    logger.info(f"   Avg chunk size: {avg_tokens:.0f} tokens")

    # Generate embeddings
    logger.info(f"   Generating embeddings...")
    embeddings = generate_embeddings([c['text'] for c in all_chunks])

    # Upload to Qdrant
    logger.info(f"   Uploading to Qdrant...")
    upload_to_qdrant(
        chunks=all_chunks,
        embeddings=embeddings,
        domain=domain,
        collection_name=collection_name,
        qdrant_host=host,
        qdrant_port=port
    )

    logger.info(f"✅ {filepath.name} - {len(all_chunks)} chunks uploaded\n")

    # Update manifest if provided
    if manifest:
        file_size_mb = filepath.stat().st_size / (1024 * 1024)
        file_type = filepath.suffix.upper().replace('.', '')

        # Try to get language from Calibre DB
        calibre_language = 'unknown'
        if calibre_db:
            try:
                calibre_book = calibre_db.match_file_to_book(filepath.name)
                if calibre_book:
                    calibre_language = calibre_book.language
                    logger.info(f"   📚 Matched to Calibre: language={calibre_language}")
            except Exception as e:
                logger.warning(f"   ⚠️  Could not lookup Calibre metadata: {e}")

        effective_language = calibre_language if calibre_language != 'unknown' else language

        manifest.add_book(
            collection_name=collection_name,
            book_path=str(filepath),
            book_title=book_title,
            author=author,
            chunks_count=len(all_chunks),
            file_size_mb=file_size_mb,
            file_type=file_type,
            language=effective_language
        )

    return len(all_chunks)


def batch_ingest(
    directory: str,
    domain: str,
    collection_name: str = 'alexandria',
    formats: List[str] = ['epub', 'pdf', 'txt', 'md'],
    resume: bool = False,
    move_completed: bool = True,
    host: str = 'localhost',
    port: int = 6333
):
    """
    Batch ingest multiple books from a directory.

    Args:
        directory: Directory containing books
        domain: Domain category for all books
        collection_name: Qdrant collection name
        formats: List of file formats to process
        resume: Skip already processed files
        move_completed: Move successfully ingested books to ../ingested/
        host: Qdrant host
        port: Qdrant port
    """
    logger.info("=" * 80)
    logger.info("📚 Alexandria Batch Ingestion")
    logger.info("=" * 80)
    logger.info(f"Directory: {directory}")
    logger.info(f"Domain: {domain}")
    logger.info(f"Collection: {collection_name}")
    logger.info(f"Formats: {', '.join(formats)}")
    logger.info(f"Resume mode: {resume}")
    logger.info(f"Move completed: {move_completed}")
    logger.info("=" * 80)
    logger.info("")

    # Initialize collection-specific tracker and manifest
    tracker = BatchIngestionTracker(tracker_file=f'batch_ingest_progress_{collection_name}.json')
    manifest = CollectionManifest(collection_name=collection_name)

    # Verify collection exists in Qdrant (reset manifest if deleted)
    manifest.verify_collection_exists(collection_name, qdrant_host=host, qdrant_port=port)

    # Initialize Calibre DB for metadata lookup (optional)
    calibre_db = None
    try:
        calibre_db = CalibreDB()  # Uses CALIBRE_LIBRARY_PATH from config
        logger.info("✅ Connected to Calibre DB for metadata enrichment")
    except Exception as e:
        logger.warning(f"⚠️  Could not connect to Calibre DB: {e}")
        logger.warning("   Continuing without Calibre metadata lookup")

    # Create ingested folder if moving completed books
    if move_completed:
        ingested_dir = Path(directory).parent / 'ingested'
        ingested_dir.mkdir(exist_ok=True)

    # Find all books
    books = find_books(directory, formats)
    logger.info(f"Found {len(books)} books to process\n")

    if not books:
        logger.warning("No books found. Exiting.")
        return

    # Process each book
    for idx, book_path in enumerate(books, 1):
        logger.info(f"[{idx}/{len(books)}] Processing {book_path.name}")

        # Skip if already processed (resume mode)
        if resume and tracker.is_processed(str(book_path)):
            logger.info(f"⏭️  Skipping (already processed)\n")
            continue

        try:
            chunks_count = ingest_book(
                filepath=book_path,
                domain=domain,
                collection_name=collection_name,
                host=host,
                port=port,
                manifest=manifest,
                calibre_db=calibre_db
            )
            tracker.mark_processed(str(book_path), chunks_count)

            # Move successfully ingested book
            if move_completed:
                ingested_path = ingested_dir / book_path.name
                shutil.move(str(book_path), str(ingested_path))
                logger.info(f"📦 Moved to: {ingested_path}\n")

        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            logger.error(f"❌ Failed to process {book_path.name}")
            logger.error(f"   Error: {error_msg}")
            logger.error(f"   Traceback: {traceback.format_exc()}")
            tracker.mark_failed(str(book_path), error_msg)
            logger.info("")
            continue

    # Print summary
    logger.info("")
    logger.info("=" * 80)
    logger.info("📊 Batch Ingestion Summary")
    logger.info("=" * 80)
    logger.info(f"Total books processed: {tracker.progress['stats']['total_books']}")
    logger.info(f"Total chunks created: {tracker.progress['stats']['total_chunks']}")
    logger.info(f"Total errors: {tracker.progress['stats']['total_errors']}")

    if tracker.progress['failed_files']:
        logger.info("\n❌ Failed files:")
        for failed in tracker.progress['failed_files']:
            logger.info(f"   - {Path(failed['filepath']).name}: {failed['error']}")

    logger.info("")
    logger.info(f"Progress saved to: {tracker.tracker_file}")
    logger.info("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description='Alexandria Batch Ingestion Script'
    )
    parser.add_argument(
        '--directory',
        type=str,
        required=True,
        help='Directory containing books to ingest'
    )
    parser.add_argument(
        '--domain',
        type=str,
        default='general',
        help='Domain category (legacy, not used for filtering)'
    )
    parser.add_argument(
        '--collection',
        type=str,
        default=QDRANT_COLLECTION,
        help=f'Qdrant collection name (default: {QDRANT_COLLECTION})'
    )
    parser.add_argument(
        '--formats',
        type=str,
        default='epub,pdf,txt,md',
        help='Comma-separated list of file formats (default: epub,pdf,txt,md)'
    )
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume from previous run (skip already processed files)'
    )
    parser.add_argument(
        '--no-move',
        action='store_true',
        help='Do not move completed books to ../ingested/ folder'
    )
    parser.add_argument(
        '--host',
        type=str,
        default=QDRANT_HOST,
        help=f'Qdrant server host (default: {QDRANT_HOST})'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=QDRANT_PORT,
        help=f'Qdrant server port (default: {QDRANT_PORT})'
    )

    args = parser.parse_args()

    # Parse formats
    formats = [fmt.strip() for fmt in args.formats.split(',')]

    # Run batch ingestion
    batch_ingest(
        directory=args.directory,
        domain=args.domain,
        collection_name=args.collection,
        formats=formats,
        resume=args.resume,
        move_completed=not args.no_move,
        host=args.host,
        port=args.port
    )


if __name__ == '__main__':
    main()
