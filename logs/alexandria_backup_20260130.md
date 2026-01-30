# Alexandria Collection Backup - 2026-01-30

**Purpose:** Record of collection state before hierarchical chunking migration.

## Collection Statistics

- **Collection:** alexandria
- **Total Points:** 8,592
- **Vector Size:** 384 (all-MiniLM-L6-v2)
- **Unique Books:** 23

## Books in Collection

| Chunks | Title | Author | Language |
|--------|-------|--------|----------|
| 924 | The Organized Mind: Thinking Straight in the Age of Information Overload | Daniel J. Levitin | eng |
| 865 | Thinking, Fast and Slow | Daniel Kahneman | eng |
| 814 | The Data Model Resource Book Vol 3: Universal Patterns | Len Silverston & Paul Agnew | eng |
| 527 | Life 3.0: Being Human in the Age of Artificial Intelligence | Max Tegmark | eng |
| 408 | Reframing: Neuro-Linguistic Programming and the Transformation of Meaning | Richard Bandler & John Grinder | eng |
| 396 | Frogs Into Princes: Neuro Linguistic Programming | Richard Bandler & John Grinder | eng |
| 395 | Clean Architecture: A Craftsman's Guide to Software Structure | Robert C. Martin | eng |
| 388 | Scary Smart: The Future of Artificial Intelligence | Mo Gawdat | eng |
| 371 | Our Final Invention: Artificial Intelligence and the End of the Human Era | James Barrat | eng |
| 366 | A Field Guide to Lies: Critical Thinking in the Information Age | Daniel J. Levitin | eng |
| 355 | Blink: The Power of Thinking Without Thinking | Malcolm Gladwell | eng |
| 340 | My Voice Will Go with You: The Teaching Tales of Milton H. Erickson | Sidney Rosen & Milton H. Erickson | eng |
| 339 | Parallel Thinking | Edward de Bono | eng |
| 328 | Phoenix: Therapeutic Patterns of Milton H. Erickson | David Gordon & Maribeth Meyers-Anderson | eng |
| 324 | Richard Bandler's Guide to Trance-formation | Richard Bandler & Paul McKenna | eng |
| 322 | Lateral Thinking | Edward de Bono | eng |
| 278 | The Structure of Magic II | Richard Bandler & John Grinder | eng |
| 259 | How to Take Smart Notes | Sönke Ahrens | eng |
| 196 | Atlas of Management Thinking | Edward de Bono | eng |
| 186 | Six Thinking Hats | Edward de Bono | eng |
| 79 | The C4 model for visualising software architecture | Simon Brown | eng |
| 70 | AI Agents with MCP | Kyle Stratis | eng |
| 62 | Generative AI for Beginners | Alex Quant | eng |

## Rollback Instructions

If hierarchical chunking fails, restore by re-ingesting these 23 books:

```bash
# Books can be re-ingested from Calibre library
# All books were using universal-semantic chunking strategy
# Parameters: threshold=0.55, min_chunk=200, max_chunk=1200
```

## Manifest Files

- `logs/alexandria_manifest.json` - Contains ingestion metadata
- `logs/alexandria_manifest.csv` - CSV export

---

**Backup Date:** 2026-01-30
**Backup Reason:** Clean slate for hierarchical chunking implementation
