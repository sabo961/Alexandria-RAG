# Alexandria - Source Tree Analysis

**Date:** 2026-02-09 (Updated)
**Project Type:** Monolith (Python Backend)
**Primary Language:** Python 3.14
**Architecture:** MCP-first design

---

## Overview

Alexandria is a multilingual knowledge platform over 9,000+ books in the Temenos Academy Library. RAG engine with semantic chunking, MCP-first architecture, guardian persona system (11 guardians), and multilingual embeddings (bge-m3, 1024-dim). All business logic lives in the `scripts/` package.

---

## Complete Directory Structure

```
alexandria/
├── .mcp.json                      # MCP Server configuration
├── requirements.txt               # Python dependencies
├── README.md                      # Project landing page
├── AGENTS.md                      # AI agent entry point
├── TODO.md                        # Task backlog
├── CHANGELOG.md                   # Completed work archive
├── billboard.md                   # Strategic pointer → brief + notebook
├── alexandria_app.py              # GUI: Streamlit dashboard (optional)
│
├── scripts/                       # BUSINESS LOGIC + MCP SERVER
│   ├── mcp_server.py              # Entry point - MCP Server (14 tools)
│   ├── ingest_books.py            # Book ingestion pipeline
│   ├── rag_query.py               # Semantic search & RAG
│   ├── calibre_db.py              # Calibre SQLite interface
│   ├── qdrant_utils.py            # Qdrant operations
│   ├── collection_manifest.py     # SQLite manifest manager
│   ├── chapter_detection.py       # Chapter boundary detection
│   ├── universal_chunking.py      # Semantic chunking (ADR 0007)
│   ├── html_sanitizer.py          # XSS prevention (Story 5.3)
│   ├── config.py                  # Configuration loader (.env)
│   ├── guardian_personas.py       # Guardian persona loader (NEW: Feb 2026)
│   │
│   ├── # Book Source Connectors
│   ├── archive_connector.py       # Internet Archive integration
│   ├── gutenberg_connector.py     # Project Gutenberg connector
│   ├── calibre_web_connector.py   # Calibre-Web API client
│   ├── cwa_ingest_pipeline.py     # Auto-ingest automation
│   ├── public_domain_pipeline.py  # Public domain sourcing
│   │
│   ├── # Batch & Migration Tools
│   ├── batch_ingest.py            # Batch orchestrator
│   ├── batch_ingest_from_file.py  # Batch from file list
│   ├── migrate_to_bge_m3.py       # BGE-M3 model migration
│   ├── reingest_collection.py     # Collection re-ingestion
│   │
│   ├── # Utility Scripts
│   ├── list_books.py              # List books in collection
│   ├── test_multilingual.py       # Multilingual RAG test (Croatian)
│   ├── pick_sample_books.py       # Sample book selector
│   │
│   └── README.md                  # Scripts package overview
│
├── docs/                          # DOCUMENTATION
│   ├── index.md                   # Documentation hub
│   ├── project-context.md         # AI agent rules (MANDATORY)
│   ├── source-tree.md             # This file
│   │
│   ├── user-docs/                 # Diataxis user documentation
│   │   ├── tutorials/             # Learning-oriented
│   │   │   ├── getting-started.md
│   │   │   └── powershell-setup.md
│   │   ├── how-to/                # Task-oriented
│   │   │   ├── common-workflows.md
│   │   │   ├── track-ingestion.md
│   │   │   ├── troubleshoot-ingestion.md
│   │   │   ├── configure-open-webui.md
│   │   │   ├── git-workflow.md
│   │   │   └── structurizr-guide.md
│   │   └── explanation/           # Understanding-oriented
│   │       ├── architecture-principles.md
│   │       └── README.md
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
│   │   │   ├── 0003-gui-as-thin-layer.md
│   │   │   └── 0007-universal-semantic-chunking.md
│   │   └── technical/             # Technical specs
│   │       ├── data-models.md
│   │       ├── QDRANT_PAYLOAD_STRUCTURE.md
│   │       └── UNIVERSAL_SEMANTIC_CHUNKING.md
│   │
│   └── development/               # BMAD internal workflow
│       ├── README.md
│       ├── strategic-brief-v1.md  # Vision poster (2026-02-09)
│       ├── strategic-notebook-2026-02-09.md  # Technical companion
│       ├── guardians/             # Guardian persona .md files (11 active)
│       │   ├── alan_kay.md
│       │   ├── ariadne.md
│       │   ├── hipatija.md
│       │   ├── lupita.md
│       │   ├── zec.md             # Default guardian
│       │   └── ...                # (+6 more)
│       ├── ideas/                 # Future visions
│       ├── backlog/               # Active TODO details
│       ├── research/              # Background analysis
│       ├── analysis/              # Session outputs
│       └── security/              # Audits
│
├── logs/                          # Runtime artifacts
│   ├── README.md
│   ├── collection_manifest_*.json
│   └── *.csv
│
├── ingest/                        # INPUT: Books to ingest
├── ingested/                      # OUTPUT: Processed books
│
├── tests/                         # Test suite
│   ├── unit/
│   └── integration/
│
├── _bmad/                         # BMAD Framework
│   ├── core/
│   ├── bmm/
│   ├── bmb/
│   └── _config/
│
└── .vscode/                       # VS Code settings
```

