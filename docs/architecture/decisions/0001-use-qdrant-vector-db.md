# ADR 0001: Use Qdrant Vector DB

## Status
Accepted

## Date
2026-01-20

## Context

Alexandria needs to store and search 384-dimensional embeddings for ~9,000 books (potentially millions of chunks). The system must support:

1. **Fast semantic similarity search** - Sub-second queries across millions of vectors
2. **Metadata filtering** - Filter by domain, author, book, date
3. **Scalability** - Start small (100 books), grow to full library (9,000+ books)
4. **Self-hosted** - No cloud vendor lock-in, data stays local
5. **Python integration** - Easy to use from Python scripts
6. **Production-ready** - Stable, documented, actively maintained

**Alternatives considered:**
- **Pinecone** - Cloud-only, vendor lock-in, costs scale with usage
- **Weaviate** - Heavy (Go-based), more complex setup
- **Milvus** - Requires multiple components (etcd, MinIO), operational overhead
- **FAISS** - Library not database, no built-in persistence or HTTP API
- **PostgreSQL + pgvector** - Good but slower for high-dimensional vectors at scale
- **Chroma** - Lightweight but less mature, fewer production deployments

## Decision

**Use Qdrant as the vector database for Alexandria.**

### Why Qdrant?

**Performance:**
- Written in Rust (fast, memory-safe)
- Sub-50ms query times for millions of vectors
- Optimized for cosine similarity (our use case)
- HNSW index for approximate nearest neighbor search

**Ease of Use:**
- Single Docker container (no complex setup)
- Native Python client (`qdrant-client`)
- REST API for other integrations
- Intuitive payload filtering

**Features:**
- Built-in persistence (no separate database needed)
- Payload indexing for metadata filtering
- Batch uploads for efficient ingestion
- Collection snapshots for backup/restore

**Self-Hosted:**
- Run on local network (192.168.0.151:6333)
- No external dependencies
- Data stays local
- No usage-based costs

**Production Ready:**
- Used in production by many companies
- Active development and community
- Good documentation
- Kubernetes-ready if needed later

## Consequences

### Positive
- **Fast queries:** <100ms for semantic search across full library
- **Simple deployment:** Single Docker container (`docker run qdrant/qdrant`)
- **Python-native:** Clean integration with `qdrant-client`
- **Flexible filtering:** Can filter by domain, author, date, etc.
- **Scalable:** Handles 9,000 books (millions of chunks) easily
- **No vendor lock-in:** Self-hosted, open source
- **Cost-effective:** No per-query or storage costs

### Negative
- **Self-hosting overhead:** Must maintain Qdrant server (upgrades, backups)
- **Single point of failure:** If Qdrant goes down, system is unusable
- **Learning curve:** Team must learn Qdrant-specific concepts (collections, payloads, filters)
- **No built-in auth:** Qdrant has no authentication by default (secure via network isolation)

### Neutral
- **Rust ecosystem:** Benefits from Rust's performance but harder to contribute to Qdrant core
- **Memory usage:** HNSW index requires significant RAM (acceptable trade-off for speed)

## Implementation

### Component
- **External System:** Qdrant Vector DB (192.168.0.151:6333)
- **Integration Point:** Scripts Package → Qdrant (via `qdrant-client`)

### Files
- `scripts/ingest_books.py` - Upload chunks to Qdrant
- `scripts/rag_query.py` - Search Qdrant for semantic matches
- `scripts/qdrant_utils.py` - Collection management operations
- `requirements.txt` - `qdrant-client` dependency

### Configuration
```python
QDRANT_HOST = "192.168.0.151"
QDRANT_PORT = 6333
VECTOR_DIMENSIONS = 384  # sentence-transformers/all-MiniLM-L6-v2
DISTANCE_METRIC = "Cosine"
```

### Deployment
```bash
# Start Qdrant server (Docker)
docker run -p 6333:6333 -v qdrant_storage:/qdrant/storage qdrant/qdrant
```

### Story
[01-INGESTION.md](../../stories/01-INGESTION.md), [03-RAG_QUERY.md](../../stories/03-RAG_QUERY.md)

## Alternatives Considered

### Alternative 1: Pinecone
**Pros:** Managed service, no ops overhead, great performance
**Cons:** Cloud-only, vendor lock-in, costs scale with usage, data leaves premises
**Rejected:** Violates self-hosting requirement, ongoing costs

### Alternative 2: FAISS
**Pros:** Very fast, Facebook-proven, CPU and GPU support
**Cons:** Library not database, no HTTP API, no persistence layer, no metadata filtering
**Rejected:** Would need to build database layer ourselves

### Alternative 3: PostgreSQL + pgvector
**Pros:** Familiar technology, good for hybrid search (text + vector)
**Cons:** Slower for high-dimensional vectors, not optimized for cosine similarity, requires PostgreSQL admin skills
**Rejected:** Performance concerns at scale, additional operational complexity

### Alternative 4: Weaviate
**Pros:** Feature-rich, GraphQL API, good documentation
**Cons:** Heavier deployment, more complex, Go-based (harder to debug)
**Rejected:** Overkill for our use case, operational overhead

### Alternative 5: Chroma
**Pros:** Python-native, very easy to use, lightweight
**Cons:** Newer project, fewer production deployments, less proven at scale
**Rejected:** Too early-stage for production use

## Related Decisions
- [ADR 0002: Domain-Specific Chunking](0002-domain-specific-chunking.md) - Chunks stored in Qdrant
- [ADR 0003: GUI as Thin Layer](0003-gui-as-thin-layer.md) - Scripts interact with Qdrant
- [ADR 0004: Collection-Specific Manifests](0004-collection-specific-manifests.md) - Manifests track Qdrant data

## References
- **Qdrant Docs:** https://qdrant.tech/documentation/
- **C4 System Context:** [01-context.md](../c4/01-context.md)
- **Performance benchmarks:** https://qdrant.tech/benchmarks/
- **Comparison table:** https://qdrant.tech/documentation/overview/comparison/

---

**Author:** Claude Code + User (Sabo)
**Reviewers:** User (Sabo)
