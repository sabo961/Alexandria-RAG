# Alexandria Source Tree

**Generated:** 2026-01-31
**Project:** Alexandria RAG System
**Type:** Monolith (Python Backend)
**Interface:** MCP Server (Model Context Protocol)

---

## Project Structure

```
alexandria/
├── requirements.txt               # Python dependencies
├── .mcp.json                      # MCP Server configuration
├── README.md                      # Project landing page
├── AGENTS.md                      # AI agent entry point
├── TODO.md                        # Task backlog (HIGH/MEDIUM/LOW)
├── CHANGELOG.md                   # Completed work archive
│
├── scripts/                       # BUSINESS LOGIC + MCP SERVER
│   ├── mcp_server.py              # ENTRY POINT - MCP Server
│   ├── __init__.py                # Package marker
│   ├── calibre_db.py              # Calibre SQLite interface
│   ├── collection_manifest.py     # Ingestion tracking
│   ├── ingest_books.py            # Book ingestion pipeline
│   ├── rag_query.py               # Semantic search & RAG
│   ├── chapter_detection.py       # Chapter boundary detection
│   ├── qdrant_utils.py            # Qdrant operations
│   ├── universal_chunking.py      # Semantic chunking (ADR 0007)
│   ├── batch_ingest.py            # Batch ingestion helper
│   └── README.md                  # Scripts package overview
│
├── docs/                          # DOCUMENTATION
│   ├── index.md                   # Documentation hub
│   ├── project-context.md         # AI agent rules (45 rules) - MANDATORY
│   ├── source-tree.md             # This file
│   │
│   ├── user-docs/                 # Diataxis user documentation
│   │   ├── tutorials/             # Learning-oriented
│   │   │   ├── getting-started.md
│   │   │   ├── professional-setup.md
│   │   │   └── powershell-setup.md
│   │   ├── how-to/                # Task-oriented
│   │   │   ├── common-workflows.md
│   │   │   ├── track-ingestion.md
│   │   │   ├── troubleshoot-ingestion.md
│   │   │   ├── configure-open-webui.md
│   │   │   ├── git-workflow.md
│   │   │   └── structurizr-guide.md
│   │   └── explanation/           # Understanding-oriented
│   │       └── architecture-principles.md
│   │
│   ├── architecture/              # Reference documentation
│   │   ├── README.md              # Architecture overview
│   │   ├── mcp-server.md          # MCP tool reference
│   │   ├── c4/                    # C4 diagrams
│   │   │   ├── 01-context.md
│   │   │   ├── 02-container.md
│   │   │   └── 03-component.md
│   │   ├── decisions/             # ADRs
│   │   │   ├── README.md
│   │   │   ├── 0001-use-qdrant-vector-db.md
│   │   │   ├── 0003-gui-as-thin-layer.md (Superseded)
│   │   │   └── 0007-universal-semantic-chunking.md (current)
│   │   └── technical/             # Technical specs
│   │       ├── data-models.md
│   │       ├── QDRANT_PAYLOAD_STRUCTURE.md
│   │       └── UNIVERSAL_SEMANTIC_CHUNKING.md
│   │
│   └── development/               # BMAD internal workflow
│       ├── README.md
│       ├── ideas/                 # Future visions (not yet TODO)
│       ├── backlog/               # Detailed accepted TODOs
│       ├── research/              # Background analysis
│       ├── analysis/              # Session outputs
│       └── security/              # Audits and guidelines
│
├── logs/                          # Runtime artifacts
│   ├── README.md
│   ├── collection_manifest_*.json # Ingestion tracking per collection
│   └── *.csv                      # CSV exports
│
├── ingest/                        # INPUT: Books to ingest
├── ingested/                      # OUTPUT: Processed books
│
├── tests/                         # Test suite
│   ├── unit/
│   └── integration/
│
├── _bmad/                         # BMAD Framework
│   ├── core/                      # Core workflows & agents
│   ├── bmm/                       # Method Module
│   ├── bmb/                       # Builder
│   └── _config/                   # Configuration
│
└── .vscode/                       # VS Code settings
```

---

## Critical Paths

### For AI Agents

| Priority | File | Purpose |
|----------|------|---------|
| 1 | `docs/project-context.md` | 45 implementation rules - MANDATORY |
| 2 | `TODO.md` | Current priorities |
| 3 | `docs/index.md` | Documentation hub |

### For Development

| Directory | Purpose |
|-----------|---------|
| `scripts/` | All business logic lives here |
| `scripts/mcp_server.py` | Entry point |
| `tests/` | Test suite |

### For Documentation

| Directory | Purpose |
|-----------|---------|
| `docs/user-docs/` | End-user documentation (Diataxis) |
| `docs/architecture/` | Technical reference, C4, ADRs |
| `docs/development/` | Internal workflow (BMAD) |

---

## Entry Point

**MCP Server** (configured in `.mcp.json`):

```
Claude Code → scripts/mcp_server.py
    ├── Query: scripts/rag_query.py
    ├── Ingest: scripts/ingest_books.py
    ├── Search: scripts/calibre_db.py
    └── Stats: scripts/qdrant_utils.py
```

---

## External Systems

```
Alexandria
    ├── Qdrant Vector DB (192.168.0.151:6333)
    ├── Calibre Library (G:\My Drive\alexandria)
    └── OpenRouter API (LLM calls)
```

---

## Task Lifecycle

```
docs/development/ideas/  →  TODO.md  →  docs/development/backlog/  →  CHANGELOG.md
     (consider)             (accept)        (in progress)               (done)
```

---

## Gitignored

| Pattern | Reason |
|---------|--------|
| `ingest/`, `ingested/` | Large book files |
| `logs/*.json`, `logs/*.csv` | Runtime artifacts |
| `__pycache__/` | Python bytecode |
| `.env` | Environment variables |

---

**Last Updated:** 2026-01-31
