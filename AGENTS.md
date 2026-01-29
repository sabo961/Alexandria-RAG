# Alexandria Agent Configuration

**Status:** This file has been **superseded by project-context.md** (BMad standard)

---

## For AI Agents - READ THIS FIRST

All AI agents working on Alexandria should read:

**Primary Reference (MANDATORY):**
- **[_bmad-output/project-context.md](_bmad-output/project-context.md)** - Critical implementation rules, technology stack, patterns, and conventions

**Project Documentation:**
- **[README.md](README.md)** - Project overview, features, quick start
- **[docs/architecture/README.md](docs/architecture/README.md)** - C4 diagrams, ADRs, technical specs
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
Streamlit GUI:    http://localhost:8501
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

**Launch GUI:**
```bash
streamlit run alexandria_app.py
```

**Query books:**
```bash
cd scripts
python rag_query.py "your question here" --limit 5
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
| **Implementation rules** | [_bmad-output/project-context.md](_bmad-output/project-context.md) |
| **Technology stack** | [_bmad-output/project-context.md](_bmad-output/project-context.md) |
| **Architecture decisions (ADRs)** | [docs/architecture/decisions/](docs/architecture/decisions/) |
| **C4 diagrams** | [docs/architecture/c4/](docs/architecture/c4/) |
| **Script documentation** | [scripts/README.md](scripts/README.md) |
| **Logging system** | [logs/README.md](logs/README.md) |
| **Quick command reference** | [docs/guides/QUICK_REFERENCE.md](docs/guides/QUICK_REFERENCE.md) |
| **Current tasks** | [TODO.md](TODO.md) |
| **Project overview** | [README.md](README.md) |

---

## Critical Architecture Principle

**ADR 0003:** All business logic lives in `scripts/` - GUI is a thin presentation layer.

- ✅ **GUI** (`alexandria_app.py`) - Calls functions from `scripts/`, displays results
- ✅ **Scripts** (`scripts/*.py`) - All logic, usable by GUI/CLI/agents
- ❌ **NEVER** - Implement logic directly in GUI

See [docs/architecture/decisions/0003-gui-as-thin-layer.md](docs/architecture/decisions/0003-gui-as-thin-layer.md)

---

## Agent Instructions

### Language & Communication
**ALWAYS communicate in ENGLISH** when working with this user.
- English responses use ~30% fewer tokens than Croatian
- Exception: Only use Croatian if explicitly requested

### Before Starting Work
1. **Read** [_bmad-output/project-context.md](_bmad-output/project-context.md) for implementation rules
2. **Check** [TODO.md](TODO.md) for current tasks and context
3. **Verify** working directory: `Alexandria/scripts`

### When Making Changes
1. Follow **Conventional Commits** format (see project-context.md)
2. Update **project-context.md** if new patterns emerge
3. Update **TODO.md** when completing tasks
4. Add **ADR** for significant architectural decisions

---

**Last Updated:** 2026-01-25
**Migration:** Migrated to project-context.md (BMad standard)
