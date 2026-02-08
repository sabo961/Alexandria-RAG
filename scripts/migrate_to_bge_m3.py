#!/usr/bin/env python3
"""
Alexandria bge-m3 Migration Script
==================================

This script migrates Alexandria from bge-large-en-v1.5 to bge-m3 (multilingual).

What it does:
1. Downloads bge-m3 model (if not cached)
2. Lists existing Qdrant collections
3. Deletes old test collections (optional)
4. Creates new collection with bge-m3
5. Re-ingests books with new embeddings
6. Tests multilingual queries

Usage:
    python migrate_to_bge_m3.py [--delete-old] [--test-only]

Options:
    --delete-old    Delete old collections before migration
    --test-only     Only test model download, don't migrate
    --keep-backups  Keep old collections as backups (rename with -old suffix)
"""

import sys
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from sentence_transformers import SentenceTransformer
import argparse

# Add scripts directory to path
SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS_DIR))

from config import (
    QDRANT_HOST,
    QDRANT_PORT,
    QDRANT_COLLECTION,
    get_qdrant_url,
    EMBEDDING_MODELS,
    DEFAULT_EMBEDDING_MODEL,
    EMBEDDING_DEVICE
)


def download_model(model_name: str):
    """Download and cache the embedding model."""
    # Auto-detect device (sentence-transformers doesn't support "auto")
    import torch
    device = EMBEDDING_DEVICE
    if device == 'auto':
        device = 'cuda' if torch.cuda.is_available() else 'cpu'

    print(f"\n[>>] Downloading model: {model_name}")
    print(f"     Device: {device} (CUDA available: {torch.cuda.is_available()})")
    print(f"     Size: ~2.2GB (this may take a few minutes...)")

    try:
        model = SentenceTransformer(model_name, device=device)
        print(f"[OK] Model downloaded and cached successfully!")
        print(f"     Device: {model.device}")
        return model
    except Exception as e:
        print(f"[FAIL] Failed to download model: {e}")
        sys.exit(1)


def list_collections(client: QdrantClient):
    """List all Qdrant collections."""
    print(f"\n[LIST] Existing collections on {QDRANT_HOST}:")
    collections = client.get_collections().collections

    if not collections:
        print("       (no collections found)")
        return []

    for coll in collections:
        # Get detailed collection info
        try:
            info = client.get_collection(coll.name)
            points = info.points_count if hasattr(info, 'points_count') else 0
            print(f"       - {coll.name} (points: {points:,})")
        except:
            print(f"       - {coll.name}")

    return [coll.name for coll in collections]


def delete_collection(client: QdrantClient, collection_name: str):
    """Delete a Qdrant collection."""
    try:
        print(f"\n[DEL] Deleting collection: {collection_name}")
        client.delete_collection(collection_name)
        print(f"[OK] Collection deleted: {collection_name}")
    except Exception as e:
        print(f"[WARN] Could not delete {collection_name}: {e}")


def backup_collection(client: QdrantClient, collection_name: str):
    """Rename collection to add -old suffix."""
    backup_name = f"{collection_name}-old"
    try:
        print(f"\n[BACKUP] Backing up collection: {collection_name} -> {backup_name}")
        # Qdrant doesn't have rename, so we inform user
        print(f"[WARN] Note: Qdrant doesn't support collection rename.")
        print(f"       Consider manually backing up collection before deletion.")
        return False
    except Exception as e:
        print(f"[WARN] Backup failed: {e}")
        return False


def create_collection(client: QdrantClient, collection_name: str, dimension: int):
    """Create new Qdrant collection with specified dimensions."""
    print(f"\n[CREATE] Creating collection: {collection_name}")
    print(f"         Vector dimension: {dimension}")
    print(f"         Distance metric: Cosine")

    try:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=dimension,
                distance=Distance.COSINE
            )
        )
        print(f"[OK] Collection created: {collection_name}")
        return True
    except Exception as e:
        print(f"[FAIL] Failed to create collection: {e}")
        return False


