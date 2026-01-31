# Development Documentation

Internal development workflow managed via BMAD methodology.

## Task Lifecycle

```
ideas/        →  epics.md  →  epic-*.md  →  CHANGELOG.md
(brainstorm)     (planning)   (stories)      (done)
```

## Folders

| Folder | Purpose |
|--------|---------|
| [ideas/](./ideas/) | Brainstorming briefs - unfiltered future visions |
| [research/](./research/) | Background analysis and competitive research |

## Files

| File | Purpose |
|------|---------|
| [epics.md](./epics.md) | Epic definitions and requirements mapping |
| epic-0-model-migration.md | Stories for Epic 0 (bge-large migration) |
| epic-1-core-search-discovery.md | Stories for Epic 1 (search & metadata) |
| epic-2-multi-collection.md | Stories for Epic 2 (collection management) |
| epic-3-multi-consumer-access.md | Stories for Epic 3 (MCP, HTTP API) |
| epic-4-scaling-performance.md | Stories for Epic 4 (9,000 book scale) |
| epic-5-quality-maintainability.md | Stories for Epic 5 (tests, tech debt, XSS security) |
| epic-6-multi-tenancy-access-control.md | Stories for Epic 6 (Phase 2-4 features) |
| epic-7-audit-monitoring.md | Stories for Epic 7 (logging, Grafana) |

## Workflow

1. **ideas/** - Brainstorm and capture possibilities
2. **epics.md** - Plan epics and requirements
3. **epic-*.md** - Break down into implementation stories
4. **CHANGELOG.md** - Archive completed work

## See Also

- [epics.md](./epics.md) - Implementation roadmap (8 epics, 23 stories)
- [CHANGELOG.md](../../CHANGELOG.md) - Completed work
- [Documentation Index](../index.md) - Full documentation hub
