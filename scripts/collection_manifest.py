"""
Alexandria Collection Manifest Tool

Maintain a manifest of what's been ingested into each collection.
Provides quick overview of collection contents without querying Qdrant.

Usage:
    # Show manifest for collection
    python collection_manifest.py show alexandria

    # Show all collections
    python collection_manifest.py list

    # Export manifest to file
    python collection_manifest.py export alexandria --output ../logs/alexandria_manifest.json

    # Sync manifest with actual Qdrant collection
    python collection_manifest.py sync alexandria
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from qdrant_client import QdrantClient
from qdrant_utils import check_qdrant_connection
from config import QDRANT_HOST, QDRANT_PORT

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CollectionManifest:
    """Manage collection manifests"""

    def __init__(self, manifest_file: str = '../logs/collection_manifest.json', collection_name: Optional[str] = None):
        """
        Initialize CollectionManifest.

        Args:
            manifest_file: Path to global manifest (for backward compatibility)
            collection_name: If provided, use collection-specific manifest file
        """
        # Support collection-specific manifest files
        if collection_name:
            # Detect logs directory (works from both GUI and scripts)
            logs_dir = Path(__file__).parent.parent / 'logs'
            if not logs_dir.exists():
                # Fallback for CLI usage from scripts directory
                logs_dir = Path('../logs')

            self.manifest_file = logs_dir / f'{collection_name}_manifest.json'
            self.progress_file = Path(f'batch_ingest_progress_{collection_name}.json')
        else:
            self.manifest_file = Path(manifest_file)
            self.progress_file = Path('batch_ingest_progress.json')

        self.manifest_file.parent.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name
        self.manifest = self._load_manifest()

    def _load_manifest(self) -> Dict:
        """Load manifest from file"""
        if self.manifest_file.exists():
            with open(self.manifest_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat(),
            'collections': {}
        }

    def verify_collection_exists(self, collection_name: str, qdrant_host: str = QDRANT_HOST, qdrant_port: int = QDRANT_PORT) -> bool:
        """
        Verify collection exists in Qdrant. If not, reset manifest for this collection.

        Args:
            collection_name: Name of collection to verify
            qdrant_host: Qdrant server host
            qdrant_port: Qdrant server port

        Returns:
            True if collection exists, False if it was deleted (and manifest reset)
        """
        # Check connection before attempting to verify collection
        is_connected, error_msg = check_qdrant_connection(qdrant_host, qdrant_port)
        if not is_connected:
            logger.error(error_msg)
            return False

        try:
            client = QdrantClient(host=qdrant_host, port=qdrant_port)
            collections = [c.name for c in client.get_collections().collections]

            if collection_name not in collections:
                # Collection was deleted - reset manifest
                if collection_name in self.manifest['collections']:
                    logger.warning(f"⚠️  Collection '{collection_name}' not found in Qdrant - resetting manifest")
                    del self.manifest['collections'][collection_name]
                    self.save_manifest()

                    # Reset progress file if exists
                    if self.progress_file.exists():
                        self.progress_file.unlink()
                        logger.info(f"🗑️  Deleted progress file: {self.progress_file}")

                return False

            return True
        except Exception as e:
            logger.error(f"❌ Error verifying collection: {e}")
            return False

    def save_manifest(self):
        """Save manifest to file (both JSON and CSV)"""
        self.manifest['last_updated'] = datetime.now().isoformat()

        # Save JSON
        with open(self.manifest_file, 'w', encoding='utf-8') as f:
            json.dump(self.manifest, f, indent=2, ensure_ascii=False)

        # Save CSV (human-readable)
        csv_file = self.manifest_file.with_suffix('.csv')
        self._export_csv(csv_file)

        logger.info(f"✅ Manifest saved to: {self.manifest_file}")
        logger.info(f"✅ CSV export saved to: {csv_file}")

    def _export_csv(self, csv_file: Path):
        """Export manifest to CSV format"""
        import csv

        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Header
            writer.writerow([
                'Collection', 'Book Title', 'Author', 'Language', 'File Type',
                'Chunks', 'Size (MB)', 'File Name', 'Ingested At'
            ])

            # Data rows
            for collection_name, collection in self.manifest['collections'].items():
                for book in collection['books']:
                    # Extract file type from filename or use stored value
                    file_type = book.get('file_type')
                    if not file_type:
                        # Fallback: extract from filename
                        file_type = Path(book['file_name']).suffix.upper().replace('.', '')

                    # Get language (with fallback for old manifests)
                    language = book.get('language', 'unknown')

                    writer.writerow([
                        collection_name,
                        book['book_title'],
                        book['author'],
                        language,
                        file_type,
                        book['chunks_count'],
                        book['file_size_mb'],
                        book['file_name'],
                        book['ingested_at'][:10]  # Just date, not time
                    ])

            # Summary row
            writer.writerow([])
            writer.writerow(['TOTAL', '', '', '', '',
                           sum(c['total_chunks'] for c in self.manifest['collections'].values()),
                           sum(c['total_size_mb'] for c in self.manifest['collections'].values()),
                           '', ''])


    def add_book(
        self,
        collection_name: str,
        book_path: str,
        book_title: str,
        author: str,
        chunks_count: int,
        file_size_mb: float,
        ingested_at: Optional[str] = None,
        file_type: Optional[str] = None,
        language: Optional[str] = None
    ):
        """Add book to manifest with metadata"""
        if collection_name not in self.manifest['collections']:
            self.manifest['collections'][collection_name] = {
                'created_at': datetime.now().isoformat(),
                'books': [],
                'total_chunks': 0,
                'total_size_mb': 0.0
            }

        collection = self.manifest['collections'][collection_name]

        # Check if book already exists
        existing_book = next(
            (b for b in collection['books'] if b['file_path'] == book_path),
            None
        )

        if existing_book:
            logger.warning(f"Book already in manifest: {book_path}")
            return

        # Add book
        # Auto-detect file type if not provided
        if not file_type:
            file_type = Path(book_path).suffix.upper().replace('.', '')

        book_entry = {
            'file_path': book_path,
            'file_name': Path(book_path).name,
            'book_title': book_title,
            'author': author,
            'file_type': file_type,
            'language': language or 'unknown',
            'chunks_count': chunks_count,
            'file_size_mb': round(file_size_mb, 2),
            'ingested_at': ingested_at or datetime.now().isoformat()
        }

        collection['books'].append(book_entry)
        collection['total_chunks'] += chunks_count
        collection['total_size_mb'] += file_size_mb

        self.save_manifest()
        logger.info(f"✅ Added to manifest: {book_title} ({chunks_count} chunks)")

    def remove_book(self, collection_name: str, book_path: str):
        """Remove book from manifest"""
        if collection_name not in self.manifest['collections']:
            logger.error(f"Collection not found: {collection_name}")
            return

        collection = self.manifest['collections'][collection_name]

        book = next(
            (b for b in collection['books'] if b['file_path'] == book_path),
            None
        )

        if not book:
            logger.error(f"Book not found: {book_path}")
            return

        collection['books'].remove(book)
        collection['total_chunks'] -= book['chunks_count']
        collection['total_size_mb'] -= book['file_size_mb']

        self.save_manifest()
        logger.info(f"✅ Removed from manifest: {book['book_title']}")

    def show_collection(self, collection_name: str):
        """Display collection contents"""
        if collection_name not in self.manifest['collections']:
            logger.error(f"Collection not found: {collection_name}")
            return

        collection = self.manifest['collections'][collection_name]

        logger.info("")
        logger.info("=" * 80)
        logger.info(f"📚 Collection: {collection_name}")
        logger.info("=" * 80)
        logger.info(f"Created: {collection.get('created_at', 'N/A')}")
        logger.info(f"Total books: {len(collection['books'])}")
        logger.info(f"Total chunks: {collection['total_chunks']}")
        logger.info(f"Total size: {collection['total_size_mb']:.2f} MB")
        logger.info("")

        if not collection['books']:
            logger.info("No books in collection")
            logger.info("")
            return

        logger.info("Books:")
        logger.info("-" * 80)

        for idx, book in enumerate(collection['books'], 1):
            logger.info(f"\n{idx}. {book['book_title']}")
            logger.info(f"   Author: {book['author']}")
            logger.info(f"   File: {book['file_name']}")
            logger.info(f"   Chunks: {book['chunks_count']}")
            logger.info(f"   Size: {book['file_size_mb']} MB")
            logger.info(f"   Ingested: {book['ingested_at'][:10]}")

        logger.info("")
        logger.info("=" * 80)

    def list_collections(self):
        """List all collections"""
        logger.info("")
        logger.info("=" * 80)
        logger.info("📚 Collection Manifest")
        logger.info("=" * 80)
        logger.info(f"Manifest file: {self.manifest_file}")
        logger.info(f"Last updated: {self.manifest['last_updated']}")
        logger.info("")

        if not self.manifest['collections']:
            logger.info("No collections in manifest")
            logger.info("")
            return

        logger.info(f"Total collections: {len(self.manifest['collections'])}")
        logger.info("")

        for name, collection in self.manifest['collections'].items():
            logger.info(f"📁 {name}")
            logger.info(f"   Books: {len(collection['books'])}")
            logger.info(f"   Chunks: {collection['total_chunks']}")
            logger.info(f"   Size: {collection['total_size_mb']:.2f} MB")
            logger.info("")

        logger.info("=" * 80)

    def sync_with_qdrant(
        self,
        collection_name: str,
        host: str = 'localhost',
        port: int = 6333
    ):
        """Sync manifest with actual Qdrant collection"""
        logger.info(f"🔄 Syncing manifest with Qdrant collection: {collection_name}")

        # Check connection before attempting to sync
        is_connected, error_msg = check_qdrant_connection(host, port)
        if not is_connected:
            logger.error(error_msg)
            return

        client = QdrantClient(host=host, port=port)

        try:
            info = client.get_collection(collection_name)
        except Exception as e:
            logger.error(f"Collection not found in Qdrant: {e}")
            return

        # Sample points to get book list
        logger.info("Sampling collection...")
        points, _ = client.scroll(
            collection_name=collection_name,
            limit=1000,  # Sample up to 1000 points
            with_payload=True,
            with_vectors=False
        )

        # Group by book
        books = {}
        for point in points:
            payload = point.payload
            book_title = payload.get('book_title', 'Unknown')
            author = payload.get('author', 'Unknown')

            if book_title not in books:
                books[book_title] = {
                    'title': book_title,
                    'author': author,
                    'chunks': 0
                }
            books[book_title]['chunks'] += 1

        logger.info(f"Found {len(books)} unique books in Qdrant")

        # Update manifest
        if collection_name not in self.manifest['collections']:
            self.manifest['collections'][collection_name] = {
                'created_at': datetime.now().isoformat(),
                'books': [],
                'total_chunks': 0,
                'total_size_mb': 0.0
            }

        collection = self.manifest['collections'][collection_name]
        collection['total_chunks'] = info.points_count

        # Sync books (basic - without file paths)
        logger.info("⚠️  Note: Synced data doesn't include file paths")
        logger.info("For complete manifest, use batch_ingest.py which logs automatically")

        logger.info("")
        logger.info("Books found in Qdrant:")
        for book_title, book_data in books.items():
            logger.info(f"  - {book_title} ({book_data['chunks']} chunks)")

        self.save_manifest()

    def export_manifest(self, collection_name: str, output_file: str):
        """Export collection manifest to file"""
        if collection_name not in self.manifest['collections']:
            logger.error(f"Collection not found: {collection_name}")
            return

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        export_data = {
            'collection_name': collection_name,
            'exported_at': datetime.now().isoformat(),
            'collection': self.manifest['collections'][collection_name]
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        logger.info(f"✅ Manifest exported to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Alexandria Collection Manifest Tool'
    )
    parser.add_argument(
        'command',
        choices=['show', 'list', 'export', 'sync', 'remove'],
        help='Command to execute'
    )
    parser.add_argument(
        'collection',
        nargs='?',
        help='Collection name (required for show/export/sync/remove)'
    )
    parser.add_argument(
        '--book',
        type=str,
        help='Book file path (for remove command)'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output file for export'
    )
    parser.add_argument(
        '--host',
        default=QDRANT_HOST,
        help=f'Qdrant host (default: {QDRANT_HOST})'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=QDRANT_PORT,
        help=f'Qdrant port (default: {QDRANT_PORT})'
    )

    args = parser.parse_args()

    manifest = CollectionManifest()

    if args.command == 'list':
        manifest.list_collections()

    elif args.command == 'show':
        if not args.collection:
            logger.error("Collection name required")
            return
        manifest.show_collection(args.collection)

    elif args.command == 'export':
        if not args.collection:
            logger.error("Collection name required")
            return
        output = args.output or f'../logs/{args.collection}_manifest.json'
        manifest.export_manifest(args.collection, output)

    elif args.command == 'sync':
        if not args.collection:
            logger.error("Collection name required")
            return
        manifest.sync_with_qdrant(args.collection, args.host, args.port)

    elif args.command == 'remove':
        if not args.collection or not args.book:
            logger.error("Collection name and --book path required")
            return
        manifest.remove_book(args.collection, args.book)


if __name__ == '__main__':
    main()
