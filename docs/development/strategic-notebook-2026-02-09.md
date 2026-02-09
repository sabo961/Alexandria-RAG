# ALEXANDRIA — Strategic Notebook

**Date:** 2026-02-09
**Type:** Technical companion to [Strategic Brief v1.0](./strategic-brief-v1.md)
**Source:** Party Mode session — full technical details and reasoning

This document preserves the detailed technical analysis, schemas, research, and reasoning from the strategic planning session. The Brief is the poster. This is the notebook behind it.

---

## Table of Contents

- [Day 0: Project SOURCE — Connector Details](#day-0-project-source--connector-details)
- [Day 1: SKOS Schema and Data Formats](#day-1-skos-schema-and-data-formats)
- [Day 3: Knowledge Graph Technology Landscape](#day-3-knowledge-graph-technology-landscape)
- [Citaonica vs Speaker's Corner](#citaonica-vs-speakers-corner)
- [The English Filter Problem](#the-english-filter-problem)
- [Knowledge Layer Architecture](#knowledge-layer-architecture)
- [Two Products Insight](#two-products-insight)
- [Tier 2 Sources (Future Connectors)](#tier-2-sources-future-connectors)
- [Neo4j on BUCO — Deployment Details](#neo4j-on-buco--deployment-details)
- [Decision Rationale Log](#decision-rationale-log)

---

## Day 0: PROJECT SOURCE — Connector Details

### BaseConnector Interface

All connectors must implement this common interface:

```python
class BaseConnector:
    """Common interface for all Alexandria source connectors."""

    def search(self, query: str, language: str = None) -> List[Result]:
        """Search for books/texts matching query, optionally filtered by language."""

    def metadata(self, id: str) -> BookMetadata:
        """Get Dublin Core-compatible metadata for a specific item."""

    def download(self, id: str, format: str = "epub") -> Path:
        """Download item in requested format. Returns local file path."""

    def languages(self) -> List[str]:
        """Return list of ISO 639 language codes this source offers."""
```

Existing connectors (`archive_connector.py`, `gutenberg_connector.py`, `calibre_web_connector.py`) should be refactored to this interface when the `scripts/connectors/` package is created.

### Connector-by-Connector Technical Details

#### 1. Wikisource (Priority #1)

- **API:** MediaWiki REST API + WS Export tool
- **EPUB endpoint:** `ws-export.wmcloud.org/book.epub?lang={code}&page={title}`
- **Search:** MediaWiki `action=query` with `list=search` parameter
- **Python tools:** `mwclient` library or raw HTTP requests
- **Key advantage:** One API, 82 languages, direct EPUB output
- **Per-language editions:** French (800K+ texts), German, Russian, Polish, Chinese among largest
- **Metadata quality:** High — structured author, date, source edition, proofreading status
- **Connector effort:** 2-3 days

#### 2. Chinese Text Project (ctext.org)

- **API:** REST API at `ctext.org/tools/api`
- **Python module:** `ctext` (dedicated, documented)
- **Download format:** JSON via API, XML
- **Collection:** 30,000+ works, ~5 billion characters
- **Organization:** By dynasty AND philosophical school (Confucian, Daoist, Legalist, Buddhist, etc.)
- **Key advantage:** The existing taxonomy is a ready-made SKOS seed for Chinese philosophy
- **Bilingual:** Classical Chinese + English translations for many texts
- **Connector effort:** 1-2 days (Python module does heavy lifting)

#### 3. SuttaCentral

- **API:** REST API at `suttacentral.net/api/docs`
- **Bulk data:** GitHub repository `suttacentral/sc-data`
- **Languages:** Pali, Sanskrit, Chinese, Tibetan + 30+ modern translation languages
- **Download format:** EPUB (major collections), HTML, JSON
- **Key advantage:** Segment-aligned parallel texts (Bilara format) — can MEASURE translation fidelity
- **Complete coverage:** Entire Pali Canon (Tipitaka) + Chinese Agama parallels + Sanskrit fragments
- **SKOS seed:** Complete taxonomy of Buddhist teachings by topic
- **Connector effort:** 1-2 days (clone GitHub repo + parse Bilara JSON)

#### 4. Gallica (BnF — Bibliothèque nationale de France)

- **API:** REST API, IIIF Image API, SRU/SRW search, OAI-PMH harvesting
- **Documentation:** `api.bnf.fr`
- **Python wrapper:** `gallipy` (existing open-source)
- **Download format:** PDF, JPEG/TIFF, ALTO XML (OCR text with coordinates)
- **Collection:** 10M+ documents (books, newspapers, manuscripts, maps, music)
- **Languages:** French (primary), Latin, Arabic, Hebrew, colonial-era languages
- **Key advantage:** Definitive for French philosophical tradition (Descartes, Pascal, Montaigne, Voltaire, Rousseau, Diderot, Bergson)
- **Note:** ALTO XML gives structured OCR text with page/line coordinates — needs parser
- **Connector effort:** 3-4 days (ALTO XML parsing adds complexity)

#### 5. Perseus Digital Library / Scaife Viewer

- **API:** CTS (Canonical Text Services) API via CapiTainS at `cts.perseids.org/api/cts`
- **Modern UI:** Scaife Viewer at `scaife.perseus.org`
- **Source data:** TEI XML on GitHub repositories
- **Collection:** 2,412 works, 3,192 editions, 69.7M words (32.1M Greek, 16.3M Latin)
- **Download format:** TEI XML (canonical), plain text from API
- **Key advantage:** Scholarly-grade encoding with word-level morphological annotations, cross-references, critical apparatus
- **Coverage:** Complete surviving corpus of Greek philosophy (Plato, Aristotle, Plotinus, Epictetus, Marcus Aurelius) and Latin philosophy (Cicero, Seneca, Lucretius, Boethius)
- **Note:** Texts come pre-segmented by book/chapter/section — natural RAG chunks
- **Connector effort:** 2-3 days (TEI XML parser needed, but texts are pre-structured)

### Source Taxonomies → SKOS Seeds

Each Tier 1 source provides existing classification systems that can be imported directly into the SKOS backbone instead of being invented from scratch:

| Source | Taxonomy provided | Maps to SKOS |
|--------|------------------|--------------|
| CText | Dynasty + philosophical school | `broader`/`narrower` concept hierarchy |
| SuttaCentral | Buddhist teaching topics, sutta categories | Complete Buddhist concept tree |
| Perseus | Subject classifications, genre, period | Classical philosophy concept tree |
| Gallica | BnF subject headings | French intellectual tradition tree |
| Wikisource | Category trees per language edition | Language-specific concept trees |

---

## Day 1: SKOS Schema and Data Formats

### SKOS-lite YAML Schema (Alexandria Extension)

Human-authored concept files follow this format:

```yaml
# alexandria_concepts.yaml

dasein:
  original_language: de
  translation_fidelity: low        # English loses meaning
  prefLabel:
    de: Dasein                      # Original is PRIMARY
  altLabel:
    en: Being-there                 # Approximation
    hr: Tubitak
  note: >
    Heidegger's concept resists translation. English "being-there"
    loses the unity of existence-in-world that German preserves.
  broader: [phenomenology]
  related: [śūnyatā, être-au-monde]
  untranslatable: true              # Alexandria extension
  wikidata: Q190588

recursion:
  original_language: en
  translation_fidelity: high        # Translates cleanly
  prefLabel:
    en: Recursion
  altLabel:
    hr: Rekurzija
    de: Rekursion
  broader: [mathematics, computer-science]
  related: [self-reference, strange-loops]
  wikidata: Q740724

dukkha:
  original_language: pi             # Pali
  translation_fidelity: low
  prefLabel:
    pi: Dukkha
  altLabel:
    en: Suffering                   # Grossly oversimplified
    hr: Patnja
    sa: Duḥkha                      # Sanskrit cognate
  note: >
    Pali concept encompassing suffering, dissatisfaction,
    impermanence-caused stress. "Suffering" captures perhaps
    30% of the semantic range.
  broader: [four-noble-truths, buddhist-philosophy]
  related: [anicca, anatta, tanha]
  untranslatable: true
  source_taxonomy: suttacentral
  wikidata: Q849584
```

### Alexandria SKOS Extensions

Standard SKOS fields: `prefLabel`, `altLabel`, `broader`, `narrower`, `related`, `exactMatch`, `note`

Alexandria additions:
- `original_language` — ISO 639 code of the concept's origin language
- `translation_fidelity: low/medium/high` — how much meaning survives translation to English
- `untranslatable: true/false` — flag for concepts that resist translation
- `source_taxonomy` — which source provided this concept's classification
- `wikidata` — Wikidata entity ID for external interoperability

### Knowledge Graph Relationship Types

When concepts move from YAML to Neo4j, these relationship types apply:

```
STANDARD SKOS:
  (concept)-[:BROADER]->(concept)
  (concept)-[:NARROWER]->(concept)
  (concept)-[:RELATED]->(concept)
  (concept)-[:EXACT_MATCH]->(wikidata_entity)

DUBLIN CORE (book metadata):
  (book)-[:SUBJECT]->(concept)           # dcterms:subject
  (book)-[:CREATOR]->(author)            # dcterms:creator
  (book)-[:LANGUAGE]->(language)          # dcterms:language

ALEXANDRIA EXTENSIONS:
  (concept)-[:APPROXIMATED_BY {loss: "high"}]->(translation)
  (concept)-[:SOURCED_FROM]->(source_taxonomy)

USER JOURNEY (Day 4):
  (user)-[:READ {timestamp, completion_pct}]->(book)
  (user)-[:SEARCHED {timestamp}]->(concept)
  (user)-[:FOUND_USEFUL {timestamp}]->(chunk)
```

### File Format Decision

- **YAML** → human-authored files (concept definitions, guardian frontmatter, configuration)
- **JSON** → machine-generated data (MCP responses, API contracts, Qdrant payloads)

Rationale: YAML supports comments (critical for translation notes like "this concept resists translation because..."), handles Croatian characters without escaping, and is already the pattern in the codebase (guardian frontmatter).

---

## Day 3: Knowledge Graph Technology Landscape

### Technology Comparison (as of February 2026)

| Technology | Maturity | Cost for 9000 books | Best for |
|---|---|---|---|
| **LightRAG** (HKU, EMNLP 2025) | Production-ready | Low — incremental indexing, ~100 tokens per query | Graph-enhanced RAG on existing Qdrant |
| **Qdrant + Neo4j hybrid** | Production-proven | Zero (both free/OSS) | Dual retrieval: vectors + relationships |
| **Graphiti** (Zep) | Mature experimental | Low | Conversation memory, temporal tracking |
| **Microsoft GraphRAG** | Expensive at scale | **~$3,700 just to index** (GPT-4: 10-20x more) | Global queries across entire corpus |
| **nano-graphrag** | Experimental | Low | Learning/prototyping GraphRAG concepts |
| **fast-graphrag** (Circlemind) | Experimental | Low | 27x faster than standard GraphRAG |

### Why LightRAG is the Sweet Spot

- **Incremental updates:** `apipeline_enqueue_documents` — add books without reindexing entire corpus
- **Qdrant support:** `QdrantVectorDBStorage` is a supported backend
- **Dual-level retrieval:** Low-level (specific entities) + high-level (broad topics spanning entities)
- **Efficiency:** ~80ms latency, 99% token reduction vs Microsoft GraphRAG
- **Performance:** 84.8% win rate on complex queries vs GraphRAG in benchmarks

### Why Microsoft GraphRAG is NOT for Alexandria

- Indexing 9000 books at ~50K words average = 450M words
- Cheapest model (DeepSeek): ~$3,700 for indexing alone
- GPT-4-Turbo: multiply by 10-20x ($37K-$74K)
- Each search query: ~$0.40 (hundreds of API calls for community traversal)
- Scalability wall at ~50K documents

### Why Graphiti is for Day 4, not Day 3

Graphiti is designed for **dynamic conversational data**, not bulk document indexing. Its bi-temporal model (event time vs ingestion time) is perfect for tracking "what did I discuss with Hipatija about epistemology last month?" but NOT for "index 9000 books."

Use Graphiti for Citaonica conversation memory. Use LightRAG + Neo4j for the book knowledge graph.

### LightRAG Proof-of-Concept Plan

1. Pick 100-200 books on ONE well-defined topic cluster (e.g., Greek philosophy, or Buddhist texts)
2. Run LightRAG entity extraction on the subset
3. Use existing Qdrant as vector backend
4. Compare retrieval quality: pure vector search vs graph-enhanced
5. If graph-enhanced wins → scale to full corpus incrementally
6. If not → investigate why before committing to full Neo4j

### Neo4j Deployment

```yaml
# docker-compose.yml addition on BUCO
neo4j:
  image: neo4j:5-community        # FREE, Apache 2.0 license
  ports:
    - "7474:7474"                  # Browser UI
    - "7687:7687"                  # Bolt protocol
  volumes:
    - neo4j_data:/data
  environment:
    NEO4J_AUTH: neo4j/alexandria
    NEO4J_server_memory_heap_initial__size: 4G
    NEO4J_server_memory_heap_max__size: 8G
    NEO4J_server_memory_pagecache_size: 4G
    # Total: ~16 GB RAM. BUCO has 80 GB. Room to spare.
```

### Cypher vs SQL for Graph Queries

```sql
-- SQLite: "find all concepts broader than 'phenomenology'"
WITH RECURSIVE broader_tree AS (
  SELECT id, label FROM concepts WHERE label = 'phenomenology'
  UNION ALL
  SELECT c.id, c.label FROM concepts c
  JOIN concept_relations cr ON c.id = cr.target_id
  JOIN broader_tree bt ON cr.source_id = bt.id
  WHERE cr.relation = 'broader'
)
SELECT * FROM broader_tree;
```

```cypher
// Neo4j: same query
MATCH (c:Concept {label: "phenomenology"})-[:BROADER*]->(broader)
RETURN broader
```

This is why we skip SQLite for graph storage.

---

## Citaonica vs Speaker's Corner

### Current: Speaker's Corner

Location: `alexandria_app.py` Section 4, Streamlit expander.

What it does:
- Text input → RAG query via `perform_rag_query()` → LLM answer
- Pattern selection dropdown (response style templates)
- Sliders: chunks to retrieve, similarity threshold, temperature
- Single-shot Q&A — no conversation memory, no follow-ups

What's already wired:
- `system_prompt` parameter in `perform_rag_query()` at line 564
- Currently fed by `selected_pattern['template']`
- Could be fed by `guardian.compose_system_prompt()` instead

### Future: Citaonica (Reading Room)

Two-step approach:

**Step 1 — Quick Win (anytime, no new infrastructure):**
- Replace pattern selector dropdown with guardian selector dropdown
- Guardian's `personality_prompt` feeds into `system_prompt`
- Same Streamlit, same RAG, same everything — different voice
- Hipatija challenges your questions, Lupita mljacka at pretentious queries, Zec structures answers
- Effort: hours, not days

**Step 2 — Full Citaonica (Day 4, needs Graphiti):**
- Real chat interface with conversation history
- Graphiti temporal memory: "What did I discuss with Hipatija last week?"
- Librarian agent routing via Dispatcher
- CURATOR integration for "What should I read next?"
- New GUI layer (separate from Streamlit scaffold, on top of same `scripts/` package)

---

## The English Filter Problem

### Why BGE-M3 Was an Epistemological Choice

English-only embedding models (e.g., OpenAI text-embedding-ada-002) create a vector space where ALL concepts are filtered through English semantics. This means:

- "Dasein" (German) → embedded as "being-there" → loses Heidegger's unity of existence-in-world
- "тоска/toska" (Russian) → embedded as "melancholy" → loses the ache for something that may not exist
- "śūnyatā" (Sanskrit) → embedded as "emptiness" → loses 2500 years of Buddhist philosophy
- "物の哀れ/mono no aware" (Japanese) → embedded as "sadness of things" → loses the aesthetic appreciation of impermanence
- "inat" (Croatian/Bosnian/Serbian) → embedded as "spite" → loses the self-destructive defiance that defines Balkan resilience

BGE-M3 (multilingual, 1024-dim) preserves the semantic fingerprint in the ORIGINAL language. The vector for "Dasein" in German occupies a DIFFERENT region of semantic space than "being-there" in English. This is not a bug — this is the feature.

### Concepts That Resist English Translation

Examples discussed in session, candidates for `translation_fidelity: low` and `untranslatable: true`:

| Concept | Language | English "translation" | What's actually lost |
|---------|----------|----------------------|---------------------|
| Dasein | German | Being-there | Unity of existence-in-world |
| тоска (toska) | Russian | Melancholy | Ache for something that may not exist |
| saudade | Portuguese | Longing | Yearning for what was loved and lost |
| 物の哀れ (mono no aware) | Japanese | Pathos of things | Gentle sorrow at the passing of things |
| dukkha | Pali | Suffering | Dissatisfaction, impermanence-caused stress |
| śūnyatā | Sanskrit | Emptiness | Dependent origination, lack of inherent existence |
| inat | Croatian | Spite | Defiance that costs more than it's worth but won't stop |
| mljackanje | Croatian | ??? | Shameless joy-sound of eating (Lupita's primary verb) |

### Graph Relationships for Translation Loss

```
(Dasein)-[:APPROXIMATED_BY {loss: "high"}]->(being-there)
(тоска)-[:APPROXIMATED_BY {loss: "high"}]->(melancholy)
(inat)-[:APPROXIMATED_BY {loss: "extreme"}]->(spite)
(recursion)-[:TRANSLATED_AS {loss: "none"}]->(rekurzija)
```

### The "Unknown Unknown" Killer Query

A query only possible with a multilingual knowledge graph:

> "Show me concepts in my library that resist English translation and are connected to each other across languages."

This finds: Dasein ↔ śūnyatā (both resist subject-object dualism), тоска ↔ saudade (both name an absence that defines presence), mono no aware ↔ čežnja (both honor impermanence).

**No English-first system can formulate this query.** Alexandria can.

---

## Knowledge Layer Architecture

### Dependency Graph

```
                    ┌─────────────────────────┐
                    │  MAKER Voting (parked)  │
                    └────────────┬────────────┘
                                 │ needs agents making decisions
                    ┌────────────▼────────────┐
                    │  Temporal Knowledge     │
                    │  Layer (Day 4)          │
                    └────────────┬────────────┘
                                 │ needs graph + user journey data
                    ┌────────────▼────────────┐
                    │  LightRAG on subset     │
                    │  (Day 3)                │
                    └───────────┬─────────────┘
                                │ needs entity/relationship model
         ┌──────────────────────┼───────────────────────┐
         │                      │                       │
┌────────▼────────┐  ┌──────────▼──────────┐  ┌─────────▼────────┐
│  Librarians     │  │  Neo4j + SKOS       │  │  Author Geo Map  │
│  (Day 2)        │  │  (Day 1)            │  │  (anytime)       │
└────────┬────────┘  └──────────┬──────────┘  └──────────────────┘
         │                      │
         └───────────┬──────────┘
              ┌──────▼──────┐
              │ PROJECT:    │
              │ SOURCE      │  ◄── DAY 0
              │ (connectors)│
              └──────┬──────┘
              ┌──────▼──────┐
              │ Alexandria  │
              │ as-is       │
              └─────────────┘
```

### Infrastructure Progression

```
Layer 0: Qdrant + semantic chunks            ← BUILT (current state)
Layer 1: Metadata graph (SKOS in Neo4j)      ← Day 1 (uses data from Day 0 sources)
Layer 2: LightRAG on topic subset            ← Day 3 (proof of concept, ~100 books)
Layer 3: Neo4j for persistent relationships  ← Day 3 (already deployed for SKOS)
Layer 4: Graphiti for conversation memory    ← Day 4 (Citaonica companion)
```

Each layer is ADDITIVE. You never throw away the previous one.

---

## Two Products Insight

John (PM) identified two possible products hiding in Alexandria:

**Product A: "Personal Knowledge Companion"**
- For Sabo (and people like Sabo)
- 9,000 books, semantic search, guardians with personality, reading journey tracking
- Value prop: "I've read hundreds of books and can't remember where I read that thing about consciousness and mathematics. Alexandria finds it in seconds — and tells me what to read next."

**Product B: "Library Intelligence Platform"**
- For institutions
- Multi-connector ingestion, MCP-first API, batch processing, reliability
- Value prop: "Point it at your library, get a semantic search engine with AI agents managing your collection."

**Decision: don't choose yet.** The Librarians concept works for BOTH. Build the shared foundation (Day 0-2). The fork happens later when the Temporal Knowledge Layer decides if it serves one user's journey or many users' queries.

The presence of Lupita (a pig that eats frosting off pretentious text) suggests this is Product A. And that's where the magic is.

---

## Tier 2 Sources (Future Connectors)

Sources worth building connectors for after Tier 1 is complete:

| Source | Collection | Languages | Notes |
|--------|-----------|-----------|-------|
| **Aozora Bunko** | 17,000 Japanese literary works | Japanese | Entire corpus on GitHub. Shift_JIS → UTF-8 conversion needed |
| **Polona** | 3.5M items (National Library of Poland) | Polish, Latin, French, German | `pypolona` Python tool ready. Many scanned images need OCR |
| **Lotsawa House** | 6,000 Tibetan Buddhist texts | Tibetan, EN, FR, DE, ES, PT, CN, JP, KR | EPUB/PDF downloads. No API — needs scraper |
| **Sacred-texts.com** | 1,700 books, 77 categories | English translations (originals referenced) | Static HTML/text files. Broadest religious/mythological coverage |
| **Bayerische Staatsbibliothek** | 3M+ digital copies | German, Latin, Greek | IIIF + OAI-PMH. German philosophy FIRST EDITIONS (Kant, Hegel, Schopenhauer) |
| **Europeana** | 58M items (discovery layer) | All European languages | Metadata portal — links to source institutions. Best as meta-search |
| **HathiTrust** | 6.7M public domain volumes (of 19M total) | 460 languages | Institutional access for bulk. Individual public domain OK |
| **Projekt Runeberg** | ~1,000 Scandinavian works | Swedish, Danish, Norwegian, Finnish, Icelandic | No API — scraping needed |
| **Lib.ru** | Tens of thousands of Russian works | Russian | Frozen since ~2008. Internet Archive has full dump |

---

## Neo4j on BUCO — Deployment Details

### BUCO Server Profile

| Component | Specification |
|-----------|---------------|
| Model | Dell PowerEdge 3660 |
| RAM | 80 GB |
| NVMe | 8 TB (4+2+2 pločice) |
| GPU | NVIDIA A2000, 12GB VRAM, 3,328 CUDA cores |
| Current services | Qdrant (port 6333) |

### Resource Allocation Plan

| Service | RAM | Storage | Port |
|---------|-----|---------|------|
| Qdrant | ~8-10 GB | ~20 GB | 6333 |
| Neo4j | ~16 GB (heap 8G + pagecache 4G + overhead) | ~2 GB initially | 7474 (UI), 7687 (Bolt) |
| **Total** | **~26 GB** | **~22 GB** | |
| **Available** | **~54 GB free** | **~7.98 TB free** | |

### Why Skip SQLite for Graph Storage

SQLite was considered as an intermediate step before Neo4j. Rejected because:
1. BUCO has resources to spare — no need to economize
2. SQLite requires painful recursive CTEs for graph traversal
3. SQLite is single-writer — blocks multi-user future
4. Migration from SQLite → Neo4j is an entire sprint of wasted work
5. SKOS concepts map natively to Neo4j nodes and edges

---

## Decision Rationale Log

### Why SKOS (not custom ontology)

- W3C standard, 20 years old, battle-tested
- Only 6 relationship types — simple enough for a solo developer
- Multilingual by design (`prefLabel`/`altLabel` per language)
- Maps directly to graph databases (Neo4j has SKOS importers)
- Wikidata and Library of Congress use compatible concepts
- You can start with YAML and grow to Neo4j — same concepts, different storage
- Alternative OWL is too complex; custom means maintaining your own standard forever

### Why Neo4j (not SQLite, not NetworkX)

- **vs SQLite:** Graph traversal in SQL = recursive CTEs = pain. Neo4j: one-line Cypher. Also, SQLite is single-writer.
- **vs NetworkX:** In-memory only. Dies when process stops. No persistence. No multi-user.
- **BUCO justification:** 80 GB RAM, 8 TB NVMe. Adding Neo4j = cup of water in swimming pool. No resource constraint.

### Why LightRAG (not Microsoft GraphRAG)

- **Cost:** GraphRAG indexing 9000 books ≈ $3,700 (cheapest model). LightRAG: fraction of that.
- **Incremental:** LightRAG supports adding books without reindexing. GraphRAG requires full regeneration.
- **Qdrant native:** LightRAG has `QdrantVectorDBStorage` backend. GraphRAG does not.
- **Performance:** 84.8% win rate vs GraphRAG in benchmarks, 99% token reduction.

### Why YAML for concepts (not JSON)

- Supports comments (critical for translation notes)
- Croatian characters without escaping ("čežnja" not "\u010de\u017enja")
- More readable for human curation
- Already the pattern in codebase (guardian frontmatter is YAML)
- JSON remains the format for machine-generated data (API responses, Qdrant payloads)

### Why Wikisource is Connector #1 (not CText or SuttaCentral)

- 82 languages from a single API — broadest possible impact
- EPUB output via WS Export — cleanest format for ingestion pipeline
- Covers German philosophy, Russian literature, French philosophy, Chinese texts, Arabic texts — all in one source
- CText and SuttaCentral are deeper but narrower; Wikisource is the ocean, they are the wells

---

*This notebook is a living document. Update it as decisions are validated, rejected, or refined.*

*"Šnjof. Pauza. Tišina. Značenje će doć."* — Lupita 🐖
