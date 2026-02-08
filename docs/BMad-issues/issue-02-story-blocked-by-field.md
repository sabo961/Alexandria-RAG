# Issue 02: Add blocked_by field to story format

**Type:** Feature Request
**Scope:** Story file format, dev-story workflow
**Priority:** Medium

## Problem

Stories with dependencies have no machine-readable way to express blocking relationships. Currently dependencies are buried in prose:

```markdown
### Dependencies

**Depends on:**
- Story 0-1: Multi-model EmbeddingGenerator
- Story 0-2: Embedding metadata in payloads
```

Agents ignore this and start working even when dependencies aren't met.

## Desired Behavior

Simple, parseable field in story header:

```markdown
# Story 0.3: Re-ingest Book Collection

Status: ready-for-dev
Blocked-by: 0-2
```

Or in YAML frontmatter:

```yaml
---
story: "0-3"
status: ready-for-dev
blocked_by: ["0-2"]
---
```

## Agent Behavior

When `dev-story` workflow starts:

1. Parse `blocked_by` field
2. Check status of blocking stories in `sprint-status.yaml`
3. If any blocker is NOT `done` → wait or notify user
4. If all blockers are `done` → proceed

```python
# Pseudocode
blockers = story.get("blocked_by", [])
for blocker in blockers:
    if get_story_status(blocker) != "done":
        print(f"Blocked by {blocker} (status: {get_story_status(blocker)})")
        return  # Don't start
```

## Benefits

- Prevents race conditions in parallel development
- Self-documenting dependencies
- Enables future automation (auto-unblock when dependency completes)
- Compatible with sprint-status.yaml tracking

## Related

- Issue 01: dev-story needs explicit story selection
- Together these enable safe parallel development without full orchestration

---

**Submitted by:** Alexandria project
**Date:** 2026-02-01
