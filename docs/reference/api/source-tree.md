# Alexandria Source Tree Analysis

**Generated:** 2026-01-26
**Project:** Alexandria RAG System
**Type:** Monolith (Python Backend)

---

## Project Structure Overview

```
alexandria/
├── 📱 alexandria_app.py              # 🔹 ENTRY POINT - Streamlit GUI (thin layer)
├── 📄 requirements.txt                # Python dependencies (pip install -r)
├── 📋 README.md                       # Project landing page
├── 📋 AGENTS.md                       # AI agent navigation hub
├── 📋 TODO.md                         # Task backlog
├── 📋 CHANGELOG.md                    # Completed work archive
│
├── 📦 scripts/                        # 🔹 BUSINESS LOGIC (core modules)
│   ├── __init__.py                    # Package marker
│   ├── calibre_db.py                  # Calibre SQLite interface
│   ├── collection_manifest.py         # Ingestion tracking
│   ├── ingest_books.py                # 🔹 Book ingestion pipeline
│   ├── rag_query.py                   # 🔹 Semantic search & RAG
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
│   ├── domains.json                   # Domain-specific config (deprecated)
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
├── 📂 assets/                         # Static GUI assets
│   └── (Images, icons for Streamlit GUI)
│
├── 📂 .streamlit/                     # Streamlit configuration
│   ├── config.toml                    # Streamlit UI settings
│   └── secrets.toml                   # 🔐 API keys (gitignored)
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
| `./` (root) | **Main application entry point** | `alexandria_app.py` (Streamlit GUI) |
| `scripts/` | **Core business logic** | All `.py` modules (importable package) |
| `logs/` | **Runtime artifacts** | Manifest files, CSV exports |
| `ingest/` → `ingested/` | **Ingestion workflow** | Files auto-moved after processing |

### Documentation

| Directory | Purpose | Key Files |
|-----------|---------|-----------|
| `docs/` | **Master documentation hub** | (Future: index.md) |
| `docs/architecture/` | **Architecture docs** | ADRs, C4 diagrams, technical specs |
| `docs/guides/` | **User/dev guides** | Quick reference, setup guides |
| `docs/research/` | **Research findings** | Proposals, experiments |
| `_bmad-output/` | **AI agent rules** | project-context.md (critical) |

### Configuration

| Directory | Purpose | Files |
|-----------|---------|-------|
| `.streamlit/` | **Streamlit config** | config.toml, secrets.toml |
| `.vscode/` | **Editor settings** | VS Code workspace config |
| `_bmad/` | **BMad framework** | Workflow definitions |

---

## Entry Points & Execution Flow

### 1. GUI Application (Primary)

```bash
streamlit run alexandria_app.py
```

**Flow:**
```
User → alexandria_app.py (Streamlit GUI)
    ├─ Calibre Tab → scripts/calibre_db.py
    ├─ Ingestion Tab → scripts/ingest_books.py
    ├─ Query Tab → scripts/rag_query.py
    └─ Collections Tab → scripts/qdrant_utils.py
```

**Binds to:** `0.0.0.0:8501` (accessible from network)

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
| `.streamlit/config.toml` | Streamlit UI settings | `.streamlit/` |
| `.streamlit/secrets.toml` | **API keys (gitignored)** | `.streamlit/` |
| `_bmad-output/project-context.md` | **AI agent rules** | `_bmad-output/` |
| `logs/collection_manifest_*.json` | Ingestion tracking | `logs/` |
| `scripts/domains.json` | Domain config (deprecated) | `scripts/` |

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
| `.streamlit/secrets.toml` | **Contains API keys** |
| `ingest/`, `ingested/` | Large book files |
| `logs/*.json`, `logs/*.csv` | Runtime artifacts |
| `__pycache__/` | Python bytecode cache |
| `.obsidian/` | Obsidian vault metadata |
| `.git/` | Git repository data |

**See:** `.gitignore` for full list

---

## Architecture Constraints (from ADRs)

### ADR 0003: GUI as Thin Layer
- **Rule:** All business logic lives in `scripts/` package
- **GUI role:** Only collect input, call scripts, display results
- **Anti-pattern:** Duplicating logic in `alexandria_app.py`

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

# Configure Streamlit secrets
# Edit .streamlit/secrets.toml with API keys

# Run GUI
streamlit run alexandria_app.py
```

### Ingestion Workflow

```
1. Place books in ingest/ folder
2. Launch GUI → Ingestion Tab
3. Select files, choose domain & collection
4. Click "Start Ingestion"
5. Books auto-move to ingested/ on success
6. Manifest updated in logs/collection_manifest_*.json
```

### Query Workflow

```
1. Launch GUI → Query Tab
2. Enter query, select collection
3. Optional: Enable LLM answer generation
4. View results (top-k chunks + sources)
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

**Generated by:** document-project workflow (exhaustive scan)
**Last Updated:** 2026-01-26
