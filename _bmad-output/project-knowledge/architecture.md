# System Architecture - Alexandria

## Executive Summary
Alexandria is a **Retrieval-Augmented Generation (RAG)** system designed for multidisciplinary knowledge synthesis. It processes local document collections (PDF, EPUB) into a vector database (Qdrant) and provides semantic search capabilities enhanced by LLM generation.

## Architecture Pattern
**Monolithic Thin-Client Pattern**
- **Backend Logic:** Encapsulated in Python modules (`scripts/`) acting as a service layer.
- **Frontend:** Streamlit (`alexandria_app.py`) acting as a thin presentation layer.
- **Data Store:** Qdrant (Vector) + Local Filesystem (Manifests/Logs) + Calibre SQLite (Metadata).

## Technology Stack

| Component | Technology | Role |
|-----------|------------|------|
| **GUI** | Streamlit | User Interface for ingestion & query |
| **Logic** | Python 3.14 | Core processing |
| **Vector DB** | Qdrant | Storing 384-dim text embeddings |
| **Embeddings** | all-MiniLM-L6-v2 | Sentence Transformers (Local inference) |
| **LLM** | OpenRouter API | Answer generation & Reranking |
| **Parsing** | PyMuPDF, EbookLib | Text extraction from documents |

## Core Subsystems

### 1. Ingestion Engine (`ingest_books.py`)
- **Input:** EPUB, PDF, TXT, MD
- **Process:**
  1.  **Text Extraction:** Format-specific parsers.
  2.  **Normalization:** Cleaning text.
  3.  **Chunking:** Domain-specific strategies (defined in `DOMAINS.json` / code).
      - *Technical:* Larger chunks, overlap.
      - *Philosophy:* Argument-based pre-chunking.
  4.  **Embedding:** Local generation using `sentence-transformers`.
  5.  **Storage:** Upsert to Qdrant + Log to Manifest.

### 2. Query Engine (`rag_query.py`)
- **Input:** Natural language query
- **Process:**
  1.  **Embed Query:** Same model as ingestion.
  2.  **Vector Search:** Query Qdrant with `fetch_multiplier`.
  3.  **Filtering:** Apply similarity threshold & domain filters.
  4.  **Reranking (Optional):** Use LLM to re-score results.
  5.  **Generation (Optional):** Send context + query to OpenRouter LLM.

### 3. Management System (`collection_manifest.py`)
- Maintains a JSON-based ledger of all ingested books.
- Prevents duplicate processing.
- Enables "resume" functionality for large batch jobs.

## Integration Architecture
- **Calibre:** Direct read access to `metadata.db` to import books without file duplication.
- **Open WebUI:** Compatible payload structure allows Qdrant collections to be used by other tools.

## Future API Roadmap
The existing `scripts/` package is designed to be imported by a future FastAPI application, enabling:
- `POST /ingest`: Trigger ingestion.
- `POST /query`: Semantic search endpoint.
- `GET /collections`: List status.
