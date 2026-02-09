#!/usr/bin/env python3
"""List all books currently in Qdrant collection."""

import sys
from pathlib import Path
from collections import defaultdict

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from qdrant_client import QdrantClient
from config import QDRANT_HOST, QDRANT_PORT, QDRANT_COLLECTION

def main():
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    # Get collection info
    try:
        collection_info = client.get_collection(QDRANT_COLLECTION)
        print(f"\n=== Collection: {QDRANT_COLLECTION} ===")
        print(f"Total chunks: {collection_info.points_count:,}")
        print(f"Vector dimension: {collection_info.config.params.vectors.size}")
        print()

        # Scroll through all points and group by book
        books = {}  # key: (source, source_id), value: book metadata + chunk count

        offset = None
        batch_size = 100

        print("Scanning collection...")

        while True:
            results = client.scroll(
                collection_name=QDRANT_COLLECTION,
                limit=batch_size,
                offset=offset,
                with_payload=True,
                with_vectors=False
            )

            points, next_offset = results

            if not points:
                break

            for point in points:
                payload = point.payload
                source = payload.get('source', 'unknown')
                source_id = payload.get('source_id', 'unknown')

                key = (source, source_id)

                if key not in books:
                    books[key] = {
                        'title': payload.get('book_title', 'Unknown'),
                        'author': payload.get('author', 'Unknown'),
                        'language': payload.get('language', 'unknown'),
                        'source': source,
                        'source_id': source_id,
                        'chunks': 0
                    }

                books[key]['chunks'] += 1

            if next_offset is None:
                break
            offset = next_offset

        print(f"\n=== Books in Collection ({len(books)} books) ===\n")

        # Sort by title
        sorted_books = sorted(books.values(), key=lambda b: b['title'].lower())

        total_chunks = 0

        for i, book in enumerate(sorted_books, 1):
            print(f"{i}. {book['title']}")
            print(f"   Author: {book['author']}")
            print(f"   Source: {book['source']}:{book['source_id']} | Language: {book['language']}")
            print(f"   Chunks: {book['chunks']:,}")
            print()

            total_chunks += book['chunks']

        print("=" * 80)
        print(f"Total: {len(books)} books, {total_chunks:,} chunks")
        print(f"Average: {total_chunks / len(books):.0f} chunks per book")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
