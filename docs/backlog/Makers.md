# ALEXANDRIA MAKER LAYER
## Backlog Brief v0.1

### VISION
Voting/consensus mechanism for critical decisions within Alexandria system.
Inspired by MAKER methodology (Cognizant AI Lab) - atomic steps,
parallel agents, consensus validation. Zero-error on critical matters.

---

### PROBLEM

Librarians work autonomously. Most decisions are OK if 80% accurate.
But some decisions are CRITICAL:

- Wrong classification of rare book
- Wrong cross-reference spreading misinformation
- Recommendation leading in wrong direction
- Deleting a "duplicate" that isn't duplicate

Cost of error: polluted database, lost trust, hours of fixing.

---

### MAKER PRINCIPLES (adapted)

#### 1. ATOMIC DECOMPOSITION
Break decision into smallest possible steps.
No: "Classify this book"
Yes: "Is this fiction?" → "Is this 20th century?" → "Is this Europe?"

#### 2. PARALLEL EXECUTION
Multiple instances work same step simultaneously.
3x LIBRARIAN gets same task, work independently.

#### 3. K-THRESHOLD VOTING
Accept decision when K agents more than competition.
k=2: needs 2 vote advantage for consensus.

#### 4. RED-FLAGGING
Reject suspicious responses BEFORE voting:
- Too long (agent "philosophizing" instead of deciding)
- Wrong format
- Contains "not sure", "maybe", hedging

---

### WHEN TO ACTIVATE MAKER
```
DECISION CRITICALITY MATRIX
═══════════════════════════════════════════════════

                    LOW COST        HIGH COST
                    of error        of error
                ┌───────────────┬───────────────┐
   REVERSIBLE   │   YOLO        │   REVIEW      │
                │   Single agent│   Human check │
                ├───────────────┼───────────────┤
   IRREVERSIBLE │   CAREFUL     │   MAKER       │
                │   Double-check│   Full voting │
                └───────────────┴───────────────┘

MAKER TRIGGERS:
- DELETE operations
- Metadata override on verified entries
- Cross-reference affecting >10 documents
- Recommendation for "mission critical" project
- Anything flagged as "rare" or "valuable"
```

---

### IMPLEMENTATION

#### MAKER WRAPPER
```
[CRITICAL DECISION]
       │
       ▼
┌─────────────────────────────────┐
│         MAKER WRAPPER           │
├─────────────────────────────────┤
│ 1. Decompose → atomic steps     │
│ 2. Spawn → N parallel agents    │
│ 3. Collect → responses          │
│ 4. Filter → red-flag removal    │
│ 5. Vote → k-threshold           │
│ 6. Decide → consensus or ESC    │
└─────────────────────────────────┘
       │
       ├──► CONSENSUS ──► Execute
       │
       └──► NO CONSENSUS ──► Escalate to human
```

#### CONFIGURATION
```yaml
maker_config:
  default_k: 2           # vote advantage for win
  default_n: 3           # parallel agents
  timeout_ms: 5000       # max time per agent

  red_flags:
    max_response_length: 200
    banned_phrases:
      - "not sure"
      - "maybe"
      - "probably"
      - "I think"
    require_format: "DECISION: X | CONFIDENCE: Y"

  escalation:
    max_rounds: 3        # retry before escalation
    notify: ["human_admin"]
```

---

### AGENTS IN MAKER MODE

Same librarians, but with MAKER wrapper:
```
LIBRARIAN (standard)
  "Classify this book"
  → 1 agent, 1 answer, done

LIBRARIAN (MAKER mode)
  "Classify this RARE book"
  → 3 agents, voting, consensus required
```

Agent doesn't know it's in MAKER mode.
Wrapper orchestrates from outside.

---

### PHASES

**F0: Proof of Concept**
- [ ] MAKER wrapper skeleton
- [ ] Hardcoded 3-agent voting
- [ ] Simple majority rule
- [ ] Manual trigger only

**F1: Red-flagging**
- [ ] Response length filter
- [ ] Phrase detection
- [ ] Format validation
- [ ] Resample logic

**F2: K-threshold**
- [ ] Configurable K
- [ ] Race-to-K implementation
- [ ] Early termination (when consensus is clear)

**F3: Atomic decomposition**
- [ ] Decision tree templates
- [ ] Auto-decompose for known task types
- [ ] Step dependency tracking

**F4: Integration**
- [ ] Trigger rules engine
- [ ] Criticality auto-detection
- [ ] Seamless wrapper for librarians

**F5: Observability**
- [ ] Voting logs
- [ ] Consensus metrics
- [ ] Error rate tracking
- [ ] Cost analysis

---

### SUCCESS METRICS

| Metric | Without MAKER | With MAKER | Target |
|---------|---------------|------------|--------|
| Critical error rate | ~5%? | <0.1% | Zero |
| Decision latency | 1x | ~3x | <5x |
| Cost per decision | 1x | ~3x | <5x |
| Human escalations | 0 | Some | <5% |

Trade-off: slower and more expensive, but RELIABLE.

---

### OPEN QUESTIONS

1. **Scope:** Only librarians or all BMad agents?
2. **Cost model:** Who pays for 3x API calls?
3. **Disagreement logging:** What do we do with "interesting" disagreements?
4. **Learning:** Can system learn which decisions need MAKER?
5. **Hybrid:** MAKER for part of decision, standard for rest?

---

### REFERENCE

- [MAKER Paper](https://arxiv.org/abs/2511.09030)
- [Cognizant Blog](https://www.cognizant.com/us/en/ai-lab/blog/maker)
- Apple "Illusion of Thinking" study
