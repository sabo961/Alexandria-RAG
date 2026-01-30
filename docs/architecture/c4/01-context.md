# C4 Level 1: System Context

**Purpose:** Shows Alexandria RAG System in its broader ecosystem - who uses it and what external systems it depends on.

---

## Diagram

View interactively: http://localhost:8081 → "SystemContext" view

Or see `workspace.dsl` lines defining the context.

---

## System Overview

**Alexandria RAG System** is a Retrieval-Augmented Generation (RAG) system that enables semantic search and knowledge synthesis across a multi-disciplinary library of ~9,000 books.

### Users

**Developer/Researcher**
- Uses Alexandria to search and analyze books
- Seeks cross-domain insights (e.g., "manufacturing patterns in 18th-century textile mills")
- Ingests new books into the system
- Queries for answers grounded in book content

### External Systems

**Qdrant Vector DB (192.168.0.151:6333)**
- **Purpose:** Stores 384-dimensional embeddings of book chunks
- **What it provides:** Fast semantic similarity search
- **Data stored:** ~153 chunks per book, metadata (domain, author, title, chunk_index)
- **Why external:** Specialized vector search engine, scales to millions of vectors

**OpenRouter API**
- **Purpose:** LLM inference for natural language answer generation
- **What it provides:** Multiple models (GPT-4, Claude, etc.) via unified API
- **Integration:** Receives retrieved chunks + user query → Returns coherent answer
- **Why external:** Provides access to state-of-the-art LLMs without local hosting

---

## Information Flow

### Ingestion Flow
```
User → Alexandria → File System (reads books) → Alexandria (chunks + embeds) → Qdrant (stores)
```

### Query Flow
```
User → Alexandria → Qdrant (semantic search) → Alexandria → OpenRouter (answer generation) → User
```

---

## Scope & Boundaries

### In Scope
- Book ingestion (EPUB, PDF, TXT, MD)
- Domain-specific chunking
- Semantic search via Qdrant
- LLM-powered answer generation
- Manifest tracking

### Out of Scope
- Book format conversion (use Calibre)
- LLM model hosting (use OpenRouter API)
- Vector DB hosting (use Qdrant server)
- Image/diagram processing (text-only)

---

## Design Drivers

### Why RAG?
- **Grounding:** LLM answers are backed by actual book content (prevents hallucination)
- **Citations:** Every answer includes source book + chunk references
- **Freshness:** New books instantly available (no model retraining)
- **Explainability:** Can trace answer back to specific passages

### Why 9,000 books?
- **Multi-disciplinary synthesis:** Technical + Psychology + Philosophy + History
- **Cross-domain insights:** "How do psychological principles apply to UX design?"
- **Gap awareness:** System knows what it doesn't know (missing books tracked)

### Why Qdrant?
- **Performance:** Sub-second search across millions of vectors
- **Flexibility:** Metadata filtering (domain, author, date)
- **Scalability:** Can grow to full library (9,383 books)

---

## Integration Points

| System | Protocol | Purpose |
|--------|----------|---------|
| Qdrant | HTTP/gRPC (Python client) | Store/retrieve embeddings |
| OpenRouter | REST API | Generate answers from context |
| Calibre | Direct SQLite read | Extract book metadata |
| File System | Local disk I/O | Read books, write logs |

---

## Related Views

- **Next Level:** [Container Diagram](02-container.md) - Internal structure of Alexandria
- **Related:** [ADR 0001: Use Qdrant Vector DB](../decisions/0001-use-qdrant-vector-db.md)

---

**Last Updated:** 2026-01-23
