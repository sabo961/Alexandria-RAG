# How Alexandria Works: Under the Hood

> **Concept:** Alexandria is not just a database; it is a **processing pipeline** that transforms raw text into semantic meaning.

## 1. The Ingestion Pipeline (The "Brain")

When you click **"Start Ingestion"** in the GUI, the `Scripts Package` takes over. Here is the step-by-step journey of a book:

### Step 1: Text Extraction (`ingest_books.py`)
- **Input:** EPUB, PDF, or TXT file.
- **Action:**
    - **EPUB:** Preserves chapter boundaries. Each chapter is treated as a logical unit.
    - **PDF:** Extract text page-by-page. *Note:* Headers/Footers are currently "noise" we need to filter better.
- **Output:** Raw text blocks with metadata (Title, Author).

### Step 2: The Chunking Router (The Decision Maker)
This is where Alexandria differs from basic RAG systems. It doesn't just slice text blindly.
- **Logic:** It looks at the **Domain** selected in the GUI.
    - **Technical:** Needs code blocks kept together. Uses *Fixed Window* (1500 tokens) with overlap.
    - **Philosophy:** Needs arguments kept intact. Uses *Argument Strategy* (experimental).
    - **Literature:** Needs scenes. Uses *Scene/Chapter Strategy*.

### Step 3: Vectorization (The Translator)
- **Model:** `all-MiniLM-L6-v2` (Local).
- **Action:** Converts each text chunk into a list of 384 numbers (a vector).
- **Why Local?** Privacy, speed, and zero cost. No API calls to OpenAI for embedding.

### Step 4: Storage (The Memory)
- **Qdrant:** Stores the vector + payload (text, book title, chapter name).
- **Manifest:** Logs the ingestion to `logs/alexandria_manifest.json` so we don't re-ingest the same book twice.

---

## 2. The Query Engine (The Librarian)

When you ask a question:

1.  **Translation:** Your question is converted into a vector (using the same "language" as the books).
2.  **Search:** Qdrant finds the nearest vectors (chunks) in 384-dimensional space.
    - *Fetch Multiplier:* We fetch 3x more results than needed to filter out low-quality matches.
3.  **Reranking (Optional):** An LLM (OpenRouter) looks at the top results and re-orders them based on true relevance (slower but smarter).
4.  **Generation:** The top chunks are sent to a generative LLM (e.g., GPT-4o-mini) with the prompt: *"Answer using only these sources..."*

## 3. Current Limitations (The Roadmap)
- **PDF Noise:** Page numbers and headers sometimes end up in chunks.
- **Philosophy Chunking:** Currently relies on regex/keywords. Needs "Semantic Chunking" (analyzing vector shifts between sentences) to be truly effective.

---
*See `docs/architecture/workspace.dsl` for the visual model.*
