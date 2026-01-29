# ALEXANDRIA TEMPORAL KNOWLEDGE LAYER
## Backlog Brief v0.1

### VISION
Temporal dimension of knowledge. Alexandria stops being a "book database"
and becomes a MAP OF INTELLECTUAL JOURNEY through knowledge space.
Every query has context: where you're coming from, what you know, where you're going.

Powered by Graphiti + Neo4j.

---

### PROBLEM

Classic RAG is AMNESIC:
- "Find similar" → here's 5 chunks
- No interaction history
- No evolution of understanding
- Every query is "first time"

Knowledge is not a snapshot. Knowledge is a JOURNEY.

---

### ARCHITECTURE
```
┌─────────────────────────────────────────────────────┐
│           GRAPHITI KNOWLEDGE GRAPH                  │
│  ═══════════════════════════════════════════════    │
│                                                     │
│  ENTITIES:                                          │
│  ├── 📚 Books                                       │
│  ├── 👤 Authors                                     │
│  ├── 💡 Concepts                                    │
│  ├── 🏛️ Schools of thought                         │
│  ├── 📅 Periods                                     │
│  └── 🧑 Users                                       │
│                                                     │
│  RELATIONSHIPS (temporal):                          │
│  ├── WROTE (author → book)                          │
│  ├── CITES (book → book)                            │
│  ├── RELATED_TO (concept ↔ concept)                 │
│  ├── BELONGS_TO (book → school)                     │
│  ├── READ (user → book) [WHEN]                      │
│  ├── SEARCHED (user → concept) [WHEN]               │
│  └── FOUND_USEFUL (user → chunk) [WHEN]             │
│                                                     │
│  BI-TEMPORAL MODEL:                                 │
│  ├── t_event: When it HAPPENED                      │
│  └── t_ingested: When we LEARNED                    │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│              QDRANT VECTOR LAYER                    │
│  ═══════════════════════════════════════════════    │
│  • Chunk embeddings                                 │
│  • Semantic similarity                              │
│  • Full-text search                                 │
│  • Fast content retrieval                           │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│              9000 BOOKS (Calibre)                   │
└─────────────────────────────────────────────────────┘
```

---

### QUERY FLOW
```
QUERY: "Books about consciousness that use mathematics"

STEP 1: GRAPHITI - Graph Traversal
─────────────────────────────────────
- consciousness ──► linked_concepts ──► mathematics
- Result: [GEB, Strange Loop, Emperor's New Mind...]
- PLUS: "Sabo already read GEB"
- PLUS: "Last searched consciousness: 2024-09"

STEP 2: PERSONALIZATION
─────────────────────────────────────
- Filter: remove already read (or rank lower)
- Boost: authors already read (Hofstadter)
- Suggest: "Next logical step on your journey"

STEP 3: QDRANT - Content Retrieval
─────────────────────────────────────
- Deep dive into specific chunks
- Relevant passages from selected books

STEP 4: RESPONSE + GRAPH UPDATE
─────────────────────────────────────
- Return results
- RECORD: Sabo searched X, got Y, at time Z
```

---

### GRAPH ENTITIES - DETAILS

#### 📚 BOOK NODE
```yaml
Book:
  id: uuid
  title: string
  calibre_id: int

  # Relationships
  written_by: -> Author
  cites: -> Book[]
  cited_by: -> Book[]
  covers_concepts: -> Concept[]
  belongs_to_school: -> School
  from_period: -> Period
```

#### 👤 AUTHOR NODE
```yaml
Author:
  id: uuid
  name: string

  # Relationships
  wrote: -> Book[]
  influenced_by: -> Author[]
  influences: -> Author[]
  associated_with: -> School[]
```

#### 💡 CONCEPT NODE
```yaml
Concept:
  id: uuid
  name: string
  description: string

  # Relationships
  related_to: -> Concept[]
  parent_concept: -> Concept
  child_concepts: -> Concept[]
  appears_in: -> Book[]
```

#### 🧑 USER JOURNEY NODE
```yaml
UserJourney:
  user_id: uuid

  # Temporal relationships
  read: -> Book[] [timestamp, completion%]
  searched: -> Concept[] [timestamp, found_useful: bool]
  bookmarked: -> Chunk[] [timestamp]
  path: -> ReadingPath[] [created, active]
```

---

