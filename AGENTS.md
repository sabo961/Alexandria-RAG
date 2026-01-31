# Alexandria - AI Agent Entry Point

**For AI Agents:** Start here, then follow the links.

---

## Required Reading

| Priority | Document | Purpose |
|----------|----------|---------|
| **1. MANDATORY** | [docs/project-context.md](docs/project-context.md) | 45 implementation rules, patterns, conventions |
| **2. Epics & Stories** | [docs/development/epics.md](docs/development/epics.md) | Implementation roadmap (8 epics, 24 stories) |
| **3. Documentation** | [docs/index.md](docs/index.md) | Full documentation hub (Diataxis structure) |

---

## Quick Reference

```
Project Root:     c:\Users\goran\source\repos\Temenos\Akademija\Alexandria
Scripts:          scripts/
Qdrant Server:    192.168.0.151:6333
Primary Interface: MCP Server (scripts/mcp_server.py)
```

---

## Key Principle

> **MCP-First Architecture:** All business logic lives in `scripts/`. MCP server is the primary interface.

---

**Last Updated:** 2026-01-31
