# ALEXANDRIA — Strategic Brief v1.0

**Date:** 2026-02-09
**Status:** REVIEW — objections welcome for 3 days
**Authors:** Party Mode session (Sabo + full BMAD team + Lupita)
**Companion:** [Strategic Notebook](./strategic-notebook-2026-02-09.md) — full technical details

---

## What Alexandria IS

A multilingual knowledge platform over 9,000+ books. RAG engine with semantic chunking, MCP-first architecture, guardian persona system (11 guardians), and multilingual embeddings (bge-m3, 1024-dim).

## What Alexandria WANTS TO BE

A system that **knows what you don't know you should ask about** — across languages, traditions, and centuries. Not a search engine. A knowledge companion that preserves meaning in its original linguistic form and reveals connections the English filter hides.

---

## Core Philosophical Commitment

**Original language is always primary. English is an approximation.**

- Kant wrote in German. "Dasein" is not "being-there."
- Dostoevsky wrote in Russian. "Toska" is not "melancholy."
- Laozi wrote in Chinese. "Dao" is not "The Way."
- The Pali Canon says "dukkha," not "suffering."
- BGE-M3 was chosen precisely because it preserves these semantic distinctions.

This is not a feature. This is the foundation everything else stands on.

---

## The Five Layers of Knowledge

Inspired by Johari's Window, applied to a knowledge system:

```
L4  UNKNOWN UNKNOWNS    Graph traversal reveals paths you never
                         thought to ask about. "Plato connects to
                         Sufism through Neoplatonism. You have 3
                         books on this. You've opened zero."

L3  GROUP KNOWLEDGE      What the team/community knows collectively.
                         Merged reading graphs, shared gaps.

L2  MY KNOWLEDGE         What I've read, searched, found useful.
                         Personal journey tracked over time.

L1  SHARED LIBRARY       Everything Alexandria knows. 9,000+ books.
                         Semantic search. RAG. (BUILT)

L0  SECRETS              Private notes, annotations, research drafts.
                         Per-user Qdrant collections.
```

Each layer builds on the one below. L1 is built. L0 is a config change. L2 needs event logging. L3-L4 need the knowledge graph.

---

## Development Roadmap

### Day 0: PROJECT SOURCE

**"There is no library without books."** — Lupita

Before ontologies, before agents, before graphs: get the right texts, in the right languages, from the right places, in clean formats.

**Current connectors (3):**
- Internet Archive (primary multilingual source)
- Project Gutenberg (mostly English)
- Calibre-Web (personal library bridge)

**New connectors to build (5):**

| # | Source | Why | Languages | Effort |
|---|--------|-----|-----------|--------|
| 1 | **Wikisource** | 6.75M texts, EPUB API, 82 languages | ALL | 2-3 days |
| 2 | **Chinese Text Project** | 30,000 works, entire Chinese philosophy | Classical Chinese + EN | 1-2 days |
| 3 | **SuttaCentral** | Complete Buddhist canon, parallel texts | Pali, Sanskrit, Chinese, Tibetan + 30 modern | 1-2 days |
| 4 | **Gallica (BnF)** | 10M docs, French philosophy originals | French, Latin, Arabic | 3-4 days |
| 5 | **Perseus** | Classical Greek/Latin, scholarly TEI | Ancient Greek, Latin | 2-3 days |

**Architecture:** Common `BaseConnector` interface (search, metadata, download, languages). All connectors conform to same pattern. LIBRARIAN agent calls them uniformly.

