---
stepsCompleted: [1, 2]
inputDocuments: ['docs/architecture/architecture-comprehensive.md', 'docs/development/research/similar-projects.md']
---

# Alexandria - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for Alexandria, decomposing the requirements from the Architecture document and competitive research into implementable stories.

> **Brownfield Note:** Alexandria is an existing RAG system with 150 books ingested. This epic breakdown focuses on completing Phase 1 (Personal Tool with Showcase-Ready Architecture) and preparing for future phases.

## Requirements Inventory

### Functional Requirements

**FR-001: Semantic Book Search**
- Vector similarity search using embeddings
- Context modes: precise/contextual/comprehensive
- Optional LLM answer generation (OpenRouter API)
- ~~Current: all-MiniLM-L6-v2 (384-dim)~~ migrated
- Migrated to: **bge-m3** (1024-dim, multilingual 100+ languages, GPU-accelerated) - ADR-0010, ADR-0012

**FR-002: Hierarchical Chunking**
- Parent chunks: Full chapters (detected via EPUB/PDF structure)
- Child chunks: Semantic segments (topic boundary detection)
- Universal semantic chunker (threshold-based, ADR-0007)

**FR-003: Multi-Format Ingestion**
- EPUB, PDF, TXT, MD, HTML support
- Calibre metadata enrichment (author, title, tags, series)
- Local file ingestion (no Calibre required)
- Configurable chunking parameters (threshold, min/max size)

**FR-004: Collection Management**
- Isolated collections per use case (ADR-0006)
- Collection-specific manifests (JSON + CSV tracking)
- Per-collection settings and quotas

**FR-005: Multi-Consumer Service** (ADR-0008)
- Tier 1 (MCP): stdio protocol for Claude Code - PRIMARY
- Tier 2 (HTTP): REST API for web/mobile clients - SECONDARY
- Tier 3 (Python lib): Direct import from scripts/ - INTERNAL

### Non-Functional Requirements

**NFR-001: Performance**
- Ingestion: ~11-13 sec/book (CPU), **~0.3 sec/book (GPU with bge-m3)** - ADR-0010
- Query: <100ms (search only), 0.15-5.5 sec (with LLM)
- Target scale: 1.35M chunks, ~6GB vectors (bge-m3, 1024-dim)

**NFR-002: Immutability Constraints** (CRITICAL)
- Embedding model locked per collection (changing = full re-ingestion)
- Distance metric: COSINE (changing = collection recreation)
- Decision window: Re-ingestion manageable NOW (150 books), prohibitive later (9,000 books)

**NFR-003: Reliability**
- Graceful degradation (works without LLM, without Calibre)
- Collection isolation prevents cross-contamination
- Manifest tracking for data integrity
- Health checks for external dependencies

**NFR-004: Maintainability**
- Single source of truth: scripts/ package (ADR-0003)
- Thin presentation layers (MCP, GUI, HTTP)
- No business logic in interfaces
- Comprehensive documentation (ADRs, C4 diagrams, API docs)

**NFR-005: Scalability**
- Current: 150 books, ~23K chunks
- Target: 9,000 books, ~1.35M chunks
- Qdrant handles billions of vectors (significant headroom)
- GPU acceleration enables fast batch processing

**NFR-006: Multi-Tenancy** (Phased Evolution - ADR-0011)
- Phase 1 (Current): Single user, multi-tenant architecture ready
- Phase 2 (Optional): Invite-only beta (5-10 users)
- Phase 3 (Future): Public beta with legal compliance
- Phase 4 (Whale): Full SaaS with enterprise features

### Additional Requirements

**From Architecture Document:**

- **Starter Template:** None (brownfield project, existing codebase in scripts/)
- **GPU Acceleration (ADR-0010):** Migrated to bge-m3 (multilingual, 1024-dim) with GPU acceleration
- **HTTP API Wrapper (ADR-0009):** FastAPI REST API for multi-consumer support (Phase 1+)
- **Implementation Patterns:** 18 conflict points documented, 15 mandatory rules for consistency
- **Competitive Differentiation:** GPU acceleration, hierarchical chunking, multi-consumer architecture, collection isolation

