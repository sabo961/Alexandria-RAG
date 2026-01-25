Evo briefa za Haikua:

---

## Task: Optimizacija Alexandria Streamlit aplikacije

### Kontekst
`alexandria_app.py` je RAG aplikacija s ~2150 linija. Glavni problem: Streamlit reruna cijelu skriptu na svaku interakciju (checkbox, button click, itd.). Cilj je minimizirati nepotrebne rerunove i poboljšati strukturu koda.

---

### 1. PRIORITET VISOK: `@st.fragment` za Query tab

**Problem:** Svaki klik na Query tabu reruna cijelu aplikaciju (2150 linija).

**Rješenje:** Wrappaj Query tab logiku u `@st.fragment` dekorator.

**Lokacija:** Linije 1969-2136

**Kako:**
```python
@st.fragment
def render_query_tab():
    st.markdown('<div class="section-header">🔍 Query Interface</div>', unsafe_allow_html=True)
    
    # ... sav postojeći kod iz tab_query bloka ...
    
# Umjesto "with tab_query:" koristi:
with tab_query:
    render_query_tab()
```

**Napomena:** Funkcija mora biti definirana PRIJE nego se poziva. Definiraj je negdje oko linije 1960.

---

### 2. PRIORITET VISOK: Cache za `load_domains()`

**Problem:** `load_domains()` čita `scripts/domains.json` na svaki rerun. Poziva se minimalno 4 puta.

**Lokacija:** Linije 209-216

**Prije:**
```python
def load_domains():
    domains_file = Path(__file__).parent / 'scripts' / 'domains.json'
    try:
        with open(domains_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return [d['id'] for d in data['domains']]
    except Exception as e:
        ...
```

**Poslije:**
```python
@st.cache_data
def load_domains():
    # ... isti kod ...
```

---

### 3. PRIORITET VISOK: Cache za `check_qdrant_health()`

**Problem:** Health check se izvršava na SVAKI rerun - nepotrebno opterećuje mrežu i usporava UI.

**Lokacija:** Linije 321-349

**Prije:**
```python
def check_qdrant_health(host: str, port: int, timeout: int = 5) -> tuple[bool, str]:
    ...
```

**Poslije:**
```python
@st.cache_data(ttl=30)  # Cache 30 sekundi
def check_qdrant_health(host: str, port: int, timeout: int = 5) -> tuple[bool, str]:
    ...
```

**Napomena:** TTL=30 znači da će se health check izvoditi maksimalno jednom u 30 sekundi, ne na svaki klik.

---

### 4. PRIORITET SREDNJI: Cache za `load_gui_settings()`

**Problem:** Čita JSON file na svaki rerun.

**Lokacija:** Linije 49-59

**Rješenje:**
```python
@st.cache_data
def load_gui_settings() -> dict:
    ...
```

**VAŽNO:** Kad se settings SPREMAJU (linija 62-67, `save_gui_settings`), treba invalidirati cache:
```python
def save_gui_settings(settings: dict) -> None:
    ...
    # Na kraju funkcije dodaj:
    load_gui_settings.clear()  # Invalidira cache
```

---

### 5. PRIORITET SREDNJI: Fragment za Calibre tab filtere

**Problem:** Svaki filter input (author, title, language, format) reruna cijelu app.

**Lokacija:** Linije 594-1009

**Rješenje:** Wrappaj filter sekciju + tablicu u fragment:
```python
@st.fragment
def render_calibre_filters_and_table(all_books):
    # Filters (linije 635-653)
    # Apply filters (linije 655-676)
    # Display table (linije 677-836)
    pass

with tab_calibre:
    # Stats ostaju IZVAN fragmenta (linije 615-631)
    # ...
    render_calibre_filters_and_table(all_books)
```

---

### 6. PRIORITET SREDNJI: Fragment za Ingested Books tab

**Lokacija:** Linije 1013-1345

**Isti princip:** Wrappaj filtere i tablicu u `@st.fragment`.

---

### 7. PRIORITET NIŽI: DRY ingestion helper

**Problem:** Calibre ingestion (linije 886-996) i Folder ingestion (linije 1458-1510) imaju gotovo identičan loop.

**Rješenje:** Izvuci shared helper funkciju:

```python
def run_ingestion_batch(
    items: list[dict],  # [{"filepath": ..., "title": ..., "author": ..., "language": ...}, ...]
    domain: str,
    collection_name: str,
    qdrant_host: str,
    qdrant_port: int,
    manifest: CollectionManifest,
    move_files: bool = False,
    ingested_dir: Path = None,
    progress_callback = None  # Za st.progress update
) -> dict:
    """
    Returns: {"success_count": int, "error_count": int, "errors": list[str]}
    """
    ...
```

**Korištenje:**
```python
# U Calibre tabu:
result = run_ingestion_batch(
    items=[{"filepath": str(f), "title": book.title, ...} for book in selected_books],
    domain=calibre_domain,
    ...
)

# U Folder tabu:
result = run_ingestion_batch(
    items=[{"filepath": row["Path"], "title": row["Title"], ...} for _, row in df.iterrows()],
    ...
)
```

---

### 8. PRIORITET NIŽI: Izvuci CSS u zasebni file

**Problem:** 120 linija CSS-a inline (linije 81-203).

**Rješenje:**

1. Kreiraj `assets/style.css` s CSS sadržajem (bez `<style>` tagova)

2. Zamijeni inline CSS s:
```python
def load_css():
    css_path = Path(__file__).parent / "assets" / "style.css"
    if css_path.exists():
        with open(css_path, 'r') as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()
```

---

### 9. BONUS: Session state dataclass

**Problem:** 20+ individualnih `st.session_state.xyz` varijabli razbacanih po kodu.

**Rješenje:** Grupiraj u dataclass:

```python
from dataclasses import dataclass, field

@dataclass
class AppState:
    # Config
    library_dir: str = "G:\\My Drive\\alexandria"
    qdrant_host: str = "192.168.0.151"
    qdrant_port: int = 6333
    openrouter_api_key: str = ""
    
    # UI state
    calibre_selected_books: set = field(default_factory=set)
    last_selected_model: str = None
    openrouter_models: dict = field(default_factory=dict)
    
    # ... ostalo

def get_app_state() -> AppState:
    if "app_state" not in st.session_state:
        st.session_state.app_state = AppState()
    return st.session_state.app_state
```

**Korištenje:**
```python
state = get_app_state()
state.library_dir = new_value  # Umjesto st.session_state.library_dir = ...
```

---

### Redoslijed implementacije

1. ✅ `@st.cache_data` na `load_domains()` - 1 minuta
2. ✅ `@st.cache_data(ttl=30)` na `check_qdrant_health()` - 1 minuta  
3. ✅ `@st.fragment` na Query tab - 5 minuta
4. ⏳ `@st.fragment` na Calibre filtere - 10 minuta
5. ⏳ `@st.fragment` na Ingested Books filtere - 10 minuta
6. ⏳ CSS extraction - 5 minuta
7. ⏳ DRY ingestion helper - 30 minuta
8. ⏳ Session state consolidation - 45 minuta

---

### Testiranje

Nakon svake promjene:
1. Pokreni `streamlit run alexandria_app.py`
2. Otvori Query tab
3. Klikni checkbox/slider - stranica NE SMIJE full refresh
4. Provjeri konzolu za errore

---

### Ne diraj
- `scripts/` folder - backend ostaje netaknut
- Logiku `perform_rag_query()`, `ingest_book()` itd.
- Manifest strukturu

---
