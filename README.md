# Alexandria - Temenos Academy Library

> *"Η Βιβλιοθήκη της Αλεξάνδρειας ήταν η μεγαλύτερη βιβλιοθήκη του αρχαίου κόσμου"*
>
> The Library of Alexandria was the largest library of the ancient world.

Semantička RAG knjižnica koja povezuje 9000 multidisciplinarnih knjiga (tehnika, psihologija, filozofija, povijest) za sintezu znanja preko domena.

**Status:** Phase 1 - Proof of Concept ✅ (Production-ready Python workflow)

---

## Quick Start

```bash
# 1. Open in VS Code
code "c:\Users\goran\source\repos\Temenos\Akademija\Alexandria"

# 2. Navigate to scripts
cd scripts

# 3. Check what's been ingested
python collection_manifest.py show alexandria

# 4. Query books
python rag_query.py "your question here" --limit 5

# 5. Ingest new books
python batch_ingest.py --directory ../ingest --domain technical --collection alexandria
```

**📖 For detailed guides, see [`docs/guides/`](docs/guides/)**

---

## Vizija

**Kratkoročno:** RAG sustav koji semantički pretražuje 9000 knjiga i vraća relevantne pasaže s citacijama

**Dugoročno:** Multidisciplinarni knowledge synthesis engine koji:
- Povezuje tehničke paterne s povijesnim precedentima
- Mapira psihološke principe u UX dizajn odluke
- Validira arhitekturalne izbore preko filozofskih okvira
- Otkriva cross-domain uvide (npr. "manufacturing execution patterns u 18th-century textile mills")

---

## Tehnologije

- **Vector DB:** Qdrant (192.168.0.151:6333)
- **Embedding Model:** sentence-transformers/all-MiniLM-L6-v2 (384-dim)
- **Chunking:** Domain-specific (Technical: 1500-2000 tokens, Psychology: 1000-1500, Philosophy: 1200-1800, History: 1500-2000)
- **Workflow:** Python CLI through VS Code
- **Ingestion:** EPUB, PDF, TXT, MD support
- **Tracking:** Automatic manifest logging

---

## Struktura Projekta

```
Alexandria/
├── README.md                           # This file
├── AGENTS.md                           # AI agent configuration & defaults
├── SETUP_COMPLETE.md                   # Original setup notes
├── requirements.txt                    # Python dependencies
│
├── .vscode/                            # VS Code configuration
│   ├── launch.json                     # Debug configurations
│   └── settings.json                   # Python settings
│
├── docs/                               # Documentation
│   ├── guides/                         # User guides
│   │   ├── QUICK_REFERENCE.md          # Command cheat sheet ⭐
│   │   ├── LOGGING_GUIDE.md            # Tracking system guide
│   │   ├── PROFESSIONAL_SETUP_COMPLETE.md  # Complete guide
│   │   └── OPEN_WEBUI_CONFIG.md        # Open WebUI integration
│   ├── alexandria-qdrant-project-proposal.md
│   └── missing-classics-analysis.md
│
├── scripts/                            # Python scripts
│   ├── ingest_books.py                 # Single book ingestion
│   ├── batch_ingest.py                 # Batch processing + auto-logging
│   ├── rag_query.py                    # Query tool (LLM-ready output)
│   ├── experiment_chunking.py          # A/B testing chunk strategies
│   ├── qdrant_utils.py                 # Collection management
│   ├── collection_manifest.py          # Track ingested books
│   ├── README.md                       # Script documentation
│   └── batch_ingest_progress.json      # Resume tracker (auto-generated)
│
├── logs/                               # Logs & manifests
│   ├── README.md                       # Logging documentation
│   └── collection_manifest.json        # Master manifest (auto-generated)
│
├── ingest/                             # Books waiting to be processed
│   ├── Silverston Vol 1.pdf
│   ├── Silverston Vol 2.pdf
│   └── Silverston Vol 3.epub
│
└── ingested/                           # Successfully processed books (moved here)
    └── README.md                       # Ingested folder documentation
```

---

## Current Status

### Ingested Collections
- **alexandria_test:** 153 chunks (Silverston Vol 3 EPUB) ✅
- **alexandria:** Empty (production collection) ⏳

### Available Scripts
| Script | Purpose | Status |
|--------|---------|--------|
| `batch_ingest.py` | Production ingestion + auto-logging | ✅ Ready |
| `rag_query.py` | Query tool (LLM-ready markdown) | ✅ Ready |
| `collection_manifest.py` | Track what's been ingested | ✅ Ready |
| `qdrant_utils.py` | Collection management | ✅ Ready |
| `experiment_chunking.py` | A/B testing | ✅ Ready |
| `ingest_books.py` | Single book (dev/testing) | ✅ Ready |

