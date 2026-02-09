# Qdrant Event Logging - Multi-User Ingest Tracking

**Status:** Proposed
**Priority:** High
**Created:** 2026-02-08
**Supersedes:** SQLite-based tracking (ALEXANDRIA_DB)

---

## Problem Statement

Current SQLite-based tracking (`alexandria.db` on NAS) has multi-user limitations:

```
ALEXANDRIA_DB = \\Sinovac\docker\calibre\alexandria\.qdrant\alexandria.db
```

**Issues:**
1. **Concurrent write conflicts** - Windows + BUCO ingesting simultaneously → lock timeouts
2. **Network file locking unreliable** - UNC/SMB locks don't work consistently with SQLite WAL mode
3. **Corruption risk** - Network interruption during transaction can corrupt database
4. **Limited visibility** - Need to mount NAS to query logs from any machine

**Current usage:**
- Ingest event logging (start, complete, error)
- Collection manifest tracking
- Performance metrics (chunking, embedding, upload durations)
- Multi-machine coordination (hostname tracking)

---

## Proposed Solution

**Use Qdrant itself as the event logging store** - unified, multi-user, globally visible.

### Architecture

**New Collection:** `alexandria_events`

```python
{
    "collection_name": "alexandria_events",
    "vectors_config": {},  # No vectors - pure metadata store
    "on_disk_payload": True,  # Store payloads on disk for performance
}
```

### Event Schema

**Event Types:**
- `ingest_start` - Book ingestion started
- `ingest_complete` - Book ingestion completed successfully
- `ingest_error` - Book ingestion failed
- `book_delete` - Book removed from collection
- `collection_recreate` - Collection rebuilt/migrated

**Payload Structure:**
```python
{
    "id": "uuid-v4",  # Unique event ID
    "vector": {},  # Empty - no embeddings needed
    "payload": {
        # Event metadata
        "event_type": "ingest_complete",
        "timestamp": "2026-02-08T15:45:32.123Z",  # ISO 8601
        "hostname": "BUCO",

        # Book identification
        "book_id": 42,  # Calibre book_id or external identifier
        "source": "calibre",  # calibre | gutenberg | archive
        "source_id": "42",  # Source-specific ID

        # Book metadata (duplicated from main collection for easy querying)
        "title": "The Great Gatsby",
        "author": "F. Scott Fitzgerald",
        "language": "en",

        # Ingestion metrics (for complete events)
        "chunks_created": 202,
        "duration_sec": 29.5,
        "chunking_sec": 8.2,
        "embedding_sec": 18.1,
        "upload_sec": 3.2,
        "model": "bge-m3",
        "device": "cuda",

        # Error details (for error events)
        "error_type": "ChunkingError",
        "error_msg": "PDF extraction failed: invalid format",
        "stacktrace": "...",

        # Versioning
        "ingest_version": "2.0",
        "code_commit": "bc62f28"  # Optional git commit hash
    }
}
```

---

## Implementation

### 1. Qdrant Logger Module

**File:** `scripts/qdrant_logger.py`

