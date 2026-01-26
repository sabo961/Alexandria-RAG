# Alexandria Feature Stories

**Purpose:** Feature-focused documentation organized by user-facing capabilities. Each story maps to specific C4 architecture components.

---

## Quick Navigation

| Story | Component | Status |
|-------|-----------|--------|
| [01-INGESTION.md](01-INGESTION.md) | Ingestion Engine | ✅ Implemented |
| [02-CHUNKING.md](02-CHUNKING.md) | Chunking Strategies | ✅ Implemented |
| [03-RAG_QUERY.md](03-RAG_QUERY.md) | RAG Query Engine | ✅ Implemented |
| [04-GUI.md](04-GUI.md) | Streamlit GUI Container | ✅ Implemented |
| [05-CALIBRE_INTEGRATION.md](05-CALIBRE_INTEGRATION.md) | Calibre Integration | ✅ Implemented |
| [06-COLLECTION_MANAGEMENT.md](06-COLLECTION_MANAGEMENT.md) | Collection Management | ✅ Implemented |
| [07-DEBUGGING_TESTING.md](07-DEBUGGING_TESTING.md) | Cross-cutting | ⏳ Ongoing |

---

## Story Structure

Each story follows this template:

```markdown
# Story: [Feature Name]

## Overview
Brief description (2-3 sentences)

## User Story
"As a [role], I want [feature] so that [benefit]"

## C4 Architecture Mapping
- **Container:** Which C4 container
- **Component:** Which C4 component(s)
- **Diagram:** Link to C4 diagram

## Implementation
- Key files involved
- Architecture decisions (link to ADRs)
- Integration points

## Current Status
✅ Completed features
⏳ In progress
📋 Planned

## Usage Examples
Common commands/workflows

## Configuration
Parameters, settings, defaults

## Known Issues
Link to TODO.md for dynamic issues

## Future Work
Enhancement ideas, optimizations

## Related
- Related stories
- Related ADRs
- Related docs
```

---

## C4 Architecture Mapping

Stories align with the C4 model architecture:

### System Context Level
All stories contribute to the overall **Alexandria RAG System** (semantic search across 9,000 books).

### Container Level

**Streamlit GUI Container:**
- [04-GUI.md](04-GUI.md) - Web interface for all user interactions

**Scripts Package Container:**
All other stories map to components within Scripts Package:
- [01-INGESTION.md](01-INGESTION.md) → Ingestion Engine
- [02-CHUNKING.md](02-CHUNKING.md) → Chunking Strategies
- [03-RAG_QUERY.md](03-RAG_QUERY.md) → RAG Query Engine
- [05-CALIBRE_INTEGRATION.md](05-CALIBRE_INTEGRATION.md) → Calibre Integration
- [06-COLLECTION_MANAGEMENT.md](06-COLLECTION_MANAGEMENT.md) → Collection Management

**Cross-Cutting:**
- [07-DEBUGGING_TESTING.md](07-DEBUGGING_TESTING.md) - Development workflow (spans all components)

### Component Level

See [C4 Component Diagram](../../reference/architecture/c4/03-component.md) for detailed internal structure.

---

## Story Dependencies

```
┌─────────────────────┐
│  Calibre Integration│
│  (05)               │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐     ┌─────────────────────┐
│  Ingestion Engine   │────►│ Chunking Strategies │
│  (01)               │     │ (02)                │
└──────────┬──────────┘     └─────────────────────┘
           │
           ▼
┌─────────────────────┐
│ Collection Mgmt     │
│ (06)                │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  RAG Query Engine   │
│  (03)               │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Streamlit GUI      │
│  (04)               │
└─────────────────────┘
```

**Explanation:**
- Calibre Integration provides book paths to Ingestion
- Ingestion uses Chunking Strategies and logs to Collection Management
- RAG Query checks Collection Management and queries Qdrant
- GUI orchestrates all components

---

## How to Use Stories

### For New Developers/AI Agents
1. Start with [04-GUI.md](04-GUI.md) to understand user interactions
2. Read stories relevant to your task
3. Reference [C4 diagrams](../../reference/architecture/c4/) for architecture context
4. Check [ADRs](../../reference/architecture/decisions/) for design rationale

### For Feature Development
1. Identify which story(ies) your feature touches
2. Read the story to understand current implementation
3. Check "Future Work" section for planned enhancements
4. Update story when adding new features

### For Bug Fixes
1. Identify which component has the bug (use C4 diagrams)
2. Read the relevant story for context
3. Check "Known Issues" section
4. Update TODO.md with bug details

### For Architecture Changes
1. Identify affected stories
2. Read related ADRs
3. Create new ADR if decision is significant
4. Update affected stories with new information

---

## Story Status Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Fully implemented and production-ready |
| ⏳ | Partially implemented or in active development |
| 📋 | Planned but not yet started |
| 🚧 | Blocked or on hold |
| ❌ | Deprecated or removed |

---

## Creating a New Story

1. **Copy template structure** (see "Story Structure" above)
2. **Use next sequential number** (08, 09, etc.)
3. **Map to C4 components** (which container/component?)
4. **Link to relevant ADRs**
5. **Update this index** with new story
6. **Cross-reference** from AGENTS.md, README.md, etc.

---

## Related Documentation

- **[C4 Architecture](../../reference/architecture/c4/)** - Visual architecture diagrams
- **[ADRs](../../reference/architecture/decisions/)** - Architecture decision records
- **[AGENTS.md](../../AGENTS.md)** - AI agent configuration
- **[README.md](../../README.md)** - Project overview
- **[TODO.md](../../TODO.md)** - Current tasks and issues

---

**Last Updated:** 2026-01-23
