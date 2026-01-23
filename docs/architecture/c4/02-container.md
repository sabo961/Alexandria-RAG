# C4 Level 2: Container Diagram

**Purpose:** Shows the major architectural components (containers) inside Alexandria RAG System and how they interact.

---

## Diagram

View interactively: http://localhost:8081 → "Containers" view

Or see `workspace.dsl` container definitions.

---

## Containers

### 1. Streamlit GUI (Web Browser)
**Technology:** Python 3.14, Streamlit
**Purpose:** Web-based interface for all user interactions

**Responsibilities:**
- Browse Calibre library with filters
- Select books for ingestion with domain assignment
- Execute RAG queries with parameter controls
- Display collection statistics and manifests
- Manage OpenRouter API configuration

**Key Features:**
- Purple gradient theme with professional layout
- Session state management for interactive features
- Real-time parameter validation
- CSV export functionality

**Architecture Principle:** **Thin presentation layer** - no business logic, only UI and user input handling.

**Related Story:** [04-GUI.md](../../stories/04-GUI.md)

---

### 2. Scripts Package (Python Modules)
**Technology:** Python 3.14
**Purpose:** Core business logic for all operations

**Responsibilities:**
- Book ingestion and processing
- Domain-specific chunking
- Semantic search and RAG queries
- Collection management and manifest tracking
- Calibre database integration

**Why Separate from GUI?**
- **CLI support:** Can be called from command line
- **AI agent support:** Agents call functions directly
- **Testing:** Unit tests without GUI overhead
- **Single source of truth:** One implementation for all interfaces

**Internal Components:** See [Component Diagram](03-component.md)

**Related ADR:** [ADR 0003: GUI as Thin Layer](../decisions/0003-gui-as-thin-layer.md)

---

### 3. File System (Storage)
**Technology:** Local disk (Windows file system)
**Purpose:** Book storage and logging

**Directory Structure:**
```
Alexandria/
├── ingest/         # Books waiting to be processed
├── ingested/       # Successfully processed books (archive)
└── logs/           # Manifest JSON/CSV files
```

**What's Stored:**
- **Books:** EPUB, PDF, TXT, MD files
- **Manifests:** Per-collection JSON manifests
- **Progress:** Batch ingestion resume files
- **Exports:** CSV exports of manifests

**Related Story:** [06-COLLECTION_MANAGEMENT.md](../../stories/06-COLLECTION_MANAGEMENT.md)

---

### 4. Calibre Database (SQLite)
**Technology:** SQLite (metadata.db)
**Purpose:** Book metadata storage

**Location:** Calibre library folder (typically `Documents/Calibre Library`)

**Schema (relevant tables):**
- `books` - Book records (id, title, sort, timestamp)
- `authors` - Author names
- `data` - File paths and formats
- `comments` - Descriptions
- `identifiers` - ISBN, etc.
- `languages` - Language codes
- `tags` - User-defined tags
- `series` - Series information

**Access Pattern:** Read-only via direct SQLite queries (no Calibre API)

**Related Story:** [05-CALIBRE_INTEGRATION.md](../../stories/05-CALIBRE_INTEGRATION.md)

---

## Container Interactions

### Ingestion Flow
```
GUI → Scripts Package → File System (read book)
Scripts Package → Calibre DB (get metadata)
Scripts Package → Qdrant (upload chunks)
Scripts Package → File System (write manifest)
```

### Query Flow
```
GUI → Scripts Package → Qdrant (search)
Scripts Package → OpenRouter (generate answer)
Scripts Package → GUI (return result)
```

### Browse Flow
```
GUI → Scripts Package → Calibre DB (query books)
Scripts Package → GUI (return book list)
```

---

## Technology Choices

### Why Streamlit?
- **Rapid development:** Professional UI in ~500 LOC
- **Python native:** No separate frontend framework
- **Interactive widgets:** Built-in session state management
- **Deployment:** Easy to share via cloud or localhost

### Why Python Scripts Package?
- **Single language:** Python for everything (no polyglot complexity)
- **Rich ecosystem:** sentence-transformers, qdrant-client, ebooklib
- **AI-friendly:** Easy for AI agents to read and modify
- **XAF parallel:** Similar to WBF2's module architecture (business logic separate from UI)

### Why SQLite for Calibre?
- **No dependencies:** Direct file access (no Calibre server needed)
- **Fast:** Indexed queries return 9,000 books in <2 seconds
- **Standard:** Calibre uses SQLite for all metadata

---

## Deployment Model

### Current: Single-User Desktop
```
[User's PC]
  ├── Alexandria (Python scripts + GUI)
  ├── Calibre Library (SQLite)
  └── Docker Desktop
        └── Qdrant (vector DB)
```

### Future: NAS Deployment (Docker)
```
[NAS - 192.168.0.151]
  ├── Docker: Alexandria Container (GUI + Scripts)
  │   ├── Port: 8501 (Streamlit)
  │   ├── Volume: /nas/books → /app/ingest
  │   ├── Volume: /nas/calibre → /app/calibre
  │   └── Secrets: .streamlit/secrets.toml
  ├── Docker: Qdrant (already running)
  │   └── Port: 6333
  ├── Calibre Library (metadata.db)
  └── Book Storage (EPUB/PDF files)
```

**Benefits:**
- Always-on access (24/7 availability)
- Multi-device support (phone, tablet, desktop)
- Centralized storage with RAID backup
- Low latency to Qdrant (same host)

**Deployment:**
```dockerfile
FROM python:3.14
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "alexandria_app.py", \
     "--server.address", "0.0.0.0"]
```

**When to Deploy:**
- GUI stable (no frequent code changes)
- Daily usage pattern established
- Need multi-device access

**Status:** Planned (see [TODO.md - Backlog #6](../../../TODO.md))

### Future: Multi-User Server (Cloud - Alternative)
```
[Web Server]
  ├── Alexandria GUI (Streamlit Cloud)
  └── Alexandria Scripts (Python backend)

[Vector Server]
  └── Qdrant (cloud or self-hosted)

[LLM API]
  └── OpenRouter (cloud)
```

**Note:** NAS deployment preferred over cloud for privacy and cost.

---

## Security Considerations

### Current Security Posture
- **Qdrant:** No authentication (local network 192.168.0.151:6333)
- **OpenRouter:** API key in `.streamlit/secrets.toml` (gitignored)
- **Calibre DB:** Read-only access (no writes)
- **File System:** Local user permissions

### Future Hardening (if multi-user)
- Qdrant authentication
- User authentication in GUI
- Role-based access control
- API rate limiting

---

## Related Views

- **Previous Level:** [System Context](01-context.md)
- **Next Level:** [Component Diagram](03-component.md)
- **Related ADR:** [ADR 0003: GUI as Thin Layer](../decisions/0003-gui-as-thin-layer.md)

---

**Last Updated:** 2026-01-23
