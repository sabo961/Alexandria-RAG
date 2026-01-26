# 📕 Reference

**Information-oriented documentation** - Technical descriptions, API specifications, and architectural blueprints for Alexandria.

Reference documentation provides dry, factual information that describes Alexandria's machinery. This is where you look up specific technical details when you need them.

## Documents in This Section

### API Documentation

- **[Data Models](./api/data-models.md)** - Complete schema for Alexandria's data structures including books, chunks, embeddings, and Qdrant collections
- **[Source Tree Analysis](./api/source-tree.md)** - Detailed breakdown of Alexandria's codebase structure, modules, and dependencies

### Architecture

#### C4 Diagrams
- **[C4 Architecture Models](./architecture/c4/)** - System Context, Container, Component, and detailed flow diagrams visualizing Alexandria's architecture

#### Architecture Decision Records (ADRs)
- **[ADR Index](./architecture/decisions/README.md)** - Complete list of architectural decisions with rationale
- Individual ADRs covering:
  - ADR-0001: Python for RAG implementation
  - ADR-0002: Context chunking strategy (superseded by ADR-0007)
  - ADR-0003: Qdrant vector database selection
  - ADR-0004: Scripts-first design pattern
  - ADR-0005: Semantic vs fixed chunking (superseded by ADR-0007)
  - ADR-0006: AI-assisted development policy
  - ADR-0007: Universal semantic chunking (current)

#### Technical Specifications
- **[Qdrant Payload Structure](./architecture/technical/QDRANT_PAYLOAD_STRUCTURE.md)** - Complete schema for vector database payloads
- **[Universal Semantic Chunking](./architecture/technical/UNIVERSAL_SEMANTIC_CHUNKING.md)** - Technical specification for adaptive chunking algorithm
- **[PDF vs EPUB Comparison](./architecture/technical/PDF_vs_EPUB_COMPARISON.md)** - Analysis of document format handling and trade-offs
- **[Additional Technical Docs](./architecture/technical/)** - Implementation details and specifications

## What Makes Reference Documentation?

Reference docs should:
- **Provide accurate technical information** that can be looked up quickly
- **Be consistent and complete** in coverage
- **Describe the machinery** without teaching or explaining
- **Follow a predictable structure** for easy navigation
- **Stay factual** without opinions or recommendations

## Navigation

- [← Back to Main Documentation](../index.md)
- [📘 Tutorials](../tutorials/index.md) | [📗 How-To Guides](../how-to-guides/index.md) | [📙 Explanation](../explanation/index.md)

---

**Next Steps**: To understand the rationale behind these technical decisions, visit [Explanation](../explanation/index.md). For practical usage, see [How-To Guides](../how-to-guides/index.md).
