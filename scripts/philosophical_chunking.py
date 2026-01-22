"""
Philosophical Argument-Based Chunking
======================================

Pre-chunks philosophical essays based on conceptual oppositions.

PROBLEM:
Token-based chunking splits philosophical arguments across chunk boundaries,
causing RAG retrieval failure. The LLM knows the answer from general knowledge
but can't cite passages from the retrieved context.

SOLUTION:
A chunk = one complete conceptual conflict (both poles + authorial stance).

USAGE:
    from philosophical_chunking import argument_prechunk

    text_blocks = argument_prechunk(text, author="Mishima")
    # Returns list of text blocks, each containing a complete argument

INTEGRATION:
    Automatically activated when domain.use_argument_chunking == True
    in domains.json. No manual configuration needed.

REFERENCE:
    See docs/argument_based_chunking_for_philosophical_texts_alexandria_rag.md
"""

from typing import List, Tuple

# Conceptual opposition pairs for different philosophical authors/styles
ARGUMENT_PAIRS = {
    "mishima": [
        (["word", "words", "language", "writing", "pen", "text"],
         ["body", "flesh", "muscle", "training", "action", "violence", "discipline"]),

        (["intellect", "mind", "thought", "abstraction", "spirit"],
         ["muscle", "strength", "pain", "physical", "flesh"]),

        (["ideal", "beauty", "form", "abstraction", "concept"],
         ["death", "blood", "destruction", "decay", "violence"]),

        (["civilization", "culture", "society", "modernity"],
         ["nature", "primitive", "instinct", "animal"]),
    ],

    "nietzsche": [
        (["slave", "herd", "weakness", "pity", "christianity"],
         ["master", "strength", "will", "power", "nobility"]),

        (["good", "evil", "morality", "guilt", "sin"],
         ["beyond", "transvaluation", "innocence", "nature"]),

        (["reason", "truth", "science", "logic"],
         ["life", "instinct", "art", "dionysian"]),
    ],

    "cioran": [
        (["hope", "progress", "optimism", "future", "illusion"],
         ["despair", "decay", "lucidity", "void", "truth"]),

        (["life", "birth", "existence", "being"],
         ["death", "suicide", "nothingness", "void"]),
    ],

    # Default pairs for general philosophical essays
    "default": [
        (["mind", "thought", "reason", "intellect", "abstraction"],
         ["body", "emotion", "instinct", "concrete", "material"]),

        (["ideal", "form", "universal", "essence"],
         ["real", "particular", "existence", "concrete"]),

        (["theory", "concept", "principle", "idea"],
         ["practice", "action", "experience", "life"]),
    ]
}


def detect_author_style(text: str, author: str = None) -> str:
    """
    Detect which argument pair set to use.

    Args:
        text: Full text of the work
        author: Optional author name hint

    Returns:
        Key to ARGUMENT_PAIRS dictionary
    """
    if author:
        author_lower = author.lower()
        if "mishima" in author_lower:
            return "mishima"
        if "nietzsche" in author_lower:
            return "nietzsche"
        if "cioran" in author_lower:
            return "cioran"

    # Simple keyword detection if no author provided
    text_lower = text[:5000].lower()  # Check first 5000 chars

    # Mishima signature
    if sum(1 for w in ["muscle", "sword", "body", "flesh"] if w in text_lower) >= 2:
        return "mishima"

    # Nietzsche signature
    if sum(1 for w in ["zarathustra", "übermensch", "will to power"] if w in text_lower) >= 1:
        return "nietzsche"

    # Cioran signature
    if sum(1 for w in ["insomnia", "void", "lucidity", "despair"] if w in text_lower) >= 2:
        return "cioran"

    return "default"


def contains_opposition(pair: Tuple[List[str], List[str]], text: str) -> bool:
    """
    Check if text contains both sides of a conceptual opposition.

    Args:
        pair: Tuple of (side_a_keywords, side_b_keywords)
        text: Text to check

    Returns:
        True if both sides present
    """
    side_a, side_b = pair
    text_lower = text.lower()

    has_side_a = any(keyword in text_lower for keyword in side_a)
    has_side_b = any(keyword in text_lower for keyword in side_b)

    return has_side_a and has_side_b


def argument_prechunk(text: str, author: str = None, min_paragraph_length: int = 200) -> List[str]:
    """
    Pre-chunk philosophical text based on argumentative structure.

    Splits text into blocks where each block contains a complete conceptual
    opposition (both poles of an argument). This preserves philosophical
    reasoning for RAG retrieval.

    Args:
        text: Full text to pre-chunk
        author: Optional author name for style detection
        min_paragraph_length: Minimum paragraph length to consider (chars)

    Returns:
        List of text blocks, each containing a complete argument

    Example:
        >>> text = "Words betray the body. The pen cannot capture muscle..."
        >>> blocks = argument_prechunk(text, author="Mishima")
        >>> # Each block will contain both "words/pen" and "body/muscle"
    """
    # Detect which opposition pairs to use
    style = detect_author_style(text, author)
    pairs = ARGUMENT_PAIRS.get(style, ARGUMENT_PAIRS["default"])

    # Split into paragraphs
    paragraphs = [
        p.strip()
        for p in text.split("\n\n")
        if len(p.strip()) > min_paragraph_length
    ]

    if not paragraphs:
        # Fallback: return full text if no valid paragraphs
        return [text]

    chunks = []
    buffer = []

    for paragraph in paragraphs:
        buffer.append(paragraph)
        joined = " ".join(buffer)

        # Check if buffer contains any complete opposition
        if any(contains_opposition(pair, joined) for pair in pairs):
            # Found a complete argument - save it
            chunks.append(joined)
            buffer = []

    # Handle remaining buffer
    if buffer:
        remaining = " ".join(buffer)
        if chunks:
            # Append to last chunk to avoid orphan paragraphs
            chunks[-1] = chunks[-1] + "\n\n" + remaining
        else:
            # No chunks yet - return as single chunk
            chunks.append(remaining)

    return chunks if chunks else [text]


def should_use_argument_chunking(domain_id: str) -> bool:
    """
    Check if argument-based chunking should be used for this domain.

    Args:
        domain_id: Domain identifier (e.g., "philosophy")

    Returns:
        True if argument chunking should be used

    Note:
        Reads from domains.json to check use_argument_chunking flag
    """
    import json
    from pathlib import Path

    domains_file = Path(__file__).parent / 'domains.json'

    try:
        with open(domains_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for domain in data.get('domains', []):
            if domain.get('id') == domain_id:
                return domain.get('use_argument_chunking', False)

    except Exception:
        pass

    return False


# CLI for testing
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test philosophical argument chunking")
    parser.add_argument('file', help='Path to text file')
    parser.add_argument('--author', help='Author name for style detection')
    parser.add_argument('--min-length', type=int, default=200, help='Min paragraph length')

    args = parser.parse_args()

    with open(args.file, 'r', encoding='utf-8') as f:
        text = f.read()

    chunks = argument_prechunk(text, author=args.author, min_paragraph_length=args.min_length)

    print(f"Original text: {len(text):,} chars")
    print(f"Pre-chunks created: {len(chunks)}")
    print(f"Style detected: {detect_author_style(text, args.author)}")
    print("\n" + "="*80 + "\n")

    for i, chunk in enumerate(chunks, 1):
        print(f"CHUNK {i} ({len(chunk):,} chars)")
        print("-" * 80)
        print(chunk[:500] + "..." if len(chunk) > 500 else chunk)
        print("\n")
