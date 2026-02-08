# Issue 01: dev-story workflow needs explicit story selection

**Type:** Feature Request
**Workflow:** `/bmad-bmm-dev-story`
**Priority:** Medium

## Problem

When running multiple dev agents in parallel, `dev-story` workflow auto-selects the first `ready-for-dev` story without asking. This causes race conditions:

```
Terminal 1: /bmad-bmm-dev-story → picks 0-2
Terminal 2: /bmad-bmm-dev-story → picks 0-2 (same!)
💥 Both agents work on same story, file conflicts
```

## Current Behavior

Workflow immediately scans for first available story and starts implementation without user confirmation.

## Desired Behavior

Option to specify which story to work on:

```bash
# Explicit story selection
/bmad-bmm-dev-story 0-2

# Or with flag
/bmad-bmm-dev-story --story 0-2
```

Or at minimum, ask before starting:

```
Found 2 stories ready-for-dev:
  1. 0-2-add-embedding-model-metadata...
  2. 0-3-re-ingest-book-collection...

Which story should I work on? [1/2]
```

## Use Case

**Parallel development with manual dispatch:**
- SM (Scrum Master) creates stories
- User dispatches specific stories to specific dev agents
- Avoids race conditions without needing full Auto-Claude orchestration

## Workaround

Currently using this prompt before workflow:
```
STOP. Wait for instructions before starting.
Work ONLY on story 0-2, ignore 0-3.
Confirm you understand before proceeding.
```

Then run `/bmad-bmm-dev-story`. Works but clunky.

## Suggested Implementation

In `dev-story` workflow, add step 0:
```yaml
- step: 0
  name: story-selection
  action: |
    If story_id provided as argument, use that.
    Otherwise, list available stories and ask user to select.
    Do NOT auto-select.
```

---

**Submitted by:** Alexandria project
**Date:** 2026-02-01
