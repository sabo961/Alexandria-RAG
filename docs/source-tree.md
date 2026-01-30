# Alexandria Source Tree Analysis

**Generated:** 2026-01-30
**Project:** Alexandria RAG System
**Type:** Monolith (Python Backend)
**Interface:** MCP Server (Model Context Protocol)

---

## Project Structure Overview

```
alexandria/
├── 📄 requirements.txt                # Python dependencies (pip install -r)
├── 📄 .mcp.json                       # 🔹 MCP Server configuration
├── 📋 README.md                       # Project landing page
├── 📋 AGENTS.md                       # AI agent navigation hub
├── 📋 TODO.md                         # Task backlog
├── 📋 CHANGELOG.md                    # Completed work archive
│
├── 📦 scripts/                        # 🔹 BUSINESS LOGIC + MCP SERVER
│   ├── mcp_server.py                  # 🔹 ENTRY POINT - MCP Server
│   ├── __init__.py                    # Package marker
│   ├── calibre_db.py                  # Calibre SQLite interface
│   ├── collection_manifest.py         # Ingestion tracking
│   ├── ingest_books.py                # 🔹 Book ingestion pipeline
│   ├── rag_query.py                   # 🔹 Semantic search & RAG
│   ├── chapter_detection.py           # Chapter boundary detection
│   ├── qdrant_utils.py                # Qdrant operations
│   ├── universal_chunking.py          # Semantic chunking (ADR 0007)
│   ├── batch_ingest.py                # Batch ingestion helper
│   ├── generate_book_inventory.py     # Calibre inventory generator
│   ├── count_file_types.py            # File type statistics
│   ├── experiment_chunking.py         # Chunking experiments
│   ├── experiment_semantic.py         # Semantic analysis experiments
│   ├── check_authors.py               # Author data validation
│   ├── check_sql_rows.py              # SQL row count checks
│   ├── fix_manifest_authors.py        # Manifest repair utility
│   └── README.md                      # Scripts package overview
│
├── 📂 docs/                           # Documentation (BMad-compliant structure)
│   ├── index.md                       # 🔹 FUTURE: Master documentation index
│   ├── project-scan-report.json       # Workflow state file
│   ├── data-models-alexandria.md      # API & data models reference
│   ├── source-tree-analysis.md        # This file
│   │
│   ├── architecture/                  # Architecture documentation
│   │   ├── README.md                  # Architecture index
│   │   ├── STRUCTURIZR.md             # C4 diagram tooling guide
│   │   │
│   │   ├── c4/                        # C4 Architecture Diagrams
│   │   │   ├── 01-context.md          # System context
│   │   │   ├── 02-container.md        # Container view
│   │   │   └── 03-component.md        # Component view
│   │   │
│   │   ├── decisions/                 # Architecture Decision Records (ADRs)
│   │   │   ├── README.md              # ADR index
│   │   │   ├── template.md            # ADR template
│   │   │   ├── 0001-use-qdrant-vector-db.md
│   │   │   ├── 0002-domain-specific-chunking.md  # (Superseded by 0007)
│   │   │   ├── 0003-gui-as-thin-layer.md
│   │   │   ├── 0004-collection-specific-manifests.md
│   │   │   ├── 0005-philosophical-argument-chunking.md  # (Superseded by 0007)
│   │   │   ├── 0006-separate-systems-architecture.md
│   │   │   └── 0007-universal-semantic-chunking.md
│   │   │
│   │   ├── technical/                 # Technical specifications
│   │   │   ├── PDF_vs_EPUB_COMPARISON.md
│   │   │   ├── QDRANT_PAYLOAD_STRUCTURE.md
│   │   │   └── UNIVERSAL_SEMANTIC_CHUNKING.md
│   │   │
│   │   └── .structurizr/              # Structurizr workspace (C4 diagram cache)
│   │
│   ├── guides/                        # User and developer guides
│   │   ├── QUICK_REFERENCE.md         # Command cheat sheet
│   │   ├── LOGGING_GUIDE.md           # Logging patterns
│   │   ├── PROFESSIONAL_SETUP_COMPLETE.md
│   │   └── OPEN_WEBUI_CONFIG.md       # OpenWebUI integration
│   │
│   ├── research/                      # Research documents
│   │   ├── alexandria-qdrant-project-proposal.md
│   │   ├── argument_based_chunking_for_philosophical_texts_alexandria_rag.md
│   │   ├── missing-classics-analysis.md
│   │   └── vector-db-cloud-comparison.md
│   │
│   ├── backlog/                       # Feature proposals & ideas
│   │   ├── Hierarchical Chunking for Alexandria RAG.md
│   │   └── Hierarchical Chunking for Alexandria RAG-additions.md
│   │
│   ├── proposals/                     # External contribution proposals
│   │   ├── README.md                  # Proposals index
│   │   └── bmad-workflow-integration-proposal.md  # GitHub issue for BMad
│   │
│   └── stories/                       # Feature stories (BMad workflow)
│       └── README.md                  # Stories index
│
├── 📂 logs/                           # Runtime logs & manifests
│   ├── collection_manifest_{name}.json   # Ingestion tracking per collection
│   ├── alexandria_manifest.csv           # CSV export of manifest
│   ├── README.md                         # Logs directory guide
│   └── *.log                             # Runtime logs (if any)
│
├── 📂 ingest/                         # 🔸 INPUT: Books to be ingested
│   └── (User places .epub/.pdf files here)
│
├── 📂 ingested/                       # 🔸 OUTPUT: Successfully ingested books
│   └── (Files auto-moved here after ingestion)
│
├── 📂 tests/                          # Test suite
│   ├── unit/                          # Unit tests
│   └── integration/                   # Integration tests
│
├── 📂 .vscode/                        # VS Code workspace settings
│   ├── settings.json                  # Editor config
│   └── launch.json                    # Debug configurations
│
├── 📂 _bmad/                          # 🔹 BMAD Framework (workflow automation)
│   ├── core/                          # BMad Core workflows & agents
│   ├── bmm/                           # BMad Method Module (project workflows)
│   ├── bmb/                           # BMad Builder (agent/workflow creation)
│   └── _config/                       # BMad configuration
│
├── 📂 _bmad-output/                   # BMad workflow outputs
│   ├── project-context.md             # 🔹 AI agent implementation rules (45 rules)
│   ├── planning-artifacts/            # Planning phase outputs
│   └── implementation-artifacts/      # Implementation phase outputs
│
└── 📂 _bmad-custom/                   # Custom BMad extensions
```