---

## Critical Directories

### `scripts/`

**Purpose:** All business logic + MCP Server entry point
**Contains:** Python modules for ingestion, querying, manifest management
**Entry Point:** `mcp_server.py`

Key modules:
- `mcp_server.py` - MCP protocol handler, 14 tools (query, ingest, guardians)
- `ingest_books.py` - Book extraction, chunking, embedding, upload
- `rag_query.py` - Semantic search, context retrieval, LLM integration
- `calibre_db.py` - Calibre library metadata access
- `qdrant_utils.py` - Vector database operations
- `guardian_personas.py` - Guardian persona loader (11 guardians from .md files)

### `docs/`

**Purpose:** All project documentation
**Contains:** User guides, architecture docs, development workflow

Structure follows hybrid model:
- **Diataxis** (user-docs/) - tutorials, how-to, explanation
- **Architecture** - C4, ADRs, technical specs
- **BMAD Development** - ideas, backlog, research, analysis

### `logs/`

**Purpose:** Runtime artifacts and ingestion tracking
**Contains:** JSON manifests, CSV exports, runtime logs

Critical files:
- `collection_manifest_{name}.json` - Tracks all ingested books
- `*.csv` - Human-readable manifest exports

---

## Entry Points

### Primary Entry: `scripts/mcp_server.py`

**Protocol:** MCP (Model Context Protocol) over stdio
**Configuration:** `.mcp.json`

```
Claude Code → scripts/mcp_server.py (14 tools)
    ├── alexandria_query()      → rag_query.py + guardian_personas.py
    ├── alexandria_guardians()  → guardian_personas.py
    ├── alexandria_search()     → calibre_db.py
    ├── alexandria_book()       → calibre_db.py
    ├── alexandria_stats()      → qdrant_utils.py
    ├── alexandria_ingest()     → ingest_books.py
    ├── alexandria_batch_ingest() → ingest_books.py
    └── alexandria_*()          → various modules (7 more tools)
```

### Secondary Entry: `alexandria_app.py` (Optional GUI)

**Protocol:** HTTP (Streamlit web interface)
**Launch:** `streamlit run alexandria_app.py`
**Port:** 8501

Thin presentation layer - all business logic delegates to `scripts/` modules

---

## External Systems

```
Alexandria
    ├── Qdrant Vector DB (192.168.0.151:6333)
    │   └── Collections: alexandria, alexandria_test
    │
    ├── Calibre Library (G:\My Drive\alexandria)
    │   └── metadata.db (SQLite)
    │
    └── OpenRouter API (optional, for LLM)
```

---

## File Organization Patterns

### Python Modules (`scripts/`)

```python
#!/usr/bin/env python3
"""Module docstring"""

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Classes and functions...

if __name__ == "__main__":
    main()
```

### Documentation (`docs/`)

- **Tutorials:** Step-by-step learning
- **How-To:** Task-focused recipes
- **Explanation:** Conceptual "why"
- **Architecture:** Technical reference

---

## Configuration Files

| File | Purpose |
|------|---------|
| `.mcp.json` | MCP Server configuration |
| `requirements.txt` | Python dependencies |
| `.env` | Environment variables (gitignored) |
| `_bmad/_config/*.yaml` | BMAD framework config |

---

## Task Lifecycle

```
docs/development/ideas/  →  TODO.md  →  docs/development/backlog/  →  CHANGELOG.md
     (consider)             (accept)        (in progress)               (done)
```

---

## Notes for Development

1. **All business logic in `scripts/`** - No logic in interface layers
2. **MCP-first** - Primary interface is MCP Server
3. **Logging, not print()** - Use `logger.info()`, `logger.error()`
4. **Manifest tracking** - Every ingested book tracked in JSON manifest
5. **External Qdrant** - Vector DB is NOT localhost (192.168.0.151)

---

_Generated using BMAD Method `document-project` workflow_
