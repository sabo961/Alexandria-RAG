# ADR-0010: GPU-Accelerated Embedding Model Selection

## Status
**Accepted** (2026-01-31) — **Implementation Note:** Actual migration used **BAAI/bge-m3** (multilingual, 100+ languages) instead of the originally recommended bge-large-en-v1.5 (English-only). The change was driven by epistemological requirements — see [ADR-0012: Original Language Primary](0012-original-language-primary.md). GPU acceleration design and all other aspects of this ADR remain valid.

## Date
2026-01-31

## Context

Alexandria currently uses `all-MiniLM-L6-v2` (384-dimensional embeddings) for semantic search. This was chosen initially for:
- Small size (~80MB)
- Fast CPU inference
- Good general-purpose quality

**Current Scale:**
- 150 books ingested (~28 minutes on CPU)
- Target: 9,000 books (~27.5 hours on CPU)

**Problem:**
The system is at a decision point:
1. Continue with current model (works, but mediocre quality)
2. Upgrade to better model (improves search quality forever)
3. **Window of opportunity:** Re-ingestion cost is manageable NOW (150 books), prohibitive later (9,000 books)

**Hardware Context:**
- **Primary machine (Dell):** 80GB RAM, 12GB VRAM (NVIDIA GPU), 4TB NVMe
- **Portable machine (Asus):** Laptop, CPU only, moderate specs
- **Deployment:** Qdrant on NAS (192.168.0.151), accessible from both machines

**Key Insight:** GPU acceleration changes the calculation entirely. What takes 50-63 hours on CPU becomes 3-4 hours on GPU.

## Decision

**Adopt `BAAI/bge-large-en-v1.5` (1024-dimensional embeddings) with GPU acceleration and CPU fallback.**

### Model Specifications

| Attribute | Value |
|-----------|-------|
| **Model** | BAAI/bge-large-en-v1.5 |
| **Dimensions** | 1024 |
| **Size** | 1.3GB |
| **Quality** | State-of-the-art for RAG retrieval (top of MTEB leaderboard) |
| **Speed (GPU)** | ~0.3s per book (batch=64) |
| **Speed (CPU)** | ~12s per book |

### Hardware-Agnostic Design

**Auto-detection logic:**
```python
import torch
from sentence_transformers import SentenceTransformer

# Detect GPU availability
device = "cuda" if torch.cuda.is_available() else "cpu"

# Load model
model = SentenceTransformer('BAAI/bge-large-en-v1.5')
model = model.to(device)

# Adjust batch size based on hardware
batch_size = 64 if device == "cuda" else 8

print(f"Using device: {device}")
if device == "cuda":
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB")
```

### Performance Comparison

#### Full Library Re-Ingestion (9,000 Books)

| Model | CPU Time | **GPU Time** | Storage | Quality |
|-------|----------|--------------|---------|---------|
| all-MiniLM-L6-v2 (current) | 27.5h | **45 min** | 2GB | ⭐⭐⭐ |
| all-mpnet-base-v2 (768-dim) | 35-38h | **1.5h** | 4GB | ⭐⭐⭐⭐ |
| **bge-large-en-v1.5 (chosen)** | 50-63h | **3-4h** | 6GB | ⭐⭐⭐⭐⭐ |

#### Query Performance (Single Query)

| Operation | Dell (GPU) | Asus (CPU) | Notes |
|-----------|------------|------------|-------|
| Embed query | <0.01s | ~0.1s | GPU 10x faster |
| Qdrant search | ~0.05s | ~0.05s | Network-bound, same |
| **Total** | **~0.06s** | **~0.15s** | Both imperceptible to humans |

**Key Insight:** Query performance is excellent even on CPU (150ms). GPU only critical for ingestion.

### Machine Role Separation

**Dell (Primary - GPU Ingestion):**
- Heavy ingestion workloads (3-4h for 9K books)
- Re-indexing and batch operations
- Testing new chunking parameters
- Query also supported (ultra-fast)

**Asus (Portable - CPU Query):**
- Query-only workloads (150ms per query)
- Connects to Qdrant on NAS (192.168.0.151)
- Model runs on CPU (acceptable for query)
- No ingestion (CPU would take 50-63 hours)

**NAS (Centralized Storage):**
- Qdrant server (192.168.0.151:6333)
- Calibre library metadata
- Accessible from Dell, Asus, or via VPN

### Migration Plan

**Phase 1: Test (30 min)**
```bash
# On Dell (GPU machine)
# 1. Install CUDA toolkit (if not present)
nvidia-smi  # Verify GPU detected

# 2. Install GPU-enabled PyTorch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 3. Test bge-large-en-v1.5
python -c "
from sentence_transformers import SentenceTransformer
import torch
model = SentenceTransformer('BAAI/bge-large-en-v1.5')
model = model.to('cuda')
embeddings = model.encode(['Test sentence'] * 100, batch_size=64, device='cuda')
print(f'Shape: {embeddings.shape}')  # Should be (100, 1024)
"
```

**Phase 2: Migrate Existing Books (8 min)**
```bash
# Create new collection with 1024 dimensions
# Re-ingest current 150 books with new model
# Test search quality vs old model
```

**Phase 3: Full Library (3-4 hours on GPU)**
```bash
# Batch ingest all 9,000 books
# Monitor GPU utilization (should be 90%+)
# Can run overnight, but fast enough for afternoon
```

## Consequences

### Positive

- ✅ **Best-in-class quality:** Top MTEB leaderboard, state-of-the-art RAG retrieval
- ✅ **GPU utilization:** 12GB VRAM fully leveraged (not wasted)
- ✅ **Fast ingestion:** 3-4 hours for 9K books (weekend project, not multi-day ordeal)
- ✅ **Future-proof:** Unlikely to need model upgrade again
- ✅ **Portable queries:** Works on Asus laptop (CPU acceptable for query)
- ✅ **Negligible storage:** 6GB for 9K books trivial on 4TB NVMe
- ✅ **Cost:** Free, local, no API dependency