---

## Critical Directories

### Production Code

| Directory | Purpose | Entry Points |
|-----------|---------|--------------|
| `scripts/` | **Core business logic + MCP Server** | `mcp_server.py` (entry point) |
| `logs/` | **Runtime artifacts** | Manifest files, CSV exports |
| `ingest/` → `ingested/` | **Ingestion workflow** | Files auto-moved after processing |
| `tests/` | **Test suite** | Unit and integration tests |

### Documentation

| Directory | Purpose | Key Files |
|-----------|---------|-----------|
| `docs/` | **Master documentation hub** | index.md |
| `docs/reference/architecture/` | **Architecture docs** | ADRs, C4 diagrams, technical specs |
| `docs/how-to-guides/` | **User guides** | Quick reference, workflows |
| `docs/tutorials/` | **Getting started** | Setup guides |
| `_bmad-output/` | **AI agent rules** | project-context.md (critical) |

### Configuration

| Directory | Purpose | Files |
|-----------|---------|-------|
| `./` (root) | **MCP config** | .mcp.json |
| `.vscode/` | **Editor settings** | VS Code workspace config |
| `_bmad/` | **BMad framework** | Workflow definitions |

---

## Entry Points & Execution Flow

### 1. MCP Server (Primary)

Configured in `.mcp.json`, runs via Claude Code:

**Flow:**
```
Claude Code → MCP Server (scripts/mcp_server.py)
    ├─ Query Tools → scripts/rag_query.py
    ├─ Ingest Tools → scripts/ingest_books.py
    ├─ Search Tools → scripts/calibre_db.py
    └─ Stats Tools → scripts/qdrant_utils.py
```

**Protocol:** stdio (Model Context Protocol)

---

### 2. CLI Scripts (Secondary)

All scripts in `scripts/` support CLI usage:

```bash
# Ingest book
python scripts/ingest_books.py book.epub --domain philosophy --collection alexandria

# Query
python scripts/rag_query.py "search query" --collection alexandria --use-llm

# Calibre stats
python scripts/calibre_db.py

# Qdrant management
python scripts/qdrant_utils.py --list
```

---

## Key Integration Points

### External Systems

```
Alexandria
    ├─ Qdrant Vector DB (192.168.0.151:6333)
    │   └─ Collections: alexandria, alexandria_test, etc.
    │
    ├─ Calibre Library (G:\My Drive\alexandria)
    │   └─ metadata.db (SQLite)
    │
    └─ OpenRouter API (LLM calls)
        └─ Claude 3.5 Sonnet, GPT-4, etc.
```

