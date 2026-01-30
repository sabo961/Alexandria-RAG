# ADR 0004: Collection-Specific Manifests

## Status
Accepted

## Date
2026-01-21

## Context

Alexandria needs to track which books have been ingested into Qdrant to:
1. **Avoid duplicate ingestion** - Check if book already processed before re-ingesting
2. **Resume batch jobs** - Continue failed batch ingestion from last successful book
3. **Audit trail** - Know exactly what's in each collection (title, author, domain, chunk count)
4. **Quick lookup** - Find book metadata without querying Qdrant
5. **CSV exports** - Human-readable reports of collection contents

**Initial implementation (2026-01-20):**
- Single global manifest: `logs/collection_manifest.json`
- Single progress file: `scripts/batch_ingest_progress.json`
- All collections shared same manifest

**Problems discovered:**
1. **Cross-contamination:** Deleting `alexandria_test` cleared manifest for `alexandria` too
2. **Stale state:** Progress file didn't reset when collection deleted from Qdrant
3. **Confusion:** Can't distinguish which books belong to which collection
4. **Experiments polluted production:** Test ingestions affected production manifest

**Requirements:**
- Each collection must have **separate manifest**
- Manifest must **auto-reset** when collection deleted from Qdrant
- Progress files must be **collection-specific** for resume functionality
- System must **verify collection exists** before reading manifest

## Decision

**Implement per-collection manifests with auto-reset on collection deletion.**

### Manifest File Pattern
```
logs/{collection_name}_manifest.json      # Per-collection manifest
logs/{collection_name}_manifest.csv       # Per-collection CSV export
scripts/batch_ingest_progress_{collection_name}.json  # Per-collection progress
```

### Examples
- `logs/alexandria_manifest.json` - Production collection
- `logs/alexandria_test_manifest.json` - Test collection
- `logs/experiment_small_manifest.json` - Experiment collection
- `scripts/batch_ingest_progress_alexandria.json` - Production progress

### Auto-Reset Behavior
When `CollectionManifest` is initialized:
1. Check if collection exists in Qdrant (`client.collection_exists()`)
2. If collection missing → Reset manifest to empty state
3. Delete progress file (stale resume data)
4. Log warning: "Collection not found in Qdrant, manifest reset"

### Backward Compatibility
- Legacy `logs/collection_manifest.json` still read if exists (for migration)
- New code writes to per-collection files only
- Users notified to migrate during first run

## Consequences

### Positive
- **Isolation:** Each collection completely independent
- **Safety:** Deleting test collection doesn't affect production
- **Clarity:** Easy to see what's in each collection (`show alexandria` vs `show alexandria_test`)
- **Auto-recovery:** Manifest auto-resets when collection deleted (no stale state)
- **Resume per collection:** Batch progress tracked separately per collection
- **Experimentation-friendly:** Can create throwaway collections without polluting production

### Negative
- **More files:** Each collection creates 3 files (manifest.json, manifest.csv, progress.json)
- **File proliferation:** 10 collections = 30 files in logs/scripts directories
- **Migration burden:** Existing users must migrate from global manifest
- **No cross-collection queries:** Can't easily query "all books across all collections" (must read all manifests)

### Neutral
- **Manual cleanup:** Deleting collection from Qdrant leaves manifest files behind (user must clean up)
- **File naming convention:** Must follow `{collection_name}_manifest.json` pattern strictly

## Implementation

### Component
- **Collection Management Component** (in Scripts Package)

### Files
- `scripts/collection_manifest.py` - Manifest management
  - `CollectionManifest.__init__()` - Initializes with `collection_name` parameter
  - `verify_collection_exists()` - Checks Qdrant, resets if missing (lines 87-104)
  - `get_manifest_path()` - Returns `logs/{collection}_manifest.json`
  - `export_to_csv()` - Exports to `logs/{collection}_manifest.csv`

- `scripts/batch_ingest.py` - Uses per-collection manifests
  - `manifest = CollectionManifest(collection_name=args.collection)` (line 295)
  - `progress_file = f"batch_ingest_progress_{args.collection}.json"` (line 301)

