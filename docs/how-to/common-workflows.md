# Alexandria Quick Reference

**Location:** `c:\Users\goran\source\repos\Temenos\Akademija\Alexandria`
**Qdrant:** `192.168.0.151:6333`
**Python:** 3.14
**Interface:** MCP Server (Claude Code)

---

## MCP Tools (Primary Interface)

### Query Tools

| Tool | Purpose |
|------|---------|
| `alexandria_query` | Semantic search with context modes |
| `alexandria_search` | Search Calibre by metadata |
| `alexandria_book` | Get book details by ID |
| `alexandria_stats` | Collection statistics |

### Ingest Tools

| Tool | Purpose |
|------|---------|
| `alexandria_ingest` | Ingest single book from Calibre |
| `alexandria_batch_ingest` | Ingest multiple books |
| `alexandria_ingest_file` | Ingest local file (no Calibre) |
| `alexandria_ingest_preview` | Preview books for ingestion |
| `alexandria_test_chunking` | Test chunking without upload |

---

## Common Workflows

### 1. Query Books

**Via Claude Code:**
```
User: What does Silverston say about the shipment pattern?
Claude: [calls alexandria_query("shipment pattern", context_mode="contextual")]
```

**With context modes:**
- `precise` - Fast, exact matches only
- `contextual` - Include chapter context (recommended)
- `comprehensive` - Include siblings (most context)

### 2. Ingest Books

**Single book:**
```
User: Ingest the Nietzsche book with ID 7970
Claude: [calls alexandria_ingest(book_id=7970)]
```

**Batch ingest:**
```
User: Ingest all Nietzsche books
Claude: [calls alexandria_batch_ingest(author="Nietzsche", limit=10)]
```

**With custom chunking:**
```
User: Ingest book 123 with smaller chunks
Claude: [calls alexandria_ingest(book_id=123, threshold=0.7, max_chunk_size=800)]
```

### 3. Check Status

**Collection stats:**
```
User: How many books are ingested?
Claude: [calls alexandria_stats()]
```

**Search for books:**
```
User: Do we have any Kahneman books?
Claude: [calls alexandria_search(author="Kahneman")]
```

---

## CLI Commands (Secondary)

### Query
```bash
cd scripts
python rag_query.py "your question" --limit 5 --context-mode contextual
```

### Query with LLM Answer (OpenRouter)
```bash
# Test retrieval quality with cheap model
python rag_query.py "your question" --answer --model meta-llama/llama-3-8b-instruct

# If weak model gives good answer = chunks are relevant ✅
```

**Available test models:**
| Model | Cost | Command |
|-------|------|---------|
| Llama-3-8B | ~$0.05/M | `--model meta-llama/llama-3-8b-instruct` |
| Mistral-7B | ~$0.05/M | `--model mistralai/mistral-7b-instruct` |
| Claude Haiku | ~$0.25/M | `--model anthropic/claude-3-haiku` |

**Config:** Add `OPENROUTER_API_KEY` to `.streamlit/secrets.toml`

### Check Manifest
```bash
python collection_manifest.py show alexandria
```

### Ingest Single Book
```bash
python ingest_books.py --file "path/to/book.epub"
```

### Collection Stats
```bash
python qdrant_utils.py stats alexandria
```

---

## Chunking Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `threshold` | 0.55 | Similarity threshold (0.0-1.0). Lower = larger chunks |
| `min_chunk_size` | 200 | Minimum words per chunk |
| `max_chunk_size` | 1200 | Maximum words per chunk |

**Examples:**
- **Smaller chunks** (precise citations): `threshold=0.7, max_chunk_size=800`
- **Larger chunks** (more context): `threshold=0.4, min_chunk_size=400, max_chunk_size=2000`

---

## Context Modes

| Mode | Speed | Returns | Use Case |
|------|-------|---------|----------|
| `precise` | ⚡ Fast | Child chunks only | Exact citations |
| `contextual` | 🔄 Medium | Children + parent chapter | Understanding context |
| `comprehensive` | 🐢 Slow | Children + parent + siblings | Deep analysis |

---

## Troubleshooting

### Connection Error
```bash
python qdrant_utils.py list
# Should show collections
```

### Check What's Ingested
```bash
python collection_manifest.py show alexandria
```

### MCP Server Not Working
1. Check `.mcp.json` configuration
2. Restart Claude Code
3. Verify Qdrant is accessible

---

## Current Collection Status

**alexandria** - Production collection
- 5 test books with hierarchical chunking
- 198 parent chunks, 3278 child chunks
- 3476 total points

---

**MCP Server Docs:** [docs/reference/mcp-server.md](../reference/mcp-server.md)
**Last Updated:** 2026-01-30