### Negative

- ⚠️ **Larger model:** 1.3GB vs 80MB (but irrelevant on NVMe)
- ⚠️ **Slower CPU ingestion:** 50-63h on Asus (but ingestion should only happen on Dell)
- ⚠️ **One-time migration cost:** Re-ingest 150 books (8 minutes, trivial)
- ⚠️ **Full library re-ingest:** If switching back would take 3-4 hours (but why would we?)

### Neutral

- 🔄 **Query speed:** Already fast on both CPU and GPU (not a differentiator)
- 🔄 **Qdrant compatibility:** Vector size change requires new collection (expected)
- 🔄 **Backward compatibility:** Old 384-dim collection can coexist (no forced migration)

## Implementation

### Component
- **Embedding Generation** - All ingestion pipelines (scripts/ingest_books.py, scripts/mcp_server.py)

### Files

**Modified:**
- `scripts/config.py` - Add `get_device()`, `get_batch_size()`, model name constant
- `scripts/ingest_books.py` - Use `get_device()` for model loading
- `scripts/mcp_server.py` - Update model name in MCP tools
- `requirements.txt` - Ensure GPU PyTorch included

**New:**
- `scripts/migrate_embeddings.py` - Migration script for existing collections

**Configuration:**
```python
# scripts/config.py additions

EMBEDDING_MODEL = "BAAI/bge-large-en-v1.5"  # Was: all-MiniLM-L6-v2
EMBEDDING_DIMENSIONS = 1024  # Was: 384

def get_device():
    """Auto-detect optimal device."""
    env_device = os.getenv("DEVICE")
    if env_device:
        return env_device
    return "cuda" if torch.cuda.is_available() else "cpu"

def get_batch_size(device):
    """Hardware-appropriate batch size."""
    return 64 if device == "cuda" else 8
```

### Testing

**GPU Validation:**
```bash
# Verify GPU detection and model loading
pytest tests/test_embeddings.py::test_gpu_detection
pytest tests/test_embeddings.py::test_model_loading
pytest tests/test_embeddings.py::test_batch_encoding_gpu
```

**Quality Comparison:**
```bash
# Compare search results: old vs new model
# Ensure quality improvement is measurable
python scripts/compare_embeddings.py \
  --old-collection alexandria \
  --new-collection alexandria_bge \
  --queries "tests/fixtures/test_queries.txt"
```

## Alternatives Considered

### Alternative 1: Keep all-MiniLM-L6-v2 (Current)
**Rejected because:**
- Mediocre quality (⭐⭐⭐ vs ⭐⭐⭐⭐⭐)
- Doesn't utilize available GPU (wasted hardware)
- Decision window closing (150 books now vs 9,000 later)
- Small file size benefit irrelevant on NVMe

### Alternative 2: all-mpnet-base-v2 (768-dim)
**Rejected because:**
- Better than current, but not best-in-class
- GPU ingestion: 1.5h vs 3-4h (marginal difference)
- Quality improvement: ⭐⭐⭐⭐ vs ⭐⭐⭐⭐⭐
- With GPU available, why compromise?

### Alternative 3: API-Based Embeddings (OpenAI, Voyage)
**Rejected because:**
- **Cost:** $0.02-$0.10 per 1M tokens (ongoing expense)
- **Vendor lock-in:** Dependent on external API
- **Privacy:** Book content sent to third party
- **Latency:** Network round-trips add delay
- **Local is free:** GPU ingestion cost = $0, query cost = $0

### Alternative 4: Multiple Models (Per-Collection)
**Considered:** Different models for different collections
**Rejected because:**
- Complexity: Managing multiple models/dimensions
- Memory: Loading multiple 1GB+ models
- Marginal benefit: bge-large-en-v1.5 is good for all domains
- Can reconsider if specific use case emerges

## Related Decisions

- **ADR-0001: Use Qdrant Vector DB** - Vector size change (384 → 1024) still supported
- **ADR-0007: Universal Semantic Chunking** - Chunking algorithm unchanged, only embeddings
- **ADR-0008: Multi-Consumer Service Model** - All consumers benefit from better embeddings
- **ADR-0011: Phased Growth Architecture** - GPU model supports all growth phases

## References

- **MTEB Leaderboard:** https://huggingface.co/spaces/mteb/leaderboard
- **bge-large-en-v1.5:** https://huggingface.co/BAAI/bge-large-en-v1.5
- **GPU Benchmarks:** Internal testing (Dell: 12GB VRAM, 80GB RAM)
- **Model Card:** See model documentation for training details and benchmarks

---

## Migration Checklist

When ready to execute:

- [ ] Verify GPU detected (`nvidia-smi`)
- [ ] Install GPU PyTorch (`pip install torch --index-url ...`)
- [ ] Test bge-large-en-v1.5 loading on GPU
- [ ] Create new Qdrant collection (`alexandria_bge`, 1024 dims)
- [ ] Re-ingest 10 test books
- [ ] Compare search quality (old vs new)
- [ ] If quality improved → Re-ingest all 150 books (~8 min)
- [ ] Update default collection to `alexandria_bge`
- [ ] Schedule full library ingestion (9K books, 3-4h)
- [ ] Update documentation and TODO.md

---

**Author:** Winston (Architect Agent) + Sabo
**Reviewers:** Sabo (Project Owner)
**Hardware:** Dell Beast (80GB RAM, 12GB VRAM, 4TB NVMe)
