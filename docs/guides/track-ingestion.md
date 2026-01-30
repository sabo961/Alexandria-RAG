# Alexandria Logging & Tracking System

**Problem Solved:** "How will I know what I processed after a few days?"

---

## Overview

Alexandria has **two tracking systems**:

1. **Collection Manifest** (`logs/collection_manifest.json`) - What's in which Qdrant collection
2. **Batch Progress Tracker** (`scripts/batch_ingest_progress.json`) - Resume functionality for batch ingestion

---

## 1. Collection Manifest (Main Registry)

### What It Logs

For each collection stores:
- **List of all books** (file path, title, author)
- **Number of chunks** per book
- **File size** (MB)
- **Timestamp** when ingested
- **Domain** category
- **Total statistics** (total chunks, total size)

### How to Use

#### Check What's in Your Collection

```bash
cd scripts

# Quick overview of all collections
python collection_manifest.py list

# Detailed view of specific collection
python collection_manifest.py show alexandria_test
```

**Output:**
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

#### Automatic Logging

`batch_ingest.py` **automatically** updates manifest:

```bash
# This will automatically record all ingested books in the manifest
python batch_ingest.py --directory ../ingest --domain technical --collection alexandria
```

No need for additional steps - everything is automatically logged!

#### Export / Backup

```bash
# Export manifest to file
python collection_manifest.py export alexandria --output ../logs/backups/alexandria_backup.json

# Windows scheduling (optional)
# Create scheduled task to backup daily
```

---

## 2. Batch Progress Tracker

### What It Logs

- **Processed files** - List of successfully processed books
- **Failed files** - List of failed files with error message
- **Statistics** - Total books, chunks, errors

### Location

`scripts/batch_ingest_progress.json`

### How to Use

#### Resume After Interruption

```bash
# If batch ingestion fails halfway, continue from where you stopped
python batch_ingest.py --directory ../ingest --domain technical --resume
```

**Resume** skips books that are already ingested.

#### Check Progress

```bash
# Windows
type batch_ingest_progress.json

# Linux/Mac
cat batch_ingest_progress.json
```

**Output:**
```json
{
  "started_at": "2026-01-21T20:00:00",
  "processed_files": [
    {
      "filepath": "c:/path/to/book1.epub",
      "chunks": 153,
      "processed_at": "2026-01-21T20:05:00"
    }
  ],
  "failed_files": [],
  "stats": {
    "total_books": 1,
    "total_chunks": 153,
    "total_errors": 0
  }
}
```

---

## Practical Examples

### Scenario 1: "Is this book already ingested?"

```bash
# Quick check manifest
python collection_manifest.py show alexandria | findstr "Silverston"

# Or check entire list
python collection_manifest.py show alexandria
```

### Scenario 2: "How much space does the collection take?"

```bash
python collection_manifest.py show alexandria
# Output shows: Total size: 123.45 MB
```

### Scenario 3: "Batch ingestion failed halfway"

```bash
# Continue from where you stopped
python batch_ingest.py --directory ../ingest --domain technical --resume

# Check what passed, what didn't
type batch_ingest_progress.json
```

### Scenario 4: "I want backup before deleting collection"

```bash
# Export manifest
python collection_manifest.py export alexandria --output ../logs/alexandria_before_delete.json

# Safe to delete now
python qdrant_utils.py delete alexandria --confirm
```

### Scenario 5: "I lost the manifest, but Qdrant has the data"

```bash
# Rebuild manifest from Qdrant
python collection_manifest.py sync alexandria

# Note: Sync doesn't recover file paths, only basic info
```

---

## File Locations

```
Alexandria/
├── logs/
│   ├── collection_manifest.json       # Master manifest (IMPORTANT!)
│   ├── README.md                      # Logging docs
│   └── backups/                       # Optional backups folder
└── scripts/
    └── batch_ingest_progress.json     # Batch resume tracker
```

---

## Best Practices

### ✅ DO

1. **Check manifest before re-ingesting**
   ```bash
   python collection_manifest.py show alexandria
   ```

