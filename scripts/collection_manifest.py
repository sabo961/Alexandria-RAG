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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CollectionManifest:
    """Manage collection manifests"""

    def __init__(self, manifest_file: str = '../logs/collection_manifest.json'):
        self.manifest_file = Path(manifest_file)
        self.manifest_file.parent.mkdir(parents=True, exist_ok=True)
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
                'Collection', 'Book Title', 'Author', 'Domain',
                'Chunks', 'Size (MB)', 'File Name', 'Ingested At'
            ])

            # Data rows
            for collection_name, collection in self.manifest['collections'].items():
                for book in collection['books']:
                    writer.writerow([
                        collection_name,
                        book['book_title'],
                        book['author'],
                        book['domain'],
                        book['chunks_count'],
                        book['file_size_mb'],
                        book['file_name'],
                        book['ingested_at'][:10]  # Just date, not time
                    ])

            # Summary row
            writer.writerow([])
            writer.writerow(['TOTAL', '', '', '',
                           sum(c['total_chunks'] for c in self.manifest['collections'].values()),
                           sum(c['total_size_mb'] for c in self.manifest['collections'].values()),
                           '', ''])


    def add_book(
        self,
        collection_name: str,
        book_path: str,
        book_title: str,
        author: str,
        domain: str,
        chunks_count: int,
        file_size_mb: float,
        ingested_at: Optional[str] = None
    ):
        """Add book to manifest"""
        if collection_name not in self.manifest['collections']:
            self.manifest['collections'][collection_name] = {
                'created_at': datetime.now().isoformat(),
                'domain': domain,
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
        book_entry = {
            'file_path': book_path,
            'file_name': Path(book_path).name,
            'book_title': book_title,
            'author': author,
            'domain': domain,
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
        logger.info(f"Domain: {collection.get('domain', 'N/A')}")
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
            logger.info(f"   Domain: {book['domain']}")
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
            logger.info(f"   Domain: {collection.get('domain', 'N/A')}")
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
            domain = payload.get('domain', 'unknown')

            if book_title not in books:
                books[book_title] = {
                    'title': book_title,
                    'author': author,
                    'domain': domain,
                    'chunks': 0
                }
            books[book_title]['chunks'] += 1

        logger.info(f"Found {len(books)} unique books in Qdrant")

        # Update manifest
        if collection_name not in self.manifest['collections']:
            self.manifest['collections'][collection_name] = {
                'created_at': datetime.now().isoformat(),
                'domain': domain,
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
        default='192.168.0.151',
        help='Qdrant host (for sync command)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=6333,
        help='Qdrant port (for sync command)'
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
