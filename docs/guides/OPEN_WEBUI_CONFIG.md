# Open WebUI Configuration

**Date:** 2026-01-23
**Open WebUI URL:** https://ai.jedai.space
**Vector Database:** Qdrant (local, shared with Alexandria)

---

## Architecture Decision (ADR-0006)

**Alexandria uses local Qdrant with separate collections:**

### Single Qdrant Instance (Dell BUCO)
- **Host:** 192.168.0.151:6333
- **Collections:**
  - `alexandria` - Curated book library (300-500 books, domain-specific)
  - `ai_agents` - AI agent workspace
  - `open_webui` - Open WebUI ad-hoc uploads
- **Cost:** $0/year (self-hosted)
- **Access:** Local network only

**Why collections?** Same database, clear separation, zero vendor lock-in, full control. See [ADR-0006](../architecture/decisions/0006-separate-systems-architecture.md) for full rationale.

---

## Open WebUI Configuration (Local Qdrant)

### Environment Variables (docker-compose.yml)

```yaml
services:
  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: open-webui
    restart: unless-stopped
    networks:
      - internal
    ports:
      - "3001:8080"
    environment:
      # Vector Database: Local Qdrant
      - VECTOR_DB=qdrant
      - QDRANT_HOST=192.168.0.151
      - QDRANT_PORT=6333
      - QDRANT_COLLECTION_NAME=open_webui
      
      # Embedding Model (match Alexandria)
      - RAG_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
      
      # LLM Providers
      - OPENAI_API_BASE_URL=https://openrouter.ai/api/v1
      - OPENAI_API_KEY=${OPENROUTER_API_KEY}
      - OLLAMA_BASE_URL=http://192.168.0.151:11434
      
      # Document Processing
      - ENABLE_WEB_SEARCH=true
    volumes:
      - open-webui-data:/app/backend/data

volumes:
  open-webui-data:

networks:
  internal:
```

### Admin Settings (Web Interface)

1. **Navigate to:** https://ai.jedai.space → Profile → Settings → Admin Settings

2. **Documents Section:**
   - Content Extraction Engine: **Default** (built-in)
   - Vector Store: Should show **Qdrant** (from env vars)
   - Collection Name: **open_webui** (from env vars)
   - Chunk Size: 1500 (optional, adjust as needed)
   - Chunk Overlap: 200 (optional, adjust as needed)

3. **RAG Settings:**
   - Embedding Model: **sentence-transformers/all-MiniLM-L6-v2** (matches Alexandria)
   - Hybrid Search: Enabled (recommended)
   - Reranking: Optional (can improve results)

---

## Usage

---

### Upload Documents to Open WebUI

1. Go to https://ai.jedai.space
2. Click **"+"** → **"Upload Document"**
3. Select PDF, TXT, EPUB, or other supported format
4. Document is processed and stored in Pinecone
5. Ask questions about the uploaded document

### Query Alexandria Books

**Open WebUI uses separate collection from Alexandria curated library.**

To search Alexandria curated books:

1. **Use Python CLI**
   ```bash
   cd c:/Users/goran/source/repos/Temenos/Akademija/Alexandria/scripts
   python rag_query.py "What does Silverston say about shipment patterns?" \
       --collection alexandria \
       --domain technical \
       --limit 5
   ```

2. **Use Streamlit GUI**
   - Launch: `streamlit run alexandria_app.py`
   - Go to **Query** tab
   - Enter question and get LLM-powered answer

3. **Switch Open WebUI to Alexandria collection (Advanced)**
   - Change env var: `QDRANT_COLLECTION_NAME=alexandria`
   - Restart Open WebUI
   - Note: Will lose access to uploaded docs in `open_webui` collection

---

## Troubleshooting

### Issue: "Failed to connect to Qdrant"

**Cause:** Dell BUCO offline or Qdrant not running.

**Fix:**
1. Check Qdrant is running: `curl http://192.168.0.151:6333/collections`
2. Verify Dell BUCO is online and accessible
3. Check network connectivity from NAS to Dell
4. Restart Open WebUI: `docker-compose restart open-webui`

### Issue: "Collection 'open_webui' not found"

**Cause:** Collection hasn't been created yet.

**Fix:**
Open WebUI will auto-create the collection on first document upload. Alternatively, create manually:
```bash
python scripts/qdrant_utils.py create open_webui --dimensions 384
```

### Issue: "Cannot query Alexandria books from Open WebUI"

**This is expected behavior.**

Open WebUI uses `open_webui` collection, Alexandria uses `alexandria` collection. They're intentionally separate for:
- Different quality levels (curated vs ad-hoc)
- Different chunking strategies
- Clear organizational boundaries

To query Alexandria: Use Streamlit GUI or Python CLI

### Issue: "Document upload fails"

**Cause:** Qdrant connection error or embedding model mismatch.

**Fix:**
1. Verify Qdrant is accessible: `curl http://192.168.0.151:6333`
2. Check docker logs: `docker logs open-webui`
3. Verify embedding model matches (all-MiniLM-L6-v2, 384 dimensions)

---

## Collection Strategy

| Collection | Purpose | Management | Quality | Use Case |
|------------|---------|------------|---------|----------|
| **alexandria** | Curated book library (300-500 books) | Streamlit + batch_ingest.py | High | Deep research on carefully selected books |
| **ai_agents** | AI agent workspace | Python scripts | Medium | Project-specific AI agent research |
| **open_webui** | Ad-hoc uploads | Open WebUI interface | Variable | Quick document Q&A |

**Key Benefits:**
- ✅ Same Qdrant instance (one database to maintain)
- ✅ Clear separation (collection boundaries)
- ✅ Zero cost (self-hosted)
- ✅ Same embedding model (consistency)
- ✅ Local speed (millisecond queries)

---

## Related Documentation

- **[ADR-0006](../architecture/decisions/0006-separate-systems-architecture.md)** - Why separate systems
- **[AGENTS.md](../../AGENTS.md)** - Alexandria configuration reference
- **[scripts/README.md](../../scripts/README.md)** - How to use Alexandria CLI tools

---

**Last Updated:** 2026-01-21 18:45
**Contact:** Sabo (BMad team)