**Technical Debt (From Known Issues):**

1. Interactive chunking GUI - lost code (CLI tool exists: experiment_chunking.py)
2. Universal chunking parameters hardcoded (should be configurable via Settings)
3. Calibre library path regression (was GUI-configurable, now hardcoded)
4. tqdm progress bars disabled globally (Streamlit stderr workaround, needs callback pattern)
5. Qdrant server location hardcoded (should be configurable via Settings)
6. Test coverage low (~4%) - comprehensive roadmap exists

**From Competitive Research (similar-projects.md):**

- **Hybrid Retrieval:** Consider BM25 + semantic fusion for improved precision
- **Legal Compliance:** DMCA safe harbor approach for Phase 3+ (user uploads)
- **Market Positioning:** Differentiate via GPU acceleration, hierarchical chunking, multi-consumer architecture

### FR Coverage Map

**FR-001 (Semantic Book Search):**
- Epic 0: ~~Model migration to bge-large-en-v1.5~~ **DONE** — migrated to bge-m3 (multilingual)
- Epic 1: Search interface and context modes
- Epic 3: MCP/HTTP API access

**FR-002 (Hierarchical Chunking):**
- Epic 1: Parent/child chunk implementation
- Epic 5: Configurable chunking parameters (fix technical debt)

**FR-003 (Multi-Format Ingestion):**
- Epic 1: EPUB/PDF/TXT/MD/HTML parsers
- Epic 4: Batch ingestion optimization
- Epic 5: Calibre path configuration (fix regression)

**FR-004 (Collection Management):**
- Epic 2: Collection isolation and manifests
- Epic 6: Access control for copyrighted/public domain separation

**FR-005 (Multi-Consumer Service):**
- Epic 3: MCP server (stdio), HTTP API (FastAPI), Python library access

**NFR-001 (Performance):**
- Epic 0: GPU-accelerated embeddings (10x speedup)
- Epic 4: Batch processing optimization

**NFR-002 (Immutability Constraints):**
- Epic 0: Model migration NOW (decision window closing)

**NFR-003 (Reliability):**
- Epic 1: Graceful degradation, health checks
- Epic 2: Collection isolation
- Epic 7: Monitoring and alerting

**NFR-004 (Maintainability):**
- Epic 3: Thin presentation layers (ADR-0003)
- Epic 5: Test coverage, configuration cleanup
- Epic 7: Structured logging and observability

**NFR-005 (Scalability):**
- Epic 4: 9,000 book target scale
- Epic 7: Performance metrics and monitoring

**NFR-006 (Multi-Tenancy):**
- Epic 6: Phase 1 architecture ready, Phase 2+ user accounts and permissions

**Technical Debt:**
- Epic 5: All 6 technical debt items addressed

## Epic List

### Epic 0: Embedding Model Migration ✅ COMPLETED

~~**FIRST PRIORITY** - Migrate embedding model to bge-large-en-v1.5~~ **DONE**

Migrated to **bge-m3** (1024-dim, multilingual 100+ languages, GPU-accelerated). The model choice was upgraded from the originally planned bge-large-en-v1.5 (English-only) to bge-m3 for epistemological reasons — preserving semantic fingerprints in original languages across 100+ linguistic traditions. See [ADR-0012](../architecture/decisions/0012-original-language-primary.md).

**User Outcome:** Users experience multilingual semantic search that preserves meaning in the original language. "Dasein" and "being-there" occupy different regions of semantic space — this is the feature, not the bug.

**FRs Covered:** FR-001 (model upgrade), NFR-001 (performance), NFR-002 (immutability window)

**ADR References:** ADR-0010 (GPU-Accelerated Embeddings), ADR-0012 (Original Language Primary)

**Implementation Notes:**
- Model: **bge-m3** (1024-dim, multilingual, GPU-accelerated) — replaces originally planned bge-large-en-v1.5
- GPU: PyTorch CUDA on BUCO (A2000 12GB) for 10x ingestion speedup (~0.3 sec/book vs 11-13 sec)
- Re-ingestion completed for all collections
- Immutability: Model is now locked (changing = full re-ingestion of 9,000+ books)

---

