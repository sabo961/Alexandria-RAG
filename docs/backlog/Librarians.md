# ALEXANDRIA LIBRARIANS
## Backlog Brief v0.1

### VISION
Specialized BMad agents that serve as an interface between
Alexandria knowledge base and external users (human and AI).
"Library system department" - people come, get what they need.

---

### AGENTS

#### 📚 LIBRARIAN
**Responsibility:** Cataloging, metadata integrity, taxonomy
**Input:** New book, uncategorized content
**Output:** Clean metadata, tags, classification
**Tools:** Qdrant, Calibre API, embedding model
**Trigger:** New book upload, batch import, quality flag

#### 🔍 RESEARCHER
**Responsibility:** Deep semantic search, cross-referencing, synthesis
**Input:** Complex query, research topic
**Output:** Curated findings, related sources, summary
**Tools:** Qdrant semantic search, hierarchical chunks, LLM synthesis
**Trigger:** Query requiring depth, "everything about X", "connect A and B"

#### 🎯 CURATOR
**Responsibility:** Personalized recommendations, reading paths
**Input:** Project/problem context, user profile
**Output:** Ranked recommendations, "start here" paths
**Tools:** User history, similarity matching, project context
**Trigger:** "What should I read about X?", "inspiration for problem Y"

#### 🗄️ ARCHIVIST
**Responsibility:** Maintenance, quality, health checks
**Input:** Scheduled triggers, anomaly detection
**Output:** Quality reports, cleanup actions, refresh tasks
**Tools:** Embedding staleness check, duplicate detection, stats
**Trigger:** Cron, manual audit, quality threshold breach

---

### ORCHESTRATION
```
[QUERY]
   │
   ▼
[DISPATCHER] ──► Query classification
   │
   ├──► Simple lookup ──► LIBRARIAN
   ├──► Deep research ──► RESEARCHER
   ├──► Recommendation ──► CURATOR
   └──► Maintenance ──► ARCHIVIST

[ESCALATION PATH]
LIBRARIAN ◄──► RESEARCHER (when metadata is insufficient)
CURATOR ◄──► RESEARCHER (when recommendation requires deep dive)
ARCHIVIST ──► LIBRARIAN (when problems are found)
```

---

### PHASES

**F0: Infrastructure**
- [ ] Auto-Claude setup
- [ ] BMad Builder installation
- [ ] MCP connector Alexandria ◄► Auto-Claude

**F1: LIBRARIAN (MVP)**
- [ ] Agent persona definition
- [ ] Calibre sync workflow
- [ ] Basic metadata extraction
- [ ] Qdrant upsert pipeline

**F2: RESEARCHER**
- [ ] Semantic search wrapper
- [ ] Cross-reference logic
- [ ] Synthesis prompt engineering
- [ ] Citation/source tracking

**F3: CURATOR**
- [ ] User context ingestion
- [ ] Recommendation algorithm
- [ ] Reading path generation

**F4: ARCHIVIST**
- [ ] Health check suite
- [ ] Scheduled maintenance
- [ ] Quality metrics dashboard

**F5: Integration**
- [ ] Dispatcher logic
- [ ] Inter-agent communication
- [ ] External API (for "external users")

---

### DEPENDENCIES
- Alexandria Qdrant instance (existing)
- Auto-Claude (installation in progress)
- BMad Builder module
- MCP server for external access

---

### OPEN QUESTIONS
1. Auth model for external users - who can access?
2. Rate limiting - how many queries per agent?
3. Priorities - which agent goes first?
4. Logging - what do we track?
