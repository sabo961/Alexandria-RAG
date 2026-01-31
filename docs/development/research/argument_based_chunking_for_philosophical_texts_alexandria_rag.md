# Argument‑Based Chunking for Philosophical Texts

**Project:** Alexandria RAG
**Audience:** Developers / maintainers
**Status:** Proposed (ready for implementation)

---

## 1. Problem Statement

The current ingestion pipeline uses **token‑based chunking** (fixed size + overlap). While this works well for technical and narrative texts, it fails for **philosophical essays** such as Yukio Mishima’s *Sun and Steel*.

Observed failure mode in RAG answers:
- The LLM correctly understands Mishima’s philosophy
- But repeatedly states: *"the provided context does not contain a specific passage"*
- The model falls back to **general knowledge**, not retrieved text

This indicates a **retrieval failure**, not a model failure.

---

## 2. Root Cause Analysis

Philosophical essays are structured around **conceptual tensions**, not topics or chapters.

In *Sun and Steel*, Mishima explicitly builds arguments through oppositions such as:

- words ↔ body
- writing ↔ action
- intellect ↔ muscle
- abstraction ↔ death

Token‑based chunking often splits these oppositions across different chunks, causing:
- Loss of argumentative unity
- Embeddings that encode "theme" but not "claim"
- Qdrant returning thematically related but non‑evidentiary chunks

Result: the RAG system has **nothing to prove the answer**, even though the model “knows” it.

---

## 3. Design Principle

> **A chunk is not a text fragment; it is one complete conceptual conflict.**

For philosophical essays:
- A valid chunk must contain **both poles of an opposition**
- And an **authorial stance**, not mere description

We call this approach **argument‑based chunking**.

---

## 4. Argument‑Based Chunking Strategy

### 4.1 Conceptual Oppositions (Heuristic)

Define explicit opposition pairs:

```python
ARGUMENT_PAIRS = [
    (["word", "words", "language", "writing"],
     ["body", "flesh", "muscle", "training", "action"]),

    (["writing", "pen", "text"],
     ["action", "violence", "discipline"]),

    (["intellect", "mind", "thought", "abstraction"],
     ["muscle", "strength", "pain"]),

    (["ideal", "beauty", "abstraction"],
     ["death", "blood", "destruction"])
]
```

This heuristic is intentionally simple:
- No NLP dependency
- No LLM call during ingestion
- Transparent and debuggable

---

### 4.2 Pre‑Chunking by Argument Detection

Before token chunking, text is split into paragraphs.

A pre‑chunk is formed when:
- Both sides of any conceptual pair appear **within the same paragraph group**

```python
def argument_prechunks(text: str) -> List[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 200]

    chunks = []
    buffer = []

    def contains(pair, text):
        a, b = pair
        t = text.lower()
        return any(x in t for x in a) and any(x in t for x in b)

    for p in paragraphs:
        buffer.append(p)
        joined = " ".join(buffer)

        if any(contains(pair, joined) for pair in ARGUMENT_PAIRS):
            chunks.append(joined)
            buffer = []

    if buffer:
        chunks.append(" ".join(buffer))

    return chunks
```

Each resulting block represents **one argumentative unit**.

---

## 5. Integration into Existing Pipeline

### Scope of Change

- **No changes** to:
  - Qdrant
  - Embeddings
  - RAG query engine
  - Batch ingestion logic

- **Single addition** before `chunk_text()`

### Conditional Activation

Argument‑based pre‑chunking is applied only when:
- `domain == "philosophy"`
- AND book title matches known essay works (e.g. *Sun and Steel*)

Example integration point (`create_chunks_from_sections`):

```python
if domain == "philosophy" and "Sun and Steel" in metadata.get("title", ""):
    text_blocks = argument_prechunks(section['text'])
else:
    text_blocks = [section['text']]

for block in text_blocks:
    chunks = chunk_text(
        text=block,
        domain=domain,
        max_tokens=max_tokens,
        overlap=overlap,
        section_name=section_name,
        book_title=book_title,
        author=author
    )
```

---

## 6. Expected Effects

After re‑ingestion:

- Embeddings encode **claims**, not just topics
- Qdrant retrieves **evidentiary chunks**
- LLM answers:
  - Cite passages
  - Paraphrase Mishima’s stance
  - Stop using epistemic disclaimers

Expected similarity scores for targeted queries:
- `0.65+` for conceptual questions

---

## 7. Validation Query

```text
Find a passage in Sun and Steel where Mishima criticizes language or writing
in contrast to physical action, and explain how this reframes truth or knowledge.
```

Success criteria:
- Retrieved chunk contains **both sides of the contrast**
- Answer references concrete argument
- No “context does not contain…” phrasing

---

## 8. Generalization

This strategy generalizes well to:
- Nietzsche
- Cioran
- Kierkegaard
- Essays with explicit dialectical structure

The opposition list can be extended per author.

---

## 9. Key Takeaway

> **Token chunking preserves text.
> Argument chunking preserves thought.**

For philosophical RAG systems, the latter is essential.

---

**End of document**