### Epic 1: Core Book Search & Discovery

Enable users to search and discover content across their book collection using semantic search with hierarchical chunking.

**User Outcome:** Users can find relevant passages in books using natural language queries, with configurable context modes (precise/contextual/comprehensive).

**FRs Covered:** FR-001 (search), FR-002 (hierarchical chunking), FR-003 (ingestion), NFR-003 (reliability)

**ADR References:** ADR-0007 (Universal Semantic Chunking), ADR-0006 (Collection Isolation)

**Implementation Notes:**

**Ingestion Pipeline:**
- Multi-format parsing: EPUB, PDF, TXT, MD, HTML
- Hierarchical chunks: Parent (chapters) + Child (semantic segments)
- **Calibre Metadata Handling:**
  - Extract ONLY: title, author, file_path
  - **SKIP Calibre tags entirely** (unreliable garbage)
  - Treat title/author with caution (verification recommended)
- **External Metadata Enrichment:**
  - Primary source: OpenLibrary API (best coverage, free)
  - Secondary: Google Books API (good metadata, quota limits)
  - Tertiary: Wikidata (author death dates, copyright info)
  - Cross-check metadata across 2+ sources for verification
  - Extract from book content when available (EPUB metadata, PDF properties)
- **Copyright Detection (Phase 3+ preparation):**
  - Calculate copyright_status from publication_year + author_death_year
  - Rules: Pre-1928 = public_domain, author_death + 70 years = public_domain
  - Default to "unknown" if insufficient data
  - Store in chunk metadata for filtering
- **Chunk Metadata Extension:**
  ```python
  chunk_metadata = {
      "book_id": ...,
      "title": "...",  # From external API (verified)
      "author": "...",  # From external API
      "publication_year": 1949,  # From external API
      "author_death_year": 1950,  # From Wikidata
      "copyright_status": "public_domain",  # Calculated
      "visibility": "public",  # public/private (Epic 6)
      "metadata_source": "openlibrary",  # Provenance
      "calibre_title": "...",  # Original (debugging only)
  }
  ```

**Search & Discovery:**
- Context modes: Precise (1 chunk), Contextual (3 chunks), Comprehensive (full chapter)
- Graceful degradation: Works without LLM, without Calibre
- Health checks for Qdrant, OpenRouter API

---

### Epic 2: Multi-Collection Organization

Enable users to organize books into isolated collections with independent settings and tracking.

**User Outcome:** Users can manage multiple book collections (e.g., work vs personal, fiction vs technical) with separate settings and quotas.

**FRs Covered:** FR-004 (collection management), NFR-003 (reliability via isolation)

**ADR References:** ADR-0006 (Collection Isolation), ADR-0004 (Collection-Specific Manifests)

**Implementation Notes:**
- Collection isolation prevents cross-contamination
- Per-collection manifests (JSON + CSV)
- Configurable chunking parameters per collection
- Usage quotas and limits
- Prepares for Phase 2+ multi-tenancy

---

### Epic 3: Multi-Consumer Access & Integration

Provide multiple access patterns for different client types (Claude Code, web apps, Python scripts).

**User Outcome:** Users and developers can access Alexandria via MCP server (Claude Code), HTTP API (web/mobile), or Python library (scripts).

**FRs Covered:** FR-005 (multi-consumer service), NFR-004 (maintainability)

**ADR References:** ADR-0008 (Multi-Consumer Service Model), ADR-0003 (GUI as Thin Layer), ADR-0009 (HTTP API Wrapper)

**Implementation Notes:**
- Tier 1 (MCP): stdio protocol for Claude Code - PRIMARY
- Tier 2 (HTTP): FastAPI REST API for web/mobile clients - SECONDARY
- Tier 3 (Python lib): Direct import from scripts/ - INTERNAL
- All tiers share business logic in scripts/ package
- Swagger/OpenAPI documentation
- API key authentication (Phase 1)

---

### Epic 4: Production Scaling & Performance

Optimize ingestion and query performance for the 9,000 book target scale.

**User Outcome:** System handles 9,000 books (~1.35M chunks) with fast ingestion and sub-100ms query times.

**FRs Covered:** FR-003 (batch ingestion), NFR-001 (performance), NFR-005 (scalability)