### Internal Data Flow

```
Calibre Library → CalibreDB → GUI Calibre Tab
      ↓
Book Files (.epub/.pdf) → ingest_books.py
      ↓
UniversalChunker → Embeddings → Qdrant
      ↓
CollectionManifest.add_book() → logs/collection_manifest_*.json
```

---

## Configuration Files

| File | Purpose | Location |
|------|---------|----------|
| `requirements.txt` | **Python dependencies** | Root |
| `.mcp.json` | **MCP Server configuration** | Root |
| `_bmad-output/project-context.md` | **AI agent rules** | `_bmad-output/` |
| `logs/collection_manifest_*.json` | Ingestion tracking | `logs/` |

---

## Test Files

**Location:** Currently none (tests planned but not implemented)

**Recommended structure** (from project-context.md):
```
tests/
├── test_ingest_books.py
├── test_rag_query.py
├── test_collection_manifest.py
└── test_calibre_db.py
```

**Run tests:** `pytest tests/` (when implemented)

---

## Gitignored Directories & Files

| Pattern | Reason |
|---------|--------|
| `ingest/`, `ingested/` | Large book files |
| `logs/*.json`, `logs/*.csv` | Runtime artifacts |
| `__pycache__/` | Python bytecode cache |
| `.obsidian/` | Obsidian vault metadata |
| `.git/` | Git repository data |
| `.env` | Environment variables |

**See:** `.gitignore` for full list

---

## Architecture Constraints (from ADRs)

### ADR 0003: MCP-First Architecture (Superseded)
- **Rule:** All business logic lives in `scripts/` package
- **MCP Server:** Exposes scripts as MCP tools
- **Anti-pattern:** Duplicating logic in interface layer

### ADR 0007: Universal Semantic Chunking
- **Chunking:** `scripts/universal_chunking.py`
- **Algorithm:** Sentence embeddings + cosine similarity
- **Thresholds:** Philosophy (0.45), Others (0.55)

### ADR 0006: External Qdrant Server
- **Location:** `192.168.0.151:6333` (NOT localhost)
- **Collections:** Separate collections per domain/experiment
- **Persistence:** Data persists on external server

---

## Development Workflow

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure MCP Server in .mcp.json
# Restart Claude Code to activate
```

### Ingestion Workflow (via Claude Code)

```
User: Ingest the Nietzsche book with ID 7970
Claude: [calls alexandria_ingest(book_id=7970)]

User: Ingest all philosophy books
Claude: [calls alexandria_batch_ingest(tag="philosophy", limit=10)]
```

### Query Workflow (via Claude Code)

```
User: What does Silverston say about shipment patterns?
Claude: [calls alexandria_query("shipment pattern", context_mode="contextual")]
```

---

## Code Organization Patterns

### Module Structure (scripts/)

Each module follows consistent pattern:

```python
#!/usr/bin/env python3
"""Module docstring"""

import logging
# ... imports ...

logging.basicConfig(...)
logger = logging.getLogger(__name__)

# Dataclasses (if any)
@dataclass
class MyData:
    ...

# Main logic classes/functions
class MyClass:
    ...

def main():
    """CLI entry point"""
    ...

if __name__ == "__main__":
    main()
```

### Logging Pattern (MANDATORY from project-context.md)

```python
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# NO print() statements - use logger
logger.info(f"✅ Loaded {count} books")
logger.error(f"❌ Failed to ingest {filepath}")
logger.warning(f"⚠️ Missing metadata for {title}")
```

---

## Future Enhancements (from TODO.md)

### HIGH PRIORITY
- Ingest Versioning (track ingestion version in Qdrant payload)
- Chunk Fingerprint (sha1 hash for deduplication)

### MEDIUM PRIORITY
- Query Modes (fact/cite/explore/synthesize)
- Calibre Path Configuration (restore GUI setting, currently hardcoded)

### LOW PRIORITY
- Multi-file Upload (GUI enhancement)

**See:** [TODO.md](../../../TODO.md) for full backlog

---

## Related Documentation

- **[Architecture Documentation](../../explanation/architecture.md)** - Complete architecture reference
- **[Data Models & API Reference](./data-models.md)** - Module APIs
- **[ADRs](../architecture/decisions/README.md)** - Architecture decisions
- **[Project Context](../../../_bmad-output/project-context.md)** - AI agent rules (45 rules)
- **[Quick Reference](../../how-to-guides/common-workflows.md)** - Command cheat sheet

---

**Last Updated:** 2026-01-30
**Updated for:** MCP-first architecture
