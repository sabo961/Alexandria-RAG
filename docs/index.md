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

1. **[Getting Started](./user-docs/tutorials/getting-started.md)** - Set up Alexandria in 15 minutes
2. **[Project Context](./project-context.md)** - What is Alexandria, rules, and patterns
3. **[Common Workflows](./user-docs/how-to/common-workflows.md)** - Command cheat sheet for daily use

**For AI Agents:**
- **[Project Context](./project-context.md)** - **MANDATORY READ** - 45 implementation rules
- **[AGENTS.md](../AGENTS.md)** - Navigation hub for AI assistants

---

## User Documentation

Organized following the [Diataxis](https://diataxis.fr) framework.

### Tutorials (Learning-oriented)

Step-by-step lessons to learn Alexandria from scratch.

- **[Getting Started](./user-docs/tutorials/getting-started.md)** - Complete setup and first ingestion
- **[Professional Setup](./user-docs/tutorials/professional-setup.md)** - Production deployment with Docker
- **[PowerShell Setup](./user-docs/tutorials/powershell-setup.md)** - Windows environment configuration

### How-To Guides (Task-oriented)

Practical recipes for accomplishing specific tasks.

- **[Common Workflows](./user-docs/how-to/common-workflows.md)** - Frequent operations and commands
- **[Track Ingestion](./user-docs/how-to/track-ingestion.md)** - Monitor and debug ingestion with logging
- **[Troubleshoot Ingestion](./user-docs/how-to/troubleshoot-ingestion.md)** - Solve common problems
- **[Configure Open WebUI](./user-docs/how-to/configure-open-webui.md)** - Connect Alexandria to Open WebUI
- **[Git Workflow](./user-docs/how-to/git-workflow.md)** - Branching strategy & Auto-Claude integration
- **[Structurizr Guide](./user-docs/how-to/structurizr-guide.md)** - Visualize C4 diagrams

### Explanation (Understanding-oriented)

Conceptual discussions and design rationale - the "why" behind decisions.

- **[Architecture Principles](./user-docs/explanation/architecture-principles.md)** - Core design philosophy and trade-offs
- **[Project Context](./project-context.md)** - Implementation rules and patterns (MANDATORY for AI agents)

---

## Architecture

System architecture documentation - C4 diagrams, ADRs, and technical specifications.

### C4 Diagrams
- **[Architecture Overview](./architecture/README.md)** - Comprehensive system architecture
- **[C4 Context Diagram](./architecture/c4/01-context.md)** - System context
- **[C4 Container Diagram](./architecture/c4/02-container.md)** - Container view
- **[C4 Component Diagram](./architecture/c4/03-component.md)** - Component details

### Architecture Decisions
- **[ADR Index](./architecture/decisions/README.md)** - Architecture Decision Records
  - [ADR-0001: Qdrant Vector DB](./architecture/decisions/0001-use-qdrant-vector-db.md)
  - [ADR-0003: GUI as Thin Layer](./architecture/decisions/0003-gui-as-thin-layer.md) (Superseded)
  - [ADR-0007: Universal Semantic Chunking](./architecture/decisions/0007-universal-semantic-chunking.md) (current)

### Technical Specs
- **[MCP Server Reference](./architecture/mcp-server.md)** - Complete tool documentation
- **[Data Models](./architecture/technical/data-models.md)** - Complete schema for Alexandria's data structures
- **[Qdrant Payload Structure](./architecture/technical/QDRANT_PAYLOAD_STRUCTURE.md)** - Vector DB payload format
- **[Universal Semantic Chunking](./architecture/technical/UNIVERSAL_SEMANTIC_CHUNKING.md)** - Chunking algorithm details
- **[PDF vs EPUB Comparison](./architecture/technical/PDF_vs_EPUB_COMPARISON.md)** - Format analysis

### Code Structure
- **[Source Tree](./source-tree.md)** - Codebase structure and module organization

---

## Development

Internal development workflow managed via BMAD methodology.

### Task Lifecycle

```
ideas/        →  TODO.md  →  backlog/  →  CHANGELOG.md
(consider)       (accepted)  (in progress) (done)
```

### Folders

| Folder | Purpose |
|--------|---------|
| **[ideas/](./development/ideas/)** | Future visions (not yet in TODO) |
| **[backlog/](./development/backlog/)** | Detailed docs for active TODO items |
| **[research/](./development/research/)** | Background analysis and research |
| **[analysis/](./development/analysis/)** | Session outputs (brainstorming, etc.) |
| **[security/](./development/security/)** | Security audits and guidelines |

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
**Version:** 2.4 (Nested structure: user-docs + architecture + development)
