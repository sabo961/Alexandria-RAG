# Alexandria Documentation Index

**Type:** Monolith (Python Backend)
**Primary Language:** Python 3.14
**Architecture:** MCP-first design
**Last Updated:** 2026-01-31

---

## Project Overview

Alexandria is a RAG (Retrieval-Augmented Generation) system providing semantic search across 9,000+ books in the Temenos Academy Library. It uses hierarchical semantic chunking and exposes all functionality via MCP Server for direct Claude Code integration.

---

## Quick Reference

| Property | Value |
|----------|-------|
| **Tech Stack** | Python 3.14, Qdrant, sentence-transformers |
| **Entry Point** | `scripts/mcp_server.py` |
| **Architecture Pattern** | MCP-first, scripts package for business logic |
| **Vector DB** | Qdrant (192.168.0.151:6333) |
| **Embedding Model** | all-MiniLM-L6-v2 (384-dim) |

---

## For AI Agents

| Priority | Document | Purpose |
|----------|----------|---------|
| **1. MANDATORY** | [project-context.md](./project-context.md) | 45 implementation rules |
| **2. Epics & Stories** | [development/epics.md](./development/epics.md) | Implementation roadmap |
| **3. Structure** | [source-tree.md](./source-tree.md) | Codebase organization |

---

## Generated Documentation

### Core Documentation

- [Project Context](./project-context.md) - AI agent implementation rules (MANDATORY)
- [Source Tree Analysis](./source-tree.md) - Annotated directory structure

### Architecture (Reference)

- [Architecture Overview](./architecture/README.md) - Comprehensive system architecture
- [MCP Server Reference](./architecture/mcp-server.md) - Complete tool documentation
- [C4 Context Diagram](./architecture/c4/01-context.md) - System context
- [C4 Container Diagram](./architecture/c4/02-container.md) - Container view
- [C4 Component Diagram](./architecture/c4/03-component.md) - Component details

### Architecture Decisions

- [ADR Index](./architecture/decisions/README.md) - All architecture decisions
  - [ADR-0001: Qdrant Vector DB](./architecture/decisions/0001-use-qdrant-vector-db.md)
  - [ADR-0003: GUI as Thin Layer](./architecture/decisions/0003-gui-as-thin-layer.md) _(Superseded)_
  - [ADR-0007: Universal Semantic Chunking](./architecture/decisions/0007-universal-semantic-chunking.md) _(Current)_

### Technical Specifications

- [Data Models](./architecture/technical/data-models.md) - Complete schema
- [Qdrant Payload Structure](./architecture/technical/QDRANT_PAYLOAD_STRUCTURE.md) - Vector DB format
- [Universal Semantic Chunking](./architecture/technical/UNIVERSAL_SEMANTIC_CHUNKING.md) - Algorithm details

---

## User Documentation

Organized following the [Diataxis](https://diataxis.fr) framework.

### Tutorials (Learning-oriented)

- [Getting Started](./user-docs/tutorials/getting-started.md) - Setup in 15 minutes
- [PowerShell Setup](./user-docs/tutorials/powershell-setup.md) - Windows configuration

### How-To Guides (Task-oriented)

- [Common Workflows](./user-docs/how-to/common-workflows.md) - Command cheat sheet
- [Track Ingestion](./user-docs/how-to/track-ingestion.md) - Monitor with logging
- [Troubleshoot Ingestion](./user-docs/how-to/troubleshoot-ingestion.md) - Solve problems
- [Configure Open WebUI](./user-docs/how-to/configure-open-webui.md) - Integration guide
- [Git Workflow](./user-docs/how-to/git-workflow.md) - Branching strategy
- [Structurizr Guide](./user-docs/how-to/structurizr-guide.md) - C4 diagram tooling

### Explanation (Understanding-oriented)

- [Architecture Principles](./user-docs/explanation/architecture-principles.md) - Design philosophy

---

## Development

Internal workflow managed via BMAD methodology.

### Task Lifecycle

```
ideas/        →  epics.md  →  epic-*.md  →  CHANGELOG.md
(brainstorm)     (planning)   (stories)     (done)
```

### Development Folders

| Folder | Purpose |
|--------|---------|
| [ideas/](./development/ideas/) | Brainstorming briefs (future concepts) |
| [research/](./development/research/) | Background analysis and competitive research |
| [security/](./development/security/) | Security audits and guidelines |

---

## Project Management

- [epics.md](./development/epics.md) - Implementation roadmap (8 epics, 23 stories)
- [epic-*.md](./development/) - Detailed stories per epic
- [CHANGELOG.md](../CHANGELOG.md) - Completed work archive
- [AGENTS.md](../AGENTS.md) - AI agent entry point

---

## Getting Started

### Prerequisites

- Python 3.14+
- Access to Qdrant server (192.168.0.151:6333)
- Calibre library path configured

### Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure MCP in Claude Code
# (see .mcp.json)

# Query the library
# Use Claude Code with alexandria_query()
```

### For AI-Assisted Development

**When planning features:**
- UI/UX → Reference: [architecture-principles.md](./user-docs/explanation/architecture-principles.md)
- Backend → Reference: [architecture/README.md](./architecture/README.md), [mcp-server.md](./architecture/mcp-server.md)
- Full-stack → Reference: All architecture docs

---

## External Resources

- **MCP Protocol:** https://modelcontextprotocol.io
- **Qdrant:** https://qdrant.tech/documentation
- **sentence-transformers:** https://www.sbert.net
- **Diataxis:** https://diataxis.fr

---

_Generated using BMAD Method `document-project` workflow_