### Test Results
- ✅ EPUB ingestion: 20 chapters → 153 chunks (~1450 tokens/chunk)
- ✅ PDF ingestion: 525 pages → 525 chunks (~200 tokens/chunk)
- ✅ Chunking quality: Validated for both formats
- ✅ Semantic search: 0.38-0.65 relevance scores (both formats)
- 📊 Comparison: See [docs/PDF_vs_EPUB_COMPARISON.md](docs/PDF_vs_EPUB_COMPARISON.md)

---

## Documentation

### 🚀 Start Here
- **[AGENTS.md](AGENTS.md)** - AI agent config & defaults (read this first!)
- **[QUICK_REFERENCE.md](docs/guides/QUICK_REFERENCE.md)** - Command cheat sheet

### 📖 User Guides
- **[LOGGING_GUIDE.md](docs/guides/LOGGING_GUIDE.md)** - Track what's been ingested
- **[PROFESSIONAL_SETUP_COMPLETE.md](docs/guides/PROFESSIONAL_SETUP_COMPLETE.md)** - Complete production guide
- **[OPEN_WEBUI_CONFIG.md](docs/guides/OPEN_WEBUI_CONFIG.md)** - Open WebUI integration (optional)

### 🔧 Technical Docs
- **[scripts/README.md](scripts/README.md)** - Script usage documentation
- **[logs/README.md](logs/README.md)** - Logging system details
- **[SETUP_COMPLETE.md](SETUP_COMPLETE.md)** - Original setup notes

### 📋 Project Docs
- **[alexandria-qdrant-project-proposal.md](docs/alexandria-qdrant-project-proposal.md)** - Project proposal
- **[missing-classics-analysis.md](docs/missing-classics-analysis.md)** - Gap analysis

---

## Common Tasks

### Check What's Been Ingested
```bash
cd scripts
python collection_manifest.py show alexandria
```

### Query Books
```bash
python rag_query.py "What does Silverston say about shipments?" --limit 5
```

### Ingest New Books
```bash
# Batch process (production)
python batch_ingest.py --directory ../ingest --domain technical --collection alexandria

# Resume after failure
python batch_ingest.py --directory ../ingest --domain technical --resume
```

### Test Retrieval Quality
```bash
python qdrant_utils.py search alexandria "your test query" --limit 5
```

### Experiment with Chunking
```bash
python experiment_chunking.py \
  --file "../ingest/book.epub" \
  --strategies small,medium,large
```

---

## Configuration

### Qdrant Server
```
Host: 192.168.0.151
Port: 6333
Status: ✅ Running
```

### Python Environment
```
Version: Python 3.14
Dependencies: requirements.txt
Virtual Env: Not used (system Python)
```

### VS Code
```
Debug configs: .vscode/launch.json (6 configurations)
Terminal default: scripts/ directory
```

---

## Phase 1 Goals (PoC)

### Immediate (This Week)
- [ ] Batch ingest all 3 Silverston books
- [ ] Test PDF ingestion quality
- [ ] Query testing with real questions

### Short-term (Next 2-4 Weeks)
- [ ] Ingest 10 representative books (mix of domains)
- [ ] Manual retrieval quality evaluation
- [ ] Compare chunking strategies

### Medium-term (1-2 Months)
- [ ] Scale to 50-100 books
- [ ] Optimize chunking based on experiments
- [ ] Production deployment strategy

---

## Next Steps

1. **Batch ingest remaining Silverston books:**
   ```bash
   cd scripts
   python batch_ingest.py --directory ../ingest --domain technical --collection alexandria
   ```

2. **Verify results:**
   ```bash
   python collection_manifest.py show alexandria
   python qdrant_utils.py stats alexandria
   ```

3. **Test retrieval:**
   ```bash
   python rag_query.py "database normalization patterns" --limit 5
   ```

---

## Support

**Project Owner:** Sabo (BMad team)
**Location:** `c:\Users\goran\source\repos\Temenos\Akademija\Alexandria`
**Qdrant Server:** 192.168.0.151:6333

**For AI Agents:** Start with [AGENTS.md](AGENTS.md) for defaults and configuration.

---

**Last Updated:** 2026-01-21
**Phase:** 1 - Proof of Concept
**Status:** ✅ Production-ready Python workflow established
