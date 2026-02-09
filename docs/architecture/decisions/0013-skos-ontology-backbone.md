# ADR 0013: SKOS Ontology Backbone

## Status
Accepted

## Date
2026-02-09

## Context

Alexandria needs a concept organization system to model relationships between topics, authors, schools of thought, and traditions across 9,000+ books. This becomes critical with the planned Librarian agents (LIBRARIAN, RESEARCHER, CURATOR, ARCHIVIST) and the Neo4j knowledge graph.

### The Problem

Current state: Calibre stores subjects as flat, unrelated English tags.

```
Book: "Gödel, Escher, Bach"
  tags: ["mathematics", "consciousness", "recursion"]
```

No relationships. "recursion" doesn't know it's related to "self-reference." "consciousness" doesn't know it's broader than "qualia." Tags are strings. The system can search for them but cannot reason about them.

### Requirements

1. **Relationships between concepts** — broader, narrower, related
2. **Multilingual labels** — Croatian + English minimum, original languages for untranslatable concepts (ADR 0012)
3. **Interoperability** — must connect to external knowledge systems (Wikidata, Library of Congress)
4. **Seeded from sources** — source taxonomies (CText, SuttaCentral, Perseus) should import directly, not be reinvented
5. **Evolvable** — start with 200-300 concepts, grow to thousands organically
6. **Lightweight** — must be maintainable by a solo developer

## Decision

**Adopt W3C SKOS (Simple Knowledge Organization System) as Alexandria's ontology backbone.**

### Why SKOS

SKOS is a W3C standard specifically designed for knowledge organization systems (thesauri, taxonomies, classification schemes). It provides exactly six core relationship types:

| Relationship | Purpose | Example |
|---|---|---|
| `skos:broader` | Concept is more general | recursion → mathematics |
| `skos:narrower` | Concept is more specific | mathematics → recursion |
| `skos:related` | Concepts are associated | recursion → self-reference |
| `skos:prefLabel` | Primary name (per language) | de: "Dasein" |
| `skos:altLabel` | Alternative name (per language) | en: "Being-there" |
| `skos:exactMatch` | Same concept in another system | wikidata:Q740724 |

Six types. Not 60. Not 600. This is the minimum viable ontology — and it's a 20-year-old W3C standard.

### Alexandria Extensions

SKOS is extended with three Alexandria-specific fields:

```yaml
dasein:
  original_language: de              # ISO 639 code
  translation_fidelity: low          # low / medium / high
  untranslatable: true               # flag for concepts resisting translation
  prefLabel:
    de: Dasein
  altLabel:
    en: Being-there
    hr: Tubitak
  broader: [phenomenology]
  related: [śūnyatā, être-au-monde]
  wikidata: Q190588
  source_taxonomy: wikisource_de     # which source provided this
```

Standard SKOS tools can read and process these files (they ignore unknown fields). Alexandria agents use the extensions for richer behavior.

### Data Format

**YAML for human authoring:**
```yaml
# concepts/philosophy.yaml
phenomenology:
  original_language: de
  translation_fidelity: medium
  prefLabel:
    de: Phänomenologie
    en: Phenomenology
    hr: Fenomenologija
  broader: [philosophy]
  narrower: [dasein, intentionality, lifeworld]
  related: [existentialism, hermeneutics]
  wikidata: Q131015
```

**Neo4j for querying:**
```cypher
// Import: YAML concepts become nodes
CREATE (c:Concept {
  id: "phenomenology",
  original_language: "de",
  translation_fidelity: "medium"
})
SET c.prefLabel_de = "Phänomenologie"
SET c.prefLabel_en = "Phenomenology"
SET c.prefLabel_hr = "Fenomenologija"

// Relationships become edges
MATCH (a:Concept {id: "phenomenology"}), (b:Concept {id: "dasein"})
CREATE (a)-[:NARROWER]->(b)
CREATE (b)-[:BROADER]->(a)
```

**Cypher query — find everything related to phenomenology:**
```cypher
MATCH (c:Concept {id: "phenomenology"})-[:NARROWER|RELATED*1..3]->(related)
RETURN related.id, related.prefLabel_de, related.prefLabel_en
```

### Concept Seeding Strategy

Do NOT invent the taxonomy from scratch. Import from source taxonomies:

| Source | Taxonomy provided | Import method |
|---|---|---|
| **Chinese Text Project** | Dynasty + philosophical school | API: `ctext.org/tools/api` |
| **SuttaCentral** | Buddhist teaching categories | GitHub: `sc-data` repo |
| **Perseus** | Subject classifications, genre, period | CTS API metadata |
| **Gallica (BnF)** | BnF subject headings | OAI-PMH metadata |
| **Wikisource** | Category trees per language | MediaWiki API categories |
| **Wikidata** | Universal concept graph | SPARQL / `skos:exactMatch` |

