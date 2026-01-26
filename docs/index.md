# Alexandria - Documentation Index

**Project:** Alexandria - Temenos Academy Library
**Type:** RAG (Retrieval-Augmented Generation) System
**Status:** Production
**Last Updated:** 2026-01-26

---

## 📋 Quick Start

**New to Alexandria?** Start here:

1. **[Project Overview](project-overview.md)** - What is Alexandria? (5-minute read)
2. **[Development Guide](development-guide-alexandria.md)** - Setup and installation
3. **[Quick Reference](guides/QUICK_REFERENCE.md)** - Command cheat sheet

**For AI Agents:**
- **[Project Context](../_bmad-output/project-context.md)** - 🔹 **MANDATORY READ** - 45 implementation rules
- **[AGENTS.md](../AGENTS.md)** - Navigation hub for AI assistants

---

## 🎯 Project Summary

| Aspect | Details |
|--------|---------|
| **Purpose** | Semantic search across 9,000+ books using RAG |
| **Architecture** | Python RAG System (Monolith) |
| **Entry Point** | `alexandria_app.py` (Streamlit GUI) |
| **Tech Stack** | Python 3.14 + Streamlit + Qdrant + sentence-transformers |
| **Vector DB** | Qdrant (external: 192.168.0.151:6333) |
| **Embedding Model** | all-MiniLM-L6-v2 (384-dimensional) |

---

## 📚 Documentation by Purpose

### 🚀 For New Users

| Document | Purpose | Time to Read |
|----------|---------|--------------|
| **[../README.md](../README.md)** | Project landing page | 3 min |
| **[Project Overview](project-overview.md)** | High-level system summary | 5 min |
| **[Quick Reference](guides/QUICK_REFERENCE.md)** | Command cheat sheet | 2 min |
| **[Professional Setup](guides/PROFESSIONAL_SETUP_COMPLETE.md)** | Advanced setup guide | 10 min |
| **[../TODO.md](../TODO.md)** | Current backlog | 3 min |
| **[../CHANGELOG.md](../CHANGELOG.md)** | Completed work archive | 5 min |

### 🤖 For AI Agents

| Document | Purpose | Critical? |
|----------|---------|-----------|
| **[../_bmad-output/project-context.md](../_bmad-output/project-context.md)** | **45 implementation rules** | 🔹 **YES** |
| **[../AGENTS.md](../AGENTS.md)** | Navigation hub | ✅ Recommended |
| **[Data Models & API](data-models-alexandria.md)** | Module APIs reference | ✅ Recommended |
| **[Architecture](architecture.md)** | System architecture | ✅ Recommended |
| **[Source Tree](source-tree-analysis.md)** | Codebase structure | Optional |

---

## 👨‍💻 For Developers

### Setup & Workflow

| Document | Purpose |
|----------|---------|
| **[Development Guide](development-guide-alexandria.md)** | Installation, setup, CLI usage, debugging |
| **[Source Tree Analysis](source-tree-analysis.md)** | Directory structure with annotations |
| **[Logging Guide](guides/LOGGING_GUIDE.md)** | Logging patterns and best practices |

### Code Reference

| Document | Purpose |
|----------|---------|
| **[Data Models & API Reference](data-models-alexandria.md)** | All scripts/ module APIs, data structures, integration points |
| **[Source Tree Analysis](source-tree-analysis.md)** | File organization, entry points, key locations |

### Tools & Utilities

| Guide | Purpose |
|-------|---------|
| **[OpenWebUI Config](guides/OPEN_WEBUI_CONFIG.md)** | OpenWebUI integration setup |

---

## 🏗️ Architecture Documentation

### High-Level Architecture

| Document | Scope | Detail Level |
|----------|-------|--------------|
| **[Architecture](architecture.md)** | Complete system | Comprehensive (12,000+ words) |
| **[Architecture Summary](architecture/ARCHITECTURE_SUMMARY.md)** | System overview | High-level |
| **[Project Overview](project-overview.md)** | Quick summary | Executive summary |

### Visual Diagrams (C4 Model)

| Diagram | Purpose | Format |
|---------|---------|--------|
| **[C4: Context](architecture/c4/01-context.md)** | System context & external dependencies | Markdown + Structurizr DSL |
| **[C4: Container](architecture/c4/02-container.md)** | Container view (GUI, Scripts, Qdrant) | Markdown + Structurizr DSL |
| **[C4: Component](architecture/c4/03-component.md)** | Component view (scripts package) | Markdown + Structurizr DSL |

**Tool:** [Structurizr Guide](architecture/STRUCTURIZR.md)

