"""
Alexandria RAG Query Tool

Simple RAG (Retrieval-Augmented Generation) query tool.
Searches Qdrant for relevant chunks and formats them for LLM consumption.

Usage:
    python rag_query.py "What does Silverston say about shipments?"
    python rag_query.py "Explain database normalization" --limit 3
    python rag_query.py "cognitive load theory" --domain psychology
"""

import argparse
import logging
from typing import List, Optional

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def rag_query(
    query: str,
    collection_name: str = 'alexandria_test',
    limit: int = 5,
    domain_filter: Optional[str] = None,
    host: str = 'localhost',
    port: int = 6333,
    output_format: str = 'markdown'
):
    """
    Perform RAG query: retrieve relevant chunks and format for LLM.

    Args:
        query: Natural language question
        collection_name: Qdrant collection to search
        limit: Number of results to return
        domain_filter: Optional domain filter (technical, psychology, etc.)
        host: Qdrant host
        port: Qdrant port
        output_format: Output format (markdown, text, json)
    """
    client = QdrantClient(host=host, port=port)

    # Generate query embedding
    logger.info(f"🔍 Query: '{query}'")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    query_vector = model.encode(query).tolist()

    # Build filter
    query_filter = None
    if domain_filter:
        query_filter = Filter(
            must=[
                FieldCondition(key="domain", match=MatchValue(value=domain_filter))
            ]
        )
        logger.info(f"📚 Filtering by domain: {domain_filter}")

    # Search
    results = client.query_points(
        collection_name=collection_name,
        query=query_vector,
        limit=limit,
        query_filter=query_filter
    ).points

    logger.info(f"✅ Retrieved {len(results)} relevant chunks\n")

    # Format output
    if output_format == 'markdown':
        print_markdown_output(query, results)
    elif output_format == 'text':
        print_text_output(query, results)
    elif output_format == 'json':
        print_json_output(query, results)
    else:
        print_markdown_output(query, results)


def print_markdown_output(query: str, results: List):
    """Format output as markdown for copying to LLM"""
    print("\n" + "=" * 80)
    print("# RAG Context for LLM")
    print("=" * 80)
    print()
    print(f"**User Question:** {query}")
    print()
    print("**Retrieved Context from Alexandria Library:**")
    print()

    for idx, result in enumerate(results, 1):
        payload = result.payload
        print(f"## Source {idx} (Relevance: {result.score:.4f})")
        print()
        print(f"- **Book:** {payload.get('book_title', 'N/A')}")
        print(f"- **Author:** {payload.get('author', 'N/A')}")
        print(f"- **Domain:** {payload.get('domain', 'N/A')}")
        print(f"- **Section:** {payload.get('section_name', 'N/A')}")
        print()
        print("**Text:**")
        print()
        print(f"> {payload.get('text', '')}")
        print()
        print("---")
        print()

    print()
    print("## Instructions for LLM")
    print()
    print("Please answer the user's question based **only** on the context provided above.")
    print("If the context doesn't contain enough information, say so.")
    print("Always cite which source(s) you used (e.g., 'According to Source 1...').")
    print()
    print("=" * 80)
    print()


def print_text_output(query: str, results: List):
    """Format output as plain text"""
    print("\n" + "=" * 80)
    print(f"QUESTION: {query}")
    print("=" * 80)
    print()

    for idx, result in enumerate(results, 1):
        payload = result.payload
        print(f"\n[Source {idx}] Score: {result.score:.4f}")
        print(f"Book: {payload.get('book_title', 'N/A')}")
        print(f"Author: {payload.get('author', 'N/A')}")
        print(f"Domain: {payload.get('domain', 'N/A')}")
        print()
        print(payload.get('text', ''))
        print("\n" + "-" * 80)


def print_json_output(query: str, results: List):
    """Format output as JSON"""
    import json

    output = {
        "query": query,
        "results": []
    }

    for result in results:
        payload = result.payload
        output["results"].append({
            "score": result.score,
            "book_title": payload.get('book_title', 'N/A'),
            "author": payload.get('author', 'N/A'),
            "domain": payload.get('domain', 'N/A'),
            "section_name": payload.get('section_name', 'N/A'),
            "text": payload.get('text', '')
        })

    print(json.dumps(output, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(
        description='Alexandria RAG Query Tool'
    )
    parser.add_argument(
        'query',
        type=str,
        help='Natural language question'
    )
    parser.add_argument(
        '--collection',
        type=str,
        default='alexandria_test',
        help='Qdrant collection name'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=5,
        help='Number of results to retrieve'
    )
    parser.add_argument(
        '--domain',
        type=str,
        help='Filter by domain (technical, psychology, philosophy, history)'
    )
    parser.add_argument(
        '--host',
        default='192.168.0.151',
        help='Qdrant host'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=6333,
        help='Qdrant port'
    )
    parser.add_argument(
        '--format',
        type=str,
        choices=['markdown', 'text', 'json'],
        default='markdown',
        help='Output format'
    )

    args = parser.parse_args()

    rag_query(
        query=args.query,
        collection_name=args.collection,
        limit=args.limit,
        domain_filter=args.domain,
        host=args.host,
        port=args.port,
        output_format=args.format
    )


if __name__ == '__main__':
    main()
