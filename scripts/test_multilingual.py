#!/usr/bin/env python3
"""Quick multilingual RAG test - bypasses rag_query.py encoding issues."""

import sys
import io

# Fix Windows terminal encoding for Croatian/multilingual output
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, r'c:\Users\goran\source\repos\Temenos\Akademija\Alexandria\scripts')

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from config import QDRANT_HOST, QDRANT_PORT, QDRANT_COLLECTION

# Query
query = "Što se nalazi u devetom krugu pakla i koje kazne tamo čekaju?"

print(f"Query: {query}")
print()

# Connect and search
client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

# Load model
model = SentenceTransformer("BAAI/bge-m3", device="cpu")
query_vector = model.encode([query])[0].tolist()

# Search
results = client.query_points(
    collection_name=QDRANT_COLLECTION,
    query=query_vector,
    limit=5,
    with_payload=True
)

print(f"=== Top {len(results.points)} Results ===\n")

for i, point in enumerate(results.points, 1):
    payload = point.payload
    score = point.score

    title = payload.get('title', 'Unknown')
    author = payload.get('author', 'Unknown')
    language = payload.get('language', 'unknown')
    text = payload.get('text', '')[:300]

    print(f"{i}. {title}")
    print(f"   Author: {author} | Language: {language} | Score: {score:.4f}")
    print(f"   Text: {text}...")
    print()
