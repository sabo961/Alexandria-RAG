# Alexandria Documentation Index

**Type:** Monolith (Python Backend)
**Primary Language:** Python 3.14
**Architecture:** MCP-first design
**Last Updated:** 2026-02-09

---

## Project Overview

Alexandria is a multilingual knowledge platform over 9,000+ books in the Temenos Academy Library. RAG engine with semantic chunking, MCP-first architecture, guardian persona system (11 guardians), and multilingual embeddings (bge-m3, 1024-dim).

**Core commitment:** Original language is always primary. English is an approximation. BGE-M3 was chosen precisely because it preserves semantic distinctions across languages.

---

## Quick Reference

| Property | Value |
|----------|-------|
| **Tech Stack** | Python 3.14, Qdrant, sentence-transformers |
| **Primary Interface** | `scripts/mcp_server.py` (MCP Server) |
| **GUI (Optional)** | `alexandria_app.py` (Streamlit) |
| **Architecture Pattern** | MCP-first, scripts package for business logic |
| **Vector DB** | Qdrant (192.168.0.151:6333) |
| **Embedding Model** | bge-m3 (1024-dim, multilingual) |

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
  - ADR-0008: Original Language Primary _(Pending)_
  - ADR-0009: SKOS Ontology Backbone _(Pending)_

### Technical Specifications

- [Data Models](./architecture/technical/data-models.md) - Complete schema
- [Qdrant Payload Structure](./architecture/technical/QDRANT_PAYLOAD_STRUCTURE.md) - Vector DB format
- [Universal Semantic Chunking](./architecture/technical/UNIVERSAL_SEMANTIC_CHUNKING.md) - Algorithm details
- [API Contracts](./api-contracts-main.md) - MCP Server tool specifications
- [Configuration & Data Persistence](./configuration-data-persistence.md) - Environment and manifest system

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

## Strategic Roadmap (2026-02-09)

- [Strategic Brief v1.0](./development/strategic-brief-v1.md) - Vision poster (what Alexandria wants to be)
- [Strategic Notebook](./development/strategic-notebook-2026-02-09.md) - Full technical details and reasoning

### Development Layers

| Day | Layer | Status | Key deliverable |
|-----|-------|--------|-----------------|
| 0 | **SOURCE** | Planned | 5 new connectors (Wikisource, CText, SuttaCentral, Gallica, Perseus) + BaseConnector interface |
| 1 | **SKOS** | Planned | W3C SKOS ontology backbone, original-language-primary, `translation_fidelity` field |
| 2 | **AGENTS** | Partial | Librarian agents (LIBRARIAN/RESEARCHER/CURATOR/ARCHIVIST); Guardians already built |
| 3 | **GRAPH** | Planned | Neo4j on BUCO + LightRAG proof-of-concept on 100-200 books |
| 4 | **TEMPORAL** | Planned | Graphiti conversation memory + Citaonica (replaces Speaker's Corner) |

### Guardian Persona System (Cuvari Alexandrije)

11 active guardians loaded from `.md` files with `alexandria:` YAML frontmatter. Guardians = WHO speaks (personality), Patterns = HOW to structure (compose at runtime).

- **Key files:** `scripts/guardian_personas.py` (loader), `scripts/mcp_server.py` (`guardian` param + `alexandria_guardians` tool)
- **Guardian dir:** `docs/development/guardians/`
- **Active:** alan_kay, ariadne, fantom, hector, hipatija, klepac, mrljac, lupita, roda, vault_e, zec (default)

### Two Products Insight

Two possible products hiding in Alexandria (identified during strategic planning):

- **Product A: "Personal Knowledge Companion"** — For Sabo (and people like Sabo). 9,000 books, semantic search, guardians with personality, reading journey tracking. *"I've read hundreds of books and can't remember where I read that thing about consciousness and mathematics. Alexandria finds it in seconds."*
- **Product B: "Library Intelligence Platform"** — For institutions. Multi-connector ingestion, MCP-first API, batch processing, reliability. *"Point it at your library, get a semantic search engine with AI agents managing your collection."*

**Decision: don't choose yet.** The Librarians concept works for BOTH. Build the shared foundation (Day 0-2). The fork happens later when the Temporal Knowledge Layer decides if it serves one user's journey or many users' queries. The presence of Lupita suggests this is Product A.

### Tier 2 Sources (Future Connectors)

After the 5 Tier 1 connectors (Day 0), these 9 sources are worth building connectors for:

| Source | Collection | Languages |
|--------|-----------|-----------|
| Aozora Bunko | 17,000 Japanese literary works | Japanese |
| Polona | 3.5M items (National Library of Poland) | Polish, Latin, French, German |
| Lotsawa House | 6,000 Tibetan Buddhist texts | Tibetan + 9 modern languages |
| Sacred-texts.com | 1,700 books, 77 categories | English translations |
| Bayerische Staatsbibliothek | 3M+ digital copies | German, Latin, Greek |
| Europeana | 58M items (discovery layer) | All European languages |
| HathiTrust | 6.7M public domain volumes | 460 languages |
| Projekt Runeberg | ~1,000 Scandinavian works | Swedish, Danish, Norwegian, Finnish, Icelandic |
| Lib.ru | Tens of thousands of Russian works | Russian |

**See:** [Strategic Notebook — Tier 2 Sources](./development/strategic-notebook-2026-02-09.md#tier-2-sources-future-connectors) for technical details.

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
