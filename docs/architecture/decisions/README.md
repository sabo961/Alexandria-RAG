# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records (ADRs) documenting significant architectural decisions in the Alexandria RAG System.

---

## What is an ADR?

An **Architecture Decision Record (ADR)** captures a significant architectural decision along with its context and consequences. ADRs help us:

- Understand **why** decisions were made (not just what was decided)
- Onboard new developers/AI agents quickly
- Avoid revisiting settled debates
- Document trade-offs explicitly
- Provide context for future changes

---

## ADR Index

| ADR | Title | Status | Date | Component |
|-----|-------|--------|------|-----------|
| [0001](0001-use-qdrant-vector-db.md) | Use Qdrant Vector DB | ✅ Accepted | 2026-01-20 | External System |
| [0002](0002-domain-specific-chunking.md) | Domain-Specific Chunking | 🔄 Superseded | 2026-01-20 | Chunking Strategies |
| [0003](0003-gui-as-thin-layer.md) | GUI as Thin Presentation Layer | ✅ Accepted | 2026-01-21 | GUI + Scripts |
| [0004](0004-collection-specific-manifests.md) | Collection-Specific Manifests | ✅ Accepted | 2026-01-21 | Collection Management |
| [0005](0005-philosophical-argument-chunking.md) | Philosophical Argument Chunking | 🔄 Superseded | 2026-01-22 | Chunking Strategies |
| [0006](0006-separate-systems-architecture.md) | Local Qdrant with Separate Collections | ✅ Accepted | 2026-01-23 | External System |
| [0007](0007-universal-semantic-chunking.md) | Universal Semantic Chunking | ✅ Accepted | 2026-01-25 | Chunking Strategies |
| [0008](0008-multi-consumer-service-model.md) | Alexandria as Multi-Consumer Knowledge Service | ✅ Accepted | 2026-01-31 | Service Architecture |
| [0009](0009-http-api-wrapper.md) | HTTP API Wrapper for Non-MCP Consumers | 🚧 Proposed | 2026-01-31 | HTTP API |
| [0010](0010-gpu-accelerated-embeddings.md) | GPU-Accelerated Embedding Model Selection | ✅ Accepted | 2026-01-31 | ML/Embeddings |
| [0011](0011-phased-growth-architecture.md) | Phased Growth Architecture (Personal → SaaS) | ✅ Accepted | 2026-01-31 | Strategic Planning |
| [0012](0012-original-language-primary.md) | Original Language Primary | ✅ Accepted | 2026-02-09 | Epistemology |
| [0013](0013-skos-ontology-backbone.md) | SKOS Ontology Backbone | ✅ Accepted | 2026-02-09 | Knowledge Organization |

**Legend:**
- ✅ Accepted - Implemented and in use
- 🚧 Proposed - Under discussion
- ❌ Rejected - Declined with rationale
- 🔄 Superseded - Replaced by newer ADR
- 📦 Deprecated - No longer relevant

---

## Creating a New ADR

1. **Copy the template:**
   ```bash
   cp template.md XXXX-your-decision-title.md
   ```

2. **Use the next sequential number** (e.g., 0006, 0007)

3. **Fill in all sections:**
   - Status (start with "Proposed")
   - Date (current date)
   - Context (problem/issue)
   - Decision (what we're doing)
   - Consequences (positive, negative, neutral)
   - Implementation (components, files, stories)
   - Alternatives (what we rejected and why)
   - Related decisions (cross-references)

4. **Update this index** with the new ADR

5. **Link from relevant stories/docs**

---

## ADR Lifecycle

### Proposed
Decision is under discussion, not yet implemented.

### Accepted
Decision is approved and implemented.

### Rejected
Decision was proposed but rejected (document why for future reference).

### Superseded
Decision was replaced by a newer ADR (link to replacement).

### Deprecated
Decision is no longer relevant but kept for historical context.

---

## ADR Conventions

### Numbering
- Use 4-digit numbers: 0001, 0002, ..., 0099, 0100
- Never reuse numbers (even for rejected ADRs)

### Naming
- Use kebab-case: `0001-use-qdrant-vector-db.md`
- Keep titles concise and descriptive
- Start with action verb when possible

### Content
- **Context first:** Explain the problem before the solution
- **Be specific:** Include concrete examples, numbers, code snippets
- **Document alternatives:** Show what was considered and rejected
- **Link extensively:** Reference C4 diagrams, stories, code, external resources

### Cross-Referencing
- Link to related ADRs
- Link from stories to ADRs
- Link from code comments to ADRs (for critical decisions)

---

## Related Resources

- **[ADR Template](template.md)** - Use this to create new ADRs
- **[C4 Architecture](../c4/)** - Visual architecture documentation
- **[Stories](../../../explanation/stories/)** - Feature-focused documentation

---

**Last Updated:** 2026-01-31
