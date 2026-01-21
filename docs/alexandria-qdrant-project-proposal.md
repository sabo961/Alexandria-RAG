---
status: proposal
priority: high
type: exploration
epic: "Alexandria RAG System"
category: knowledge-management
started: 2026-01-21
assignee: Sabo
tags: [qdrant, rag, multidisciplinary, knowledge-graph, ai-research]
---

# Alexandria RAG System - Project Proposal

**Motivation:** 9000-book multidisciplinary library (technical + psychology + philosophy + history) deserves better than Ctrl+F. Let's build a semantic search RAG system that can answer questions like:

- *"How did Venice merchant guilds handle freight routing 800 years ago?"*
- *"What does Gestalt psychology say about data visualization?"*
- *"How would Kant evaluate the ethics of replacing manual workers with AI automation?"*
- *"What patterns from Len Silverston's Data Model Resource Book apply to WBF Distribution?"*

**Why separate project:**
- Useful for ANY software project, not just WBF2
- Will evolve unpredictably (knowledge graphs, citation networks, concept mapping)
- Different tech stack (Python, Qdrant, Open WebUI, possibly LangChain)
- Different audience (software engineers, researchers, knowledge workers)

---

## Vision

**Short-term:** RAG system that can semantically search 9000 books and return relevant passages with citations

**Long-term:** Multidisciplinary knowledge synthesis engine that:
- Connects technical patterns with historical precedents
- Maps psychological principles to UX design decisions
- Validates architectural choices against philosophical frameworks
- Discovers cross-domain insights (e.g., "manufacturing execution patterns in 18th-century textile mills")

---

## Technical Stack (Proposed)

- **Vector DB:** Qdrant (open-source, self-hosted)
- **Embedding Model:** sentence-transformers/all-MiniLM-L6-v2 (or better)
- **Chunking Strategy:** Domain-specific (see below)
- **UI:** Open WebUI (or custom Streamlit app)
- **Ingestion Pipeline:** Python (PyMuPDF, openpyxl, BeautifulSoup for EPUB/HTML)
- **LLM:** Claude API for synthesis (not for embeddings - too expensive)

---

## Chunking Strategy by Domain

### Technical Books (Databases, Software Architecture, AI)

**Chunk Size:** 1500-2000 tokens (larger chunks preserve context)

**Rationale:**
- Technical explanations need full context (diagrams, code examples, multi-paragraph explanations)
- Too-small chunks lose critical setup/background
- Examples: Silverston's shipment pattern chapter (5 pages), Fowler's refactoring examples (3 pages)

**Metadata to capture:**
- Book title, author, chapter, section, page range
- Diagrams/tables (OCR extract or reference)
- Code examples (syntax-highlighted, language-tagged)

**Special handling:**
- **Diagrams:** Extract as images, store in Qdrant metadata, OCR text for searchability
- **Code blocks:** Tag with language, extract as separate searchable chunks
- **Reference tables:** Index as structured data (JSON metadata)

### Psychology Books (Kahneman, Cialdini, Gestalt Theory)

**Chunk Size:** 1000-1500 tokens (concept-focused)

**Rationale:**
- Psychological concepts often self-contained (Kahneman's System 1/System 2, Cialdini's 6 principles)
- Smaller chunks allow precise retrieval for UX/change management questions
- Examples: "Loss aversion in decision-making" (2 pages), "Gestalt proximity principle" (1 page)

**Metadata to capture:**
- Concept name (e.g., "Cognitive Load Theory", "Social Proof")
- Study citations (if mentioned)
- Application domain (UX, organizational change, persuasion)

### Philosophy Books (Kant, Aristotle, Ethics)

**Chunk Size:** 1200-1800 tokens (argument-preserving)

**Rationale:**
- Philosophical arguments require setup → claim → justification structure
- Too-small chunks lose logical flow
- Examples: Kant's Categorical Imperative explanation (4 pages), Aristotle's virtue ethics (3 pages)