### Architecture Decision Records (ADRs)

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| **[0001](architecture/decisions/0001-use-qdrant-vector-db.md)** | Use Qdrant Vector DB | ✅ Accepted | 2026-01-20 |
| **[0002](architecture/decisions/0002-domain-specific-chunking.md)** | Domain-Specific Chunking | 🔄 Superseded by 0007 | 2026-01-20 |
| **[0003](architecture/decisions/0003-gui-as-thin-layer.md)** | GUI as Thin Presentation Layer | ✅ Accepted | 2026-01-21 |
| **[0004](architecture/decisions/0004-collection-specific-manifests.md)** | Collection-Specific Manifests | ✅ Accepted | 2026-01-21 |
| **[0005](architecture/decisions/0005-philosophical-argument-chunking.md)** | Philosophical Argument Chunking | 🔄 Superseded by 0007 | 2026-01-22 |
| **[0006](architecture/decisions/0006-separate-systems-architecture.md)** | Local Qdrant with Separate Collections | ✅ Accepted | 2026-01-23 |
| **[0007](architecture/decisions/0007-universal-semantic-chunking.md)** | Universal Semantic Chunking | ✅ Accepted | 2026-01-25 |

**Index:** [ADR README](architecture/decisions/README.md)

### Technical Specifications

| Spec | Purpose |
|------|---------|
| **[PDF vs EPUB Comparison](architecture/technical/PDF_vs_EPUB_COMPARISON.md)** | Format comparison analysis |
| **[Qdrant Payload Structure](architecture/technical/QDRANT_PAYLOAD_STRUCTURE.md)** | Vector DB schema |
| **[Universal Semantic Chunking](architecture/technical/UNIVERSAL_SEMANTIC_CHUNKING.md)** | Chunking algorithm details |

---

## 🔬 Research & Proposals

### Research Documents

| Document | Topic |
|----------|-------|
| **[Alexandria-Qdrant Proposal](research/alexandria-qdrant-project-proposal.md)** | Original project proposal |
| **[Argument-Based Chunking](research/argument_based_chunking_for_philosophical_texts_alexandria_rag.md)** | Philosophical chunking research |
| **[Missing Classics Analysis](research/missing-classics-analysis.md)** | Library gap analysis |
| **[Vector DB Cloud Comparison](research/vector-db-cloud-comparison.md)** | Vector DB evaluation |

### Backlog & Ideas

| Document | Topic |
|----------|-------|
| **[Hierarchical Chunking](backlog/Hierarchical%20Chunking%20for%20Alexandria%20RAG.md)** | Feature proposal |
| **[Hierarchical Chunking - Additions](backlog/Hierarchical%20Chunking%20for%20Alexandria%20RAG-additions.md)** | Extended proposal |

### External Contributions

| Proposal | Target | Status |
|----------|--------|--------|
| **[BMad Workflow Integration](proposals/bmad-workflow-integration-proposal.md)** | github.com/bmadcode/bmad-method | 📝 Draft |

**Index:** [Proposals README](proposals/README.md)

---

## 📦 Project Management (BMad Framework)

### Workflow Tracking

| File | Purpose |
|------|---------|
| **[../TODO.md](../TODO.md)** | Prioritized backlog (HIGH/MEDIUM/LOW) |
| **[../CHANGELOG.md](../CHANGELOG.md)** | Completed work archive |
| **[../_bmad-output/project-context.md](../_bmad-output/project-context.md)** | AI agent implementation rules (45 rules) |

### BMad Outputs

| Directory | Purpose |
|-----------|---------|
| **[../_bmad-output/](../_bmad-output/)** | BMad workflow outputs (project-context, artifacts) |
| **[../_bmad/](../_bmad/)** | BMad framework (workflows, agents, config) |

---

## 📖 Stories & Features

**Index:** [Stories README](stories/README.md)

---

## 🔧 Generated Documentation (This Scan)

**Workflow:** document-project (exhaustive scan)
**Generated:** 2026-01-26

| Document | Purpose | Status |
|----------|---------|--------|
| **[index.md](index.md)** | This file - Master index | ✅ Complete |
| **[project-overview.md](project-overview.md)** | High-level summary | ✅ Complete |
| **[architecture.md](architecture.md)** | Comprehensive architecture | ✅ Complete |
| **[data-models-alexandria.md](data-models-alexandria.md)** | API & data models | ✅ Complete |
| **[source-tree-analysis.md](source-tree-analysis.md)** | Codebase structure | ✅ Complete |
| **[development-guide-alexandria.md](development-guide-alexandria.md)** | Dev setup & workflow | ✅ Complete |
| **[project-scan-report.json](project-scan-report.json)** | Workflow state file | ✅ Complete |

