# Idea: Author Geography Map

**Status:** Idea
**Created:** 2026-01-30
**Effort:** Medium (2-3 days)

---

## Concept

Visualize geographic distribution of authors in the Calibre library using Datasette's cluster-map plugin.

## Why

- See which regions/countries are most represented
- Discover blind spots in collection (e.g., few African authors?)
- Cool visualization for library overview

## Technical Approach

1. **Extract authors** from Calibre `authors` table (~3000-4000 unique)
2. **Enrich with Wikidata** - query birthplace/nationality via SPARQL API
3. **Geocode** places to lat/long (OpenStreetMap Nominatim or similar)
4. **Store** in new table `author_locations`:
   ```sql
   CREATE TABLE author_locations (
       author_id INTEGER PRIMARY KEY,
       author_name TEXT,
       birthplace TEXT,
       country TEXT,
       latitude REAL,
       longitude REAL,
       wikidata_id TEXT,
       book_count INTEGER
   );
   ```
5. **Visualize** with `datasette-cluster-map` plugin

**Schema option A** - Add columns to existing `authors` table (cleaner, no JOIN):
   ```sql
   ALTER TABLE authors ADD COLUMN birthplace TEXT;
   ALTER TABLE authors ADD COLUMN country TEXT;
   ALTER TABLE authors ADD COLUMN latitude REAL;
   ALTER TABLE authors ADD COLUMN longitude REAL;
   ALTER TABLE authors ADD COLUMN wikidata_id TEXT;
   ```
   *Note: Test on backup first - verify Calibre doesn't overwrite custom columns.*

**Schema option B** - Separate table with FK (safer but requires JOIN):
   ```sql
   CREATE TABLE author_locations (...);
   ```

## Implementation Note

**Run on NAS MASTER database** - Not on local Google Drive backup copy. Enrichment writes to source of truth, then syncs down.

**Use Claude Haiku for enrichment** - This is ideal batch work for the smaller model:
- Repetitive pattern (lookup author → parse → geocode)
- No deep reasoning required
- ~60x cheaper than Opus
- Can process all 3000+ authors cost-effectively

## Challenges

- ~30-40% authors may not have Wikidata entries
- Historical place names (Königsberg → Kaliningrad)
- Pseudonyms and pen names
- Rate limiting on Wikidata/geocoding APIs

## Dependencies

- `datasette-cluster-map` plugin
- Wikidata SPARQL endpoint
- Geocoding service (Nominatim is free but rate-limited)

## Datasette Write Access

Datasette is read-only by default. Options for writing:
- `datasette-write-ui` plugin - web form for editing
- `datasette-insert-api` plugin - REST API for inserts
- **Recommended:** Direct SQLite via Python script for bulk enrichment (3000+ authors), Datasette only for viewing/map

## Alternatives

- Manual curation for top 100 most-published authors only
- Use LLM to guess nationality from name (less accurate)
- Skip geocoding, just do country-level aggregation (choropleth map)

---

## References

- datasette-cluster-map: https://datasette.io/plugins/datasette-cluster-map
- Wikidata SPARQL: https://query.wikidata.org/
- Nominatim: https://nominatim.org/