**Metadata to capture:**
- Philosopher name, work title, concept name
- Ethical framework (deontology, consequentialism, virtue ethics)
- Application domain (business ethics, AI ethics, professional responsibility)

### History Books (Industrial Revolution, Merchant Guilds, Manufacturing)

**Chunk Size:** 1500-2000 tokens (narrative-preserving)

**Rationale:**
- Historical case studies need context (who, what, when, why, outcome)
- Too-small chunks lose causal connections
- Examples: Venice merchant guild freight routing (6 pages), Lowell textile mill production systems (8 pages)

**Metadata to capture:**
- Time period (century, decade)
- Geography (Venice, England, New England)
- Industry (textile, maritime, manufacturing)
- Historical outcome (success/failure, lessons learned)

---

## Qdrant Collection Schema (Proposed)

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

client = QdrantClient(host="localhost", port=6333)

# Create collection
client.create_collection(
    collection_name="alexandria",
    vectors_config=VectorParams(
        size=384,  # all-MiniLM-L6-v2 embedding dimension
        distance=Distance.COSINE
    )
)

# Point structure
point = PointStruct(
    id=1,  # UUID or auto-increment
    vector=[0.1, 0.2, ...],  # 384-dim embedding
    payload={
        # Core metadata
        "book_title": "The Data Model Resource Book Vol 1",
        "author": "Len Silverston",
        "domain": "technical",  # technical/psychology/philosophy/history
        "subdomain": "database-design",  # database-design/ux/ethics/manufacturing

        # Location metadata
        "chapter": "7",
        "section": "Shipment Patterns",
        "page_start": 145,
        "page_end": 152,

        # Content metadata
        "text": "Full chunk text here...",
        "text_length": 1850,
        "concepts": ["Party-Role pattern", "Shipment cost allocation", "Multi-leg transport"],

        # Special metadata (domain-specific)
        "has_diagram": True,
        "diagram_url": "s3://alexandria/diagrams/silverston_ch7_shipment_erd.png",
        "has_code": False,
        "citations": [],  # For academic books

        # Ingestion metadata
        "ingested_at": "2026-01-21T10:00:00Z",
        "chunk_strategy": "large-context-technical",
        "embedding_model": "all-MiniLM-L6-v2"
    }
)
```

---

## Example Queries & Use Cases

### Query 1: Technical Pattern Validation
**Question:** *"How should I model multi-carrier shipments in a relational database?"*

**Expected Qdrant Retrieval:**
1. Silverston Ch7: Shipment patterns (Party-Role, multi-leg transport)
2. Date/Darwen: Relational theory (normalization, FK design)
3. Fowler: Analysis Patterns (Shipment/Consignment pattern)

**Synthesis (via Claude API):**
- Recommend Line-level carrier (Silverston's Party-Role pattern)
- Explain normalization rationale (Date/Darwen)
- Show UML diagram (Fowler)

### Query 2: UX/Psychology Cross-Domain
**Question:** *"Why do users struggle with WBF's filter UI?"*

**Expected Qdrant Retrieval:**
1. Norman: Design of Everyday Things (affordances, signifiers)
2. Kahneman: Thinking, Fast and Slow (cognitive load, System 1 vs 2)
3. Gestalt: Principles of visual perception (proximity, similarity)

**Synthesis:**
- Diagnose cognitive load issues (Kahneman)
- Recommend affordance improvements (Norman)
- Apply Gestalt proximity for grouping filters

### Query 3: Historical Pattern Mining
**Question:** *"How did 19th-century factories optimize production flow?"*

**Expected Qdrant Retrieval:**
1. Lowell textile mills case study (interchangeable parts, assembly line precursor)
2. Taylor: Principles of Scientific Management (time studies, workflow optimization)
3. Ford: My Life and Work (assembly line, single-piece flow)

**Synthesis:**
- Historical precedent for WBF's production sequencing
- Lessons learned (over-optimization → worker burnout)
- Modern adaptation (Toyota Production System → Kanban)

### Query 4: Ethical AI Decision
**Question:** *"Should WBF automate quality inspection (replaces manual inspectors)?"*

**Expected Qdrant Retrieval:**
1. Kant: Categorical Imperative (treating workers as means vs ends)
2. Mill: Utilitarianism (greatest good for greatest number)
3. Aristotle: Nicomachean Ethics (virtue ethics, human flourishing)

**Synthesis:**
- Kantian analysis: Is automation treating workers as mere tools?
- Utilitarian calculation: Net benefit (efficiency vs unemployment)
- Virtue ethics: Does it promote human excellence or deskilling?

---

## Next Steps (If Approved as Separate Project)

### Phase 1: Proof of Concept (1-2 weeks)
1. **Run Alexandria census batch** → Get exact book count & formats
2. **Ingest 10 representative books** (2 technical, 2 psychology, 2 philosophy, 2 history)
3. **Test chunking strategies** (compare 1000 vs 1500 vs 2000 token chunks)
4. **Build basic Qdrant query script** (Python CLI)
5. **Validate retrieval quality** (manual evaluation of top-10 results)

### Phase 2: Full Ingestion Pipeline (2-4 weeks)
1. **PDF ingestion** (PyMuPDF, handle OCR for scanned books)
2. **EPUB/MOBI ingestion** (BeautifulSoup, handle DRM-free formats)
3. **Metadata extraction** (title, author, TOC parsing)
4. **Diagram extraction** (OCR diagrams, store as images + text)
5. **Batch ingestion** (process all 9000 books, progress tracking)

### Phase 3: UI & Integration (2-3 weeks)
1. **Open WebUI setup** (connect to Qdrant, configure models)
2. **Custom search UI** (Streamlit app with domain filters, citation tracking)
3. **Claude API integration** (synthesis layer, not just retrieval)
4. **Citation formatting** (APA/MLA export, "Show me the page" feature)

### Phase 4: Advanced Features (Future)
1. **Concept graph** (Neo4j knowledge graph linking concepts across books)
2. **Citation network** (which books reference each other)
3. **Historical timeline** (search by time period: "1850-1900 manufacturing")
4. **Cross-domain recommendations** ("If you liked Silverston's Party-Role pattern, read Fowler's Analysis Patterns")

---

## Project Home (Proposed)

**Option A:** Separate GitHub repo (`alexandria-rag`)
- Standalone project, can be used for any domain (not just WBF2)
- CI/CD for ingestion pipeline
- Docker Compose (Qdrant + Open WebUI)

**Option B:** WBF2 journey subfolder (`docs/journey/alexandria/`)
- Keeps it in WBF2 context (but conceptually separate)
- Can reference WBF-specific use cases
- Easier to cross-reference

**Recommendation:** **Option A** - This will grow beyond WBF2.

---

## Open Questions

1. **Embedding model:** all-MiniLM-L6-v2 (fast, 384-dim) or larger model (e.g., bge-large-en, 1024-dim)?
2. **Chunk overlap:** Should chunks overlap by 100-200 tokens to preserve context?
3. **OCR strategy:** Pre-process scanned PDFs with Tesseract, or skip OCR for now?
4. **Metadata standardization:** Extract author/title from filename (Calibre naming), or parse PDF metadata?
5. **Multilingual books:** Do you have books in Croatian/German/French? (affects embedding model choice)

---

**Decision Point:** Should we spin this off as `alexandria-rag` separate project, or keep as WBF2 journey subfolder?

**My recommendation:** Separate project. This has legs beyond WBF2.

---

**Last Updated:** 2026-01-21
**Proposal Author:** Mary (Business Analyst agent)
**Awaiting:** Sabo's decision (separate project vs WBF2 journey)