### TEMPORAL QUERIES
```cypher
// What did Sabo read about consciousness BEFORE discovering Hofstadter?
MATCH (u:User {name: "Sabo"})-[r:READ]->(b:Book)-[:COVERS]->(c:Concept {name: "consciousness"})
WHERE r.timestamp < date("2024-06-01")
RETURN b.title, r.timestamp
ORDER BY r.timestamp

// How did understanding of "recursion" evolve?
MATCH path = (u:User)-[r:SEARCHED*]->(c:Concept {name: "recursion"})
RETURN r.timestamp, r.context, r.found_useful
ORDER BY r.timestamp

// Recommend NEXT book on the path
MATCH (u:User)-[:READ]->(read:Book)-[:CITES]->(next:Book)
WHERE NOT (u)-[:READ]->(next)
AND (next)-[:COVERS]->(c:Concept)<-[:SEARCHED]-(u)
RETURN next, count(*) as relevance
ORDER BY relevance DESC
LIMIT 5
```

---

### SYNC PIPELINE
```
CALIBRE LIBRARY          GRAPHITI              QDRANT
     │                      │                     │
     │  [New book]          │                     │
     ├─────────────────────►│                     │
     │                      │                     │
     │          [Extract entities]                │
     │          [Create nodes]                    │
     │          [Detect relationships]            │
     │                      │                     │
     │                      │  [Chunk + Embed]    │
     │                      ├────────────────────►│
     │                      │                     │
     │          [Link book → chunks]              │
     │                      │                     │

ENTITY EXTRACTION (per book):
├── Authors (NER + metadata)
├── Cited books (bibliography parsing)
├── Concepts (LLM extraction)
├── People (NER)
├── Time periods
└── Schools of thought (LLM classification)
```

---

### IMPLEMENTATION PHASES

**F0: Infrastructure**
- [ ] Neo4j instance (Docker)
- [ ] Graphiti setup
- [ ] Connect to existing Qdrant
- [ ] Basic MCP connector

**F1: Book Graph (static)**
- [ ] Book nodes from Calibre
- [ ] Author nodes + WROTE relationships
- [ ] Concept extraction pipeline
- [ ] CITES relationships (bibliography parsing)

**F2: Relationship Discovery**
- [ ] Concept linking (RELATED_TO)
- [ ] Author influence mapping
- [ ] School/Period classification
- [ ] Cross-book concept mapping

**F3: User Journey Tracking**
- [ ] User node
- [ ] READ relationships with timestamp
- [ ] SEARCHED log
- [ ] FOUND_USEFUL feedback loop

**F4: Personalized Retrieval**
- [ ] "Next book" recommendation
- [ ] "Already know" context injection
- [ ] Reading path generation
- [ ] Knowledge gap detection

**F5: Temporal Queries**
- [ ] "How did my understanding of X evolve?"
- [ ] "What did I know about Y before date Z?"
- [ ] "Path from book A to book B through concepts"

---

### INTEGRATION WITH LIBRARIANS
```
┌─────────────────────────────────────────────┐
│  LIBRARIANS (BMad agents)                   │
├─────────────────────────────────────────────┤
│                                             │
│  LIBRARIAN ──► Entity extraction            │
│               ──► Graph node creation       │
│               ──► Relationship detection    │
│                                             │
│  RESEARCHER ──► Graph traversal             │
│              ──► Temporal queries           │
│              ──► Path finding               │
│                                             │
│  CURATOR ────► User journey analysis        │
│             ──► Personalized recommendations│
│             ──► Reading path generation     │
│                                             │
│  ARCHIVIST ──► Graph health checks          │
│             ──► Orphan node detection       │
│             ──► Relationship validation     │
│                                             │
└─────────────────────────────────────────────┘
```

---

### METRICS

| Metric | Description | Target |
|---------|-------------|--------|
| Graph coverage | % books with extracted entities | >90% |
| Concept linkage | Avg relationships per concept | >5 |
| Path findability | % successful "A→B" queries | >80% |
| Recommendation relevance | User feedback score | >4/5 |
| Query latency | Graph traversal time | <500ms |

---

### OPEN QUESTIONS

1. **Entity extraction model** - LLM or specialized NER?
2. **Concept taxonomy** - Flat or hierarchical?
3. **User privacy** - Journey data local or sync?
4. **Graph size** - Scaling for 50k+ books?
5. **Feedback loop** - How does user mark "useful"?

---

### REFERENCE

- [Graphiti GitHub](https://github.com/getzep/graphiti)
- [Zep Paper](https://arxiv.org/abs/2501.13956)
- [Neo4j + Graphiti Blog](https://neo4j.com/blog/developer/graphiti-knowledge-graph-memory/)
- Alexandria existing Qdrant setup