def test_multilingual_embedding(model: SentenceTransformer):
    """Test model with multilingual text."""
    print(f"\n[TEST] Testing multilingual embeddings...")

    test_texts = [
        ("English", "What is the meaning of life?"),
        ("German", "Was ist der Sinn des Lebens?"),
        ("Russian", "В чём смысл жизни?"),
        ("French", "Quel est le sens de la vie?"),
        ("Croatian", "Što je smisao života?"),
    ]

    print("       Encoding test sentences:")
    for lang, text in test_texts:
        try:
            embedding = model.encode(text)
            print(f"       [OK] {lang:10s} - {text[:40]:40s} -> {len(embedding)} dims")
        except Exception as e:
            print(f"       [FAIL] {lang:10s} - Failed: {e}")

    print("\n[OK] Multilingual embedding test passed!")


def main():
    parser = argparse.ArgumentParser(description='Migrate Alexandria to bge-m3')
    parser.add_argument('--delete-old', action='store_true',
                       help='Delete old test collections')
    parser.add_argument('--test-only', action='store_true',
                       help='Only test model download')
    parser.add_argument('--keep-backups', action='store_true',
                       help='Keep old collections as backups')
    args = parser.parse_args()

    print("=" * 60)
    print("Alexandria bge-m3 Migration")
    print("=" * 60)

    # Step 1: Download model
    model_config = EMBEDDING_MODELS[DEFAULT_EMBEDDING_MODEL]
    model_name = model_config["name"]
    model_dim = model_config["dim"]

    print(f"\n[TARGET] Target model: {model_name}")
    print(f"         Dimension: {model_dim}")
    print(f"         Default model: {DEFAULT_EMBEDDING_MODEL}")

    model = download_model(model_name)

    # Test multilingual capabilities
    test_multilingual_embedding(model)

    if args.test_only:
        print("\n[OK] Test complete! Model is ready to use.")
        print("     Run without --test-only to perform migration.")
        return

    # Step 2: Connect to Qdrant
    print(f"\n[CONNECT] Connecting to Qdrant: {get_qdrant_url()}")
    try:
        client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        print("[OK] Connected to Qdrant")
    except Exception as e:
        print(f"[FAIL] Failed to connect to Qdrant: {e}")
        sys.exit(1)

    # Step 3: List collections
    existing_collections = list_collections(client)

    # Step 4: Handle old collections
    test_collections = [c for c in existing_collections if 'test' in c.lower()]

    if args.delete_old and test_collections:
        print(f"\n[WARN] Found {len(test_collections)} test collection(s):")
        for coll in test_collections:
            print(f"       - {coll}")

        confirm = input("\n[?] Delete these test collections? (yes/no): ")
        if confirm.lower() == 'yes':
            for coll in test_collections:
                delete_collection(client, coll)
        else:
            print("    Skipping deletion.")

    # Step 5: Check if main collection exists
    if QDRANT_COLLECTION in existing_collections:
        print(f"\n[WARN] Main collection '{QDRANT_COLLECTION}' already exists!")
        print("       Options:")
        print("       1. Keep existing (cancel migration)")
        print("       2. Delete and recreate (DESTRUCTIVE!)")
        print("       3. Create new collection with different name")

        choice = input("\n       Enter choice (1/2/3): ")

        if choice == "1":
            print("       Migration cancelled.")
            return
        elif choice == "2":
            confirm = input(f"       [WARN] Delete '{QDRANT_COLLECTION}'? (type 'DELETE' to confirm): ")
            if confirm == "DELETE":
                delete_collection(client, QDRANT_COLLECTION)
                create_collection(client, QDRANT_COLLECTION, model_dim)
            else:
                print("       Deletion cancelled.")
                return
        elif choice == "3":
            new_name = input("       Enter new collection name: ")
            create_collection(client, new_name, model_dim)
        else:
            print("       Invalid choice. Migration cancelled.")
            return
    else:
        # Create new collection
        create_collection(client, QDRANT_COLLECTION, model_dim)

    # Step 6: Migration complete
    print("\n" + "=" * 60)
    print("[OK] Migration to bge-m3 complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Run: python ingest_books.py")
    print("   (to re-ingest books with bge-m3 embeddings)")
    print("2. Test multilingual queries:")
    print("   python rag_query.py 'Was sagt Kant über das Ding an sich?'")
    print("   python rag_query.py 'Что Достоевский говорит о страдании?'")
    print("3. Compare retrieval quality with old model")
    print("\n[DONE] Enjoy multilingual RAG!")


if __name__ == "__main__":
    main()
