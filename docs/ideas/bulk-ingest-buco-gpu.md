# Bulk Ingestion on BUCO with GPU Acceleration

**Date:** 2026-01-30
**Priority:** High (for scaling to full library)
**Status:** Idea

## Problem

Ingesting hundreds of books from ZenBook (development machine) is slow:
- No CUDA support (Vulkan graphics only)
- ~30 sec/book for embedding generation (CPU-bound)
- 500 books = 4+ hours

## Solution

Run bulk ingestion directly on BUCO (Dell 3660) which has:
- **12GB NVIDIA VRAM** - CUDA acceleration for embeddings
- **80GB RAM** - large batch processing
- **Qdrant localhost** - zero network latency

## Expected Performance

| Machine | Embedding Time | 500 Books | Speedup |
|---------|---------------|-----------|---------|
| ZenBook (CPU) | ~30 sec/book | ~4 hours | baseline |
| BUCO (GPU) | ~2-3 sec/book | ~25 min | **10-15x** |

## Implementation Requirements

### 1. GPU Support (Minor)
```python
# EmbeddingGenerator - auto-detect CUDA
import torch
device = 'cuda' if torch.cuda.is_available() else 'cpu'
model = SentenceTransformer('all-MiniLM-L6-v2', device=device)
```

### 2. Parallel Book Processing (Medium)
```python
from concurrent.futures import ProcessPoolExecutor

def bulk_ingest(book_paths, max_workers=4):
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(ingest_book, book_paths))
    return results
```

### 3. Progress Reporting (Nice to Have)
- Real-time terminal output: book title, author, progress
- ETA calculation based on average time per book
- Summary at end: success/failed counts

### 4. Resume Capability (Already Exists)
- Collection manifest tracks ingested books
- `alexandria_batch_ingest` skips already-ingested books
- Just need to ensure manifest is consulted in bulk mode

## Testing Approach

1. Test on BUCO directly (SSH or local terminal)
2. Start with 10-20 books to verify GPU is being used
3. Monitor VRAM usage with `nvidia-smi`
4. Scale to 100, then full library

## Dependencies

- `torch` with CUDA support on BUCO
- `sentence-transformers` (already installed)
- NVIDIA drivers on BUCO (verify with `nvidia-smi`)

## Open Questions

- [ ] Is PyTorch with CUDA installed on BUCO?
- [ ] What's the optimal `max_workers` for parallel processing?
- [ ] Should we add a dedicated `/bulk-ingest` CLI command?

## Related

- `scripts/ingest_books.py` - current ingestion logic
- `scripts/collection_manifest.py` - tracking ingested books
- `scripts/mcp_server.py` - `alexandria_batch_ingest` tool
