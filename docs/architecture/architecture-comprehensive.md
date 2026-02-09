---
stepsCompleted: [1, 2, 3, 5, 8]
inputDocuments: ['docs/project-context.md', 'scripts/*.py (via exploration)', 'docs/architecture/README.md', 'docs/architecture/decisions/*.md (11 ADRs)']
workflowType: 'architecture'
project_name: 'Alexandria'
user_name: 'Sabo'
date: '2026-01-31'
completedAt: '2026-01-31'
status: 'complete'
location: 'docs/architecture/architecture-comprehensive.md (moved from docs/development/ideas/ - brownfield adaptation)'
skippedSteps: [4, 6, 7]
skippedReason: 'Brownfield adaptation - Step 4 (Decisions) covered by 11 ADRs, Step 6 (Structure) already exists in scripts/, Step 7 (Validation) trivial for brownfield'
---

# Architecture Comprehensive Document

> **Note:** This document was created via BMAD Architecture Workflow but moved to `docs/architecture/` (instead of `docs/development/ideas/`) because Alexandria is a **brownfield project** documenting existing architecture, not a greenfield project planning new architecture. For greenfield projects, this would remain in `docs/development/ideas/`.

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

---

## Project Context Analysis

### Overview

Alexandria is a **Retrieval-Augmented Generation (RAG) system** for semantic search across book collections. Originally conceived as a personal tool for searching a 9,000-book Calibre library, the architecture has evolved to support **multi-consumer service model** with phased growth potential (personal → invite-only → public beta → full SaaS).

**Current Status:**
- **Phase:** Phase 1 (Personal Tool with Showcase-Ready Architecture)
- **Scale:** 150 books ingested, ~23,000 chunks in Qdrant
- **Target:** 9,000 books, ~1.35M chunks (~2-6GB vectors depending on model)
- **Hardware:** GPU-accelerated (Dell: 80GB RAM, 12GB VRAM, 4TB NVMe)

### Functional Requirements (From Existing Implementation)

**Core Capabilities:**

1. **Semantic Book Search (FR-001)**
   - Vector similarity search using embeddings
   - Context modes: precise/contextual/comprehensive
   - Optional LLM answer generation (OpenRouter API)
   - **Multi-model support:** Runtime model selection per collection
     - all-MiniLM-L6-v2 (384-dim) - lightweight, CPU-friendly
     - BAAI/bge-large-en-v1.5 (1024-dim) - high quality, GPU-accelerated
     - BAAI/bge-m3 (1024-dim) - multilingual (100+ languages), GPU-accelerated **(default)**
   - Collection metadata tracks which model was used for ingestion

2. **Hierarchical Chunking (FR-002)**
   - Parent chunks: Full chapters (detected via EPUB/PDF structure)
   - Child chunks: Semantic segments (topic boundary detection)
   - Universal semantic chunker (threshold-based, ADR-0007)

3. **Multi-Format Ingestion (FR-003)**
   - EPUB, PDF, TXT, MD, HTML support
   - Calibre metadata enrichment (author, title, tags, series)
   - Local file ingestion (no Calibre required)
   - Configurable chunking parameters (threshold, min/max size)

4. **Collection Management (FR-004)**
   - Isolated collections per use case (ADR-0006)
   - Collection-specific manifests (JSON + CSV tracking)
   - Per-collection settings and quotas

5. **Multi-Consumer Service (FR-005)** - ADR-0008
   - **Tier 1 (MCP):** stdio protocol for Claude Code - PRIMARY
   - **Tier 2 (HTTP):** REST API for web/mobile clients - SECONDARY
   - **Tier 3 (Python lib):** Direct import from scripts/ - INTERNAL

### Non-Functional Requirements

**Performance (NFR-001):**
- Ingestion: ~11-13 sec/book (CPU), **~0.3 sec/book (GPU with bge-m3)** - ADR-0010
- Query: <100ms (search only), 0.15-5.5 sec (with LLM)
- Target scale: 1.35M chunks, ~6GB vectors (bge-m3, 1024-dim)

**Immutability Constraints (NFR-002):** - CRITICAL
- Embedding model locked per collection (changing = full re-ingestion)
- Distance metric: COSINE (changing = collection recreation)
- **Multi-model coexistence:** Different collections can use different models
- Query must use same model as collection's ingestion model

**Reliability (NFR-003):**
- Graceful degradation (works without LLM, without Calibre)
- Collection isolation prevents cross-contamination
- Manifest tracking for data integrity
- Health checks for external dependencies

**Maintainability (NFR-004):**
- Single source of truth: scripts/ package (ADR-0003)
- Thin presentation layers (MCP, GUI, HTTP)
- No business logic in interfaces
- Comprehensive documentation (ADRs, C4 diagrams, API docs)

**Scalability (NFR-005):**
- Current: 150 books, ~23K chunks
- Target: 9,000 books, ~1.35M chunks
- Qdrant handles billions of vectors (significant headroom)
- GPU acceleration enables fast batch processing

**Multi-Tenancy (NFR-006)** - Phased Evolution (ADR-0011)
- **Phase 1 (Current):** Single user, multi-tenant architecture ready
- **Phase 2 (Optional):** Invite-only beta (5-10 users)
- **Phase 3 (Future):** Public beta with legal compliance
- **Phase 4 (Whale):** Full SaaS with enterprise features

### Scale & Complexity Assessment

**Project Complexity:** MEDIUM-HIGH

**Complexity Indicators:**
- ✅ Production system with real data (150 books ingested, expanding to 9,000)
- ✅ External dependencies (Qdrant, Calibre, OpenRouter)
- ✅ Multi-format parsing (EPUB/PDF structural complexity)
- ✅ ML/embedding pipeline (sentence-transformers, PyTorch, GPU)
- ✅ Multi-consumer architecture (MCP, HTTP, Python lib)
- ✅ Hierarchical data model (parent/child chunks, collections)
- ✅ Phased growth potential (personal → SaaS evolution path)
- ⚠️ No authentication yet (planned for Phase 2+)
- ⚠️ No distributed deployment yet (NAS planned, Kubernetes for Phase 4)

**Primary Technical Domain:** RAG (Retrieval-Augmented Generation) Knowledge Service

