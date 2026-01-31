# Alexandria Architecture Principles

**Purpose:** Explain the "why" behind Alexandria's design decisions.

---

## Core Philosophy

> **MCP-First Architecture:** All business logic lives in `scripts/`. MCP server is the primary interface.

Alexandria prioritizes:
1. **Simplicity** - No framework overhead (no LangChain)
2. **Testability** - Business logic separate from interface
3. **AI Integration** - Direct Claude Code access via MCP
4. **Single Source of Truth** - One pipeline, one manifest system

---

## Principle 1: MCP-First Design

**Decision:** GUI development abandoned. MCP server is the primary interface.

**Why?**
- Single source of truth (no duplication between GUI and API)
- Multiple interfaces possible (MCP, CLI) from same codebase
- Easy testing (no UI overhead)
- Direct integration with Claude Code

**Implementation:**
- MCP Server (`scripts/mcp_server.py`) exposes tools
- All business logic lives in `scripts/` package
- MCP tools call scripts, return results

**Anti-pattern:** Duplicating logic in interface layer

**Benefits:**
- Testability (scripts can be unit tested)
- Reusability (scripts usable from CLI and MCP)
- Maintainability (single source of truth for logic)
- AI Integration (direct Claude Code access)

**See:** [ADR 0003: GUI as Thin Layer](../architecture/decisions/0003-gui-as-thin-layer.md)

---

## Principle 2: Collection Isolation

**Decision:** Each collection has separate manifests and can use different settings.

**Why?**
- Prevents cross-contamination between collections
- Allows experimentation (test different chunking strategies)
- Supports multiple use cases (personal library, research corpus)

**Implementation:**
- `logs/{collection}_manifest.json` - Master manifest
- `logs/{collection}_manifest.csv` - Human-readable export
- Separate Qdrant collections per domain/experiment

**Benefits:**
- Data integrity (no cross-contamination)
- Experimentation (A/B test chunking strategies)
- Flexibility (different settings per collection)

**See:** [ADR 0004: Collection-Specific Manifests](../architecture/decisions/0004-collection-specific-manifests.md)

---

## Principle 3: Progressive Enhancement

**Decision:** Core functionality works with minimal dependencies. Advanced features are optional.

**Why?**
- Easier onboarding (start simple, add features as needed)
- Resilience (system degrades gracefully)
- Flexibility (choose features based on use case)

**Examples:**
- Ingestion works without Calibre DB (use folder ingestion)
- Query works without OpenRouter (search-only mode)
- MCP is primary, CLI is secondary

---

## Principle 4: Universal Semantic Chunking

**Decision:** Split text at semantic boundaries, not fixed token windows.

**Why?**
- Fixed windows destroy context (split mid-paragraph, mid-argument)
- Semantic boundaries preserve meaning
- Works across all domains and languages

**Algorithm:**
1. Split text into sentences
2. Embed each sentence
3. Calculate cosine similarity between consecutive sentences
4. Low similarity = topic shift = chunk boundary
5. Enforce min/max size constraints

**Trade-off:** 6x slower than fixed-window, but significantly better retrieval quality.

**See:** [ADR 0007: Universal Semantic Chunking](../architecture/decisions/0007-universal-semantic-chunking.md)

---

## Principle 5: Hierarchical Context

**Decision:** Two-level chunking (parent=chapter, child=semantic chunk).

**Why?**
- Flat chunks lose chapter context
- Users need to understand where content fits
- Different queries need different context levels

**Implementation:**
- **Parent chunks**: One per chapter, contains full chapter text
- **Child chunks**: Semantic chunks within chapter, linked via `parent_id`

**Context Modes:**
| Mode | Returns | Use Case |
|------|---------|----------|
| `precise` | Child chunks only | Fast, exact citations |
| `contextual` | Children + parent | Understanding context |
| `comprehensive` | Children + parent + siblings | Deep analysis |

---

## Anti-Goals (Consciously NOT Doing)

These are deliberate exclusions, not missing features:

| Anti-Goal | Rationale |
|-----------|-----------|
| Complex GUI | MCP + Claude Code is primary interface |
| Domain tagging | Content determines topic, not pre-assigned labels |
| Multiple pipelines | Single universal pipeline reduces complexity |
| LangChain/frameworks | Keep simple, avoid abstraction overhead |
| Shared Qdrant ownership | Single source of truth |

---

## Key Trade-offs

| Decision | Benefit | Cost |
|----------|---------|------|
| Semantic chunking | Better retrieval quality | 6x slower ingestion |
| Hierarchical chunks | Rich context | More storage, complex queries |
| MCP-first | AI integration | No standalone GUI |
| Single embedding model | Consistency | Can't upgrade without re-ingestion |

---

## Immutable Constraints

These cannot be changed without significant rework:

1. **Embedding Model** - `all-MiniLM-L6-v2` (384-dim). Changing requires full re-ingestion.
2. **Distance Metric** - COSINE. Hardcoded across all scripts.
3. **Qdrant Server** - External at 192.168.0.151:6333.

---

**See Also:**
- [ADR Index](../architecture/decisions/README.md) - All architecture decisions
- [Project Context](../project-context.md) - Implementation rules
- [Architecture Reference](../architecture/README.md) - Technical specifications

---

**Last Updated:** 2026-01-31
