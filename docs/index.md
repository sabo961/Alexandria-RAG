# Alexandria Documentation

**Welcome to Alexandria** - a Python-based RAG (Retrieval-Augmented Generation) system providing semantic search across 9,000+ books in the Temenos Academy Library.

**Quick Facts:**
- **Tech Stack:** Python 3.14, Streamlit GUI, Qdrant vector database, sentence-transformers
- **Vector DB:** Qdrant (external: 192.168.0.151:6333)
- **Embedding Model:** all-MiniLM-L6-v2 (384-dimensional)
- **Architecture:** Monolithic backend with scripts-first design pattern

---

## 📋 Quick Start

**New to Alexandria?** Start here:

1. **[Project Overview](./explanation/project-overview.md)** - What is Alexandria and what problems does it solve?
2. **[Getting Started Tutorial](./tutorials/getting-started.md)** - Set up Alexandria in 15 minutes
3. **[Common Workflows](./how-to-guides/common-workflows.md)** - Command cheat sheet for daily use

**For AI Agents:**
- **[Project Context](../_bmad-output/project-context.md)** - 🔹 **MANDATORY READ** - 45 implementation rules
- **[AGENTS.md](../AGENTS.md)** - Navigation hub for AI assistants

---

## 📚 Documentation by Purpose

Alexandria's documentation follows the **[Diataxis framework](https://diataxis.fr)** - organized by what you need to accomplish:

### 📘 [Tutorials](./tutorials/index.md) - Learn by Doing

**Learning-oriented:** Step-by-step lessons to gain hands-on experience with Alexandria.

- **[Getting Started with Alexandria](./tutorials/getting-started.md)** - Complete setup and first ingestion
- **[Professional Setup Guide](./tutorials/professional-setup.md)** - Production deployment with Docker
- **[Structurizr Architecture Visualization](./tutorials/structurizr-guide.md)** - Visualize C4 diagrams

**👉 Start here if:** You're new to Alexandria and want to learn by building something.

---

### 📗 [How-To Guides](./how-to-guides/index.md) - Solve Specific Problems

**Problem-oriented:** Practical recipes for accomplishing specific tasks.

- **[Common Workflows](./how-to-guides/common-workflows.md)** - Frequent operations and commands
- **[Track Document Ingestion](./how-to-guides/track-ingestion.md)** - Monitor and debug ingestion with logging
- **[Configure Open WebUI Integration](./how-to-guides/configure-open-webui.md)** - Connect Alexandria to Open WebUI

**👉 Start here if:** You know what you want to do and need directions to get it done.

---

### 📕 [Reference](./reference/index.md) - Look Up Technical Information

**Information-oriented:** Dry, factual technical descriptions and API specifications.

#### API Documentation
- **[Data Models](./reference/api/data-models.md)** - Complete schema for Alexandria's data structures
- **[Source Tree Analysis](./reference/api/source-tree.md)** - Codebase structure and module organization

#### Architecture
- **[C4 Diagrams](./reference/architecture/c4/)** - Visual architecture models (Context, Container, Component)
- **[Architecture Decision Records (ADRs)](./reference/architecture/decisions/README.md)** - History of significant decisions
  - [ADR-0001: Qdrant Vector DB](./reference/architecture/decisions/0001-use-qdrant-vector-db.md)
  - [ADR-0003: GUI as Thin Layer](./reference/architecture/decisions/0003-gui-as-thin-layer.md)
  - [ADR-0007: Universal Semantic Chunking](./reference/architecture/decisions/0007-universal-semantic-chunking.md) (current)
- **[Technical Specifications](./reference/architecture/technical/)** - Detailed implementation specs
  - [Qdrant Payload Structure](./reference/architecture/technical/QDRANT_PAYLOAD_STRUCTURE.md)
  - [Universal Semantic Chunking](./reference/architecture/technical/UNIVERSAL_SEMANTIC_CHUNKING.md)
  - [PDF vs EPUB Comparison](./reference/architecture/technical/PDF_vs_EPUB_COMPARISON.md)

**👉 Start here if:** You need to look up specific technical details or API information.

---

### 📙 [Explanation](./explanation/index.md) - Understand the Design

**Understanding-oriented:** Discussions that clarify concepts and illuminate design decisions.

- **[Project Overview](./explanation/project-overview.md)** - High-level introduction and context
- **[Architecture Overview](./explanation/architecture.md)** - Comprehensive architectural discussion
- **[Research Documents](./explanation/research/)** - Investigation reports and technical research
- **[Proposals](./explanation/proposals/)** - Project proposals and strategic initiatives
- **[User Stories](./explanation/stories/)** - Product requirements and feature specifications

**👉 Start here if:** You want to understand why Alexandria works the way it does.

---

## 🎯 Learning Paths

