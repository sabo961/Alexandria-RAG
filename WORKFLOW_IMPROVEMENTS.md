# Workflow Improvements - File Management & Tracking

**Date:** 2026-01-21
**Changes:** Automatic file organization + CSV export + Better tracking

---

## What Changed

### 1. Automatic File Management ✅

**Before:**
```
ingest/
├── book1.pdf      ❓ Was this ingested?
├── book2.epub     ❓ Was this ingested?
└── book3.pdf      ❓ Was this ingested?
```

**After:**
```
ingest/
└── (empty - all books processed)

ingested/
├── book1.pdf      ✅ Successfully ingested
├── book2.epub     ✅ Successfully ingested
└── book3.pdf      ✅ Successfully ingested
```

### 2. CSV Export for Easy Reading ✅

**Before:**
- Only JSON manifest (hard to read)

**After:**
- JSON manifest (for programs)
- **CSV manifest** (for humans) - open in Excel/LibreOffice

### 3. Status from Files, Not Documentation ✅

**Before:**
- Status hardcoded in AGENTS.md
- Gets out of sync quickly

**After:**
- Check `ingest/` folder → what's pending
- Check `ingested/` folder → what's done
- Check `collection_manifest.csv` → full details

---

## New Workflow

### Step 1: Add Books
```bash
# Copy new books to ingest folder
cp /path/to/books/*.pdf ingest/
```

### Step 2: Ingest
```bash
cd scripts

# Batch process all books
python batch_ingest.py --directory ../ingest --domain technical --collection alexandria

# Books automatically move to ingested/ folder after success
```

### Step 3: Verify
```bash
# Option 1: Quick visual check
ls ../ingest/      # Should be empty
ls ../ingested/    # Should contain all books

# Option 2: Check manifest (CSV - human-readable)
start ../logs/collection_manifest.csv  # Windows
# OR
open ../logs/collection_manifest.csv   # Mac
# OR
libreoffice ../logs/collection_manifest.csv  # Linux

# Option 3: Check manifest (command line)
python collection_manifest.py show alexandria
```

---

## CSV Manifest Format

```csv
Collection,Book Title,Author,Domain,Chunks,Size (MB),File Name,Ingested At
alexandria,Silverston Vol 3,Len Silverston,technical,153,34.2,Silverston Vol 3.epub,2026-01-21
alexandria,Silverston Vol 1,Len Silverston,technical,245,3.4,Silverston Vol 1.pdf,2026-01-21
...

TOTAL,,,, 398,37.6,,
```

**Open with:**
- Excel (Windows)
- Numbers (Mac)
- LibreOffice Calc (Linux)
- Any text editor

---

## File Organization

```
Alexandria/
├── ingest/                    # ⏳ Waiting to be processed
│   └── (new books go here)
│
├── ingested/                  # ✅ Successfully processed
│   ├── book1.pdf
│   ├── book2.epub
│   └── ...
│
└── logs/
    ├── collection_manifest.json     # Machine-readable
    └── collection_manifest.csv      # Human-readable ⭐ NEW!
```

---

## Batch Ingest Options

### Default (Recommended)
```bash
# Automatically moves completed books to ingested/
python batch_ingest.py --directory ../ingest --domain technical --collection alexandria
```

### Keep Files in Place
```bash
# Use --no-move to keep books in ingest/ folder
python batch_ingest.py --directory ../ingest --domain technical --no-move
```

### Resume After Failure
```bash
# Skips already processed books
python batch_ingest.py --directory ../ingest --domain technical --resume
```

---

## Benefits

### Visual Status
- **Empty `ingest/`** → All books processed ✅
- **Files in `ingest/`** → Still pending ⏳

### Easy Audit
- Open `collection_manifest.csv` in Excel
- Sort by date, domain, size, etc.
- Filter by collection

### Avoid Re-processing
- Books automatically removed from `ingest/`
- No accidental duplicate ingestion

### Archive
- Keep original files in `ingested/`
- Verify quality before deletion
- Restore if needed

---

## Common Tasks

### Check What's Pending
```bash
ls ingest/
```

### Check What's Done
```bash
ls ingested/
```

### View Full Details (CSV)
```bash
# Windows
start logs\collection_manifest.csv

# Mac
open logs/collection_manifest.csv

# Linux
libreoffice logs/collection_manifest.csv
```

### View Full Details (Command Line)
```bash
cd scripts
python collection_manifest.py show alexandria
```

### Re-ingest a Book
```bash
# 1. Move book back
mv ingested/book.pdf ingest/

# 2. Delete from Qdrant
python qdrant_utils.py delete-points alexandria --book "Book Title"

# 3. Remove from manifest
python collection_manifest.py remove alexandria --book "path/to/book.pdf"

# 4. Re-ingest
python batch_ingest.py --directory ../ingest --domain technical
```

---

## Migration from Old Workflow

If you have books already ingested but still in `ingest/` folder:

### Option 1: Move Manually
```bash
# Check what's been ingested
python collection_manifest.py show alexandria

# Move those books to ingested/
mv ingest/Silverston*.* ingested/
```

### Option 2: Use --no-move for Old Books
```bash
# Keep existing books in ingest/
# New ingestions will still move automatically
python batch_ingest.py --directory ../ingest --domain technical
```

---

## Updated Documentation

- **[AGENTS.md](../AGENTS.md)** - Status now checked from files, not hardcoded
- **[ingested/README.md](../ingested/README.md)** - New folder documentation
- **[logs/collection_manifest.csv](../logs/collection_manifest.csv)** - Human-readable manifest (auto-generated)
- **[.gitignore](../.gitignore)** - Ignores ingested books (keeps folder structure)

---

## Summary

✅ **Automatic file management** - Books move to `ingested/` after success
✅ **CSV export** - Open in Excel for easy reading
✅ **Status from files** - Check folders, not documentation
✅ **Visual confirmation** - Empty `ingest/` = all done
✅ **Archive** - Keep originals in `ingested/` for reference

**Key Improvement:** Never again wonder "Was this book ingested?" - just check the folders! 🎯

---

**Last Updated:** 2026-01-21 21:00
