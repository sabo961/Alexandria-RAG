# Issue 03: Agents need visible "attention required" indicator

**Type:** UX Improvement
**Scope:** All agent workflows
**Priority:** High

## Problem

When running multiple agents in parallel terminals, it's hard to notice when an agent needs user input. Agents that are waiting for a response look identical to agents that are working or finished.

Current state:
```
Terminal 1: [wall of text... question buried somewhere...]
Terminal 2: [wall of text... waiting for input...]
Terminal 3: [wall of text... done? waiting? unclear...]
```

User has to read through output to find if agent is:
- Still working
- Waiting for input
- Finished
- Errored

## Desired Behavior

Clear visual indicator when agent needs attention:

```
Terminal 1:
   ...output...
   ⚠️ ════════════════════════════════════════════════
   ⚠️  WAITING FOR INPUT
   ⚠️  Question: Should I proceed with migration?
   ⚠️ ════════════════════════════════════════════════
```

Or use terminal bell/notification:
```python
print("\a")  # Terminal bell
```

Or colored output:
```
\033[1;33m[WAITING]\033[0m Your response needed...
```

## Suggested Indicators

| State | Indicator |
|-------|-----------|
| Working | 🔄 or spinner |
| Needs input | ⚠️ + bell + box |
| Completed | ✅ + summary |
| Error | ❌ + details |

## Implementation

In agent workflows, wrap user questions:

```python
def ask_user(question: str) -> str:
    print("\a")  # Terminal bell
    print("⚠️ " + "═" * 50)
    print("⚠️  WAITING FOR INPUT")
    print(f"⚠️  {question}")
    print("⚠️ " + "═" * 50)
    return input("> ")
```

## Benefits

- Faster response to agent needs
- Better parallel workflow management
- Less context switching / reading through logs
- Works without dashboard (pure terminal)

---

**Submitted by:** Alexandria project
**Date:** 2026-02-01
