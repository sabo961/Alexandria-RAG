# Alexandria Agent Configuration

**Status:** This file has been **superseded by project-context.md** (BMad standard)

---

## For AI Agents - READ THIS FIRST

All AI agents working on Alexandria should read:

**Primary Reference (MANDATORY):**
- **[docs/project-context.md](docs/project-context.md)** - Critical implementation rules, technology stack, patterns, and conventions

**Project Documentation:**
- **[README.md](README.md)** - Project overview, features, quick start
- **[docs/index.md](docs/index.md)** - Documentation hub
- **[TODO.md](TODO.md)** - Current sprint tasks and completed work

---

## Quick Reference

### Key Locations

**Paths:**
```
Root:    c:\Users\goran\source\repos\Temenos\Akademija\Alexandria
Scripts: c:\Users\goran\source\repos\Temenos\Akademija\Alexandria\scripts
```

**External Services:**
```
Qdrant Server:    192.168.0.151:6333
MCP Server:       scripts/mcp_server.py (configured in .mcp.json)
Structurizr:      http://localhost:8081 (run scripts/start-structurizr.bat)
```

**Python Environment:**
```
Version: Python 3.14
Dependencies: requirements.txt
```

### Essential Commands

**Check ingestion status:**
```bash
cd scripts
python collection_manifest.py show alexandria
```

**Query books (CLI):**
```bash
cd scripts
python rag_query.py "your question here" --limit 5 --context-mode contextual
```

**MCP Server (Primary Interface):**
```bash
# Configured in .mcp.json - restart Claude Code to activate
# Query tools: alexandria_query, alexandria_search, alexandria_book, alexandria_stats
# Ingest tools: alexandria_ingest, alexandria_batch_ingest, alexandria_ingest_file
# Docs: docs/architecture/mcp-server.md
```

**Run tests:**
```bash
pytest tests/                    # All tests
pytest tests/ui/ -v --headed     # UI tests with browser visible
```

**Explore Calibre database:**
```bash
datasette "G:/My Drive/alexandria/metadata.db" --port 8002
# Open http://localhost:8002 - visual SQL explorer for Calibre metadata
```

---

## Where to Find What

| Topic | Location |
|-------|----------|
| **Implementation rules** | [docs/project-context.md](docs/project-context.md) |
| **Technology stack** | [docs/project-context.md](docs/project-context.md) |
| **Architecture decisions (ADRs)** | [docs/architecture/decisions/](docs/architecture/decisions/) |
| **Architecture overview** | [docs/architecture/README.md](docs/architecture/README.md) |
| **Script documentation** | [scripts/README.md](scripts/README.md) |
| **Logging system** | [logs/README.md](logs/README.md) |
| **Quick command reference** | [docs/how-to/common-workflows.md](docs/how-to/common-workflows.md) |
| **Current tasks** | [TODO.md](TODO.md) |
| **Project overview** | [README.md](README.md) |
| **MCP Server docs** | [docs/architecture/mcp-server.md](docs/architecture/mcp-server.md) |

---

## Critical Architecture Principle

**MCP-First Design:** All business logic lives in `scripts/` - MCP server is the primary interface.

- ✅ **MCP Server** (`scripts/mcp_server.py`) - Exposes scripts as MCP tools
- ✅ **Scripts** (`scripts/*.py`) - All logic, usable by MCP/CLI
- ❌ **GUI Development** - Abandoned in favor of MCP-first approach

See [docs/architecture/mcp-server.md](docs/architecture/mcp-server.md)

---

## Agent Instructions

### Language & Communication
**ALWAYS communicate in ENGLISH** when working with this user.
- English responses use ~30% fewer tokens than Croatian
- Exception: Only use Croatian if explicitly requested

### Before Starting Work
1. **Read** [docs/project-context.md](docs/project-context.md) for implementation rules
2. **Check** [TODO.md](TODO.md) for current tasks and context
3. **Verify** working directory: `Alexandria/scripts`

### When Making Changes
1. Follow **Conventional Commits** format (see project-context.md)
2. Update **project-context.md** if new patterns emerge
3. Update **TODO.md** when completing tasks
4. Add **ADR** for significant architectural decisions

---

**Last Updated:** 2026-01-30
**Migration:** Migrated to project-context.md (BMad standard)