Start with 200-300 concepts seeded from these sources. The LIBRARIAN agent grows the taxonomy as new books are ingested.

### Interoperability

| Standard | Purpose in Alexandria |
|---|---|
| **SKOS** | Concept organization (broader/narrower/related) |
| **Dublin Core** (dcterms) | Book metadata (subject, creator, language) |
| **Wikidata** | External entity linking via `skos:exactMatch` |

A SKOS-compatible tool (e.g., Skosmos, PoolParty) can read Alexandria's concept files. Library systems using Library of Congress Subject Headings can map via `skos:exactMatch`. Alexandria is not an island.

### Storage Progression

```
Today:     YAML files (human-authored concepts)
                ↓
Day 1:     Neo4j (import YAML → nodes/edges)
                ↓
Day 3+:    Neo4j + LightRAG (graph-enhanced retrieval)
```

YAML remains the authoring format. Neo4j is the runtime query engine. No conflict — same concepts, different access patterns.

## Consequences

### Positive
- Standard-based — 20-year W3C standard, no maintenance burden
- Multilingual by design — `prefLabel`/`altLabel` per language natively
- Interoperable — Wikidata, Library of Congress, other SKOS systems can exchange data
- Simple — 6 relationship types, learnable in 15 minutes
- Graph-native — SKOS concepts map directly to Neo4j nodes and edges
- Source-seeded — taxonomies imported from CText, SuttaCentral, Perseus, not invented
- Evolvable — start with 200, grow to 20,000 without schema changes

### Negative
- Learning curve — SKOS terminology is new (but simpler than SQL)
- YAML curation — someone must maintain concept files (LIBRARIAN agent helps)
- Limited expressiveness — SKOS cannot model complex ontological relationships (for that, you need OWL, which is deliberately avoided)

### Neutral
- Alexandria extensions (`translation_fidelity`, `untranslatable`, `source_taxonomy`) are non-standard but harmless — standard tools ignore them
- Re-tagging existing Calibre books to SKOS concepts is an ongoing process, not a one-time migration

## Alternatives Considered

### Alternative 1: Custom Ontology
**Approach:** Design Alexandria-specific concept model from scratch
**Rejected:** Means maintaining your own standard forever. No interoperability. No external tools. Reinventing what W3C already solved.

### Alternative 2: OWL (Web Ontology Language)
**Approach:** Full ontology with classes, properties, restrictions, reasoning
**Pros:** Maximum expressiveness
**Rejected:** Massively complex. Requires ontology engineering expertise. Overkill for a knowledge organization system. SKOS is specifically designed for this use case; OWL is designed for formal reasoning.

### Alternative 3: Flat Tags (Status Quo)
**Approach:** Keep Calibre's flat subject tags, add more tags
**Rejected:** No relationships. "recursion" and "self-reference" remain disconnected. Cannot support graph traversal, CURATOR recommendations, or "unknown unknown" discovery.

### Alternative 4: Schema.org
**Approach:** Use Schema.org vocabulary for structuring knowledge
**Pros:** Widely adopted, SEO-friendly
**Rejected:** Schema.org is designed for web content markup, not knowledge organization. No native broader/narrower/related relationships. SKOS is the right tool for this job.

## Related Decisions

- [ADR 0012: Original Language Primary](0012-original-language-primary.md) — Defines the `prefLabel` language policy
- [ADR 0001: Use Qdrant Vector DB](0001-use-qdrant-vector-db.md) — SKOS concepts link to Qdrant chunks via `dcterms:subject`
- [ADR 0007: Universal Semantic Chunking](0007-universal-semantic-chunking.md) — Chunks carry concept metadata
- [ADR 0011: Phased Growth Architecture](0011-phased-growth-architecture.md) — SKOS enables the graph layer (Day 1→3)

## References

- **SKOS Reference:** https://www.w3.org/2004/02/skos/
- **SKOS Primer:** https://www.w3.org/TR/skos-primer/
- **Strategic Brief:** `docs/development/strategic-brief-v1.md` — Day 1: SKOS Ontology Backbone
- **Strategic Notebook:** `docs/development/strategic-notebook-2026-02-09.md` — SKOS Schema and Data Formats section

---

**Author:** Party Mode session (Sabo + BMAD team)
**Reviewers:** Paige (schema design), Winston (architecture), Bob (backlog impact)
**Origin:** Strategic planning session 2026-02-09