### Manifest Structure
```json
{
  "created_at": "2026-01-21T...",
  "last_updated": "2026-01-23T...",
  "books": [
    {
      "file_path": "c:/path/to/book.epub",
      "book_title": "Title",
      "author": "Author",
      "domain": "technical",
      "language": "ENG",
      "file_type": "EPUB",
      "chunks_count": 153,
      "file_size_mb": 34.2,
      "ingested_at": "2026-01-23T..."
    }
  ],
  "total_chunks": 153,
  "total_size_mb": 34.2
}
```

### Usage
```python
# Initialize manifest for specific collection
manifest = CollectionManifest(collection_name="alexandria")

# Check if book already ingested
if manifest.is_book_ingested(file_path):
    print("Already processed, skipping...")

# Log newly ingested book
manifest.log_book(
    file_path=file_path,
    book_title=title,
    author=author,
    domain=domain,
    chunks_count=len(chunks),
    file_size_mb=size_mb
)

# Export to CSV
manifest.export_to_csv()  # Writes to logs/alexandria_manifest.csv
```

### CLI Commands
```bash
# Show manifest for specific collection
python collection_manifest.py show alexandria
python collection_manifest.py show alexandria_test

# List all collections (finds all *_manifest.json files)
python collection_manifest.py list

# Export manifest
python collection_manifest.py export alexandria --output backup.json
```

### Story
[06-COLLECTION_MANAGEMENT.md](../../../explanation/stories/06-COLLECTION_MANAGEMENT.md)

## Alternatives Considered

### Alternative 1: Single Global Manifest with Collection Field
**Structure:**
```json
{
  "collections": {
    "alexandria": { "books": [...] },
    "alexandria_test": { "books": [...] }
  }
}
```
**Pros:** Single file, easy to query all collections
**Cons:** Cross-contamination risk, harder to isolate, all-or-nothing file locking
**Rejected:** Safety concerns, harder to reset individual collections

### Alternative 2: Database (SQLite)
**Pros:** Structured queries, transactions, foreign keys, joins
**Cons:** Additional dependency, overkill for simple tracking, more complex backup/restore
**Rejected:** JSON files sufficient for current scale

### Alternative 3: Store Manifest in Qdrant
**Pros:** Single source of truth, no file management
**Cons:** Can't check manifest if Qdrant is down, slower than file access, harder to export
**Rejected:** Manifest should survive Qdrant deletion

### Alternative 4: No Manifest (Query Qdrant Directly)
**Pros:** No duplicate state, Qdrant is source of truth
**Cons:** Can't check what's ingested if Qdrant down, no file path history, no audit trail
**Rejected:** Manifest provides important audit trail and offline access

## Migration Path

### For Existing Installations
1. **Detect legacy manifest:** Check for `logs/collection_manifest.json`
2. **Extract collection data:** Read global manifest
3. **Split into per-collection files:**
   ```python
   for collection_name, data in global_manifest.items():
       write_to_file(f"logs/{collection_name}_manifest.json", data)
   ```
4. **Verify against Qdrant:** Ensure collections still exist
5. **Rename legacy file:** `collection_manifest.json` → `collection_manifest_legacy.json`
6. **Log migration:** Print summary of migrated collections

### Implemented in Code
- `CollectionManifest.__init__()` checks for legacy file on first run
- Prompts user to run migration script
- Preserves legacy file as backup

## Related Decisions
- [ADR 0001: Use Qdrant Vector DB](0001-use-qdrant-vector-db.md) - Manifests track Qdrant data
- [ADR 0003: GUI as Thin Layer](0003-gui-as-thin-layer.md) - GUI displays manifests via scripts

## References
- **C4 Component Diagram:** [03-component.md](../c4/03-component.md) - Collection Management component
- **Logging guide:** [Track Ingestion](../../../how-to-guides/track-ingestion.md)
- **logs/README.md:** [logs/README.md](../../../logs/README.md)

---

**Author:** Claude Code + User (Sabo)
**Reviewers:** User (Sabo)
**Implementation Date:** 2026-01-21