> Details: [Strategic Notebook — Connector Architecture](./strategic-notebook-2026-02-09.md#day-0-project-source--connector-details)

### Day 1: SKOS ONTOLOGY BACKBONE

**Standard:** SKOS (W3C) — not custom. Six relationship types. Battle-tested. Interoperable.

**Key decisions:**
- Original language as `prefLabel`, English as `altLabel`
- `translation_fidelity: low/medium/high` per concept
- Seed from source taxonomies (CText schools, SuttaCentral taxonomy, Perseus categories)
- Start with ~200-300 concepts. Grow organically.
- Storage: YAML files for authoring, Neo4j for querying

**Interoperability:** Dublin Core for book metadata, SKOS for concepts, Wikidata links for external mapping. Alexandria speaks the world's language, not its own dialect.

> Details: [Strategic Notebook — SKOS Schema](./strategic-notebook-2026-02-09.md#day-1-skos-schema-and-data-formats)

### Day 2: AGENTS (Librarians + Guardians)

**Librarians** (WHAT they do):
- LIBRARIAN — cataloging, metadata integrity, SKOS tagging
- RESEARCHER — deep semantic search, cross-referencing, synthesis
- CURATOR — recommendations, reading paths, "unknown unknowns"
- ARCHIVIST — health checks, quality, maintenance

**Guardians** (WHO speaks): Alan Kay, Ariadne, Fantom iz opere, Hector, Hipatija, Klepac, Mrljac, Lupita, Roda, Vault-E, Zec

Orthogonal design: Guardian = personality, Librarian = capability. Compose at runtime.

**Dispatcher:** Query classification routes to specialist. Simple lookup -> LIBRARIAN. Deep research -> RESEARCHER. "What should I read?" -> CURATOR. Maintenance -> ARCHIVIST.

### Day 3: KNOWLEDGE GRAPH

**Infrastructure:** Neo4j on BUCO (Dell PowerEdge 3660, 80GB RAM, 8TB NVMe). Docker. Free Community Edition. Already runs Qdrant at ~20% capacity.

**LightRAG** proof-of-concept on 100-200 books from one topic cluster. Validate that graph-enhanced retrieval beats pure vector search. If yes, scale. If no, investigate.

**Hybrid retrieval:** Qdrant for fast similarity, Neo4j for relationship traversal. Shared IDs. Combined context for LLM.

> Details: [Strategic Notebook — Knowledge Graph Technology](./strategic-notebook-2026-02-09.md#day-3-knowledge-graph-technology-landscape)

### Day 4: TEMPORAL KNOWLEDGE LAYER

**Graphiti** for conversation memory in Citaonica (reading room chat interface). Track research journeys: what was asked, what was discovered, how understanding evolved.

**Citaonica** replaces Speaker's Corner (current Streamlit Q&A expander) with a guardian-powered conversational interface. Two-step approach: quick guardian swap in existing UI now, full chat with Graphiti memory later.

**Event logging** (starts Day 0): Track queries, found-useful signals, reading history. Feeds the temporal layer when it arrives.

> Details: [Strategic Notebook — Citaonica Design](./strategic-notebook-2026-02-09.md#citaonica-vs-speakers-corner)

---

## Key Architectural Decisions

| Decision | Call | Type | ADR needed? |
|----------|------|------|-------------|
| Embedding model | **bge-m3** (multilingual, 1024-dim) | Type 1 — committed | Already decided |
| Language priority | **Original language primary** | Type 1 — committed | [ADR-0012](../architecture/decisions/0012-original-language-primary.md) |
| Ontology backbone | **SKOS (W3C standard)** | Type 1 — committed | [ADR-0013](../architecture/decisions/0013-skos-ontology-backbone.md) |
| Concept storage | **Neo4j on BUCO** (skip SQLite) | Type 2 — easy to start | No |
| File formats | **YAML for humans, JSON for machines** | Type 2 — already the pattern | No |
| GUI strategy | **Streamlit = personal scaffold, MCP = primary** | Type 2 — ADR-0003 stands | No |
| MAKER voting | **Parked** — needs autonomous agents first | Future | No |

---

## Infrastructure: BUCO

| Component | Spec | Current load | After Neo4j |
|-----------|------|-------------|-------------|
| RAM | 80 GB | ~10 GB (Qdrant) | ~25 GB |
| NVMe | 8 TB (4+2+2) | ~50 GB | ~52 GB |
| GPU | A2000 12GB | Idle (ingestion only) | Idle |
| **Headroom** | | **~85% free** | **~70% free** |

---

## Open Questions (Objections Welcome)

1. **Connector priority order** — is Wikisource really #1, or should CText/SuttaCentral come first given the "skinuti engleski filtar" mission?
2. **SKOS granularity** — how deep do we go? Top-level schools of thought, or down to individual concepts?
3. **Neo4j vs SQLite for Day 0** — do we really need Neo4j before we have SKOS content, or is SQLite fine for connector metadata?
4. **Citaonica timeline** — Phase 2 GUI is Day 4, but is there demand sooner?
5. **What did we miss?** — The Phantom of the Opera has not spoken. Objections, counterarguments, and uncomfortable questions are welcome.

---

## Who Said What

- **Hipatija** challenged the English filter assumption and validated the epistemological foundation
- **Winston** drew the layer architecture and dependency graph
- **Mary** identified the Johari Window model and competitive moat
- **Bob** structured the backlog and identified Type 1 vs Type 2 decisions
- **Amelia** assessed connector APIs and recommended YAML + Neo4j
- **Paige** designed the SKOS-lite format with `translation_fidelity`
- **John** identified two possible products (Personal Companion vs Library Platform) and said "don't choose yet"
- **Lupita** reprioritized the entire roadmap with one sentence

---

*Ovaj brief je rezultat Party Mode sesije. Odstoji 3 dana. Tko ima prigovor — neka govori ili zauvijek suti.*

*Osim Lupite. Ona ne suti nikad.* 🐖
