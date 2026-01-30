# C4 Level 2: Container Diagram

**Purpose:** Shows the major architectural components (containers) inside Alexandria RAG System and how they interact.

**Updated:** 2026-01-30 (MCP-first architecture)

---

## Diagram

View interactively: http://localhost:8081 → "Containers" view

Or see `workspace.dsl` container definitions.

---

## Containers

### 1. MCP Server (Primary Interface)
**Technology:** Python 3.14, FastMCP
**Purpose:** Primary interface for Claude Code and MCP clients

**Responsibilities:**
- Expose query tools (alexandria_query, alexandria_search, etc.)
- Expose ingest tools (alexandria_ingest, alexandria_batch_ingest, etc.)
- Provide collection statistics and book details
- Handle progress tracking for long operations

**Key Features:**
- stdio protocol for MCP communication
- Structured JSON responses
- Context modes (precise, contextual, comprehensive)
- Configurable chunking parameters

**Architecture Principle:** **MCP-first design** - MCP Server is the primary interface, all business logic in scripts package.

**Related ADR:** [ADR 0003: GUI as Thin Layer](../decisions/0003-gui-as-thin-layer.md) (Superseded)

---

### 2. Scripts Package (Python Modules)
**Technology:** Python 3.14
**Purpose:** Core business logic for all operations

**Responsibilities:**
- Book ingestion and processing (hierarchical chunking)
- Universal semantic chunking
- Semantic search with context modes
- Collection management and manifest tracking
- Calibre database integration

**Why Separate Package?**
- **MCP support:** Called by MCP Server
- **CLI support:** Can be called from command line
- **Testing:** Unit tests without interface overhead
- **Single source of truth:** One implementation for all interfaces

**Internal Components:** See [Component Diagram](03-component.md)

**Related ADR:** [ADR 0003: MCP-First Architecture](../decisions/0003-gui-as-thin-layer.md) (Superseded)

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

**Related Story:** [06-COLLECTION_MANAGEMENT.md](../../../explanation/stories/06-COLLECTION_MANAGEMENT.md)

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

**Related Story:** [05-CALIBRE_INTEGRATION.md](../../../explanation/stories/05-CALIBRE_INTEGRATION.md)

---

## Container Interactions

### Ingestion Flow
```
Claude Code → MCP Server → Scripts Package → File System (read book)
Scripts Package → Calibre DB (get metadata)
Scripts Package → Qdrant (upload parent + child chunks)
Scripts Package → File System (write manifest)
```

### Query Flow
```
Claude Code → MCP Server → Scripts Package → Qdrant (search children)
Scripts Package → Qdrant (fetch parent context)
Scripts Package → OpenRouter (generate answer - optional)
MCP Server → Claude Code (return RAGResult)
```

### Search Flow
```
Claude Code → MCP Server → Scripts Package → Calibre DB (query books)
MCP Server → Claude Code (return book list)
```

---

## Technology Choices

### Why MCP Server?
- **Claude Code integration:** Direct access from Claude Code terminal
- **Structured protocol:** Model Context Protocol (stdio)
- **No UI maintenance:** Focus on business logic, not UI development
- **AI-native:** Designed for AI agent workflows

### Why Python Scripts Package?
- **Single language:** Python for everything (no polyglot complexity)
- **Rich ecosystem:** sentence-transformers, qdrant-client, ebooklib
- **AI-friendly:** Easy for AI agents to read and modify
- **Testable:** Unit tests without interface overhead

### Why SQLite for Calibre?
- **No dependencies:** Direct file access (no Calibre server needed)
- **Fast:** Indexed queries return 9,000 books in <2 seconds
- **Standard:** Calibre uses SQLite for all metadata

---

## Deployment Model

### Current: MCP Server + Claude Code
```
[User's PC]
  ├── Claude Code (MCP Client)
  │   └── .mcp.json (configuration)
  ├── Alexandria MCP Server (scripts/mcp_server.py)
  ├── Calibre Library (SQLite - G:\My Drive\alexandria)
  └── External Qdrant Server (192.168.0.151:6333)
```

### Future: NAS Deployment
```
[NAS - 192.168.0.151]
  ├── Alexandria MCP Server
  │   └── Accessible via SSH or remote MCP
  ├── Docker: Qdrant (already running)
  │   └── Port: 6333
  ├── Calibre Library (metadata.db)
  └── Book Storage (EPUB/PDF files)
```

**Benefits:**
- Always-on access (24/7 availability)
- Centralized storage with RAID backup
- Low latency to Qdrant (same host)
- Multi-machine access via remote MCP

---

## Security Considerations

### Current Security Posture
- **MCP Server:** stdio protocol (local only, no network exposure)
- **Qdrant:** No authentication (local network 192.168.0.151:6333)
- **OpenRouter:** API key in environment variable (optional)
- **Calibre DB:** Read-only access (no writes)
- **File System:** Local user permissions

### Future Hardening (if multi-user)
- Qdrant authentication
- Remote MCP authentication
- API rate limiting

---

## Related Views

- **Previous Level:** [System Context](01-context.md)
- **Next Level:** [Component Diagram](03-component.md)
- **Related ADR:** [ADR 0003: MCP-First Architecture](../decisions/0003-gui-as-thin-layer.md) (Superseded)

---

**Last Updated:** 2026-01-30 (MCP-first architecture)
