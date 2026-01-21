# Alexandria Logs Directory

This directory contains logs and manifests of ingested books.

---

## Files

### collection_manifest.json
Master manifest tracking what's been ingested into each collection.

**Structure:**
```json
{
  "created_at": "2026-01-21T...",
  "last_updated": "2026-01-21T...",
  "collections": {
    "alexandria": {
      "created_at": "2026-01-21T...",
      "domain": "technical",
      "books": [
        {
          "file_path": "c:/path/to/book.epub",
          "file_name": "book.epub",
          "book_title": "Title",
          "author": "Author",
          "domain": "technical",
          "chunks_count": 153,
          "file_size_mb": 34.2,
          "ingested_at": "2026-01-21T..."
        }
      ],
      "total_chunks": 153,
      "total_size_mb": 34.2
    }
  }
}
```

### batch_ingest_progress.json
Progress tracker for batch ingestion (resume functionality).

**Location:** `../scripts/batch_ingest_progress.json`

---

## Usage

### View What's Been Ingested

```bash
# Show all collections
python collection_manifest.py list

# Show specific collection
python collection_manifest.py show alexandria

# Show detailed info
python collection_manifest.py show alexandria_test
```

**Example Output:**
```
================================================================================
📚 Collection: alexandria_test
================================================================================
Domain: technical
Created: 2026-01-21T18:14:13
Total books: 1
Total chunks: 153
Total size: 34.20 MB

Books:
--------------------------------------------------------------------------------

1. The Data Model Resource Book Vol 3: Universal Patterns for Data Modeling
   Author: Len Silverston
   File: The Data Model Resource Book Vol 3.epub
   Domain: technical
   Chunks: 153
   Size: 34.2 MB
   Ingested: 2026-01-21
```

### Export Manifest

```bash
# Export to file
python collection_manifest.py export alexandria --output ../logs/alexandria_backup.json
```

### Sync with Qdrant

If manifest gets out of sync, rebuild it from Qdrant:

```bash
python collection_manifest.py sync alexandria
```

**Note:** Synced data won't include original file paths. For complete tracking, always use `batch_ingest.py` which logs automatically.

### Remove Book from Manifest

```bash
python collection_manifest.py remove alexandria --book "path/to/book.epub"
```

---

## Automatic Logging

`batch_ingest.py` automatically updates the manifest when ingesting books:

```bash
# This will automatically log to manifest
python batch_ingest.py --directory ../ingest --domain technical --collection alexandria
```

**What gets logged:**
- Book file path (absolute path)
- Book title and author
- Domain category
- Number of chunks created
- File size in MB
- Ingestion timestamp

---

## Troubleshooting

### "Collection not found"
The collection hasn't been ingested yet. Run `batch_ingest.py` first.

### Manifest out of sync
If you manually delete books from Qdrant:
```bash
# Rebuild manifest from Qdrant
python collection_manifest.py sync alexandria
```

### Lost file paths after sync
Sync only recovers basic info (title, author, chunks). For complete tracking:
1. Keep backups of manifest before deleting
2. Use `batch_ingest.py` with `--resume` to avoid re-ingesting

---

## Best Practices

1. **Always use batch_ingest.py for ingestion** - it logs automatically
2. **Check manifest before re-ingesting** - avoid duplicates
3. **Backup manifest periodically**:
   ```bash
   python collection_manifest.py export alexandria --output ../logs/backups/alexandria_$(date +%Y%m%d).json
   ```
4. **Use `--resume` flag** when re-running failed ingestions

---

## Quick Reference

```bash
# What's in alexandria collection?
python collection_manifest.py show alexandria

# What's been processed in current batch?
cat batch_ingest_progress.json

# List all collections
python collection_manifest.py list

# Export manifest
python collection_manifest.py export alexandria --output backup.json
```

---

**Last Updated:** 2026-01-21