**ADR References:** ADR-0010 (GPU Acceleration)

**Implementation Notes:**
- Batch ingestion pipeline (parallel processing)
- GPU-accelerated embeddings (done in Epic 0)
- Query optimization (<100ms search, 0.15-5.5 sec with LLM)
- Target: 1.35M chunks, ~6GB vectors
- Qdrant capacity: Billions of vectors (significant headroom)
- Progress callbacks (fix tqdm technical debt)

---

### Epic 5: Quality & Maintainability

Address technical debt and improve test coverage for long-term maintainability.

**User Outcome:** Codebase is well-tested, configurable, and maintainable for future development.

**FRs Covered:** FR-002 (configurable chunking), FR-003 (configurable paths), NFR-004 (maintainability)

**ADR References:** ADR-0003 (Single Source of Truth), project-context.md (testing rules)

**Implementation Notes:**
- Fix 6 technical debt items:
  1. Recreate interactive chunking GUI (lost code)
  2. Make universal chunking parameters configurable (Settings sidebar)
  3. Restore Calibre library path configuration (regression fix)
  4. Replace tqdm with callback pattern (Streamlit stderr fix)
  5. Make Qdrant server location configurable (Settings)
  6. Increase test coverage from ~4% to >80%
- Comprehensive test roadmap exists
- Playwright UI tests + pytest unit tests
- Configuration refactoring (hardcoded → Settings sidebar)

---

### Epic 6: Multi-Tenancy & Access Control

Prepare architecture for Phase 2+ multi-user support with access control for content licensing.

**User Outcome:** System supports multiple users with account groups, permissions, and copyrighted/public domain content separation.

**FRs Covered:** FR-004 (collection access control), NFR-006 (multi-tenancy)

**ADR References:** ADR-0011 (Phased Growth Architecture), ADR-0006 (Collection Isolation)

**Implementation Notes:**

**Collection Visibility by Phase & User Group:**

- **Phase 1 (Current - Single User):**
  - Single user (you), all collections private
  - All content types allowed (copyrighted material OK, personal use)
  - No external access

- **Phase 2 (Invite-Only, 5-10 Users):**
  - Users upload THEIR OWN books to private collections
  - No cross-user visibility (each user sees only their collections)
  - All copyrighted material allowed (users own rights to their uploads)
  - Manual invite system (admin creates accounts)

- **Phase 3 (Public Registration - CRITICAL for Legal Compliance):**
  - **FREE Tier Users:**
    - Read-only access to PUBLIC DOMAIN collection ONLY
    - Cannot see ANY copyrighted/private collections
    - Cannot upload books
    - Anonymous access allowed (no account required)
  - **PRO Tier Users ($9/month):**
    - Everything in FREE tier (public domain read access)
    - Can upload to PRIVATE collection (copyrighted material OK, user warrants rights)
    - Private collections visible ONLY to owner
    - NEVER visible to external/free users
  - **Public Domain Collection:**
    - ~600 Standard Ebooks (public domain verified)
    - Visible to ALL users (including anonymous/free tier)
    - Read-only for everyone
    - Separate Qdrant collection: `public_alexandria`
  - **Legal Safeguards:**
    - ToS: Users warrant they have rights to uploads
    - DMCA safe harbor: Takedown process for reported infringements
    - Privacy Policy: GDPR-lite compliance
    - Acceptable Use Policy: No piracy, no abuse

- **Phase 4 (Enterprise SaaS):**
  - **Team Collections:** Shared within account group (5-50 users per organization)
  - **Access Control Lists (ACLs):** Admin defines who can see which collections
  - **SSO Integration:** External identity provider for user groups (SAML, OIDC)
  - **Custom Permissions:** Read-only, read-write, admin per collection
  - **Audit Trails:** Who accessed what, when (Epic 7 integration)

**Technical Implementation:**
- SQLite user database (Phase 2+): users, roles, permissions, API keys
- Collection metadata: `visibility` field (private, shared, public)
- API middleware: Enforce visibility rules before query execution
- Collection isolation (ADR-0006): Each collection has owner + ACL

---