Choose your role to follow a recommended path through the documentation:

### 🆕 New User Path
Perfect for first-time users who want to get Alexandria running quickly.

1. [Project Overview](./explanation/project-overview.md) - Understand what Alexandria does
2. [Getting Started Tutorial](./tutorials/getting-started.md) - Set up and run Alexandria
3. [Common Workflows](./how-to-guides/common-workflows.md) - Learn daily commands
4. [Track Ingestion](./how-to-guides/track-ingestion.md) - Monitor your first document ingestion

### 👨‍💻 Developer Path
For developers implementing features or fixing bugs.

1. [Getting Started Tutorial](./tutorials/getting-started.md) - Set up development environment
2. [Data Models Reference](./reference/api/data-models.md) - Understand Alexandria's API
3. [Source Tree Analysis](./reference/api/source-tree.md) - Navigate the codebase
4. [Architecture Overview](./explanation/architecture.md) - Grasp the system design
5. [ADR-0003: GUI as Thin Layer](./reference/architecture/decisions/0003-gui-as-thin-layer.md) - Critical design principle
6. [Common Workflows](./how-to-guides/common-workflows.md) - Daily development tasks

### 🤖 AI Agent Path
For AI assistants implementing features or answering questions.

1. **[Project Context](../_bmad-output/project-context.md)** - 🔹 **MANDATORY** - 45 implementation rules
2. [Architecture Overview](./explanation/architecture.md) - System design and patterns
3. [Data Models Reference](./reference/api/data-models.md) - Module APIs
4. [ADRs](./reference/architecture/decisions/README.md) - Decision history
5. [How-To Guides](./how-to-guides/index.md) - Problem-solving recipes
6. **[AGENTS.md](../AGENTS.md)** - AI-specific navigation guidance

### 🏗️ Architect Path
For understanding architectural decisions and system design.

1. [Architecture Overview](./explanation/architecture.md) - Complete system architecture
2. [C4 Diagrams](./reference/architecture/c4/) - Visual models
3. [ADRs](./reference/architecture/decisions/README.md) - Decision history with rationale
4. [Technical Specifications](./reference/architecture/technical/) - Detailed specs
5. [Research Documents](./explanation/research/) - Technical investigations

---

## 📖 What is Diataxis?

**[Diataxis](https://diataxis.fr)** is a documentation framework that organizes content into four quadrants based on user needs:

| | **Learning** | **Problem-Solving** |
|---|---|---|
| **Practical** | 📘 **Tutorials** - Lessons | 📗 **How-To Guides** - Directions |
| **Theoretical** | 📙 **Explanation** - Discussion | 📕 **Reference** - Description |

This structure helps you find the right documentation for your current need:
- **Learning something new?** → Tutorials
- **Solving a specific problem?** → How-To Guides
- **Looking up technical details?** → Reference
- **Understanding the design?** → Explanation

---

## 📦 Project Management

### Workflow Tracking
- **[TODO.md](../TODO.md)** - Prioritized backlog (HIGH/MEDIUM/LOW)
- **[CHANGELOG.md](../CHANGELOG.md)** - Completed work archive
- **[Project Context](../_bmad-output/project-context.md)** - AI agent implementation rules

### BMad Framework Integration
- **[BMad Outputs](../_bmad-output/)** - Workflow artifacts and project context
- **[BMad Framework](../_bmad/)** - Workflows, agents, and configuration

---

## 🔐 Critical Files (DO NOT DELETE)

| File | Why Critical |
|------|--------------|
| **requirements.txt** | Official Python dependency file (used by pip) |
| **project-context.md** | AI agent implementation rules (45 rules) |
| **.streamlit/secrets.toml** | API keys (gitignored, must recreate if deleted) |
| **collection_manifest_*.json** | Ingestion tracking (data loss if deleted) |

---

## 📞 Getting Help

### Where to Look
1. **Search this index** for relevant documentation by purpose (Tutorials/How-To/Reference/Explanation)
2. **Check [TODO.md](../TODO.md)** for known issues
3. **Review [CHANGELOG.md](../CHANGELOG.md)** for recent changes
4. **Consult [Project Context](../_bmad-output/project-context.md)** for implementation rules

### External Resources
- **Streamlit:** https://docs.streamlit.io
- **Qdrant:** https://qdrant.tech/documentation
- **sentence-transformers:** https://www.sbert.net
- **BMad Method:** https://github.com/bmadcode/bmad-method
- **Diataxis Framework:** https://diataxis.fr

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

**Documentation Structure:** Diataxis Framework (Tutorials, How-To Guides, Reference, Explanation)
**Last Updated:** 2026-01-26
**Version:** 2.0 (Diataxis Restructuring)

**👆 Navigate by purpose using the quadrant links above.**
