# Alexandria – Improvement Backlog (Predloženo)

Ovaj dokument sadrži **konkretnu, prioritetiziranu listu poboljšanja** za Alexandria sustav, temeljenu na postojećoj arhitekturi, kodu i workflowima.

Cilj nije dodavati nove slojeve, nego **ojačati postojeći motor** bez narušavanja dizajna (thin GUI, scripts-first, agent-neutral).

---

## P0 — Stabilnost i determinističnost (odmah / kratko)

### 1. Ingest Versioning (minimalno)
**Problem:** Ne postoji formalni trag *kojim pravilima* je knjiga ingestirana.

**Prijedlog:**
- Dodati u payload:
  - `ingest_version`
  - `chunking_strategy`
  - `embedding_model`

**Dobit:**
- siguran re-ingest
- mogućnost usporedbe rezultata
- bez migracija

---

### 2. Stabilni Chunk Fingerprint
**Problem:** Teško je razlikovati “isti” chunk između dva ingest-a.

**Prijedlog:**
- Uvesti `chunk_fingerprint = sha1(book_id + section + order + text)`

**Dobit:**
- diff ingest-a
- selective re-index
- audit

---

### 3. Retrieval Explain Mode
**Problem:** Nije uvijek jasno *zašto* je nešto vraćeno.

**Prijedlog:**
- `explain=True` flag u `rag_query.py`
- vratiti: score, distance, chunk_id, book

**Dobit:**
- lakše debugiranje
- agenti mogu učiti iz retrievala

---

## P1 — Kvaliteta znanja i kontrole (srednji rok)

### 4. Query Modes (policy, ne API explosion)
**Prijedlog:**
- Jedan endpoint, više modova:
  - `fact`
  - `cite`
  - `explore`
  - `synthesize`

**Dobit:**
- predvidivo ponašanje
- manji prompt-hackovi

---

### 5. Domain-Aware Retrieval Weights
**Problem:** Svi chunkovi tretirani jednako.

**Prijedlog:**
- Domain weight multiplier (npr. philosophy > fiction)

**Dobit:**
- bolji recall
- manje šuma

---

### 6. Retrieval Self-Test Suite
**Prijedlog:**
- Mali set canonical pitanja po domeni
- Snapshot očekivanih izvora (ne teksta)

**Dobit:**
- regresijska zaštita
- mir kod refactora

---

## P2 — Operativna ergonomija (kasnije)

### 7. Ingest Diff Tool
**Prijedlog:**
- Script: `compare_ingest(v1, v2)`
- Razlike u chunk count, size, coverage

---

### 8. Soft Delete + Re-Ingest Flow
**Prijedlog:**
- Flag `active=false` u payloadu
- fizičko brisanje tek kasnije

---

### 9. Performance Telemetry (lightweight)
**Prijedlog:**
- Log vremena:
  - embedding
  - upload
  - search
  - LLM answer

---

## P3 — Strateški, ali niskorizični dodaci

### 10. Pluggable Embedding Backends
**Prijedlog:**
- Adapter pattern za embedding modele

---

### 11. Read-Only Public Query API
**Prijedlog:**
- Minimalni FastAPI wrapper
- Bez ingest mogućnosti

---

## Anti-goals (svjesno ne raditi)

- ❌ Više ingest pipelinea
- ❌ Logika u GUI-ju
- ❌ Dijeljeni Qdrant ownership
- ❌ Framework-heavy RAG (LangChain / sl.)

---

## Mentalni kompas

> Ako poboljšanje ne stane u `scripts/` bez mijenjanja klijenata — vjerojatno nije dobro.

---

**Status:** prijedlog
**Autor:** AI
**Napomena:** Lista je namjerno konzervativna — fokus na stabilnost, ne feature creep.

