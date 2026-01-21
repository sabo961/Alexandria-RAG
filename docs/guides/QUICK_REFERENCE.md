# Alexandria Quick Reference

**Location:** `c:\Users\goran\source\repos\Temenos\Akademija\Alexandria`
**Qdrant:** `192.168.0.151:6333`
**Python:** 3.14

---

## Most Common Commands

### Query Existing Data
```bash
cd scripts
python rag_query.py "your question here" --limit 5
```

### Check What's Been Ingested
```bash
# Quick manifest view
python collection_manifest.py show alexandria

# Detailed Qdrant stats
python qdrant_utils.py stats alexandria_test
```

### Ingest Single Book
```bash
python ingest_books.py \
  --file "../ingest/book.epub" \
  --domain technical \
  --collection alexandria_test
```

### Batch Ingest Folder
```bash
python batch_ingest.py \
  --directory ../ingest \
  --domain technical \
  --collection alexandria
```

### Test Search Quality
```bash
python qdrant_utils.py search alexandria_test "test query" --limit 5
```

---

## Common Workflows

### 1. Add New Books
```bash
# Copy books to ingest folder
# Then run batch ingest (automatically logs to manifest)
python batch_ingest.py --directory ../ingest --domain technical --resume

# Check what was ingested
python collection_manifest.py show alexandria
```

### 2. Test Retrieval Quality
```bash
# Option A: Python CLI
python rag_query.py "your question" --limit 5

# Option B: Direct search
python qdrant_utils.py search alexandria_test "your query" --limit 5
```

### 3. Experiment with Chunking
```bash
python experiment_chunking.py \
  --file "../ingest/book.epub" \
  --strategies small,medium,large
```

### 4. Copy Collection for Backup
```bash
python qdrant_utils.py copy alexandria_test alexandria_backup
```

### 5. Clean Up Test Collections
```bash
python qdrant_utils.py delete test_collection --confirm
```

---

## VS Code Shortcuts

- **Ctrl+`** - Toggle terminal
- **Ctrl+Shift+`** - New terminal
- **F5** - Start debugging (use launch configurations)
- **Ctrl+C** - Stop running script
- **Ctrl+P** - Quick file open

---

## Tracking What's Been Ingested

### View Manifest
```bash
# Show all collections
python collection_manifest.py list

# Show specific collection
python collection_manifest.py show alexandria

# Export to file
python collection_manifest.py export alexandria --output ../logs/backup.json
```

**Manifest Location:** `logs/collection_manifest.json`

### What Gets Logged
- Book file path
- Title, author, domain
- Number of chunks
- File size (MB)
- Ingestion timestamp

---

## Script Arguments Cheat Sheet

### collection_manifest.py
```
list                      List all collections
show <collection>         Show collection contents
export <collection>       Export manifest to file
  --output <file>
sync <collection>         Sync manifest with Qdrant
remove <collection>       Remove book from manifest
  --book <path>
```

### ingest_books.py
```
--file        Path to book file (required)
--domain      technical|psychology|philosophy|history (required)
--collection  Collection name (default: alexandria)
--host        Qdrant host (default: 192.168.0.151)
--port        Qdrant port (default: 6333)
```

### batch_ingest.py
```
--directory   Directory with books (required)
--domain      Domain category (required)
--collection  Collection name (default: alexandria)
--formats     File formats (default: epub,pdf,txt,md)
--resume      Skip already processed files
--host        Qdrant host (default: 192.168.0.151)
--port        Qdrant port (default: 6333)
```

### rag_query.py
```
query         Natural language question (required)
--collection  Collection name (default: alexandria_test)
--limit       Number of results (default: 5)
--domain      Filter by domain
--format      markdown|text|json (default: markdown)
--host        Qdrant host (default: 192.168.0.151)
--port        Qdrant port (default: 6333)
```

### qdrant_utils.py
```
list                          List all collections
stats <collection>            Show collection stats
search <collection> <query>   Search collection
copy <source> <target>        Copy collection
delete <collection>           Delete collection
alias <collection> <alias>    Create alias
delete-points <collection>    Delete specific points
  --domain <domain>
  --book <title>
```

---

## Debugging in VS Code

1. Open file you want to debug (e.g., `scripts/ingest_books.py`)
2. Set breakpoints (click left of line number)
3. Press **F5** and select configuration
4. Use debug toolbar:
   - **Continue** (F5)
   - **Step Over** (F10)
   - **Step Into** (F11)
   - **Step Out** (Shift+F11)
   - **Stop** (Shift+F5)

---

## Troubleshooting

### Connection Error
```bash
# Test Qdrant connection
python qdrant_utils.py list
# Should show collections, not error
```

### Import Error
```bash
# Reinstall dependencies
pip install -r ../requirements.txt
```

### "Collection not found"
```bash
# List available collections
python qdrant_utils.py list
```

### Script Not Found
```bash
# Make sure you're in scripts folder
cd c:\Users\goran\source\repos\Temenos\Akademija\Alexandria\scripts
```

---

## Current Collections

- **alexandria_test** - Test collection (153 chunks, Silverston Vol 3)
- **alexandria** - Production collection (to be populated)

---

## Next Steps (PoC Phase)

- [ ] Ingest remaining 2 Silverston PDFs
- [ ] Test PDF ingestion quality
- [ ] Ingest 2 psychology books
- [ ] Compare chunking strategies
- [ ] Manual retrieval quality evaluation

---

**Quick Links:**
- [Full Documentation](scripts/README.md)
- [Setup Complete](SETUP_COMPLETE.md)
- [Open WebUI Config](OPEN_WEBUI_CONFIG.md)

**Last Updated:** 2026-01-21 20:20
