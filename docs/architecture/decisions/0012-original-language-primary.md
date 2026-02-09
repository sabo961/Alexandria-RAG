# ADR 0012: Original Language Primary

## Status
Accepted

## Date
2026-02-09

## Context

Alexandria is a multilingual knowledge platform with 9,000+ books spanning German philosophy, Russian literature, South American writers, Buddhist texts, classical Greek/Latin, Croatian, and many other traditions.

### The English Filter Problem

Standard RAG systems embed all text through English-centric models. This creates a systemic distortion:

- **"Dasein"** (German) → embedded as "being-there" → loses Heidegger's unity of existence-in-world
- **"тоска" (toska)** (Russian) → embedded as "melancholy" → loses the ache for something that may not exist
- **"śūnyatā"** (Sanskrit) → embedded as "emptiness" → loses 2,500 years of Buddhist philosophy
- **"dukkha"** (Pali) → embedded as "suffering" → captures perhaps 30% of the semantic range
- **"saudade"** (Portuguese) → embedded as "longing" → loses the yearning for what was loved and lost
- **"物の哀れ (mono no aware)"** (Japanese) → embedded as "sadness of things" → loses aesthetic appreciation of impermanence
- **"inat"** (Croatian/Bosnian/Serbian) → embedded as "spite" → loses self-destructive defiance that defines Balkan resilience

English is not a neutral medium. English is a **filter** that deforms the semantic field of concepts from other linguistic traditions.

### Embedding Model Choice (ADR 0010)

BGE-M3 (1024-dim, 100+ languages) was chosen in ADR 0010 for GPU performance, but the deeper reason is epistemological: it preserves the semantic fingerprint in the original language. The vector for "Dasein" in German occupies a DIFFERENT region of semantic space than "being-there" in English. This is the feature, not the bug.

### Metadata Convention

Without an explicit policy, metadata defaults to English:
- Calibre stores subjects as English tags
- Search interfaces present results in English
- Concept labels default to English `prefLabel`

This creates a mismatch: embeddings preserve multilingual semantics, but metadata flattens everything back to English.

## Decision

**Original language is always primary. English is an approximation.**

This applies across all layers of the system:

### 1. SKOS Concept Labels

```yaml
# CORRECT: Original language is prefLabel
dasein:
  prefLabel:
    de: Dasein                    # PRIMARY
  altLabel:
    en: Being-there               # APPROXIMATION
    hr: Tubitak

# WRONG: English as default
dasein:
  prefLabel:
    en: Being-there               # THIS IS NOT THE CONCEPT
  altLabel:
    de: Dasein
```

### 2. Translation Fidelity Tracking

Every concept carries a `translation_fidelity` field:

```yaml
translation_fidelity: low    # English loses significant meaning
translation_fidelity: medium # English approximates but misses nuance
translation_fidelity: high   # Translates cleanly (e.g., "recursion")
```

Concepts with `translation_fidelity: low` are flagged as `untranslatable: true`.

### 3. Graph Relationships

Translation loss is modeled as a typed relationship:

```cypher
(Dasein)-[:APPROXIMATED_BY {loss: "high"}]->(being_there)
(recursion)-[:TRANSLATED_AS {loss: "none"}]->(rekurzija)
```

### 4. Agent Behavior

When a guardian or librarian agent encounters a concept with `translation_fidelity: low`:
- Quote the original language term first
- Provide the English approximation with a warning
- Example: *"The original concept is 'Dasein' (German). English approximation: 'being-there'. Warning: translation loses significant nuance."*

### 5. Retrieval

When searching, the system:
- Embeds the query with BGE-M3 (preserving multilingual semantics)
- Returns results with original-language concept labels
- Flags when results span untranslatable concepts

## Consequences

### Positive
- Preserves semantic integrity across 100+ languages
- Enables the "unknown unknown" killer query: *"Show me concepts in my library that resist English translation and are connected across languages"*
- Aligns metadata with embedding model behavior (BGE-M3 already preserves this; now metadata does too)
- SKOS multilingual labels provide free interoperability with other knowledge systems
- Makes Alexandria fundamentally different from English-first RAG systems

### Negative
- Concept curation requires multilingual awareness (harder for English-only contributors)
- UI must handle non-Latin scripts gracefully
- More complex concept files (prefLabel per language vs single string)

### Neutral
- Does not require users to speak other languages — the system mediates between original and user language
- Concepts that translate cleanly (e.g., mathematical terms) are unaffected by this policy

## Alternatives Considered

### Alternative 1: English as Default, Other Languages as Supplements
**Approach:** English `prefLabel`, other languages as `altLabel`
**Rejected:** Perpetuates the English filter. Misaligns with BGE-M3 embedding behavior. Concepts like "Dasein" are NOT English concepts with German translations — they are German concepts that English approximates.

### Alternative 2: No Language Policy (Let It Evolve)
**Approach:** Don't specify, let each concept define its own primary language organically
**Rejected:** Without policy, English wins by default (Calibre metadata, developer habits, LLM training data bias). Explicit policy needed.

### Alternative 3: All Languages Equal (No Primary)
**Approach:** All language labels are equal, no `prefLabel`/`altLabel` distinction
**Rejected:** SKOS requires `prefLabel`. Also, conceptual accuracy matters — "Dasein" IS the concept, "being-there" is a lossy encoding.

## Related Decisions

- [ADR 0010: GPU-Accelerated Embedding Model Selection](0010-gpu-accelerated-embeddings.md) — BGE-M3 choice enables this policy
- [ADR 0013: SKOS Ontology Backbone](0013-skos-ontology-backbone.md) — SKOS provides the multilingual label structure
- [ADR 0007: Universal Semantic Chunking](0007-universal-semantic-chunking.md) — Chunks preserve original language text

## References

- **Strategic Brief:** `docs/development/strategic-brief-v1.md` — Core Philosophical Commitment section
- **Strategic Notebook:** `docs/development/strategic-notebook-2026-02-09.md` — The English Filter Problem section
- **BGE-M3 Paper:** https://arxiv.org/abs/2402.03216
- **SKOS Reference:** https://www.w3.org/2004/02/skos/

---

**Author:** Party Mode session (Sabo + BMAD team)
**Reviewers:** Hipatija (challenged assumptions), Winston (architecture), Paige (schema design)
**Origin:** Strategic planning session 2026-02-09
