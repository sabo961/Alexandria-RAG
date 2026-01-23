"""
Alexandria RAG Query Engine
============================

Unified RAG (Retrieval-Augmented Generation) system for querying the Alexandria knowledge base.

FEATURES
--------
- Semantic search via Qdrant vector database
- Similarity threshold filtering (removes irrelevant results)
- Optional LLM-based reranking (improves result quality)
- OpenRouter integration for answer generation
- CLI and Python module interfaces

BASIC USAGE (CLI)
-----------------
Simple query:
    python rag_query.py "What does Silverston say about shipments?"

With domain filter:
    python rag_query.py "cognitive load" --domain psychology

With similarity threshold:
    python rag_query.py "database design" --threshold 0.6

ADVANCED USAGE (CLI)
--------------------
Enable LLM reranking (better relevance):
    python rag_query.py "shipment patterns" --rerank

Generate LLM answer (full RAG):
    python rag_query.py "What is normalization?" --answer

Use specific model:
    python rag_query.py "cognitive load" --answer --model "gpt-4o-mini"

Combine all features:
    python rag_query.py "database design patterns" \
        --domain technical \
        --threshold 0.6 \
        --rerank \
        --rerank-model "meta-llama/llama-3.2-3b-instruct:free" \
        --answer \
        --model "gpt-4o-mini" \
        --fetch-multiplier 5 \
        --format json

PYTHON MODULE USAGE
-------------------
Simple retrieval:
    from rag_query import perform_rag_query

    result = perform_rag_query(
        query="What is cognitive load?",
        threshold=0.5
    )

    for chunk in result.results:
        print(f"{chunk['book_title']}: {chunk['text'][:100]}")

Full RAG with reranking:
    result = perform_rag_query(
        query="Explain database normalization",
        domain_filter="technical",
        threshold=0.6,
        enable_reranking=True,
        rerank_model="meta-llama/llama-3.2-3b-instruct:free",
        generate_llm_answer=True,
        answer_model="gpt-4o-mini",
        openrouter_api_key=api_key
    )

    print(result.answer)
    print(f"Sources: {len(result.results)} chunks")

AI AGENT USAGE
--------------
For AI agents calling this tool:

1. Simple search (no API key needed):
    result = perform_rag_query(
        query="user's question",
        collection_name="alexandria",
        limit=5,
        domain_filter="technical",  # or psychology, philosophy, history, literature
        threshold=0.5
    )

2. With reranking (requires API key):
    result = perform_rag_query(
        query="user's question",
        threshold=0.5,
        enable_reranking=True,
        rerank_model="meta-llama/llama-3.2-3b-instruct:free",
        openrouter_api_key=os.environ.get("OPENROUTER_API_KEY")
    )

3. Full RAG answer (requires API key):
    result = perform_rag_query(
        query="user's question",
        generate_llm_answer=True,
        answer_model="gpt-4o-mini",
        openrouter_api_key=os.environ.get("OPENROUTER_API_KEY")
    )

    # Return answer to user
    return result.answer

CLI PARAMETERS
--------------
Required:
    query                 Natural language question

Search options:
    --collection NAME     Qdrant collection (default: alexandria)
    --limit N             Number of results (default: 5)
    --domain DOMAIN       Filter by domain: technical, psychology, philosophy, history, literature
    --threshold FLOAT     Similarity threshold 0.0-1.0 (default: 0.5)
    --fetch-multiplier N  Fetch limit×N results for filtering (default: 3, min fetch: 20)

Reranking:
    --rerank              Enable LLM reranking
    --rerank-model MODEL  Model for reranking (default: meta-llama/llama-3.2-3b-instruct:free)

Answer generation:
    --answer              Generate LLM answer
    --model MODEL         Model for answer (default: meta-llama/llama-3.2-3b-instruct:free)

API:
    --api-key KEY         OpenRouter API key (or set OPENROUTER_API_KEY env var)

Output:
    --format FORMAT       Output format: markdown, text, json (default: markdown)

Qdrant:
    --host HOST           Qdrant host (default: 192.168.0.151)
    --port PORT           Qdrant port (default: 6333)

AVAILABLE MODELS
----------------
Free models (--model or --rerank-model):
    meta-llama/llama-3.2-3b-instruct:free
    meta-llama/llama-3.2-1b-instruct:free
    qwen/qwen-2.5-7b-instruct:free
    mistralai/mistral-7b-instruct:free

Paid models (better quality):
    openai/gpt-4o-mini
    openai/gpt-4o
    anthropic/claude-3.5-sonnet
    anthropic/claude-3.5-haiku

DOMAINS
-------
Available domain filters:
    technical     - Programming, databases, data modeling, engineering
    psychology    - Psychology, therapy, human behavior
    philosophy    - Philosophy, ethics, existentialism
    history       - Historical works, biographies
    literature    - Fiction, novels (Mishima, Murakami, etc.)

EXAMPLES
--------
1. Basic semantic search:
    python rag_query.py "What is the shipment pattern?"

2. Domain-filtered search:
    python rag_query.py "cognitive load theory" --domain psychology --limit 3

3. High-quality retrieval (with reranking):
    python rag_query.py "database normalization" \
        --domain technical \
        --threshold 0.6 \
        --rerank \
        --limit 5

4. Full RAG answer:
    export OPENROUTER_API_KEY="sk-or-v1-..."
    python rag_query.py "Explain Mishima's philosophy" \
        --domain literature \
        --answer \
        --model "gpt-4o-mini"

5. JSON output for scripting:
    python rag_query.py "data modeling patterns" \
        --domain technical \
        --answer \
        --format json > output.json

OUTPUT FORMATS
--------------
markdown  - Human-readable with sections (default)
text      - Plain text, compact
json      - Structured JSON for parsing

RETURN VALUES (Python module)
------------------------------
RAGResult object with:
    .query            - Original query string
    .results          - List of dicts with: score, book_title, author, domain, section_name, text
    .answer           - Generated answer (if generate_llm_answer=True)
    .filtered_count   - Number of initial results before filtering
    .reranked         - Boolean, whether reranking was used

TIPS
----
- Start with threshold=0.5, adjust based on results
- Use reranking for critical queries where quality > speed
- Free models are fast and good enough for most queries
- Paid models (gpt-4o-mini) offer better answer quality
- Domain filters significantly improve precision
- JSON output is ideal for AI agents and scripting
- Increase --fetch-multiplier (4-5) for better quality when using reranking
- Lower --fetch-multiplier (2) for faster queries when quality is sufficient

TROUBLESHOOTING
---------------
"No results above threshold":
    → Lower --threshold value (try 0.3)
    → Remove --domain filter
    → Check if collection has relevant content

"API key required":
    → Set OPENROUTER_API_KEY environment variable
    → Or pass --api-key parameter
    → Get key from https://openrouter.ai/keys

"Qdrant connection error":
    → Check if Qdrant is running: http://192.168.0.151:6333
    → Verify --host and --port parameters

ARCHITECTURE
------------
This is the unified RAG query engine used by:
- CLI (this script)
- Streamlit GUI (alexandria_app.py)
- AI agents
- Python automation scripts

Single source of truth for RAG logic.
"""