---

## 🗂️ Documentation Maintenance

### Update Frequency

| Document Type | Update Trigger |
|---------------|----------------|
| **ADRs** | When significant architecture decision made |
| **project-context.md** | When rules/patterns change |
| **CHANGELOG.md** | After completing each story/sprint |
| **TODO.md** | Weekly or as priorities shift |
| **Architecture docs** | When system architecture changes |
| **API docs** | When module APIs change |

### Quality Checklist

- [ ] All ADRs have status (Accepted/Rejected/Superseded)
- [ ] Superseded ADRs link to replacement ADR
- [ ] project-context.md reflects current implementation rules
- [ ] Generated docs have "Last Updated" dates
- [ ] Broken links identified and fixed
- [ ] Code examples tested and verified

---

## 🎓 Learning Path

### For New Developers

1. **[Project Overview](project-overview.md)** - Understand what Alexandria does
2. **[Development Guide](development-guide-alexandria.md)** - Set up local environment
3. **[Quick Reference](guides/QUICK_REFERENCE.md)** - Learn common commands
4. **[Source Tree Analysis](source-tree-analysis.md)** - Navigate the codebase
5. **[Data Models & API](data-models-alexandria.md)** - Understand module APIs
6. **[ADR 0003: GUI as Thin Layer](architecture/decisions/0003-gui-as-thin-layer.md)** - Critical architecture principle
7. **[ADR 0007: Universal Semantic Chunking](architecture/decisions/0007-universal-semantic-chunking.md)** - Core innovation

### For AI Agents

1. **[project-context.md](../_bmad-output/project-context.md)** - 🔹 **START HERE** - 45 critical rules
2. **[AGENTS.md](../AGENTS.md)** - Navigation guidance
3. **[Data Models & API](data-models-alexandria.md)** - Module reference
4. **[Architecture](architecture.md)** - System overview
5. **[TODO.md](../TODO.md)** - Current priorities

### For Architects

1. **[Architecture](architecture.md)** - Complete system architecture
2. **[C4 Diagrams](architecture/c4/)** - Visual models (Context, Container, Component)
3. **[ADRs](architecture/decisions/README.md)** - Decision history & rationale
4. **[Technical Specs](architecture/technical/)** - Detailed specifications

---

## 📞 Getting Help

### Where to Look

1. **Search this index** for relevant documentation
2. **Check [TODO.md](../TODO.md)** for known issues
3. **Review [CHANGELOG.md](../CHANGELOG.md)** for recent changes
4. **Consult [project-context.md](../_bmad-output/project-context.md)** for implementation rules

### External Resources

- **Streamlit:** https://docs.streamlit.io
- **Qdrant:** https://qdrant.tech/documentation
- **sentence-transformers:** https://www.sbert.net
- **BMad Method:** https://github.com/bmadcode/bmad-method

---

## 🔐 Critical Files (DO NOT DELETE)

| File | Why Critical |
|------|--------------|
| **requirements.txt** | Official Python dependency file (used by pip) |
| **project-context.md** | AI agent implementation rules (45 rules) |
| **.streamlit/secrets.toml** | API keys (gitignored, must recreate if deleted) |
| **collection_manifest_*.json** | Ingestion tracking (data loss if deleted) |

---

## 📈 Project Statistics

| Metric | Value |
|--------|-------|
| **Total Books** | ~9,000 |
| **Collections** | 2+ (alexandria, alexandria_test, etc.) |
| **Python Modules** | 15 in scripts/ package |
| **Architecture Decisions** | 7 ADRs (5 accepted, 2 superseded) |
| **Documentation Files** | 40+ markdown files |
| **Lines of Code** | ~12,000 (estimated) |

---

## 🎯 Next Steps

**For New Contributors:**
1. Read [Development Guide](development-guide-alexandria.md)
2. Set up local environment
3. Review [TODO.md](../TODO.md) for available tasks
4. Check [project-context.md](../_bmad-output/project-context.md) for implementation rules

**For AI Agents:**
1. **Read [project-context.md](../_bmad-output/project-context.md)** (MANDATORY)
2. Review [Data Models & API](data-models-alexandria.md)
3. Check [TODO.md](../TODO.md) for current priorities
4. Implement features following ADR 0003 (thin GUI layer principle)

---

**Index Version:** 1.0
**Generated by:** document-project workflow (exhaustive scan)
**Last Updated:** 2026-01-26

**👆 This is your primary entry point for AI-assisted development and project navigation.**