### Epic 7: Audit Logging & Monitoring

Implement comprehensive audit logging and observability stack for compliance, debugging, and operations.

**User Outcome:** System events are logged to SQLite for audit trails, and monitored via Grafana dashboards for health and performance oversight.

**FRs Covered:** NFR-003 (reliability), NFR-004 (maintainability via observability), NFR-005 (scalability monitoring)

**ADR References:** ADR-0011 (Phase 2+ requirements), project-context.md (logging patterns)

**Implementation Notes:**
- **SQLite Audit Database** (local, always-on):
  - **System Events** (always logged):
    - Errors, performance degradation, API failures
    - Ingestion events, re-ingestion triggers
    - Admin actions: Configuration changes, user management (Phase 2+)
    - Access control: Permission changes, account modifications
    - Compliance: DMCA takedowns, privacy requests (Phase 3+)
  - **User Actions** (privacy-sensitive, opt-in only with explicit consent):
    - **Personal Journaling Mode** (opt-in, user-controlled):
      - User explicitly consents: "Track my activity for personal diary"
      - Logs: Search queries, books read, timestamps, bookmarks, notes
      - Purpose: Personal learning journal, knowledge journey tracking
      - Retention: Until user revokes consent or deletes account
      - Export: JSON/CSV export of personal diary data
      - **GDPR Basis**: Article 6(1)(a) Consent + Article 6(1)(f) Legitimate Interest (personal journaling)
    - **System Improvement** (opt-in, anonymized):
      - User consents: "Share anonymized data for system improvement"
      - Logs: Query count, performance metrics, error patterns (NO personal data, NO book titles)
      - Anonymization: Hash user IDs, aggregate statistics only
      - Retention: 90 days, then aggregated/deleted
      - **GDPR Basis**: Article 6(1)(a) Consent
    - **Privacy Controls**:
      - Phase 1: Local only, user controls their data, consent flag in settings
      - Phase 2: Opt-in consent UI (clear purpose, easy revoke), export/delete functionality
      - Phase 3+: Full GDPR compliance (consent audit trail, right to access, right to erasure)
      - **Consent Requirements**:
        - Explicit checkbox (NOT pre-checked)
        - Clear purpose explanation (personal diary vs system improvement)
        - Easy to revoke (one-click disable in settings)
        - Audit trail (consent date, IP, purpose)
      - **NEVER log without consent**: Query content, book titles, sensitive personal data
      - **User Rights**: Export personal diary (JSON/CSV), Delete all activity logs, Revoke consent anytime
- **Grafana Monitoring Stack:**
  - Prometheus: Metrics collection (query latency, ingestion throughput, error rates)
  - Grafana: Dashboards (system health, usage patterns, performance trends)
  - Alertmanager: Alerts (disk space, API failures, slow queries)
  - Log aggregation: Structured logs → searchable (Loki or ELK stack)
- **Structured Logging:**
  - Application logs: logger.info/error/warning/debug (already implemented)
  - Business event logs: SQLite audit.db (new)
  - Centralized aggregation: Grafana Loki or ELK (Phase 3+)
- **Compliance Reporting:**
  - Audit trail exports for legal requests (Phase 3+)
  - GDPR data access reports (Phase 3+)
  - Usage analytics for scaling decisions

---

## Future Epics (Strategic Roadmap Day 0-4)

> **Updated 2026-02-09:** Aligned with [Strategic Brief v1.0](./strategic-brief-v1.md) and [Strategic Notebook](./strategic-notebook-2026-02-09.md). The Day 0-4 roadmap replaces the earlier Phase 3-4+ timeline for knowledge infrastructure epics. Each day builds on the previous — connectors feed SKOS, SKOS feeds agents, agents feed the graph, the graph feeds temporal knowledge.

These concepts are documented in [docs/development/ideas/](./README.md) and the strategic brief:

### Epic 8: Source Connectors - Multilingual Public Domain Sources

**Vision:** Expand Alexandria's source base beyond Internet Archive and Gutenberg with 5 new multilingual public domain connectors.