import argparse
import logging
import os
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from ingest_books import generate_embeddings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class RAGResult:
    """Result from RAG query"""
    query: str
    results: List[Dict[str, Any]]
    answer: Optional[str] = None
    filtered_count: int = 0
    reranked: bool = False
    initial_count: int = 0
    error: Optional[str] = None

    @property
    def sources(self) -> List[Dict[str, Any]]:
        """Alias for results (for backward compatibility with GUI)"""
        return self.results


def search_qdrant(
    query: str,
    collection_name: str,
    limit: int,
    domain_filter: Optional[str],
    threshold: float,
    host: str,
    port: int,
    fetch_multiplier: int = 3
) -> tuple[List[Any], int]:
    """
    Search Qdrant and apply similarity threshold filtering.

    Returns:
        (filtered_results, initial_count)
    """
    client = QdrantClient(host=host, port=port)

    # Generate query embedding
    logger.info(f"🔍 Query: '{query}'")
    query_vector = generate_embeddings([query])[0]

    # Build filter
    query_filter = None
    if domain_filter and domain_filter != "all":
        query_filter = Filter(
            must=[FieldCondition(key="domain", match=MatchValue(value=domain_filter))]
        )
        logger.info(f"📚 Filtering by domain: {domain_filter}")

    # Fetch more results than needed for better filtering/reranking
    # fetch_multiplier controls how many extra results to retrieve
    fetch_limit = max(20, limit * fetch_multiplier)

    # Search
    initial_results = client.query_points(
        collection_name=collection_name,
        query=query_vector,
        limit=fetch_limit,
        query_filter=query_filter
    ).points

    logger.info(f"✅ Retrieved {len(initial_results)} initial results")

    # Apply similarity threshold filter
    filtered_results = [r for r in initial_results if r.score >= threshold]

    if len(filtered_results) < len(initial_results):
        logger.info(f"🎯 Filtered to {len(filtered_results)} results above threshold ({threshold:.2f})")

    return filtered_results, len(initial_results)


