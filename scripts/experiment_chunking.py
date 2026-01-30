"""
Alexandria Chunking Strategy Experiment Tool

Compare different chunking strategies to find optimal parameters.
Useful for A/B testing chunk sizes and evaluating retrieval quality.

Usage:
    # Test 3 different chunk sizes on same book
    python experiment_chunking.py --file "../ingest/Silverston Vol 3.epub" --strategies small,medium,large

    # Custom chunk size comparison
    python experiment_chunking.py --file "book.pdf" --custom-sizes 1000,1500,2000

    # Evaluate retrieval quality with test queries
    python experiment_chunking.py --file "book.epub" --strategies small,large --evaluate
"""

import argparse
import logging
from typing import List, Dict, Tuple
from pathlib import Path
import statistics

from ingest_books import (
    extract_text_from_epub,
    extract_text_from_pdf,
    extract_text_from_txt,
    chunk_text,
    generate_embeddings,
    upload_to_qdrant,
    get_token_count,
    DOMAIN_CHUNK_SIZES
)
from qdrant_utils import search_collection
from config import QDRANT_HOST, QDRANT_PORT

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Predefined chunking strategies for experimentation
CHUNKING_STRATEGIES = {
    'small': {'min': 800, 'max': 1200, 'overlap': 100},
    'medium': {'min': 1200, 'max': 1800, 'overlap': 150},
    'large': {'min': 1800, 'max': 2500, 'overlap': 200},
    'technical_default': DOMAIN_CHUNK_SIZES['technical'],
    'psychology_default': DOMAIN_CHUNK_SIZES['psychology'],
    'philosophy_default': DOMAIN_CHUNK_SIZES['philosophy'],
    'history_default': DOMAIN_CHUNK_SIZES['history'],
}


def analyze_chunks(chunks: List[Dict]) -> Dict:
    """
    Analyze chunk statistics.

    Args:
        chunks: List of chunk dictionaries

    Returns:
        Dictionary with statistics
    """
    token_counts = [get_token_count(c['text']) for c in chunks]

    return {
        'total_chunks': len(chunks),
        'avg_tokens': statistics.mean(token_counts),
        'median_tokens': statistics.median(token_counts),
        'min_tokens': min(token_counts),
        'max_tokens': max(token_counts),
        'std_dev': statistics.stdev(token_counts) if len(token_counts) > 1 else 0
    }


def chunk_with_strategy(
    chapters: List[Dict],
    strategy: Dict,
    book_title: str,
    author: str,
    domain: str = 'technical'
) -> Tuple[List[Dict], Dict]:
    """
    Chunk text with specific strategy and return chunks + stats.

    Args:
        chapters: List of chapter dictionaries
        strategy: Chunking strategy parameters
        book_title: Book title
        author: Author name
        domain: Domain category

    Returns:
        Tuple of (chunks, statistics)
    """
    # Temporarily override domain chunk sizes
    original_sizes = DOMAIN_CHUNK_SIZES[domain].copy()
    DOMAIN_CHUNK_SIZES[domain] = strategy

    all_chunks = []
    for chapter in chapters:
        chunks = chunk_text(
            text=chapter['text'],
            domain=domain,
            section_name=chapter['name'],
            book_title=book_title,
            author=author
        )
        all_chunks.extend(chunks)

    # Restore original sizes
    DOMAIN_CHUNK_SIZES[domain] = original_sizes

    # Analyze chunks
    stats = analyze_chunks(all_chunks)

    return all_chunks, stats