2. **Use --resume when re-running batch ingestion**
   ```bash
   python batch_ingest.py --directory ../ingest --domain technical --resume
   ```

3. **Backup manifest periodically**
   ```bash
   python collection_manifest.py export alexandria --output ../logs/backups/backup_$(date +%Y%m%d).json
   ```

4. **Always use batch_ingest.py for production ingestion** (logs automatically)

### ❌ DON'T

1. **Don't manually edit collection_manifest.json** (use tools)
2. **Don't delete manifest file** (you'll lose history)
3. **Don't ingest same book twice** (check manifest first)
4. **Don't use ingest_books.py for production** (doesn't update manifest)

---

## Troubleshooting

### "Collection not found in manifest"

**Cause:** Collection hasn't been ingested yet, or manifest was deleted.

**Fix:**
```bash
# If collection exists in Qdrant, sync it
python collection_manifest.py sync alexandria

# If collection doesn't exist, ingest books
python batch_ingest.py --directory ../ingest --domain technical --collection alexandria
```

### "Manifest out of sync with Qdrant"

**Cause:** Manual deletion from Qdrant, or manifest file was corrupted.

**Fix:**
```bash
# Rebuild from Qdrant
python collection_manifest.py sync alexandria

# Note: File paths will be lost in sync
```

### "Duplicate books in collection"

**Cause:** Ingested same book twice without checking manifest.

**Fix:**
```bash
# Option A: Delete entire collection and re-ingest with --resume
python qdrant_utils.py delete alexandria --confirm
python batch_ingest.py --directory ../ingest --domain technical --collection alexandria

# Option B: Delete specific points by book title
python qdrant_utils.py delete-points alexandria --book "Book Title"
python collection_manifest.py remove alexandria --book "path/to/book.epub"
```

---

## Quick Reference Commands

```bash
# What's in my collection?
python collection_manifest.py show alexandria

# List all collections
python collection_manifest.py list

# Resume failed batch ingestion
python batch_ingest.py --directory ../ingest --domain technical --resume

# Export manifest
python collection_manifest.py export alexandria --output backup.json

# Rebuild manifest from Qdrant
python collection_manifest.py sync alexandria

# Check batch progress
type batch_ingest_progress.json
```

---

## Integration with Workflow

### Standard Ingestion Workflow

```bash
# 1. Copy new books to ingest folder
cp /path/to/new/books/*.pdf ../ingest/

# 2. Check what's already ingested (avoid duplicates)
python collection_manifest.py show alexandria

# 3. Run batch ingestion (automatically logs)
python batch_ingest.py --directory ../ingest --domain technical --collection alexandria

# 4. Verify results
python collection_manifest.py show alexandria
python qdrant_utils.py stats alexandria

# 5. Test retrieval
python rag_query.py "test query" --collection alexandria --limit 5
```

---

## Manifest Schema

```json
{
  "created_at": "ISO 8601 timestamp",
  "last_updated": "ISO 8601 timestamp",
  "collections": {
    "collection_name": {
      "created_at": "ISO 8601 timestamp",
      "domain": "technical|psychology|philosophy|history",
      "books": [
        {
          "file_path": "absolute path to book file",
          "file_name": "book.epub",
          "book_title": "extracted title",
          "author": "extracted author",
          "domain": "domain category",
          "chunks_count": 153,
          "file_size_mb": 34.2,
          "ingested_at": "ISO 8601 timestamp"
        }
      ],
      "total_chunks": 153,
      "total_size_mb": 34.2
    }
  }
}
```

---

## Summary

✅ **Automatic logging** - `batch_ingest.py` logs everything
✅ **Quick checks** - `collection_manifest.py show <name>`
✅ **Resume support** - `--resume` flag for failed ingestions
✅ **Backup/export** - `collection_manifest.py export`
✅ **Sync from Qdrant** - `collection_manifest.py sync` (recovery)

**Key Takeaway:** Always use `batch_ingest.py` for production - automatically logs everything you need to know!

---

**Last Updated:** 2026-01-21