def rerank_with_llm(
    results: List[Any],
    query: str,
    limit: int,
    rerank_model: str,
    openrouter_api_key: str
) -> List[Any]:
    """
    Rerank results using LLM relevance scoring.

    Args:
        results: Initial search results
        query: User query
        limit: Final number of results to return
        rerank_model: OpenRouter model ID
        openrouter_api_key: API key

    Returns:
        Reranked results (top N)
    """
    import requests

    logger.info(f"🤖 Reranking top {min(10, len(results))} results with {rerank_model}...")

    rerank_scores = []
    for result in results[:10]:  # Only rerank top 10 to save API calls
        rerank_prompt = f"""Rate the relevance of this text to the question on a scale of 0-10.

Question: {query}

Text: {result.payload.get('text', '')[:500]}

Respond with only a number from 0-10."""

        try:
            rerank_response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {openrouter_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": rerank_model,
                    "messages": [{"role": "user", "content": rerank_prompt}]
                },
                timeout=30
            )

            if rerank_response.status_code == 200:
                score_text = rerank_response.json()["choices"][0]["message"]["content"]
                score = float(score_text.strip())
                rerank_scores.append((result, score))
            else:
                logger.warning(f"Rerank API error {rerank_response.status_code}, using default score")
                rerank_scores.append((result, 5.0))
        except (ValueError, KeyError, IndexError, Exception) as e:
            logger.warning(f"Rerank parse error: {e}, using default score")
            rerank_scores.append((result, 5.0))

    # Sort by rerank score and take top results
    rerank_scores.sort(key=lambda x: x[1], reverse=True)
    reranked_results = [r[0] for r in rerank_scores[:limit]]

    logger.info(f"✅ Reranked to top {len(reranked_results)} most relevant chunks")
    return reranked_results


def generate_answer(
    query: str,
    results: List[Any],
    model: str,
    openrouter_api_key: str,
    temperature: float = 0.7
) -> str:
    """
    Generate answer using OpenRouter LLM.

    Args:
        query: User query
        results: Retrieved context chunks
        model: OpenRouter model ID
        openrouter_api_key: API key
        temperature: Controls randomness (0.0-2.0)

    Returns:
        Generated answer text
    """
    import requests

    # Build RAG context
    context_parts = []
    for idx, result in enumerate(results, 1):
        p = result.payload
        context_parts.append(
            f"[Source {idx}] Book: {p.get('book_title', 'Unknown')} by {p.get('author', 'Unknown')}\n"
            f"Content: {p.get('text', '')}\n"
        )

    rag_context = "\n---\n".join(context_parts)

    # Build prompt
    system_prompt = (
        "You are Alexandria, a helpful assistant with access to a knowledge base of books. "
        "Answer the user's question based on the provided context from the knowledge base. "
        "If the context doesn't contain enough information, say so. "
        "Always cite your sources by mentioning the book title and author."
    )

    user_prompt = f"Context from knowledge base:\n\n{rag_context}\n\nUser Question: {query}\n\nPlease provide a comprehensive answer based on the context above."

    logger.info(f"🤖 Generating answer with {model}...")

    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/yourusername/alexandria",
            "X-Title": "Alexandria RAG System"
        },
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature
        },
        timeout=60
    )

    if response.status_code == 200:
        answer = response.json()["choices"][0]["message"]["content"]
        logger.info("✅ Answer generated successfully")
        return answer
    else:
        error_msg = f"OpenRouter API error {response.status_code}: {response.text}"
        logger.error(error_msg)
        raise Exception(error_msg)