```python
#!/usr/bin/env python3
"""
Qdrant Event Logger
===================

Unified event logging to Qdrant for multi-user visibility and tracking.
Replaces SQLite-based alexandria.db with Qdrant collection.
"""

import socket
from datetime import datetime
from uuid import uuid4
from typing import Dict, List, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue

from config import QDRANT_HOST, QDRANT_PORT, INGEST_VERSION

EVENTS_COLLECTION = "alexandria_events"


class QdrantLogger:
    """Event logger using Qdrant as storage backend."""

    def __init__(self):
        self.client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        self.hostname = socket.gethostname()
        self._ensure_collection()

    def _ensure_collection(self):
        """Create events collection if it doesn't exist."""
        collections = self.client.get_collections().collections
        if EVENTS_COLLECTION not in [c.name for c in collections]:
            self.client.create_collection(
                collection_name=EVENTS_COLLECTION,
                vectors_config={},  # No vectors
                on_disk_payload=True
            )

    def log_event(self, event_type: str, payload: Dict) -> str:
        """
        Log an event to Qdrant.

        Args:
            event_type: Type of event (ingest_start, ingest_complete, ingest_error)
            payload: Event-specific data

        Returns:
            Event ID (UUID)
        """
        event_id = str(uuid4())

        event_payload = {
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "hostname": self.hostname,
            "ingest_version": INGEST_VERSION,
            **payload  # Merge in event-specific fields
        }

        point = PointStruct(
            id=event_id,
            vector={},
            payload=event_payload
        )

        self.client.upsert(
            collection_name=EVENTS_COLLECTION,
            points=[point]
        )

        return event_id

    def log_ingest_start(self, book_id: int, source: str, source_id: str,
                         title: str, author: str, language: str) -> str:
        """Log book ingestion start."""
        return self.log_event("ingest_start", {
            "book_id": book_id,
            "source": source,
            "source_id": source_id,
            "title": title,
            "author": author,
            "language": language
        })

    def log_ingest_complete(self, book_id: int, source: str, source_id: str,
                           title: str, author: str, language: str,
                           chunks: int, duration_sec: float,
                           chunking_sec: float, embedding_sec: float, upload_sec: float,
                           model: str, device: str) -> str:
        """Log successful book ingestion."""
        return self.log_event("ingest_complete", {
            "book_id": book_id,
            "source": source,
            "source_id": source_id,
            "title": title,
            "author": author,
            "language": language,
            "chunks_created": chunks,
            "duration_sec": duration_sec,
            "chunking_sec": chunking_sec,
            "embedding_sec": embedding_sec,
            "upload_sec": upload_sec,
            "model": model,
            "device": device
        })

    def log_ingest_error(self, book_id: int, source: str, source_id: str,
                        title: str, error_type: str, error_msg: str) -> str:
        """Log ingestion failure."""
        return self.log_event("ingest_error", {
            "book_id": book_id,
            "source": source,
            "source_id": source_id,
            "title": title,
            "error_type": error_type,
            "error_msg": error_msg
        })

    def get_recent_events(self, limit: int = 100, event_type: Optional[str] = None) -> List[Dict]:
        """
        Query recent events.

        Args:
            limit: Maximum number of events to return
            event_type: Filter by event type (optional)

        Returns:
            List of event payloads sorted by timestamp descending
        """
        scroll_filter = None
        if event_type:
            scroll_filter = Filter(
                must=[FieldCondition(key="event_type", match=MatchValue(value=event_type))]
            )

        results = self.client.scroll(
            collection_name=EVENTS_COLLECTION,
            scroll_filter=scroll_filter,
            limit=limit,
            with_payload=True,
            with_vectors=False
        )

        events = [point.payload for point in results[0]]

        # Sort by timestamp descending (most recent first)
        events.sort(key=lambda e: e.get("timestamp", ""), reverse=True)

        return events

    def get_book_history(self, source: str, source_id: str) -> List[Dict]:
        """Get all events for a specific book."""
        results = self.client.scroll(
            collection_name=EVENTS_COLLECTION,
            scroll_filter=Filter(
                must=[
                    FieldCondition(key="source", match=MatchValue(value=source)),
                    FieldCondition(key="source_id", match=MatchValue(value=source_id))
                ]
            ),
            limit=1000,
            with_payload=True,
            with_vectors=False
        )

        events = [point.payload for point in results[0]]
        events.sort(key=lambda e: e.get("timestamp", ""))

        return events

    def get_stats(self) -> Dict:
        """Get ingestion statistics."""
        # Get all complete events
        complete_events = self.get_recent_events(limit=10000, event_type="ingest_complete")

        total_books = len(complete_events)
        total_chunks = sum(e.get("chunks_created", 0) for e in complete_events)
        total_duration = sum(e.get("duration_sec", 0) for e in complete_events)

        # Group by hostname
        by_host = {}
        for event in complete_events:
            host = event.get("hostname", "unknown")
            if host not in by_host:
                by_host[host] = {"books": 0, "chunks": 0}
            by_host[host]["books"] += 1
            by_host[host]["chunks"] += event.get("chunks_created", 0)

        return {
            "total_books_ingested": total_books,
            "total_chunks_created": total_chunks,
            "total_duration_hours": total_duration / 3600,
            "avg_chunks_per_book": total_chunks / total_books if total_books > 0 else 0,
            "by_hostname": by_host
        }
```

### 2. Update ingest_books.py

**Replace SQLite calls with Qdrant logger:**

```python
# At top of file
from qdrant_logger import QdrantLogger

# In main ingestion loop
logger_qdrant = QdrantLogger()

# Before processing book
event_id = logger_qdrant.log_ingest_start(
    book_id=book_id,
    source="calibre",
    source_id=str(book_id),
    title=title,
    author=author,
    language=language
)

try:
    # ... chunking, embedding, upload ...

    # On success
    logger_qdrant.log_ingest_complete(
        book_id=book_id,
        source="calibre",
        source_id=str(book_id),
        title=title,
        author=author,
        language=language,
        chunks=len(chunks),
        duration_sec=total_duration,
        chunking_sec=chunk_time,
        embedding_sec=embed_time,
        upload_sec=upload_time,
        model=model_id,
        device=device
    )

except Exception as e:
    # On error
    logger_qdrant.log_ingest_error(
        book_id=book_id,
        source="calibre",
        source_id=str(book_id),
        title=title,
        error_type=type(e).__name__,
        error_msg=str(e)
    )
    raise
```

### 3. Query/Reporting CLI

**File:** `scripts/view_events.py`

