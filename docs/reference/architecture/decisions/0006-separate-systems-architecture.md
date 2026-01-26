# ADR-0006: Local Qdrant with Separate Collections Architecture

**Date:** 2026-01-23  
**Status:** Accepted  
**Deciders:** Goran (BMad Team)

---

## Context

During planning for production deployment, we explored various cloud vector database options (Pinecone, Qdrant Cloud). After analysis:

**Concerns identified:**
- Pinecone free tier reduced from 1M → 100K vectors (aggressive cuts)
- Vendor lock-in risks with proprietary APIs
- Cost unpredictability with cloud services
- Data privacy (books in US cloud servers)

**Evaluation:**
- Qdrant Cloud: 1M vectors free, but adds complexity
- Pinecone: Too small, vendor lock-in risk
- Local Qdrant: Already working, free, full control

---

## Decision

**Use local Qdrant with separate collections for different use cases:**

### Single Qdrant Instance (Dell BUCO)
- **Host:** 192.168.0.151:6333
- **Management:** Self-hosted, full control
- **Cost:** $0/year (hardware already owned)
- **Access:** Local network only

### Collection Strategy

**1. Alexandria Collection (Curated Books)**
- **Collection:** `alexandria`
- **Purpose:** Curated book library (300-500 essential books)
- **Chunking:** Domain-specific optimized
- **Management:** Streamlit GUI + batch_ingest.py
- **Users:** Admins (ingestion, management)
- **Quality:** High (carefully curated)

**2. AI Agents Collection**
- **Collection:** `ai_agents`
- **Purpose:** AI agent workspace for project research
- **Chunking:** Flexible, project-specific
- **Management:** Python scripts, CLI tools
- **Users:** AI agents (Claude, GPT-4, etc.)
- **Quality:** Medium (temporary, experimental)

**3. Open WebUI Collection**
- **Collection:** `open_webui`
- **Purpose:** Ad-hoc document uploads via Open WebUI
- **Chunking:** General-purpose (Open WebUI default)
- **Management:** Open WebUI interface
- **Users:** Researchers, quick queries
- **Quality:** Variable (user-uploaded content)

---

## Rationale

### Benefits of Single Qdrant with Multiple Collections

**Technical:**
- ✅ **Single database to maintain** - One Qdrant instance, simpler operations
- ✅ **Zero cost** - Self-hosted, no cloud fees
- ✅ **Collection isolation** - Each use case has dedicated namespace
- ✅ **Same embedding model** - Consistency across collections
- ✅ **Full control** - No vendor dependencies
- ✅ **Local speed** - Millisecond query latency

**Organizational:**
- ✅ **Clear separation** - Collections define boundaries
- ✅ **Flexible workflows** - Each collection managed differently
- ✅ **Data privacy** - Everything stays on local infrastructure
- ✅ **Predictable** - No surprise tier reductions or pricing changes

**Risk Mitigation:**
- ✅ **No vendor lock-in** - Qdrant is open source
- ✅ **Future flexibility** - Can move to Qdrant Cloud anytime (same API)
- ✅ **Backup ready** - Local copies + manifest system

### Collection Workflows

**Alexandria Collection:**
```
Use Case: "Deep research on Mishima's philosophy in curated library"
Flow: Streamlit → Select books → Domain-optimized chunking → Qdrant/alexandria → RAG query
```

**AI Agents Collection:**
```
Use Case: "AI agent needs context for project about data modeling"
Flow: Agent API call → Python script → Qdrant/ai_agents → Return chunks (no LLM)
```

**Open WebUI Collection:**
```
Use Case: "Quick question about PDF I just uploaded"
Flow: Upload via Open WebUI → Qdrant/open_webui → Chat interface → Answer
```

---

## Consequences

### Positive
- ✅ Single Qdrant instance to maintain
- ✅ Zero ongoing costs
- ✅ Full data control and privacy
- ✅ Collection-level isolation
- ✅ Same API everywhere (easy to use)
- ✅ No vendor lock-in risks

### Negative
- ⚠️ Open WebUI needs Qdrant configuration (not Pinecone)
- ⚠️ Dell BUCO must stay online for access
- ⚠️ Local network only (no remote access without VPN)

### Mitigation
- Configure Open WebUI to use `VECTOR_DB=qdrant` with `open_webui` collection
- Keep Dell BUCO running (it's already hosting Ollama anyway)
- For remote access: Set up VPN or consider Qdrant Cloud later (same API)

---

## Implementation

### Qdrant Instance (Dell BUCO)
```yaml
# Already running at 192.168.0.151:6333
# No changes needed to existing setup
Collections:
  - alexandria         # Curated books (300-500 books)
  - alexandria_test    # Testing collection
  - ai_agents          # AI agent workspace
  - open_webui         # Open WebUI uploads
```

### Alexandria (Streamlit GUI)
```python
# No changes needed
QDRANT_HOST = "192.168.0.151"
QDRANT_PORT = 6333
DEFAULT_COLLECTION = "alexandria"
```

### Open WebUI Configuration
```yaml
# docker-compose.yml for Open WebUI
services:
  open-webui:
    environment:
      # Use local Qdrant
      - VECTOR_DB=qdrant
      - QDRANT_HOST=192.168.0.151
      - QDRANT_PORT=6333
      - QDRANT_COLLECTION_NAME=open_webui
      
      # Embedding model (match Alexandria)
      - RAG_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
      
      # Other settings
      - OPENAI_API_BASE_URL=https://openrouter.ai/api/v1
      - OLLAMA_BASE_URL=http://192.168.0.151:11434
```

### AI Agent Access
```python
from qdrant_client import QdrantClient

# Connect to local Qdrant
client = QdrantClient(host="192.168.0.151", port=6333)

# Query ai_agents collection
results = client.search(
    collection_name="ai_agents",
    query_vector=embedding,
    limit=5
)
```

---

## Related Decisions

- **ADR-0001:** Use Qdrant Vector DB (still valid, now with multiple collections)
- **ADR-0002:** Domain-Specific Chunking (Alexandria collection)
- **ADR-0003:** GUI as Thin Layer (Alexandria Streamlit)

---

## Notes

This decision prioritizes **cost control, data privacy, and vendor independence** over cloud convenience. The single Qdrant instance with multiple collections provides clear separation while maintaining simplicity.

**Rejected alternatives:**
- Pinecone: Free tier too small (100K vectors), vendor lock-in risk
- Qdrant Cloud: Adds complexity without clear benefit for local-first workflow
- Mixed approach: Unnecessary complexity

**Future considerations:**
- If remote access becomes critical, migrate to Qdrant Cloud (same API)
- If collections grow beyond capacity, can shard or upgrade Dell BUCO
- Open WebUI can be switched to use different collection if needed

---

**Last Updated:** 2026-01-23  
**Author:** Cline (AI Assistant) + Goran