def perform_rag_query(
    query: str,
    collection_name: str = 'alexandria',
    limit: int = 5,
    domain_filter: Optional[str] = None,
    threshold: float = 0.5,
    enable_reranking: bool = False,
    rerank_model: Optional[str] = None,
    generate_llm_answer: bool = False,
    answer_model: Optional[str] = None,
    openrouter_api_key: Optional[str] = None,
    host: str = '192.168.0.151',
    port: int = 6333,
    fetch_multiplier: int = 3,
    temperature: float = 0.7
) -> RAGResult:
    """
    Unified RAG query function.

    Args:
        query: Natural language question
        collection_name: Qdrant collection to search
        limit: Number of final results to return
        domain_filter: Optional domain filter (technical, psychology, etc.)
        threshold: Similarity score threshold (0.0-1.0)
        enable_reranking: Whether to rerank with LLM
        rerank_model: Model for reranking (required if enable_reranking=True)
        generate_llm_answer: Whether to generate answer with LLM
        answer_model: Model for answer generation (required if generate_llm_answer=True)
        openrouter_api_key: OpenRouter API key (required if using LLM features)
        host: Qdrant host
        port: Qdrant port
        fetch_multiplier: How many times 'limit' to fetch from Qdrant (default: 3)
                         Fetches limit * fetch_multiplier results for better filtering/reranking
                         Min fetch is always 20 to ensure quality pool

    Returns:
        RAGResult object with results and optional answer
    """
    # Validate inputs
    if enable_reranking and not rerank_model:
        raise ValueError("rerank_model required when enable_reranking=True")
    if generate_llm_answer and not answer_model:
        raise ValueError("answer_model required when generate_llm_answer=True")
    if (enable_reranking or generate_llm_answer) and not openrouter_api_key:
        raise ValueError("openrouter_api_key required for LLM features")

    # Step 1: Search Qdrant with threshold filtering
    try:
        filtered_results, initial_count = search_qdrant(
            query=query,
            collection_name=collection_name,
            limit=limit,
            domain_filter=domain_filter,
            threshold=threshold,
            host=host,
            port=port,
            fetch_multiplier=fetch_multiplier
        )
    except Exception as e:
        logger.error(f"Qdrant search failed: {str(e)}")
        return RAGResult(
            query=query,
            results=[],
            filtered_count=0,
            initial_count=0,
            reranked=False,
            error=f"Qdrant search failed: {str(e)}"
        )

    if len(filtered_results) == 0:
        logger.warning(f"⚠️ No results above similarity threshold {threshold:.2f}")
        return RAGResult(
            query=query,
            results=[],
            filtered_count=0,
            initial_count=initial_count,
            reranked=False
        )

    # Step 2: Optional LLM reranking
    if enable_reranking:
        try:
            final_results = rerank_with_llm(
                results=filtered_results,
                query=query,
                limit=limit,
                rerank_model=rerank_model,
                openrouter_api_key=openrouter_api_key
            )
            reranked = True
        except Exception as e:
            logger.error(f"Reranking failed: {str(e)}")
            # Fall back to filtered results without reranking
            final_results = filtered_results[:limit]
            reranked = False
    else:
        final_results = filtered_results[:limit]
        reranked = False

    # Convert results to dict format
    results_data = []
    for result in final_results:
        p = result.payload
        results_data.append({
            'score': result.score,
            'book_title': p.get('book_title', 'Unknown'),
            'author': p.get('author', 'Unknown'),
            'domain': p.get('domain', 'Unknown'),
            'section_name': p.get('section_name', 'Unknown'),
            'text': p.get('text', '')
        })

    # Step 3: Optional answer generation
    answer = None
    if generate_llm_answer:
        try:
            answer = generate_answer(
                query=query,
                results=final_results,
                model=answer_model,
                openrouter_api_key=openrouter_api_key,
                temperature=temperature
            )
        except Exception as e:
            logger.error(f"Failed to generate answer: {str(e)}")
            return RAGResult(
                query=query,
                results=results_data,
                answer=None,
                filtered_count=len(filtered_results),
                initial_count=initial_count,
                reranked=reranked,
                error=str(e)
            )

    return RAGResult(
        query=query,
        results=results_data,
        answer=answer,
        filtered_count=len(filtered_results),
        initial_count=initial_count,
        reranked=reranked
    )


