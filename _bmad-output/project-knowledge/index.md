# Alexandria Project Knowledge Base

> **Priority Update (Jan 2026):** Focus shifted from API development to **High-Fidelity Ingestion**. The goal is quality over quantity. API/Thin-client architecture is documented but currently on hold.

## 1. System Overview
- **[Project Overview](./project-scan-report.json)** - Scan metadata and stats.
- **[System Architecture](./architecture.md)** - Technical design (Ingestion, Query, Storage).
- **[Source Tree Analysis](./source-tree-analysis.md)** - Codebase map and module responsibilities.

## 2. Ingestion & Data Quality (Critical)
The core value of Alexandria is the *quality* of its vectors.
- **Strategies:** defined in `scripts/ingest_books.py` and `scripts/domains.json`.
- **Experimental:** `scripts/philosophical_chunking.py` (Argument-based).
- **Goal:** Implement semantic chunking to preserve logical flow in essays/philosophy.

## 3. Architecture Context
- **Pattern:** Monolithic Thin-Client (Streamlit + Python Scripts).
- **Database:** Qdrant (Vector) + SQLite (Calibre Metadata).
- **Documentation:** See `docs/` in the project root for C4 diagrams.

## 4. Next Steps (Roadmap)
1.  **Ingest Refinement:** Review current chunking vs. semantic chunking.
2.  **Domain Tuning:** Specific rules for History vs. Philosophy vs. Tech.
3.  **Data Quality:** Validate retrieval accuracy before mass ingestion.
