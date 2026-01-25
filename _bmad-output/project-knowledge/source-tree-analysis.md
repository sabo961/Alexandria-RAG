# Source Tree Analysis - Alexandria

## Directory Structure

```
Alexandria/
├── alexandria_app.py           # 🌟 MAIN ENTRY POINT (Streamlit GUI)
├── requirements.txt            # Project dependencies
├── AGENTS.md                   # AI Agent configuration
├── README.md                   # Project overview
├── scripts/                    # 🧠 CORE BUSINESS LOGIC (The "Brain")
│   ├── batch_ingest.py         # Bulk ingestion orchestration
│   ├── ingest_books.py         # Core ingestion & chunking logic
│   ├── rag_query.py            # RAG query engine (Search + LLM Answer)
│   ├── qdrant_utils.py         # Vector DB management
│   ├── collection_manifest.py  # Ingestion tracking system
│   ├── philosophical_chunking.py # Specialized chunking strategy
│   └── domains.json            # Domain configuration
├── docs/                       # Project documentation
│   ├── architecture/           # C4 diagrams & decisions
│   │   └── workspace.dsl       # Structurizr DSL definition
│   ├── guides/                 # User guides
│   └── stories/                # Feature requirements
├── logs/                       # Runtime logs & manifests
│   └── *_manifest.json         # Tracking records of ingested books
├── ingest/                     # Staging area for new books
└── ingested/                   # Archive of processed books
```

## Critical Folders Analysis

### `scripts/` (Business Logic Layer)
This is the most critical directory. It contains all the reusable logic that decouples the GUI from the backend operations.
- **Key Modules:**
  - `ingest_books.py`: Handles file parsing (PDF/EPUB), text cleaning, chunking strategies, embedding generation, and Qdrant upload.
  - `rag_query.py`: A unified interface for querying. It abstracts Qdrant client calls, similarity filtering, and OpenRouter LLM integration.
  - `collection_manifest.py`: Implements a file-based JSON registry of all ingested content to avoid duplicates and allow resuming.

### `docs/architecture/` (System Design)
Contains the `workspace.dsl` which defines the C4 model. This is the source of truth for the system's intended architecture.

### `logs/` (State Management)
Acts as a simple local database for tracking ingestion state. The manifest files (`*_manifest.json`) are critical for the "resume" functionality in batch ingestion.

## Entry Points
1.  **GUI:** `streamlit run alexandria_app.py`
2.  **CLI:** `python scripts/rag_query.py "query"` or `python scripts/batch_ingest.py`
3.  **Future API:** (Planned) Will utilize `scripts/` modules directly.