```python
#!/usr/bin/env python3
"""View Alexandria ingestion events from Qdrant."""

import argparse
from datetime import datetime
from qdrant_logger import QdrantLogger


def print_event(event, index=None):
    """Pretty print a single event."""
    prefix = f"[{index}] " if index is not None else ""
    timestamp = event.get("timestamp", "")
    event_type = event.get("event_type", "unknown")
    hostname = event.get("hostname", "unknown")
    title = event.get("title", "Unknown")

    print(f"\n{prefix}{timestamp} | {event_type} | {hostname}")
    print(f"    {title}")

    if event_type == "ingest_complete":
        chunks = event.get("chunks_created", 0)
        duration = event.get("duration_sec", 0)
        model = event.get("model", "unknown")
        print(f"    Chunks: {chunks} | Duration: {duration:.1f}s | Model: {model}")

    elif event_type == "ingest_error":
        error = event.get("error_msg", "")
        print(f"    ERROR: {error}")


def main():
    parser = argparse.ArgumentParser(description="View Alexandria events")
    parser.add_argument("--limit", type=int, default=20, help="Number of events to show")
    parser.add_argument("--type", choices=["start", "complete", "error"], help="Filter by event type")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    parser.add_argument("--book", help="Show history for specific book (source:id)")

    args = parser.parse_args()

    logger = QdrantLogger()

    if args.stats:
        stats = logger.get_stats()
        print("\n=== Ingestion Statistics ===")
        print(f"Total books ingested: {stats['total_books_ingested']:,}")
        print(f"Total chunks created: {stats['total_chunks_created']:,}")
        print(f"Total duration: {stats['total_duration_hours']:.1f} hours")
        print(f"Avg chunks/book: {stats['avg_chunks_per_book']:.0f}")
        print("\nBy hostname:")
        for host, data in stats['by_hostname'].items():
            print(f"  {host}: {data['books']} books, {data['chunks']:,} chunks")

    elif args.book:
        source, source_id = args.book.split(":")
        events = logger.get_book_history(source, source_id)
        print(f"\n=== History for {source}:{source_id} ({len(events)} events) ===")
        for i, event in enumerate(events, 1):
            print_event(event, i)

    else:
        event_type_map = {"start": "ingest_start", "complete": "ingest_complete", "error": "ingest_error"}
        event_type = event_type_map.get(args.type) if args.type else None

        events = logger.get_recent_events(limit=args.limit, event_type=event_type)

        type_str = f" ({args.type})" if args.type else ""
        print(f"\n=== Recent Events{type_str} (showing {len(events)}) ===")

        for i, event in enumerate(events, 1):
            print_event(event, i)


if __name__ == "__main__":
    main()
```

**Usage:**
```bash
# Recent events
python view_events.py --limit 50

# Only errors
python view_events.py --type error

# Statistics
python view_events.py --stats

# Book history
python view_events.py --book calibre:42
```

---

## Migration Plan

### Phase 1: Add Qdrant Logging (Parallel with SQLite)
1. Create `qdrant_logger.py` module
2. Update `ingest_books.py` to log to BOTH SQLite and Qdrant
3. Test on single book ingestion
4. Verify events appear in `alexandria_events` collection

### Phase 2: Validate & Switch
1. Run batch ingestion with dual logging
2. Compare SQLite vs Qdrant logs for consistency
3. Test query performance with `view_events.py`
4. Switch to Qdrant-only logging (remove SQLite calls)

### Phase 3: Cleanup
1. Remove `ALEXANDRIA_DB` from `config.py`
2. Update `.gitignore` comments (logs/*.db no longer needed for tracking)
3. Archive existing SQLite logs (optional - for historical reference)
4. Update documentation

---

## Benefits

✅ **Multi-user safe** - Qdrant handles concurrent writes natively
✅ **Global visibility** - Query from any machine without mounting NAS
✅ **Fast queries** - Qdrant optimized for metadata filtering
✅ **Unified storage** - Embeddings + events in same system
✅ **Scalable** - Handles millions of events easily
✅ **No corruption risk** - No network file locking issues
✅ **Rich querying** - Filter by host, date, book, event type, etc.
✅ **Future-proof** - Easy to add dashboards, analytics, alerting

---

## Risks & Mitigations

**Risk:** Qdrant downtime = no event logging
**Mitigation:** Already true for embeddings. If Qdrant is down, ingestion can't proceed anyway.

**Risk:** Events collection grows large over time
**Mitigation:** Use `on_disk_payload=True`, implement retention policy (delete events older than 1 year)

**Risk:** Breaking change for existing tools expecting SQLite
**Mitigation:** Provide migration period with dual logging, update all scripts before full cutover

---

## Future Enhancements

1. **Real-time dashboard** - Streamlit page showing live ingestion progress
2. **Alerting** - Slack/email notifications on ingestion errors
3. **Analytics** - Aggregate stats by model, language, source, time period
4. **Event replay** - Re-ingest failed books from error events
5. **Audit trail** - Track deletions, re-ingestions, collection rebuilds
6. **Export** - Generate reports (CSV, JSON) for analysis

---

## Decision

**Approved by:** TBD
**Implementation start:** TBD
**Target completion:** TBD

---

## References

- Current SQLite tracking: `scripts/ingest_books.py` lines 400-450
- Qdrant client docs: https://qdrant.tech/documentation/
- Event-driven architecture patterns: https://martinfowler.com/eaaDev/EventSourcing.html
