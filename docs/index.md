# Alexandria Documentation

**Welcome to Alexandria** - a Python-based RAG (Retrieval-Augmented Generation) system providing semantic search across 9,000+ books in the Temenos Academy Library.

**Quick Facts:**
- **Tech Stack:** Python 3.14, MCP Server, Qdrant vector database, sentence-transformers
- **Vector DB:** Qdrant (external: 192.168.0.151:6333)
- **Embedding Model:** all-MiniLM-L6-v2 (384-dimensional)
- **Architecture:** MCP-first design, scripts package for business logic
- **Chunking:** Hierarchical (parent chapters + child semantic chunks)

---

## Quick Start

**New to Alexandria?**

1. **[Getting Started](./tutorials/getting-started.md)** - Set up Alexandria in 15 minutes
2. **[Project Context](./project-context.md)** - What is Alexandria, rules, and patterns
3. **[Common Workflows](./how-to/common-workflows.md)** - Command cheat sheet for daily use

**For AI Agents:**
- **[Project Context](./project-context.md)** - **MANDATORY READ** - 45 implementation rules
- **[AGENTS.md](../AGENTS.md)** - Navigation hub for AI assistants

---

## Tutorials (Learning-oriented)

Step-by-step lessons to learn Alexandria from scratch.

- **[Getting Started](./tutorials/getting-started.md)** - Complete setup and first ingestion
- **[Professional Setup](./tutorials/professional-setup.md)** - Production deployment with Docker
- **[PowerShell Setup](./tutorials/powershell-setup.md)** - Windows environment configuration

---

## How-To Guides (Task-oriented)

Practical recipes for accomplishing specific tasks.

- **[Common Workflows](./how-to/common-workflows.md)** - Frequent operations and commands
- **[Track Ingestion](./how-to/track-ingestion.md)** - Monitor and debug ingestion with logging
- **[Troubleshoot Ingestion](./how-to/troubleshoot-ingestion.md)** - Solve common problems
- **[Configure Open WebUI](./how-to/configure-open-webui.md)** - Connect Alexandria to Open WebUI
- **[Git Workflow](./how-to/git-workflow.md)** - Branching strategy & Auto-Claude integration
- **[Structurizr Guide](./how-to/structurizr-guide.md)** - Visualize C4 diagrams

---

## Reference (Information-oriented)

Technical descriptions and specifications.

### Architecture
- **[Architecture Overview](./architecture/README.md)** - Comprehensive system architecture
- **[C4 Context Diagram](./architecture/c4/01-context.md)** - System context
- **[C4 Container Diagram](./architecture/c4/02-container.md)** - Container view
- **[C4 Component Diagram](./architecture/c4/03-component.md)** - Component details
- **[MCP Server Reference](./architecture/mcp-server.md)** - Complete tool documentation

### Technical Specs
- **[Data Models](./architecture/technical/data-models.md)** - Complete schema for Alexandria's data structures
- **[Qdrant Payload Structure](./architecture/technical/QDRANT_PAYLOAD_STRUCTURE.md)** - Vector DB payload format
- **[Universal Semantic Chunking](./architecture/technical/UNIVERSAL_SEMANTIC_CHUNKING.md)** - Chunking algorithm details
- **[PDF vs EPUB Comparison](./architecture/technical/PDF_vs_EPUB_COMPARISON.md)** - Format analysis

### Code Structure
- **[Source Tree](./source-tree.md)** - Codebase structure and module organization

### Security
- **[Security Overview](./security/SECURITY.md)** - Security guidelines and policies
- **[Unsafe HTML Audit](./security/unsafe_html_audit.md)** - HTML sanitization audit

---

## Explanation (Understanding-oriented)

Conceptual discussions and design rationale - the "why" behind decisions.

- **[Architecture Principles](./explanation/architecture-principles.md)** - Core design philosophy and trade-offs
- **[Project Context](./project-context.md)** - Implementation rules and patterns (MANDATORY for AI agents)
- **[ADR Index](./architecture/decisions/README.md)** - Architecture Decision Records
  - [ADR-0001: Qdrant Vector DB](./architecture/decisions/0001-use-qdrant-vector-db.md)
  - [ADR-0003: GUI as Thin Layer](./architecture/decisions/0003-gui-as-thin-layer.md) (Superseded)
  - [ADR-0007: Universal Semantic Chunking](./architecture/decisions/0007-universal-semantic-chunking.md) (current)

---

## Development (Internal)

Not Diataxis - internal development workflow managed via BMAD methodology.

### Task Lifecycle

```
ideas/                      "Consider"    Visions, briefs (not committed)
    │
    ▼
TODO.md                     "Accepted"    Prioritized backlog (HIGH/MED/LOW)
    │
    ▼
backlog/                    "Specifying"  Detailed specs for active items
    │
    ▼
planning-artifacts/         "Planning"    Sprint planning, workflow status
    │
    ▼
implementation-artifacts/   "Executing"   BMAD stories, acceptance criteria
    │
    ▼
CHANGELOG.md                "Done"        Historical archive
```

### Folders

| Folder | Stage | Purpose |
|--------|-------|---------|
| **[ideas/](./ideas/)** | Consider | Future visions (not yet in TODO) |
| **[backlog/](./backlog/)** | In Progress | Detailed docs for active TODO items |
| **[planning-artifacts/](./planning-artifacts/)** | BMAD | Sprint planning, workflow status |
| **[implementation-artifacts/](./implementation-artifacts/)** | BMAD | Stories, acceptance criteria |
| **[research/](./research/)** | Reference | Background analysis and research |
| **[analysis/](./analysis/)** | Archive | Session outputs (brainstorming, etc.) |

---

## Project Management

- **[TODO.md](../TODO.md)** - Prioritized backlog (HIGH/MEDIUM/LOW)
- **[CHANGELOG.md](../CHANGELOG.md)** - Completed work archive
- **[AGENTS.md](../AGENTS.md)** - AI agent navigation hub

---

## External Resources

- **MCP Protocol:** https://modelcontextprotocol.io
- **Qdrant:** https://qdrant.tech/documentation
- **sentence-transformers:** https://www.sbert.net
- **Diataxis:** https://diataxis.fr

---

**Last Updated:** 2026-01-31
**Version:** 2.3 (Diataxis + BMAD workflow integration)
