#!/usr/bin/env python3
"""
Alexandria Ingestion Experiment: Fixed vs Semantic Chunking
==========================================================

This script compares the current fixed-window chunking strategy
with a new semantic similarity-based strategy on Nietzsche's texts.
"""

import sys
import os
from pathlib import Path
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import re

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "scripts"))

from scripts.ingest_books import extract_text, chunk_text, EmbeddingGenerator

def split_into_sentences(text: str) -> list:
    """Simple sentence splitter using regex."""
    # Split by ., !, or ? followed by whitespace
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if len(s.strip()) > 10]

def semantic_chunking(sentences: list, embeddings: np.ndarray, threshold: float = 0.6) -> list:
    """
    Groups sentences into chunks based on semantic similarity shifts.
    A new chunk starts when similarity between adjacent sentences drops below threshold.
    """
    chunks = []
    current_chunk_sentences = []
    
    if len(sentences) == 0:
        return []

    current_chunk_sentences.append(sentences[0])
    
    for i in range(1, len(sentences)):
        # Calculate similarity between current sentence and previous one
        similarity = cosine_similarity(
            embeddings[i-1].reshape(1, -1), 
            embeddings[i].reshape(1, -1)
        )[0][0]
        
        if similarity < threshold:
            # Theme change detected! Start new chunk
            chunks.append(" ".join(current_chunk_sentences))
            current_chunk_sentences = [sentences[i]]
        else:
            current_chunk_sentences.append(sentences[i])
            
    # Add last chunk
    if current_chunk_sentences:
        chunks.append(" ".join(current_chunk_sentences))
        
    return chunks

def run_experiment(filename: str, domain: str = "philosophy"):
    file_path = project_root / "ingest" / filename
    print(f"\n" + "="*80)
    print(f"🧪 EXPERIMENT: {filename}")
    print("="*80)
    
    # 1. Extract Text
    print(f"📖 Extracting text...")
    sections, metadata = extract_text(str(file_path))
    full_text = "\n\n".join([s['text'] for s in sections])
    # Take a sample for faster testing (first 10,000 characters)
    sample_text = full_text[:15000]
    print(f"✅ Text extracted ({len(full_text):,} chars). Using sample of {len(sample_text):,} chars.")

    # 2. Fixed Chunking (Current Strategy)
    print(f"⚙️ Running Fixed Chunking (Standard)...")
    fixed_chunks = chunk_text(sample_text, domain=domain, max_tokens=1500, overlap=200)
    
    # 3. Semantic Chunking (New Strategy)
    print(f"🧠 Running Semantic Chunking (V2)...")
    sentences = split_into_sentences(sample_text)
    print(f"   Detected {len(sentences)} sentences.")
    
    embedder = EmbeddingGenerator()
    embeddings = embedder.generate_embeddings(sentences)
    
    # Try different thresholds
    for threshold in [0.5, 0.6, 0.7]:
        sem_chunks = semantic_chunking(sentences, np.array(embeddings), threshold=threshold)
        
        print(f"\n--- RESULTS (Threshold: {threshold}) ---")
        print(f"Fixed Chunks: {len(fixed_chunks)}")
        print(f"Semantic Chunks: {len(sem_chunks)}")
        
        # Compare first few boundaries
        print(f"\n🔍 SAMPLE CHUNKS (Semantic):")
        for i, chunk in enumerate(sem_chunks[:3]):
            print(f"\nCHUNK {i+1} ({len(chunk.split())} words):")
            print("-" * 40)
            print(chunk[:400] + "...")

    print("\n" + "="*80)

if __name__ == "__main__":
    # Test on Beyond Good and Evil
    test_file = "Beyond Good and Evil - Friedrich Nietzsche.epub"
    run_experiment(test_file)