**Connectors:**
| # | Source | Languages | Effort |
|---|--------|-----------|--------|
| 1 | **Wikisource** (6.75M texts, 82 languages) | ALL | 2-3 days |
| 2 | **Chinese Text Project** (30,000 works) | Classical Chinese + EN | 1-2 days |
| 3 | **SuttaCentral** (Buddhist canon, parallel texts) | Pali, Sanskrit, Chinese, Tibetan + 30 modern | 1-2 days |
| 4 | **Gallica (BnF)** (10M docs) | French, Latin, Arabic | 3-4 days |
| 5 | **Perseus** (Classical texts, TEI) | Ancient Greek, Latin | 2-3 days |

**Architecture:** Common `BaseConnector` interface (`search()`, `metadata()`, `download()`, `languages()`). All connectors conform to same pattern. LIBRARIAN agent calls them uniformly.

**Roadmap:** **Day 0 SOURCE** — "There is no library without books." Before ontologies, before agents, before graphs.

**ADR References:** [ADR-0012](../architecture/decisions/0012-original-language-primary.md) (original language primary drives connector selection)

**Source:** [Strategic Brief — Day 0](./strategic-brief-v1.md#day-0-project-source), [Strategic Notebook — Connector Architecture](./strategic-notebook-2026-02-09.md#day-0-project-source--connector-details)

---

### Epic 9: SKOS Ontology Backbone + Neo4j

**Vision:** Replace flat Calibre tags with W3C SKOS concept organization. Neo4j as runtime query engine on BUCO server.

**Components:**
- **SKOS concepts** in YAML: `prefLabel` (original language), `altLabel` (English approximation), `broader`/`narrower`/`related` relationships
- **Alexandria extensions**: `translation_fidelity` (low/medium/high), `untranslatable` flag, `original_language`, `source_taxonomy`
- **Neo4j** on BUCO (Dell PowerEdge 3660, 80GB RAM, 8TB NVMe): Import YAML concepts as nodes/edges
- **Concept seeding**: Import taxonomies from CText, SuttaCentral, Perseus, Gallica, Wikisource — NOT invented from scratch
- **Interoperability**: Dublin Core for book metadata, SKOS for concepts, Wikidata links via `skos:exactMatch`

**Roadmap:** **Day 1 SKOS** — 200-300 seed concepts, grow organically. LIBRARIAN agent expands as books are ingested.

**ADR References:** [ADR-0013](../architecture/decisions/0013-skos-ontology-backbone.md) (SKOS backbone), [ADR-0012](../architecture/decisions/0012-original-language-primary.md) (original language as prefLabel)

**Source:** [Strategic Brief — Day 1](./strategic-brief-v1.md#day-1-skos-ontology-backbone), [Strategic Notebook — SKOS Schema](./strategic-notebook-2026-02-09.md#day-1-skos-schema-and-data-formats)

---

### Epic 10: Librarians - AI Agent Orchestration Layer

**Vision:** Specialized agents that serve as interface between Alexandria and users. Orthogonal with Guardian personas: Librarian = WHAT they do, Guardian = WHO speaks.

**Agents:**
- **LIBRARIAN**: Cataloging, metadata integrity, SKOS tagging
- **RESEARCHER**: Deep semantic search, cross-referencing, synthesis
- **CURATOR**: Personalized recommendations, reading paths, "unknown unknowns"
- **ARCHIVIST**: Maintenance, quality checks, health monitoring

**Dispatcher:** Query classification routes to specialist. Simple lookup -> LIBRARIAN. Deep research -> RESEARCHER. "What should I read?" -> CURATOR. Maintenance -> ARCHIVIST.

**Roadmap:** **Day 2 AGENTS** — requires SKOS backbone (Day 1) for LIBRARIAN tagging and CURATOR recommendations.

**Source:** [librarians.md](./ideas/librarians.md), [Strategic Brief — Day 2](./strategic-brief-v1.md#day-2-agents-librarians--guardians)

---

### Epic 11: Knowledge Graph - LightRAG + Neo4j

**Vision:** Graph-enhanced retrieval combining Qdrant (fast vector similarity) with Neo4j (relationship traversal). LightRAG proof-of-concept on 100-200 books.

**Components:**
- **Neo4j** (already deployed in Epic 9): SKOS concepts + book-concept relationships
- **LightRAG** (HKU, EMNLP 2025): Graph-enhanced RAG on top of existing Qdrant. Supports `QdrantVectorDBStorage`. 84.8% win rate vs Microsoft GraphRAG at 99% token reduction.
- **Hybrid retrieval**: Qdrant for fast similarity, Neo4j for relationship traversal. Shared IDs. Combined context for LLM.

**Roadmap:** **Day 3 GRAPH** — PoC on one topic cluster. Validate that graph-enhanced retrieval beats pure vector search. If yes, scale. If no, investigate.

**Source:** [Strategic Brief — Day 3](./strategic-brief-v1.md#day-3-knowledge-graph), [Strategic Notebook — Knowledge Graph Technology](./strategic-notebook-2026-02-09.md#day-3-knowledge-graph-technology-landscape)

---

### Epic 12: Temporal Knowledge Layer - Graphiti + Citaonica

**Vision:** Conversation memory and temporal knowledge tracking. Citaonica (reading room) replaces Speaker's Corner with guardian-powered conversational interface.

**Components:**
- **Graphiti** (Zep): Temporal knowledge graph for conversation memory. Bi-temporal model: t_event (when it happened), t_ingested (when we learned).
- **Citaonica**: Two-step approach — (1) quick guardian swap in existing Streamlit UI now, (2) full chat with Graphiti memory later.
- **Event logging** (starts Day 0): Track queries, found-useful signals, reading history. Feeds the temporal layer.
- **Temporal queries**: "How did my understanding evolve?", "What did I read before discovering X?"

**Roadmap:** **Day 4 TEMPORAL** — requires Knowledge Graph (Day 3) and event data accumulated from Day 0.

**Privacy Note:** User journey tracking must be opt-in, GDPR compliant, with data retention limits.

**Source:** [temporal-knowledge-layer.md](./ideas/temporal-knowledge-layer.md), [Strategic Brief — Day 4](./strategic-brief-v1.md#day-4-temporal-knowledge-layer)

---

### Epic 13 (Parked): Makers - Consensus Voting for Critical Decisions

**Vision:** MAKER methodology (atomic steps, parallel agents, k-threshold voting) for zero-error critical decisions.

**Use Cases:**
- Delete operations (irreversible)
- Metadata override on verified entries
- Cross-reference affecting >10 documents
- Rare/valuable book operations

**Approach:**
- Parallel execution: 3+ agents work same task independently
- K-threshold voting: Consensus required (k=2 advantage)
- Red-flagging: Reject suspicious responses before voting
- Escalation: Human review if no consensus

**Status:** **Parked** — needs autonomous agents (Epic 10) operational first.

**Source:** [makers.md](./ideas/makers.md)

---

### Epic 14 (Future): Author Geography Map

**Vision:** Visualize geographic distribution of authors using Datasette cluster-map.

**Approach:**
- Enrich author metadata via Wikidata (birthplace, nationality)
- Geocode to lat/long
- Visualize via datasette-cluster-map plugin

**Dependencies:** Epic 1 metadata enrichment (capture wikidata_id, birthplace during ingestion)

**Phase:** Phase 2-3 (visualization feature, independent of Day 0-4 roadmap)

**Source:** [author-geography-map.md](./ideas/author-geography-map.md)

---

## Roadmap Dependency Graph

```
Day 0: SOURCE (Epic 8)     ─── Connectors feed books into Alexandria
         │
Day 1: SKOS (Epic 9)       ─── Concepts organize what connectors bring
         │
Day 2: AGENTS (Epic 10)    ─── Librarians use SKOS to tag and recommend
         │
Day 3: GRAPH (Epic 11)     ─── Neo4j + LightRAG enable "unknown unknowns"
         │
Day 4: TEMPORAL (Epic 12)  ─── Graphiti + Citaonica track knowledge journeys
```

> See [Strategic Brief v1.0](./strategic-brief-v1.md) for the full roadmap and [Strategic Notebook](./strategic-notebook-2026-02-09.md) for technical details.

## Next Steps

After approval of this epic structure, proceed to Step 3: Create Stories for detailed story breakdown with acceptance criteria.