**Cross-Cutting Concerns:**
- **Logging:** Mandatory structured logging (logger.*, no print statements)
- **Error handling:** Connection validation, graceful degradation, fallback strategies
- **Path normalization:** Windows long paths (>248 chars via `\\?\` prefix)
- **Progress tracking:** Currently disabled (tqdm), needs callback pattern refactor
- **Testing:** Low coverage (~4%), comprehensive roadmap exists
- **GPU management:** Auto-detect CUDA, CPU fallback for portability
- **Multi-machine support:** GPU ingestion (Dell), CPU query (Asus laptop)

### Technical Constraints & Dependencies

**Hard Constraints (Cannot Change Without Migration):**

1. **Embedding Models (ADR-0010):**
   - **Supported:** all-MiniLM-L6-v2 (384-dim), BAAI/bge-large-en-v1.5 (1024-dim), BAAI/bge-m3 (1024-dim)
   - **Default:** bge-m3 (multilingual, 100+ languages, GPU-accelerated — ADR-0012: original language primary)
   - **Constraint:** Model locked per collection at ingestion time
   - **Runtime selection:** Query uses collection's model automatically
   - **Model registry:** Configurable via EMBEDDING_MODELS in config.py

2. **Distance Metric:** COSINE
   - Hardcoded across ingestion and query
   - Changing requires collection recreation

3. **Python Version:** 3.14+

4. **Qdrant Server:** External (192.168.0.151:6333)
   - Currently external to codebase
   - NAS deployment planned (Docker)

5. **Calibre Library:** SQLite metadata.db
   - External metadata source
   - Optional (local file ingestion also supported)

**Soft Constraints (Configurable):**
- Chunking parameters (threshold, min/max size)
- Collection names and quotas
- OpenRouter API (optional, for LLM answers)
- Deployment topology (local, NAS, Docker, Kubernetes)
- Authentication method (API keys, OAuth2, SSO)

**External Dependencies:**

**Core:**
- Qdrant ≥1.7.1 (vector database)
- sentence-transformers ≥2.3.1 (embeddings)
- PyTorch ≥2.0.0 (ML framework, CUDA-enabled for GPU)
- FastMCP ≥2.0.0 (MCP protocol)

**Integrations:**
- Calibre (book metadata, optional)
- OpenRouter API (optional LLM inference)

**Future (Phased):**
- FastAPI (HTTP API, Phase 1)
- SQLite/PostgreSQL (user management, Phase 2+)
- Stripe (payments, Phase 3+)
- Email service (SendGrid/SES, Phase 3+)

### Architectural Implications

**Strengths:**
- ✅ Clean separation: MCP-first, thin layers (ADR-0003)
- ✅ Collection isolation prevents consumer conflicts (ADR-0006)
- ✅ Semantic chunking preserves coherence (ADR-0007)
- ✅ Service-oriented mindset (ADR-0008)
- ✅ GPU-accelerated for performance (ADR-0010)
- ✅ Phased growth path documented (ADR-0011)
- ✅ 11 ADRs document critical decisions
- ✅ Comprehensive existing architecture docs (C4 diagrams, technical specs)

**Gaps Addressed:**
- ✅ Multi-consumer model formalized (ADR-0008)
- ✅ HTTP API blueprint ready (ADR-0009)
- ✅ GPU embedding strategy (ADR-0010)
- ✅ Growth roadmap (ADR-0011)

**Future Considerations (Phased):**
- **Phase 2:** User accounts, private collections, invite system
- **Phase 3:** Public beta (legal compliance, DMCA, public domain collection)
- **Phase 4:** Enterprise features (SSO, teams, admin dashboard, support)

### Architectural Components (Estimated)

**Current (Phase 1):**
1. **MCP Server Layer** (stdio protocol)
2. **HTTP API Layer** (planned, ADR-0009)
3. **Business Logic Layer** (scripts/ package - 7 core modules)
4. **External Systems Integration** (Qdrant, Calibre, OpenRouter)
5. **Data Layer** (Qdrant collections, manifests)

**Future (Phased Growth):**
- User Management (Phase 2+)
- Payment Integration (Phase 3+)
- Admin Dashboard (Phase 3+)
- Enterprise Features (Phase 4)

### Known Issues & Technical Debt

From `docs/project-context.md` (45 rules):

1. ⚠️ **Interactive chunking GUI - LOST CODE**
   - CLI tool exists: `experiment_chunking.py`
   - GUI version code not saved during refactor

2. ⚠️ **Universal chunking parameters hardcoded**
   - Should be configurable via Settings
   - Currently requires code changes

3. ⚠️ **Calibre library path regression**
   - Was GUI-configurable, now hardcoded
   - Need to restore Settings sidebar

4. ⚠️ **tqdm progress bars disabled globally**
   - Workaround for Streamlit stderr issues
   - May be obsolete, needs review
   - Proposed: Callback pattern (ADR-0011 discussion)

5. ⚠️ **Qdrant server location hardcoded**
   - Should be configurable via Settings
   - Currently: 192.168.0.151:6333

6. ⚠️ **Test coverage low (~4%)**
   - Comprehensive roadmap exists
   - Critical gaps: mcp_server.py, rag_query.py, ingest_books.py

---

**Summary:** Alexandria is a production-ready RAG system with strong architectural foundations (11 ADRs, comprehensive docs, clean separation of concerns) and a documented phased growth path from personal tool to potential SaaS. Current focus is Phase 1 (personal tool with showcase-ready architecture), with clear evolution path documented for future phases.

## Technology Stack Analysis

> **Brownfield Adaptation:** This section documents the existing technology stack rather than evaluating starter templates (which applies to greenfield projects).

### Primary Technology Domain

**RAG (Retrieval-Augmented Generation) Knowledge Service** - Python-based ML/AI system for semantic search across book collections.

### Existing Technology Stack (Rationale)

**Core Runtime & Language:**
- **Python 3.14+**
- **Rationale:** Best-in-class ML/AI ecosystem, GPU acceleration support (PyTorch/CUDA), rapid prototyping, extensive libraries for embeddings and vector operations

**Primary Interface:**
- **FastMCP ≥2.0.0** (Model Context Protocol)
- **Rationale:** Direct Claude Code integration (stdio transport), tool-based API, primary use case for personal RAG queries

**Secondary Interface (Planned - ADR-0009):**
- **FastAPI** (HTTP REST API)
- **Rationale:** Modern async framework, auto-generated OpenAPI docs, type hints, supports multi-consumer model (web/mobile clients)

**ML/Embeddings:**
- **sentence-transformers ≥2.3.1** + **PyTorch ≥2.0.0** (CUDA-enabled)
- **huggingface_hub[hf_xet]** (optional) - Xet protocol for faster model downloads
- **Models (multi-model registry):**
  - all-MiniLM-L6-v2 (384-dim) - lightweight, fast, CPU-friendly
  - BAAI/bge-large-en-v1.5 (1024-dim) - high quality, English-only, GPU-accelerated
  - BAAI/bge-m3 (1024-dim) - multilingual (100+ languages), GPU-accelerated **(default)**
- **Rationale:** Runtime model selection enables A/B testing, gradual migration, and hardware-appropriate choices. Default changed to bge-m3 for multilingual support (ADR-0012: original language primary — preserves semantic fingerprints across languages). GPU acceleration for bge-m3 (3-4h for 9K books vs 50-63h CPU), local/free (no API costs). Xet protocol enables chunked parallel downloads with resume capability for large models (1GB+).

**Vector Database:**
- **Qdrant ≥1.7.1** (self-hosted)
- **Rationale:** No vendor lock-in, data privacy, zero recurring costs, handles billions of vectors, Python client, COSINE distance support

**Book Parsing:**
- **EbookLib 0.18** (EPUB), **PyMuPDF ≥1.24.0** (PDF), **BeautifulSoup4 + lxml** (HTML/XML)
- **Rationale:** Multi-format support required for 9K book library, robust parsing, metadata extraction

**Metadata Source:**
- **Calibre** (SQLite metadata.db)
- **Rationale:** Existing 9K book library already in Calibre, rich metadata (author, tags, series, ISBN), optional (local file ingestion also supported)

**Optional Services:**
- **OpenRouter API** (LLM inference for answer generation/reranking)
- **Rationale:** Cost-effective ($0.02-$0.10 per 1M tokens), multiple models available, pay-per-use, optional (search works without it)

### Architectural Patterns Established

**Service Architecture:**
- MCP-first (ADR-0003) - Primary interface
- Thin presentation layers (no business logic in interfaces)
- scripts/ package as single source of truth
- Multi-consumer ready (ADR-0008) - MCP, HTTP, Python lib tiers

**Multi-Tenancy & Isolation:**
- Collection-based isolation (ADR-0006)
- Per-collection manifests and settings
- Prepared for phased growth (ADR-0011) - personal → invite-only → public → SaaS

**GPU Acceleration:**
- Auto-detect CUDA (GPU when available, CPU fallback)
- Hardware-agnostic queries (fast on both)
- Ingestion optimized for GPU batch processing (ADR-0010)

**Phased Evolution:**
- Phase 1 (Current): Personal tool with showcase-ready architecture
- Phase 2-4 (Optional): Documented growth path to full SaaS

### Development Experience & Tooling

**Code Quality:**
- **black 23.12.1** (formatter), **flake8 7.0.0** (linter)
- **Rationale:** Consistent style, enforced via CI (planned)

**Testing:**
- **pytest 7.4.3** + **pytest-cov** (unit/integration)
- **Rationale:** Standard Python testing, coverage tracking, ~4% coverage (roadmap exists to improve)

**Deployment:**
- **Docker + Docker Compose**
- **Rationale:** Reproducible environments, easy showcase deployment, NAS deployment ready

**Documentation:**
- **11 ADRs** (Architecture Decision Records)
- **C4 diagrams** (Context, Container, Component levels)
- **Swagger/OpenAPI** (auto-generated from FastAPI)
- **Rationale:** Comprehensive docs prevent "dev team playing drums on their own" 😂

### Architectural Decisions Made by Existing Stack

✅ **Language:** Python (ML/AI ecosystem dominance)  
✅ **Primary Interface:** MCP stdio (Claude Code integration)  
✅ **Secondary Interface:** HTTP REST (web/mobile consumers)  
✅ **Vector DB:** Qdrant self-hosted (no vendor lock-in)  
✅ **Embeddings:** Local GPU-accelerated (no API bills)  
✅ **Testing:** pytest (Python standard)  
✅ **Deployment:** Docker (portable, reproducible)  
✅ **Multi-tenancy:** Collection isolation (growth-ready)

### What the Stack Enables (Without Rebuilding)

**Current Capabilities:**
- ✅ GPU-accelerated ingestion (3-4h for 9K books)
- ✅ Fast queries on any hardware (150ms CPU, 60ms GPU)
- ✅ Multi-format book support (EPUB, PDF, TXT, MD, HTML)
- ✅ MCP integration (Claude Code primary interface)
- ✅ Optional LLM answers (OpenRouter API)

**Future-Ready:**
- ✅ HTTP API (FastAPI, ADR-0009)
- ✅ Multi-user (collection isolation, ADR-0006)
- ✅ User uploads (private collections)
- ✅ Phased growth path (ADR-0011)

### Rejected Alternatives

**API-Based Embeddings (OpenAI, Voyage):**
- ❌ Rejected: Ongoing costs ($0.02-$0.10 per 1M tokens), vendor lock-in, privacy concerns, network latency
- ✅ Chosen: Local GPU embeddings (zero cost, private, fast)

**Cloud Vector DB (Pinecone, Qdrant Cloud):**
- ❌ Rejected: Vendor lock-in, recurring costs, tier reductions (Pinecone 1M → 100K free tier)
- ✅ Chosen: Self-hosted Qdrant (full control, zero cost, privacy)

**Single Embedding Model (one-size-fits-all):**
- ❌ Rejected: No flexibility for A/B testing, hardware constraints, gradual migration
- ✅ Chosen: Multi-model registry with runtime selection
  - Default: bge-m3 (multilingual, GPU-accelerated — ADR-0012)
  - Alternative: bge-large-en-v1.5 (English-only, high quality, GPU-accelerated)
  - Fallback: all-MiniLM-L6-v2 (lightweight, CPU-friendly, comparison baseline)

---

**Summary:** Alexandria's technology stack is optimized for ML/AI workloads with GPU acceleration, self-hosted infrastructure (zero recurring costs), and multi-consumer service model. The stack enables phased growth from personal tool to potential SaaS without architectural rewrites. All major decisions are documented in 11 ADRs with clear rationale.

## Implementation Patterns & Consistency Rules

> **Brownfield Adaptation:** This section documents existing coding patterns and conventions established in the scripts/ package to ensure consistent implementation by all developers and AI agents.

**Purpose:** Prevent "dev team playing drums on their own" by formalizing established patterns that ensure code consistency, maintainability, and compatibility across all modules.

### Pattern Categories Overview

Alexandria has **18 potential conflict points** where AI agents or developers could make different choices without explicit guidance. These patterns eliminate ambiguity and ensure consistent implementation.

---

### Naming Patterns

#### Function and Variable Naming

**Convention:** `snake_case` for all functions, variables, and module-level constants (except UPPERCASE constants)

**Examples (Established):**
```python
# Functions
def normalize_file_path(file_path: str) -> str:
def validate_file_access(file_path: str) -> Tuple[bool, Optional[str]]:
def extract_from_ncx(content_opf_path: Path) -> List[Chapter]:
def generate_embeddings(texts: List[str], batch_size: int = 32) -> np.ndarray:
def perform_rag_query(query: str, collection_name: str, limit: int = 5) -> RAGResult:

# Variables
EMBEDDING_MODELS = {
    "minilm": {"name": "all-MiniLM-L6-v2", "dim": 384},
    "bge-large": {"name": "BAAI/bge-large-en-v1.5", "dim": 1024},
    "bge-m3": {"name": "BAAI/bge-m3", "dim": 1024},
}
DEFAULT_EMBEDDING_MODEL = "bge-m3"
qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
calibre_db_instance = None
chapter_list = []
```

**Anti-Patterns (Never Use):**
```python
# ❌ camelCase
def normalizeFilePath(filePath: str) -> str:
def validateFileAccess(filePath: str):

# ❌ PascalCase for functions
def NormalizeFilePath(file_path: str) -> str:
```

---

#### Class Naming

**Convention:** `PascalCase` for all classes, with dataclasses strongly preferred for data structures

**Examples (Established):**
```python
# Classes
class CalibreBook:
class CalibreDB:
class Chapter:
class UniversalChunker:
class EmbeddingGenerator:
class CollectionManifest:
class RAGResult:

# Dataclasses (preferred)
@dataclass
class CalibreBook:
    id: int
    title: str
    author: str
    path: str

    def __repr__(self):
        return f"<CalibreBook: {self.title} by {self.author}>"

@dataclass
class RAGResult:
    query: str
    results: List[Dict[str, Any]]
    answer: Optional[str] = None

    @property
    def sources(self) -> List[Dict[str, Any]]:
        return self.results
```

---

#### Module Naming

**Convention:** Descriptive, lowercase names with underscores indicating purpose

**Examples (Established):**
```python
# Core modules
config.py                  # Configuration management
calibre_db.py             # Calibre database access
qdrant_utils.py           # Qdrant vector DB operations
collection_manifest.py    # Manifest management
chapter_detection.py      # Chapter/section detection
universal_chunking.py     # Semantic chunking
html_sanitizer.py         # HTML cleaning
rag_query.py              # RAG query pipeline
ingest_books.py           # Book ingestion orchestration
mcp_server.py             # MCP protocol server
```

**Anti-Patterns (Never Use):**
```python
# ❌ camelCase modules
calibreDb.py
qdrantUtils.py

# ❌ Vague names
utils.py                  # Too generic - what utils?
helpers.py                # Too generic - what helpers?
```

---

#### Constants

**Convention:** `UPPERCASE` for module-level constants, grouped at top of module

**Examples (Established):**
```python
# Configuration constants
QDRANT_HOST = os.environ.get('QDRANT_HOST', '192.168.0.151')
QDRANT_PORT = int(os.environ.get('QDRANT_PORT', '6333'))
CALIBRE_LIBRARY_PATH = os.environ.get('CALIBRE_LIBRARY_PATH', r'G:\My Drive\alexandria')

# Security constants
DANGEROUS_TAGS = {"script", "iframe", "object", "embed", "link", "style"}
DANGEROUS_ATTRIBUTES = {"onclick", "onerror", "onload", "href"}

# Model constants
DEFAULT_EMBEDDING_MODEL = "bge-m3"
EMBEDDING_DIMENSIONS = 1024
```

---

### Code Structure Patterns

#### Section Organization

**Convention:** Use comment headers to demarcate logical sections within modules

**Format:**
```python
# ============================================================================
# SECTION NAME (ALL CAPS)
# ============================================================================

# Functions and classes for this section...
```

**Examples (Established):**
```python
# From ingest_books.py
# ============================================================================
# TEXT EXTRACTION
# ============================================================================

def extract_text_from_epub(file_path: Path) -> Tuple[str, Dict]:
    """Extract text from EPUB file."""
    ...

def extract_text_from_pdf(file_path: Path) -> Tuple[str, Dict]:
    """Extract text from PDF file."""
    ...

# ============================================================================
# CHUNKING
# ============================================================================

def chunk_text_semantically(text: str, threshold: float = 0.5) -> List[str]:
    """Chunk text using semantic boundary detection."""
    ...
```

**Benefits:**
- Clear visual separation
- Easy navigation in large files
- Consistent code organization

---

#### Module Organization

**Convention:** Organize modules by responsibility, with clear boundaries

**Established Pattern:**
```
scripts/
├── config.py                 # Single source of truth for configuration
├── calibre_db.py            # Database access only
├── qdrant_utils.py          # Vector DB operations only
├── collection_manifest.py   # Manifest management only
├── chapter_detection.py     # Chapter detection algorithms only
├── universal_chunking.py    # Chunking strategies only
├── html_sanitizer.py        # HTML cleaning only
├── rag_query.py             # RAG query pipeline orchestration
├── ingest_books.py          # Book ingestion orchestration
└── mcp_server.py            # MCP protocol server (thin layer)
```

**Principles:**
- **Single Responsibility:** Each module has one clear purpose
- **No Cross-Cutting Logic:** Business logic stays in scripts/, presentation stays in interfaces
- **Configuration Centralization:** All config in config.py, imported by other modules
- **Thin Layers:** MCP server, HTTP API, GUI are thin wrappers around scripts/ (ADR-0003)

---

### Error Handling Patterns

#### Tuple Return Pattern (Success Flag)

**Convention:** Functions that can fail return `Tuple[bool, Optional[str]]` or `Tuple[ReturnType, Optional[str]]`

**Examples (Established):**
```python
def check_qdrant_connection(host: str, port: int, timeout: int = 5) -> Tuple[bool, Optional[str]]:
    """
    Check if Qdrant server is reachable.

    Returns:
        Tuple of (is_connected, error_message):
            - (True, None) if connection successful
            - (False, error_msg) if connection failed with helpful debugging hints
    """
    try:
        response = requests.get(f"http://{host}:{port}/health", timeout=timeout)
        if response.status_code == 200:
            return True, None
        else:
            return False, f"Qdrant server returned status {response.status_code}"
    except (ConnectionError, TimeoutError, requests.exceptions.ConnectionError) as e:
        error_msg = f"""
❌ Cannot connect to Qdrant server at {host}:{port}

Possible causes:
  1. VPN not connected
  2. Firewall blocking port {port}
  3. Qdrant server not running

Connection error: {str(e)}
"""
        return False, error_msg
```

**Usage:**
```python
connected, error = check_qdrant_connection(QDRANT_HOST, QDRANT_PORT)
if not connected:
    logger.error(error)
    return
```

**Benefits:**
- Explicit success/failure handling
- Rich error messages with debugging hints
- No exception bubbling for expected failures
- Caller controls error handling

---

#### Exception Handling Pattern

**Convention:** Catch specific exceptions, provide helpful error messages

**Examples (Established):**
```python
# Specific exceptions
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
except FileNotFoundError as e:
    logger.error(f"File not found: {file_path}")
    raise
except PermissionError as e:
    logger.error(f"Permission denied: {file_path}")
    raise
except UnicodeDecodeError as e:
    logger.warning(f"Encoding issue in {file_path}, trying latin-1")
    with open(file_path, 'r', encoding='latin-1') as f:
        content = f.read()

# Multiple exception types
try:
    response = requests.get(url, timeout=10)
except (ConnectionError, TimeoutError, requests.exceptions.ConnectionError) as e:
    logger.error(f"Network error: {e}")
    return None
```

**Anti-Patterns (Never Use):**
```python
# ❌ Bare except
try:
    risky_operation()
except:
    pass

# ❌ Too broad exception
try:
    risky_operation()
except Exception as e:
    pass

# ❌ Silent failures
try:
    risky_operation()
except FileNotFoundError:
    pass  # Should at least log
```

---

#### Multi-Line Error Messages

**Convention:** Use multi-line strings with emoji indicators and debugging hints

**Template:**
```python
error_msg = f"""
❌ [ERROR CATEGORY]

Problem description: {specific_issue}

Possible causes:
  1. First common cause
  2. Second common cause
  3. Third common cause

Technical details: {technical_info}

Suggested action: What to try next
"""
```

**Examples (Established):**
```python
# From qdrant_utils.py
error_msg = f"""
❌ Cannot connect to Qdrant server at {host}:{port}

Possible causes:
  1. VPN not connected
  2. Firewall blocking port {port}
  3. Qdrant server not running

Connection error: {str(e)}
"""

# From calibre_db.py
error_msg = f"""
❌ Cannot open Calibre database at {db_path}

Possible causes:
  1. Database file doesn't exist
  2. File is corrupted
  3. Wrong Calibre library path

Error: {str(e)}

Check CALIBRE_LIBRARY_PATH in .env file.
"""
```

---

### Logging Patterns

#### Logger Setup (Standard Pattern)

**Convention:** Each module creates its own logger using `__name__`

**Established Pattern:**
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
```

**Environment Variable Control:**
```python
# Optional: Allow environment variable override
log_level_str = os.getenv('ALEXANDRIA_LOG_LEVEL', 'INFO').upper()
log_level = getattr(logging, log_level_str, logging.INFO)
logging.basicConfig(level=log_level, ...)
```

---

#### Logging Levels

**Convention:** Use appropriate levels with structured messages

**Examples (Established):**
```python
# INFO - General progress and status
logger.info(f"[SEARCH] Query: '{query}'")
logger.info(f"[OK] Found {len(results)} results")
logger.info(f"🎯 Loading embedding model: {model_name}")

# WARNING - Potential issues (non-fatal)
logger.warning(f"[WARN] Collection '{collection_name}' not found, using default")
logger.warning(f"⚠️ Low confidence score: {score:.2f}")

# ERROR - Errors that don't stop execution
logger.error(f"[ERROR] Failed to parse EPUB: {file_path}")
logger.error(f"❌ Qdrant connection failed: {error}")

# DEBUG - Detailed diagnostic info
logger.debug(f"[DEBUG] Chunk size: {len(chunk)} chars")
logger.debug(f"[DEBUG] Embedding shape: {embeddings.shape}")
```

**Structured Logging Prefixes:**
- `[SEARCH]` - Search operations
- `[FILTER]` - Filtering operations
- `[BOOK]` - Book processing
- `[OK]` - Success states
- `[WARN]` - Warnings
- `[ERROR]` - Errors

**Emoji Indicators (Optional):**
- `🎯` - Loading/initializing
- `🤖` - AI/ML operations
- `✅` - Success
- `⚠️` - Warning
- `❌` - Error

---

#### NO Print Statements

**Critical Rule:** NEVER use `print()` for logging - ALWAYS use `logger.*`

**Rationale (from project-context.md):**
- Print statements break MCP stdio protocol
- No control over output destination
- No log level filtering
- No structured logging

**Exception:**
- `config.py` has `print_config()` debugging utility
- Only for manual debugging, not production code

**Anti-Patterns (Never Use):**
```python
# ❌ NEVER
print("Processing book...")
print(f"Error: {e}")

# ✅ ALWAYS
logger.info("Processing book...")
logger.error(f"Error: {e}")
```

---

### Documentation Patterns

#### Docstring Style: Google Format

**Convention:** Use Google-style docstrings with Args, Returns, Raises sections

**Template:**
```python
def function_name(param1: Type1, param2: Type2 = default) -> ReturnType:
    """
    Brief description of what the function does (one line).

    Extended description with more details if needed. Can span
    multiple lines and explain complex behavior.

    Args:
        param1: Description of param1
        param2: Description of param2 (default: default_value)

    Returns:
        Description of return value, including structure if complex

    Raises:
        ExceptionType: When this exception is raised

    Example:
        >>> result = function_name("value", 42)
        >>> print(result)
        'expected output'
    """
    ...
```

**Examples (Established):**
```python
def check_qdrant_connection(host: str, port: int, timeout: int = 5) -> Tuple[bool, Optional[str]]:
    """
    Check if Qdrant server is reachable.

    Args:
        host: Qdrant server hostname or IP address
        port: Qdrant server port
        timeout: Connection timeout in seconds (default: 5)

    Returns:
        Tuple of (is_connected, error_message):
            - (True, None) if connection successful
            - (False, error_msg) if connection failed with helpful debugging hints
    """
    ...

def extract_text_from_epub(file_path: Path) -> Tuple[str, Dict]:
    """
    Extract text content from EPUB file.

    Parses EPUB structure using ebooklib, extracts text from all
    content documents, and preserves chapter boundaries.

    Args:
        file_path: Path to EPUB file

    Returns:
        Tuple of (text_content, metadata):
            - text_content: Full extracted text
            - metadata: Dict with 'title', 'author', 'language'

    Raises:
        FileNotFoundError: If EPUB file doesn't exist
        ValueError: If file is not a valid EPUB
    """
    ...
```

---

#### Module-Level Docstrings

**Convention:** Every module starts with a docstring describing its purpose

**Template:**
```python
"""
Module Title
============

Brief description of module purpose.

USAGE
-----
Example usage or integration notes.

Configuration in .env:
    SETTING_NAME=value

NOTES
-----
- Important note 1
- Important note 2
"""
```

**Examples (Established):**
```python
# From mcp_server.py
"""
Alexandria MCP Server
=====================

Model Context Protocol server for the Alexandria RAG system.

USAGE
-----
This server is designed to be used with Claude Code via stdio transport.

Configuration in .mcp.json:
{
  "alexandria": {
    "command": "python",
    "args": ["path/to/mcp_server.py"],
    "env": {
      "QDRANT_HOST": "192.168.0.151",
      "QDRANT_PORT": "6333"
    }
  }
}

ARCHITECTURE
------------
This is a thin presentation layer (ADR-0003) that wraps scripts/ business logic.
All RAG operations delegate to rag_query.py, ingest_books.py, etc.
"""

# From qdrant_utils.py
"""
Qdrant Vector Database Utilities
=================================

Low-level operations for Qdrant vector database interaction.

Provides connection management, collection operations, and
vector search functionality for Alexandria RAG system.

NOTES
-----
- Uses COSINE distance metric (hardcoded, changing requires collection recreation)
- Auto-retries on connection failures
- Provides helpful error messages for VPN/firewall issues
"""
```

---

#### Type Hints (Mandatory)

**Convention:** All functions MUST have complete type hints

**Examples (Established):**
```python
# Function parameters and return type
def generate_embeddings(
    texts: List[str],
    batch_size: int = 32,
    device: str = "cpu"
) -> np.ndarray:
    ...

# Optional return types
def get_book_by_id(book_id: int) -> Optional[CalibreBook]:
    ...

# Tuple returns
def validate_file(file_path: str) -> Tuple[bool, Optional[str]]:
    ...

# Complex types
def process_results(
    results: List[Dict[str, Any]],
    metadata: Dict[str, str]
) -> RAGResult:
    ...

# Union types
def parse_config(value: Union[str, int, float]) -> Any:
    ...
```

**Anti-Patterns (Never Use):**
```python
# ❌ Missing type hints
def process_book(book_id):
    ...

# ❌ Incomplete type hints
def process_book(book_id: int):
    ...  # Missing return type

# ❌ Using Any when specific type is known
def get_books() -> Any:
    ...  # Should be List[CalibreBook]
```

---

### Configuration Patterns

#### Centralized Configuration (config.py)

**Convention:** ALL configuration in `config.py`, imported by other modules

**Pattern:**
```python
# config.py - Single source of truth
import os

# Qdrant Configuration
QDRANT_HOST = os.environ.get('QDRANT_HOST', '192.168.0.151')
QDRANT_PORT = int(os.environ.get('QDRANT_PORT', '6333'))

# Calibre Configuration
CALIBRE_LIBRARY_PATH = os.environ.get('CALIBRE_LIBRARY_PATH', r'G:\My Drive\alexandria')

# Model Configuration
EMBEDDING_MODEL = os.environ.get('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
EMBEDDING_DIMENSIONS = int(os.environ.get('EMBEDDING_DIMENSIONS', '384'))

def get_qdrant_url() -> str:
    """Construct full Qdrant URL from config."""
    return f"http://{QDRANT_HOST}:{QDRANT_PORT}"
```

**Usage in other modules:**
```python
# Other modules import from config
from config import QDRANT_HOST, QDRANT_PORT, CALIBRE_LIBRARY_PATH
from config import get_qdrant_url

# Never hardcode configuration
qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)  # ✅
qdrant_client = QdrantClient(host="192.168.0.151", port=6333)      # ❌
```

---

#### Environment Variable Priority

**Convention:** Layered configuration with priority order

**Priority (Highest to Lowest):**
1. **Environment variables** (e.g., `export QDRANT_HOST=localhost`)
2. **.env file** in project root
3. **.streamlit/secrets.toml** (for API keys, legacy)
4. **Hardcoded defaults** in config.py

**Example:**
```python
# config.py loads .env if present
from pathlib import Path

env_file = Path(__file__).parent.parent / '.env'
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            key, value = line.split('=', 1)
            # Only set if not already in environment
            if key not in os.environ:
                os.environ[key] = value.strip('"\'')
```

**Benefits:**
- Development: Use .env file
- Production: Use environment variables
- CI/CD: Override with env vars
- Never commit secrets (..env in .gitignore)

---

### Import Organization

#### Import Order (PEP 8 Standard)

**Convention:** Three groups, separated by blank lines

**Order:**
1. **Standard library imports**
2. **Third-party imports**
3. **Local imports**

**Examples (Established):**
```python
# Standard library
import os
import sys
import logging
import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass

# Third-party packages
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import fitz  # PyMuPDF
import requests

# Local imports
from config import QDRANT_HOST, QDRANT_PORT, CALIBRE_LIBRARY_PATH
from qdrant_utils import check_qdrant_connection, create_collection
from calibre_db import CalibreDB, CalibreBook
from collection_manifest import CollectionManifest
```

**Sorting Within Groups:**
- Alphabetical by module name
- `from X import Y` after `import X`

---

#### Relative vs Absolute Imports

**Convention:** Use absolute imports with module names

**Examples (Established):**
```python
# ✅ Absolute imports (preferred)
from config import QDRANT_HOST
from qdrant_utils import check_qdrant_connection
from calibre_db import CalibreDB

# ❌ Relative imports (avoid)
from .config import QDRANT_HOST
from ..scripts.qdrant_utils import check_qdrant_connection
```

**Rationale:**
- scripts/ is a flat package (not nested)
- Absolute imports work from any entry point (MCP, CLI, tests)
- Relative imports break when scripts are imported from different locations

---

### Testing Patterns

#### Test File Organization

**Convention:** Mirror source structure in tests/ directory

**Pattern:**
```
scripts/
├── config.py
├── qdrant_utils.py
├── calibre_db.py
└── ingest_books.py

tests/
├── test_config.py
├── test_qdrant_utils.py
├── test_calibre_db.py
└── test_ingest_books.py
```

---

#### Test Function Naming

**Convention:** `test_<function_name>_<scenario>` format

**Examples:**
```python
# From tests/test_qdrant_utils.py
def test_check_qdrant_connection_success():
    """Test successful Qdrant connection."""
    ...

def test_check_qdrant_connection_failure():
    """Test Qdrant connection failure handling."""
    ...

def test_create_collection_with_valid_params():
    """Test collection creation with valid parameters."""
    ...

def test_create_collection_already_exists():
    """Test collection creation when collection exists."""
    ...
```

---

#### Pytest Conventions

**Convention:** Use pytest fixtures for setup/teardown

**Examples:**
```python
import pytest
from pathlib import Path

@pytest.fixture
def temp_calibre_db(tmp_path):
    """Create temporary Calibre database for testing."""
    db_path = tmp_path / "metadata.db"
    # Setup
    create_test_database(db_path)
    yield db_path
    # Teardown (automatic)

def test_calibre_db_query(temp_calibre_db):
    """Test Calibre database query."""
    db = CalibreDB(temp_calibre_db)
    books = db.get_all_books()
    assert len(books) > 0
```

**Test Coverage Target:**
- Current: ~4% (technical debt)
- Target: 80%+ for critical modules
- Priority: mcp_server.py, rag_query.py, ingest_books.py

---

### Platform-Specific Patterns

#### Windows Long Path Handling

**Convention:** Use `\\?\` prefix for paths >248 chars on Windows

**Established Pattern:**
```python
def normalize_file_path(file_path: str) -> Tuple[str, bool]:
    """
    Normalize file path for cross-platform compatibility.

    Handles Windows long paths (>248 chars) by adding \\?\ prefix.

    Args:
        file_path: File path to normalize

    Returns:
        Tuple of (normalized_path, used_long_path_prefix)
    """
    abs_path = os.path.abspath(file_path)
    used_long_path = False

    if os.name == "nt" and not abs_path.startswith("\\\\?\\"):
        if len(abs_path) >= 248:
            path_for_open = "\\\\?\\" + abs_path
            used_long_path = True
            return path_for_open, used_long_path

    return abs_path, used_long_path
```

**Usage:**
```python
# Always use normalize_file_path for file operations
path, used_prefix = normalize_file_path(file_path)
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()
```

---

### Resource Management Patterns

#### Singleton for Expensive Resources

**Convention:** Use singleton pattern for models, databases that are expensive to load

**Examples (Established):**
```python
class EmbeddingGenerator:
    """Singleton with multi-model cache."""

    _instance = None
    _models = {}  # Cache per model_id

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_model(self, model_id: str = None):
        """Lazy load model on first use, cache by model_id."""
        from config import EMBEDDING_MODELS, DEFAULT_EMBEDDING_MODEL
        model_id = model_id or DEFAULT_EMBEDDING_MODEL

        if model_id not in self._models:
            model_config = EMBEDDING_MODELS[model_id]
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            logger.info(f"🎯 Loading embedding model: {model_config['name']} on {device}")
            self._models[model_id] = SentenceTransformer(model_config['name'], device=device)
        return self._models[model_id]

# Usage
generator = EmbeddingGenerator()
model = generator.get_model("bge-large")  # Loads and caches
model = generator.get_model("minilm")     # Loads different model, also cached
```

**Benefits:**
- Each model loaded once across entire session
- Multiple models cached simultaneously
- Lazy loading (only when needed)
- Runtime model selection per collection

---

#### Lazy Initialization Pattern

**Convention:** Load expensive resources on first use, not at import time

**Examples (Established):**
```python
# Module-level singleton
calibre_db_instance = None

def get_calibre_db() -> CalibreDB:
    """Get Calibre database instance (lazy loaded)."""
    global calibre_db_instance
    if calibre_db_instance is None:
        calibre_db_instance = CalibreDB(CALIBRE_LIBRARY_PATH)
    return calibre_db_instance

# Usage
db = get_calibre_db()  # Loads only when first called
```

---

### Data Structure Patterns

#### Dataclass for Structured Data

**Convention:** Use `@dataclass` for all structured data types

**Benefits:**
- Automatic `__init__`, `__repr__`, `__eq__`
- Type hints enforced
- Immutability option with `frozen=True`
- Default values with `field(default=...)`

**Examples (Established):**
```python
@dataclass
class CalibreBook:
    """Represents a book from Calibre library."""
    id: int
    title: str
    author: str
    path: str
    tags: List[str] = field(default_factory=list)
    series: Optional[str] = None
    series_index: Optional[float] = None

    def __repr__(self):
        return f"<CalibreBook: {self.title} by {self.author}>"

@dataclass
class RAGResult:
    """RAG query result with sources and optional LLM answer."""
    query: str
    results: List[Dict[str, Any]]
    answer: Optional[str] = None
    context_mode: str = "contextual"

    @property
    def sources(self) -> List[Dict[str, Any]]:
        """Alias for results for backwards compatibility."""
        return self.results

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "query": self.query,
            "results": self.results,
            "answer": self.answer,
            "context_mode": self.context_mode
        }
