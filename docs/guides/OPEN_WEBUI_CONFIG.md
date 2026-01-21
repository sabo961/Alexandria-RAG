# Open WebUI Configuration for Alexandria

**Date:** 2026-01-21
**Open WebUI URL:** https://ai.jedai.space
**Qdrant Server:** 192.168.0.151:6333

---

## Current Issue: Connection Error

**Error Message:**
```
Error connecting to endpoint: ('Connection aborted.', ConnectionResetError(104, 'Connection reset by peer'))
```

**Root Cause:**
The "Content Extraction Engine" is configured to use `http://192.168.0.151:6333` as an external document loader, but this URL is actually the Qdrant vector database. Open WebUI expects a document extraction service (like Apache Tika) at this endpoint, not a vector database.

---

## Fix: Correct Open WebUI Settings

### Step 1: Fix Content Extraction Engine

Navigate to **Admin Settings → Documents**:

1. **Content Extraction Engine:** Change from "External" to **"Default"**
2. Remove the URL `http://192.168.0.151:6333` from the External URL field

This will make Open WebUI use its built-in extraction engine (Unstructured.io library).

### Step 2: Configure Qdrant Connection (Environment Variables)

Open WebUI uses **ChromaDB by default** for vector storage. To use Qdrant instead, you need to configure environment variables in your Open WebUI deployment.

#### If Open WebUI is running in Docker:

Edit your `docker-compose.yml` or Docker run command to add:

```yaml
services:
  open-webui:
    environment:
      - VECTOR_DB=qdrant  # Use Qdrant instead of ChromaDB
      - QDRANT_HOST=192.168.0.151
      - QDRANT_PORT=6333
      # Optional: If Qdrant requires authentication
      # - QDRANT_API_KEY=your_api_key_here
```

Or if using Docker run:
```bash
docker run -d \
  -e VECTOR_DB=qdrant \
  -e QDRANT_HOST=192.168.0.151 \
  -e QDRANT_PORT=6333 \
  -p 3000:8080 \
  ghcr.io/open-webui/open-webui:main
```

#### If Open WebUI is running as a Python app:

Create/edit `.env` file in Open WebUI directory:
```env
VECTOR_DB=qdrant
QDRANT_HOST=192.168.0.151
QDRANT_PORT=6333
```

### Step 3: Verify Collection Name

Open WebUI expects a specific collection name. By default it uses `open_webui`.

**Option A: Use Open WebUI's default collection**

When ingesting books, use:
```bash
python ingest_books.py \
  --file "../ingest/Silverston Vol 3.epub" \
  --domain technical \
  --collection open_webui
```

**Option B: Configure Open WebUI to use custom collection**

Add to environment variables:
```yaml
QDRANT_COLLECTION_NAME=alexandria
```

---

## Recommended Configuration

### Open WebUI Settings (UI)

**Admin Settings → Documents:**
- ✅ Content Extraction Engine: **Default** (not External)
- ✅ Chunk Size: **1500** (matches our ingestion)
- ✅ Chunk Overlap: **200** (matches our ingestion)
- ✅ Vector Store: Should show **Qdrant** (after env vars configured)

**Admin Settings → Models:**
- ✅ Embedding Model: **sentence-transformers/all-MiniLM-L6-v2** (matches our ingestion)

**Admin Settings → Documents → RAG:**
- ✅ Hybrid Search: **Enabled** (combines vector + keyword search)
- ✅ Reranking Model: **Default** (or leave disabled for initial testing)

### Environment Variables

```env
# Vector Database
VECTOR_DB=qdrant
QDRANT_HOST=192.168.0.151
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=alexandria_test

# Embedding Model
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Optional: Document Processing
CHUNK_SIZE=1500
CHUNK_OVERLAP=200
```

---

## Testing the Setup

### 1. Verify Qdrant Connection

After configuring environment variables, restart Open WebUI and check logs:

```bash
# Docker logs
docker logs -f open-webui

# Look for messages like:
# "Connected to Qdrant at 192.168.0.151:6333"
# "Using collection: alexandria_test"
```

### 2. Test RAG Query

1. Go to https://ai.jedai.space
2. Select a RAG-enabled model
3. Ask: **"What does Silverston say about shipment patterns?"**
4. Expected: Should retrieve relevant chunks from `alexandria_test` collection

### 3. Check Retrieved Documents

In the chat response, Open WebUI should show:
- ✅ Document snippets from Silverston Vol 3
- ✅ Source citation (book title, author)
- ✅ Relevance score

---

## Alternative: Use Python CLI (Bypass Open WebUI)

If configuring Open WebUI environment variables is complex, you can use the Python CLI approach:

### Search via CLI
```bash
cd scripts
python qdrant_utils.py search alexandria_test "shipment patterns" --limit 5
```

### LLM Integration (Manual)
1. Run search via CLI → copy results
2. Paste results into Open WebUI chat manually
3. Ask LLM to answer question based on provided context

---

## Troubleshooting

### Issue: "Collection not found: open_webui"

**Cause:** Open WebUI expects a collection named `open_webui` but you ingested to `alexandria_test`.

**Fix:**
```bash
# Create alias pointing to your collection
cd scripts
python qdrant_utils.py alias alexandria_test open_webui
```

### Issue: "Embedding dimension mismatch"

**Cause:** Open WebUI is using a different embedding model than our ingestion script.

**Fix:** Ensure both use the same model:
- Ingestion: `all-MiniLM-L6-v2` (384-dim)
- Open WebUI: Set `EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2`

### Issue: "No results returned"

**Cause:** Query embeddings generated by Open WebUI don't match ingestion embeddings.

**Fix:**
1. Verify embedding model is the same
2. Test search via Python CLI first:
   ```bash
   python qdrant_utils.py search alexandria_test "test query" --limit 5
   ```
3. If CLI works but Open WebUI doesn't → check Open WebUI Qdrant connection

---

## Current Status

| Component | Status | Notes |
|-----------|--------|-------|
| Python Ingestion | ✅ Working | 153 chunks from Silverston Vol 3 ingested |
| Qdrant Collection | ✅ Ready | `alexandria_test` collection at 192.168.0.151:6333 |
| Python CLI Search | ✅ Working | Semantic search returns relevant results |
| Open WebUI Config | ⚠️ **Needs Fix** | Content Extraction Engine incorrectly set to External |
| Open WebUI RAG | ❌ **Not Working** | Connection error due to misconfiguration |

---

## Next Steps

1. **Fix Content Extraction Engine** → Set to "Default"
2. **Configure Environment Variables** → Add Qdrant connection details
3. **Restart Open WebUI** → Apply new configuration
4. **Test RAG Query** → Verify it retrieves from `alexandria_test`
5. **Ingest More Books** → Add psychology, philosophy, history books

---

**Last Updated:** 2026-01-21 18:45
**Contact:** Sabo (BMad team)