def print_results(result: RAGResult, format: str = 'markdown'):
    """Print RAG results in specified format"""
    if format == 'json':
        import json
        output = {
            'query': result.query,
            'filtered_count': result.filtered_count,
            'reranked': result.reranked,
            'results': result.results,
            'answer': result.answer
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))

    elif format == 'markdown':
        print("\n" + "=" * 80)
        print("# Alexandria RAG Results")
        print("=" * 80)
        print(f"\n**Query:** {result.query}")
        print(f"**Retrieved:** {len(result.results)} chunks (filtered from {result.filtered_count})")
        print(f"**Reranked:** {'Yes' if result.reranked else 'No'}")

        if result.answer:
            print("\n## 💡 Answer\n")
            print(result.answer)

        print("\n## 📚 Sources\n")
        for idx, r in enumerate(result.results, 1):
            print(f"### Source {idx} (Relevance: {r['score']:.4f})")
            print(f"- **Book:** {r['book_title']}")
            print(f"- **Author:** {r['author']}")
            print(f"- **Domain:** {r['domain']}")
            print(f"- **Section:** {r['section_name']}")
            print(f"\n> {r['text'][:500]}{'...' if len(r['text']) > 500 else ''}\n")
            print("---\n")

    else:  # text
        print(f"\nQuery: {result.query}")
        print(f"Results: {len(result.results)} chunks\n")

        if result.answer:
            print("ANSWER:")
            print(result.answer)
            print("\n" + "-" * 80 + "\n")

        for idx, r in enumerate(result.results, 1):
            print(f"[{idx}] {r['book_title']} by {r['author']} (Score: {r['score']:.4f})")
            print(r['text'][:300] + "...\n")


def main():
    parser = argparse.ArgumentParser(description='Alexandria RAG Query Engine')

    # Required
    parser.add_argument('query', type=str, help='Natural language question')

    # Search options
    parser.add_argument('--collection', type=str, default='alexandria', help='Qdrant collection')
    parser.add_argument('--limit', type=int, default=5, help='Number of results')
    parser.add_argument('--domain', type=str, help='Filter by domain')
    parser.add_argument('--threshold', type=float, default=0.5, help='Similarity threshold (0.0-1.0)')
    parser.add_argument('--fetch-multiplier', type=int, default=3,
                       help='Fetch limit*N results from Qdrant for better filtering (default: 3)')

    # Reranking
    parser.add_argument('--rerank', action='store_true', help='Enable LLM reranking')
    parser.add_argument('--rerank-model', type=str, default='meta-llama/llama-3.2-3b-instruct:free',
                       help='Model for reranking')

    # Answer generation
    parser.add_argument('--answer', action='store_true', help='Generate LLM answer')
    parser.add_argument('--model', type=str, default='meta-llama/llama-3.2-3b-instruct:free',
                       help='Model for answer generation')

    # API
    parser.add_argument('--api-key', type=str, help='OpenRouter API key (or set OPENROUTER_API_KEY env var)')

    # Output
    parser.add_argument('--format', type=str, choices=['markdown', 'text', 'json'],
                       default='markdown', help='Output format')

    # Qdrant
    parser.add_argument('--host', type=str, default='192.168.0.151', help='Qdrant host')
    parser.add_argument('--port', type=int, default=6333, help='Qdrant port')

    args = parser.parse_args()

    # Get API key
    api_key = args.api_key or os.environ.get('OPENROUTER_API_KEY')

    try:
        result = perform_rag_query(
            query=args.query,
            collection_name=args.collection,
            limit=args.limit,
            domain_filter=args.domain,
            threshold=args.threshold,
            enable_reranking=args.rerank,
            rerank_model=args.rerank_model if args.rerank else None,
            generate_llm_answer=args.answer,
            answer_model=args.model if args.answer else None,
            openrouter_api_key=api_key,
            host=args.host,
            port=args.port,
            fetch_multiplier=args.fetch_multiplier
        )

        print_results(result, format=args.format)

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == '__main__':
    main()