```

---

### Enforcement Guidelines

#### All AI Agents and Developers MUST:

1. **✅ Use `snake_case` for functions/variables, `PascalCase` for classes**
2. **✅ Use dataclasses with type hints for structured data**
3. **✅ Centralize configuration in config.py, use environment variables**
4. **✅ Organize code with section headers (`# ===...===`)**
5. **✅ Use Google-style docstrings with Args, Returns sections**
6. **✅ Use `logger.*` exclusively (NO `print()` statements)**
7. **✅ Return tuples with success flags for expected failures**
8. **✅ Import order: stdlib → third-party → local**
9. **✅ Add comprehensive type hints to all functions**
10. **✅ Use singleton pattern for expensive resources (models, databases)**
11. **✅ Provide multi-line error messages with debugging hints**
12. **✅ Follow Windows long path handling for file operations**
13. **✅ Use lazy initialization for expensive resources**
14. **✅ Mirror source structure in tests/**
15. **✅ Name tests: `test_<function>_<scenario>`**

#### Pattern Violations Will Result In:

- **Code review rejection**
- **CI/CD pipeline failures** (when implemented)
- **Inconsistent codebase** (defeats purpose of these patterns)
- **Confusion for future developers/agents**

---

### Pattern Examples

#### Good Example (Follows All Patterns):

```python
"""
Book Validator Module
=====================

Validates book files before ingestion into Alexandria.

Checks file format, size, accessibility, and encoding.
"""

import os
import logging
from pathlib import Path
from typing import Tuple, Optional, List

from config import MAX_FILE_SIZE_MB

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# FILE VALIDATION
# ============================================================================

def validate_book_file(
    file_path: str,
    allowed_extensions: List[str] = ['.epub', '.pdf', '.txt']
) -> Tuple[bool, Optional[str]]:
    """
    Validate book file for ingestion.

    Checks file existence, extension, size, and readability.

    Args:
        file_path: Path to book file
        allowed_extensions: List of allowed file extensions (default: ['.epub', '.pdf', '.txt'])

    Returns:
        Tuple of (is_valid, error_message):
            - (True, None) if validation passed
            - (False, error_msg) if validation failed with specific reason

    Example:
        >>> valid, error = validate_book_file("/path/to/book.epub")
        >>> if valid:
        >>>     print("Book is valid")
    """
    path = Path(file_path)

    # Check existence
    if not path.exists():
        error_msg = f"""
❌ File not found: {file_path}

Check that:
  1. File path is correct
  2. File has not been moved or deleted
  3. You have read permissions
"""
        return False, error_msg

    # Check extension
    if path.suffix.lower() not in allowed_extensions:
        error_msg = f"""
❌ Unsupported file format: {path.suffix}

Allowed formats: {', '.join(allowed_extensions)}
File: {file_path}
"""
        return False, error_msg

    # Check file size
    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        error_msg = f"""
❌ File too large: {size_mb:.1f} MB

Maximum size: {MAX_FILE_SIZE_MB} MB
File: {file_path}

Consider splitting large books into volumes.
"""
        return False, error_msg

    logger.info(f"✅ Validated book file: {path.name} ({size_mb:.1f} MB)")
    return True, None
```

**This example demonstrates:**
- ✅ Module docstring
- ✅ Import organization (stdlib → third-party → local)
- ✅ Logger setup
- ✅ Section headers
- ✅ `snake_case` function name
- ✅ Type hints (all parameters and return)
- ✅ Google-style docstring
- ✅ Tuple return with success flag
- ✅ Multi-line error messages with debugging hints
- ✅ Structured logging with emoji

---

#### Anti-Pattern Example (Violates Multiple Patterns):

```python
# ❌ Missing module docstring
# ❌ No logging setup

import os
from pathlib import Path

# ❌ Missing type hints
def ValidateFile(filePath):
    # ❌ PascalCase function name
    # ❌ camelCase parameter
    # ❌ No docstring
    # ❌ Using print instead of logger
    print(f"Checking {filePath}")

    if not Path(filePath).exists():
        # ❌ Returns inconsistent types (bool vs string)
        return "File not found"

    # ❌ Single-line error, no debugging hints
    if Path(filePath).suffix not in ['.epub', '.pdf']:
        return False

    # ❌ No type hints on return
    return True
```

**Problems:**
- No module docstring
- Missing type hints
- Wrong naming conventions (PascalCase function, camelCase param)
- Using `print()` instead of `logger.*`
- No docstring
- Inconsistent return types (bool vs string)
- Poor error messages
- No structured organization

---

### Pattern Validation

**Code Review Checklist:**

Before committing code, verify:

- [ ] Module has docstring
- [ ] All functions have Google-style docstrings
- [ ] All functions have complete type hints
- [ ] Naming follows snake_case/PascalCase conventions
- [ ] Imports ordered: stdlib → third-party → local
- [ ] Using `logger.*` not `print()`
- [ ] Error messages are multi-line with debugging hints
- [ ] Configuration imported from config.py (not hardcoded)
- [ ] Section headers used for code organization
- [ ] Tests mirror source structure

**Automated Checks (CI/CD - Planned):**
- black (code formatting)
- flake8 (linting)
- mypy (type checking)
- pytest (test coverage)

---

**Summary:** These implementation patterns ensure consistent, maintainable code across all Alexandria modules. Following these patterns prevents "dev team playing drums on their own" and ensures seamless collaboration between AI agents and human developers.