def experiment_chunking(
    filepath: str,
    strategies: List[str],
    custom_sizes: List[Tuple[int, int, int]] = None,
    domain: str = 'technical',
    collection_prefix: str = 'experiment',
    host: str = QDRANT_HOST,
    port: int = QDRANT_PORT
):
    """
    Run chunking experiments with different strategies.

    Args:
        filepath: Path to book file
        strategies: List of strategy names
        custom_sizes: List of (min, max, overlap) tuples
        domain: Domain category
        collection_prefix: Prefix for collection names
        host: Qdrant host
        port: Qdrant port
    """
    logger.info("=" * 80)
    logger.info("🔬 Alexandria Chunking Strategy Experiment")
    logger.info("=" * 80)
    logger.info(f"File: {filepath}")
    logger.info(f"Domain: {domain}")
    logger.info(f"Strategies: {', '.join(strategies)}")
    logger.info("=" * 80)
    logger.info("")

    # Extract text
    filepath_obj = Path(filepath)
    ext = filepath_obj.suffix.lower()

    logger.info(f"📖 Extracting text from {ext} file...")

    if ext == '.epub':
        chapters, metadata = extract_text_from_epub(filepath)
        book_title = metadata.get('title', filepath_obj.stem)
        author = metadata.get('author', 'Unknown')
    elif ext == '.pdf':
        pages, metadata = extract_text_from_pdf(filepath)
        chapters = pages
        book_title = metadata.get('title', filepath_obj.stem)
        author = metadata.get('author', 'Unknown')
    elif ext in ['.txt', '.md']:
        text, metadata = extract_text_from_txt(filepath)
        chapters = [{'text': text, 'name': filepath_obj.stem}]
        book_title = filepath_obj.stem
        author = 'Unknown'
    else:
        raise ValueError(f"Unsupported format: {ext}")

    logger.info(f"   Book: {book_title} by {author}")
    logger.info(f"   Sections: {len(chapters)}\n")

    # Run experiments
    results = []

    for strategy_name in strategies:
        if strategy_name not in CHUNKING_STRATEGIES:
            logger.warning(f"⚠️  Unknown strategy: {strategy_name}, skipping")
            continue

        logger.info(f"🧪 Testing strategy: {strategy_name}")
        strategy = CHUNKING_STRATEGIES[strategy_name]
        logger.info(f"   Config: min={strategy['min']}, max={strategy['max']}, overlap={strategy['overlap']}")

        # Chunk with strategy
        chunks, stats = chunk_with_strategy(
            chapters=chapters,
            strategy=strategy,
            book_title=book_title,
            author=author,
            domain=domain
        )

        logger.info(f"   Results:")
        logger.info(f"      Total chunks: {stats['total_chunks']}")
        logger.info(f"      Avg tokens: {stats['avg_tokens']:.0f}")
        logger.info(f"      Median tokens: {stats['median_tokens']:.0f}")
        logger.info(f"      Min/Max: {stats['min_tokens']}/{stats['max_tokens']}")
        logger.info(f"      Std dev: {stats['std_dev']:.0f}")

        # Upload to separate collection
        collection_name = f"{collection_prefix}_{strategy_name}"
        logger.info(f"   Uploading to collection: {collection_name}...")

        embeddings = generate_embeddings([c['text'] for c in chunks])
        upload_to_qdrant(
            chunks=chunks,
            embeddings=embeddings,
            domain=domain,
            collection_name=collection_name,
            host=host,
            port=port
        )

        logger.info(f"✅ Strategy '{strategy_name}' completed\n")

        results.append({
            'strategy': strategy_name,
            'config': strategy,
            'stats': stats,
            'collection': collection_name
        })

    # Custom size experiments
    if custom_sizes:
        for idx, (min_size, max_size, overlap) in enumerate(custom_sizes, 1):
            strategy_name = f"custom_{idx}"
            logger.info(f"🧪 Testing custom strategy: {strategy_name}")
            strategy = {'min': min_size, 'max': max_size, 'overlap': overlap}
            logger.info(f"   Config: min={min_size}, max={max_size}, overlap={overlap}")

            chunks, stats = chunk_with_strategy(
                chapters=chapters,
                strategy=strategy,
                book_title=book_title,
                author=author,
                domain=domain
            )

            logger.info(f"   Results:")
            logger.info(f"      Total chunks: {stats['total_chunks']}")
            logger.info(f"      Avg tokens: {stats['avg_tokens']:.0f}")

            collection_name = f"{collection_prefix}_{strategy_name}"
            embeddings = generate_embeddings([c['text'] for c in chunks])
            upload_to_qdrant(
                chunks=chunks,
                embeddings=embeddings,
                domain=domain,
                collection_name=collection_name,
                host=host,
                port=port
            )

            logger.info(f"✅ Custom strategy {idx} completed\n")

            results.append({
                'strategy': strategy_name,
                'config': strategy,
                'stats': stats,
                'collection': collection_name
            })

    # Print comparison table
    logger.info("")
    logger.info("=" * 80)
    logger.info("📊 Chunking Strategy Comparison")
    logger.info("=" * 80)
    logger.info("")
    logger.info(f"{'Strategy':<20} {'Chunks':<10} {'Avg Tokens':<12} {'Median':<10} {'Std Dev':<10}")
    logger.info("-" * 80)

    for result in results:
        stats = result['stats']
        logger.info(
            f"{result['strategy']:<20} "
            f"{stats['total_chunks']:<10} "
            f"{stats['avg_tokens']:<12.0f} "
            f"{stats['median_tokens']:<10.0f} "
            f"{stats['std_dev']:<10.0f}"
        )

    logger.info("")
    logger.info("=" * 80)
    logger.info("✅ Experiment complete!")
    logger.info("")
    logger.info("Next steps:")
    logger.info("1. Test retrieval quality with test queries:")
    logger.info(f"   python qdrant_utils.py search <collection_name> \"test query\" --limit 5")
    logger.info("")
    logger.info("2. Compare collections:")
    for result in results:
        logger.info(f"   - {result['collection']}")
    logger.info("")
    logger.info("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description='Alexandria Chunking Strategy Experiment Tool'
    )
    parser.add_argument(
        '--file',
        type=str,
        required=True,
        help='Path to book file'
    )
    parser.add_argument(
        '--strategies',
        type=str,
        help='Comma-separated list of strategy names (small,medium,large,technical_default,etc.)'
    )
    parser.add_argument(
        '--custom-sizes',
        type=str,
        help='Custom chunk sizes as "min:max:overlap" (e.g., "1000:1500:150,2000:2500:200")'
    )
    parser.add_argument(
        '--domain',
        type=str,
        default='technical',
        choices=['technical', 'psychology', 'philosophy', 'history'],
        help='Domain category (default: technical)'
    )
    parser.add_argument(
        '--collection-prefix',
        type=str,
        default='experiment',
        help='Prefix for collection names (default: experiment)'
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

    # Parse strategies
    strategies = []
    if args.strategies:
        strategies = [s.strip() for s in args.strategies.split(',')]

    # Parse custom sizes
    custom_sizes = []
    if args.custom_sizes:
        for size_spec in args.custom_sizes.split(','):
            parts = size_spec.split(':')
            if len(parts) != 3:
                logger.error(f"Invalid custom size format: {size_spec}")
                continue
            custom_sizes.append((int(parts[0]), int(parts[1]), int(parts[2])))

    if not strategies and not custom_sizes:
        logger.error("Must specify --strategies or --custom-sizes")
        return

    # Run experiments
    experiment_chunking(
        filepath=args.file,
        strategies=strategies,
        custom_sizes=custom_sizes,
        domain=args.domain,
        collection_prefix=args.collection_prefix,
        host=args.host,
        port=args.port
    )


if __name__ == '__main__':
    main()
