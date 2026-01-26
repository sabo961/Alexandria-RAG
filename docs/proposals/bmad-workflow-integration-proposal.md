# Make `generate-project-context` and `document-project` Workflows Interdependent

**Describe your idea**

The `generate-project-context` and `document-project` workflows should be interdependent. Currently, they operate independently, but making `document-project` an optional first step would provide automated codebase discovery that significantly enhances the quality of `project-context.md` rules.

**Current behavior:**
- `generate-project-context` manually discovers configurations via Grep/Glob/Read during execution
- `document-project` automatically scans codebases and creates architecture documentation
- No cross-references or integration between these workflows

**Proposed behavior:**
- `generate-project-context` checks if codebase scan exists (from `document-project`)
- If found, uses scan data to auto-detect hardcoded values, patterns, anti-patterns
- If not found, optionally prompts user to run `document-project` first
- Falls back to manual discovery if user declines

---

**Why is this needed?**

### Problem This Solves

1. **Redundant Discovery Work**: AI agents manually Grep/Glob for configurations that `document-project` already scans automatically.

2. **Lower Quality Rules**: Without codebase scan data, `project-context.md` rules lack file locations and cross-references.

   **Example (current manual approach):**
   ```markdown
   9. **Qdrant server location: `192.168.0.151:6333`**
      - External server, NOT localhost
   ```

   **Example (enhanced with codebase scan):**
   ```markdown
   9. **Qdrant server location: `192.168.0.151:6333`**
      - Found in: scripts/qdrant_utils.py:15, alexandria_app.py:42
      - Hardcoded in: 3 locations (see docs/codebase/configurations.md)
      - Refactor needed: Extract to config.json
   ```

3. **Missed Opportunities**: Projects that run `document-project` don't benefit from that work when later running `generate-project-context`.

### Benefits for BMad Community

- **Better onboarding**: New projects get both human docs (`docs/codebase/`) and AI rules (`project-context.md`)
- **Higher quality rules**: Auto-detection vs manual discovery
- **Time savings**: Reduce discovery phase from ~20 minutes to ~5 minutes
- **Consistency**: Both workflows understand the codebase structure

---

**How should it work?**

### Implementation Approach

**1. Add Optional Dependency Metadata**

```yaml
# In _bmad/bmm/workflows/generate-project-context/metadata.yaml
optional_dependencies:
  - document-project

recommended_sequence:
  - document-project  # Run first for automated discovery
  - generate-project-context
```

**2. Update Discovery Phase Logic**

```markdown
## Phase 0: Pre-Discovery Check (NEW)

Before starting manual discovery:

1. Check if `docs/codebase/` directory exists
2. If YES:
   - Load architecture-summary.md, configurations.md, technology-stack.md
   - Use scan data to pre-populate project-context.md sections
   - Manual discovery fills gaps only
3. If NO:
   - Ask user: "Run /document-project first? (Recommended for richer rules)"
   - User accepts → Run document-project → Use output
   - User declines → Proceed with manual Grep/Glob (current behavior)
```

**3. Workflow Integration Options**

**Option A: Interactive Prompt (Recommended)**
```
User runs: /generate-project-context
  ↓
Check: docs/codebase/ exists?
  ├─ NO → Prompt: "Run /document-project first for automated discovery?"
  │        ├─ Yes → Auto-invoke document-project → Use scan data
  │        └─ No → Manual discovery (current behavior)
  └─ YES → Use existing scan + manual discovery for gaps
```

**Option B: Command Flag**
```bash
/generate-project-context --with-codebase-scan
# Runs document-project first if not already done
```

**4. Cross-Reference in `document-project`**

Add completion message:
```markdown
✅ Codebase documentation generated in docs/codebase/

This documentation can be used by:
- /generate-project-context - Creates AI agent rules from this scan
- Human developers - Architecture reference
```

### Edge Cases to Handle

1. **Stale scan**: Detect if `docs/codebase/` older than code changes (via timestamps)
   - Warn: "Scan outdated. Re-run /document-project?"

2. **Partial scan**: Check `scan-metadata.yaml` for scope
   - Fill gaps with manual discovery

3. **Greenfield projects**: Empty codebase detected
   - Skip codebase scan, focus on design artifacts

---

**PR**

Not currently working on implementation, but happy to collaborate if BMad maintainers are interested in this enhancement.

Workflow changes needed:
- `_bmad/bmm/workflows/generate-project-context/instructions.md` - Add Phase 0 pre-discovery check
- `_bmad/bmm/workflows/generate-project-context/metadata.yaml` - Add optional dependency
- `_bmad/bmm/workflows/document-project/instructions.md` - Add completion cross-reference

---

**Additional context**

### How This Was Discovered

**Project:** Alexandria RAG System (9,000-book semantic search using Qdrant vector DB)
**Session:** Documentation consolidation sprint (2026-01-26)
**Participants:** User (Sabo) + Claude Sonnet 4.5

**Discovery Timeline:**

1. ✅ Ran `/generate-project-context` successfully
   - Created `project-context.md` with 45 rules across 7 sections
   - Manually discovered hardcoded configs via Grep/Glob:
     - Qdrant server at `192.168.0.151:6333`
     - Calibre library path hardcoded (refactor regression)
     - Universal Semantic Chunking parameters in code
     - tqdm disabled globally via environment variable

2. 🤔 User asked: *"How do you search the repo? Is there an index?"*
   - I explained: "On-the-fly Grep/Glob/Read, no prebuilt index"

3. 💡 User: *"Shouldn't that be part of a workflow?"*
   - I discovered `/document-project` exists but wasn't auto-invoked

4. ❓ User: *"Are these two workflows interdependent?"*
   - Analysis: **NO** (but they SHOULD be)

5. ✨ User: *"Great idea! You can communicate directly with BMad team via GitHub!"*
   - This proposal was born

### Real-World Impact (Alexandria Project)

**If re-run with integration:**
- ✅ Auto-detect 15+ hardcoded configurations (vs manual Grep for each)
- ✅ Reduce discovery time: ~20 minutes → ~5 minutes
- ✅ Cross-reference 8+ ADRs automatically from architecture scan
- ✅ Richer "Critical Don't-Miss Rules" with file locations

### Alternatives Considered

| Alternative | Pros | Cons | Decision |
|-------------|------|------|----------|
| Keep workflows independent | Simple, no coupling | Redundant work, lower quality rules | ❌ Rejected |
| Merge into one workflow | Single command | Too heavyweight, not modular | ❌ Rejected |
| Make `document-project` mandatory | Always have scan | Forces overhead on greenfield projects | ❌ Rejected |
| **Optional dependency (proposed)** | **Flexible, automated when available** | **Slight complexity** | ✅ **Recommended** |

### Related Workflows

- `workflow-init` - Could recommend this combo as Phase 0 setup
- `check-implementation-readiness` - Could verify both docs exist before implementation

### Success Metrics

**For BMad users:**
- Higher quality `project-context.md` files
- Fewer missed anti-patterns
- Better first-time project experience
- Reduced manual discovery time

---

**Submitted by:** User (Sabo) - Alexandria RAG System project
**Discovered by:** Claude Sonnet 4.5 during documentation consolidation
**Date:** 2026-01-26

**Co-Authored-By:** Claude Sonnet 4.5 <noreply@anthropic.com>
