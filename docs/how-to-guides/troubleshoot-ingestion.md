# Troubleshooting Alexandria Ingestion

**Problem Solved:** "Ingestion fails and I don't know why - how do I fix it?"

---

## Quick Diagnosis

Start here to identify your issue:

```
Ingestion Failed?
│
├─ Error mentions "ModuleNotFoundError" or "ImportError"
│  └─ → See: Module Import Errors
│
├─ Error mentions "Connection refused" or "timeout"
│  └─ → See: Qdrant Connection Errors
│
├─ Error mentions "long path" or "file name too long" (Windows)
│  └─ → See: Windows Long Path Limitations
│
├─ Error mentions "encoding" or "UnicodeDecodeError"
│  └─ → See: PDF Encoding Problems
│
├─ Error mentions "MemoryError" or "killed"
│  └─ → See: Memory Issues with Large Files
│
├─ Error mentions "Permission denied"
│  └─ → See: File Permission Errors
│
├─ Error mentions "not supported" or "unknown format"
│  └─ → See: Unsupported File Format Errors
│
├─ Resume doesn't work or skips wrong files
│  └─ → See: Batch Ingestion Resume Failures
│
├─ Chunks are too small/large or retrieval quality is poor
│  └─ → See: Chunk Size Configuration Issues
│
└─ Model download hangs or fails
   └─ → See: Embedding Model Download Issues
```

---

## Common Error Categories

### 1. Module Import Errors

#### 🔴 Symptoms
```
ModuleNotFoundError: No module named 'ebooklib'
ModuleNotFoundError: No module named 'fitz'
ImportError: cannot import name 'SentenceTransformer'
```

#### 🔍 Cause
Missing Python dependencies. Alexandria requires several libraries for different file formats:
- `ebooklib` - For EPUB files
- `PyMuPDF` (imports as `fitz`) - For PDF files
- `sentence-transformers` - For embeddings
- `qdrant-client` - For Qdrant connection

#### ✅ Solution

**Option A: Install all dependencies**
```bash
cd scripts
pip install -r requirements.txt
```

**Option B: Install specific missing module**
```bash
# For EPUB support
pip install EbookLib

# For PDF support
pip install PyMuPDF

# For embeddings
pip install sentence-transformers

# For Qdrant
pip install qdrant-client
```

**Verify installation:**
```bash
python -c "import ebooklib; import fitz; import sentence_transformers; print('All modules installed!')"
```

#### 🛡️ Prevention
- Always run `pip install -r requirements.txt` after cloning repo
- Use virtual environment to avoid conflicts
- Document custom dependencies if you add new file format support

---

### 2. Qdrant Connection Errors

#### 🔴 Symptoms
```
ConnectionRefusedError: [Errno 111] Connection refused
qdrant_client.http.exceptions.UnexpectedResponse: 504 Gateway Timeout
requests.exceptions.ConnectionError: HTTPConnectionPool
```

#### 🔍 Cause
1. Qdrant server is not running
2. Wrong host/port configuration
3. Firewall blocking connection
4. Qdrant crashed or is overloaded

#### ✅ Solution

**Step 1: Check if Qdrant is running**
```bash
# Check Docker container status
docker ps | grep qdrant

# If not running, start it
docker start qdrant

# If container doesn't exist, run new instance
docker run -d -p 6333:6333 -v qdrant_storage:/qdrant/storage qdrant/qdrant
```

**Step 2: Verify network connectivity**
```bash
# Test connection to Qdrant (Windows)
curl http://192.168.0.151:6333/collections

# Or use Python
python -c "from qdrant_client import QdrantClient; client = QdrantClient(host='192.168.0.151', port=6333); print('Connected!', client.get_collections())"
```

**Step 3: Check configuration**
```bash
# Verify host/port in your command
python ingest_books.py --file book.epub --domain technical --host 192.168.0.151 --port 6333

# Or check qdrant_utils.py default values
grep -n "DEFAULT_HOST\|DEFAULT_PORT" qdrant_utils.py
```

**Step 4: Check Qdrant logs**
```bash
# View container logs
docker logs qdrant

# Follow logs in real-time
docker logs -f qdrant
```

#### 🛡️ Prevention
- Create Docker Compose file to ensure Qdrant always runs
- Add health check script: `scripts/check_qdrant.sh`
- Use connection pooling and retry logic
- Monitor Qdrant disk space (collections need storage)

---

### 3. Embedding Model Download Issues

#### 🔴 Symptoms
```
Downloading (…)ce_transformers_config.json: 0%|          | 0.00/1.18k [00:00<?, ?B/s]
[Hangs indefinitely]

urllib3.exceptions.ReadTimeoutError: HTTPSConnectionPool
requests.exceptions.SSLError: [SSL: CERTIFICATE_VERIFY_FAILED]
```

#### 🔍 Cause
1. First-time model download from HuggingFace (large file)
2. Network firewall blocking HuggingFace
3. Slow internet connection
4. SSL certificate issues
5. HuggingFace API rate limiting

#### ✅ Solution

**Option A: Pre-download model manually**
```bash
# Download model before ingestion
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# This downloads to: C:\Users\<user>\.cache\huggingface\hub\
```

**Option B: Use environment variable for cache**
```bash
# Set custom cache location (if default has no space)
export TRANSFORMERS_CACHE=/path/to/large/drive/cache
python ingest_books.py --file book.epub --domain technical
```

**Option C: Bypass SSL verification (corporate firewall)**
```bash
# NOT RECOMMENDED for production, but works for testing
export CURL_CA_BUNDLE=""
python ingest_books.py --file book.epub --domain technical
```

**Option D: Use proxy if behind firewall**
```bash
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080
python ingest_books.py --file book.epub --domain technical
```

**Verify model is downloaded:**
```bash
# Windows
dir %USERPROFILE%\.cache\huggingface\hub\

# Linux/Mac
ls ~/.cache/huggingface/hub/
```

#### 🛡️ Prevention
- Pre-download models on new machines: `python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"`
- Keep cached models in shared network location
- Add retry logic with exponential backoff
- Document proxy settings for team

---

### 4. Windows Long Path Limitations (MAX_PATH)

#### 🔴 Symptoms
```
FileNotFoundError: [Errno 2] No such file or directory: 'C:\\Users\\...\\very\\long\\path\\...'
OSError: [Errno 22] Invalid argument: 'C:\\Users\\...\\extremely\\long\\file\\name.epub'
```

This happens when path exceeds 260 characters (Windows MAX_PATH limit).

#### 🔍 Cause
Windows has a 260-character path limit by default. With nested folders like:
```
C:\Users\goran\source\repos\Temenos\Akademija\Alexandria\ingest\technical\database\design\patterns\...
```
You quickly hit the limit.

#### ✅ Solution

**Option A: Enable long path support (Windows 10+)**
```bash
# 1. Run as Administrator in PowerShell
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force

# 2. Enable in Python (add to script top)
import sys
if sys.platform == 'win32':
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.SetDllDirectoryW(None)

# 3. Restart computer
```

**Option B: Use UNC path prefix**
```bash
# Convert regular path to UNC path
# From: C:\Users\goran\source\...\book.epub
# To:   \\?\C:\Users\goran\source\...\book.epub

python ingest_books.py --file "\\?\C:\Users\goran\source\repos\...\book.epub" --domain technical
```

**Option C: Move files to shorter path**
```bash
# Move ingest folder closer to root
# From: C:\Users\goran\source\repos\Temenos\Akademija\Alexandria\ingest
# To:   C:\ingest

# Update batch_ingest.py command
python batch_ingest.py --directory C:\ingest --domain technical
```

**Option D: Use symlink (symbolic link)**
```bash
# Create symlink with short name
mklink /D C:\alex C:\Users\goran\source\repos\Temenos\Akademija\Alexandria

# Use short path
cd C:\alex\scripts
python batch_ingest.py --directory C:\alex\ingest --domain technical
```

#### 🛡️ Prevention
- Enable long path support on new Windows installations
- Keep folder structures shallow (max 3-4 levels deep)
- Use short, descriptive folder names
- Store large book collections in `C:\books\` instead of deep user folders
- Add path length validation in `batch_ingest.py`

---

### 5. PDF Encoding Problems

#### 🔴 Symptoms
```
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 10
PyPDF2.errors.PdfReadError: EOF marker not found
fitz.fitz.FileDataError: cannot open document
```

#### 🔍 Cause
1. PDF contains non-UTF8 text (scanned images, special characters)
2. Corrupted PDF file
3. Password-protected or encrypted PDF
4. PDF created with unusual software (incompatible format)

#### ✅ Solution

**Step 1: Check if PDF is corrupted**
```bash
# Try opening in Adobe Reader or browser
# If it doesn't open, file is corrupted - re-download

# Validate PDF structure
python -c "import fitz; doc = fitz.open('book.pdf'); print(f'Pages: {doc.page_count}')"
```

**Step 2: Check if PDF is encrypted**
```bash
python -c "import fitz; doc = fitz.open('book.pdf'); print(f'Encrypted: {doc.is_encrypted}')"
```

If encrypted, decrypt first:
```bash
pip install pikepdf

python -c "import pikepdf; pdf = pikepdf.open('encrypted.pdf', password='yourpassword'); pdf.save('decrypted.pdf')"
```

**Step 3: Extract text with fallback encoding**
```python
# Add to ingest_books.py extract_text_from_pdf():
try:
    text = page.get_text("text")
except UnicodeDecodeError:
    # Fallback: extract as bytes and decode with errors='ignore'
    text = page.get_text("text", errors='ignore')
```

**Step 4: OCR scanned PDFs**
```bash
# For scanned PDFs (images, not text)
pip install pytesseract
# Install Tesseract OCR: https://github.com/tesseract-ocr/tesseract

# Extract text from images
python -c "import fitz; from PIL import Image; import pytesseract; ..."
```

**Step 5: Skip problematic PDF**
```bash
# Just skip it and continue with others
# batch_ingest.py already has error handling for this
python batch_ingest.py --directory ../ingest --domain technical --resume
```

#### 🛡️ Prevention
- Validate PDFs before ingestion: `python validate_pdfs.py --directory ../ingest`
- Keep source PDFs (don't delete after failed ingestion)
- Use PDF repair tools: `qpdf --check book.pdf`
- Add OCR pipeline for scanned books
- Log problematic PDFs to `logs/failed_pdfs.txt`

---

### 6. Memory Issues with Large Files

#### 🔴 Symptoms
```
MemoryError: Unable to allocate array
Killed
Process finished with exit code 137 (out of memory)
Python process uses 8GB+ RAM and crashes
```

#### 🔍 Cause
1. Large PDF (500+ MB) loaded entirely into memory
2. Processing thousands of books without clearing memory
3. Embedding model + book content exceed available RAM
4. Memory leak in chunking logic

#### ✅ Solution

**Step 1: Process files in smaller batches**
```bash
# Instead of ingesting 9000 books at once, split into batches
python batch_ingest.py --directory ../ingest/batch1 --domain technical
python batch_ingest.py --directory ../ingest/batch2 --domain technical
```

**Step 2: Reduce chunk size to use less memory**
```python
# In ingest_books.py, reduce chunk size temporarily
DOMAIN_CHUNK_SIZES = {
    'technical': {'min': 800, 'max': 1200, 'overlap': 100},  # Smaller chunks
}
```

**Step 3: Increase system swap space (Linux)**
```bash
# Create 8GB swap file
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

**Step 4: Use streaming for large PDFs**
```python
# Process PDF page-by-page instead of loading entire file
def extract_text_from_pdf_streaming(file_path):
    doc = fitz.open(file_path)
    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        text = page.get_text("text")
        yield text
        page = None  # Explicitly free memory
```

**Step 5: Monitor memory usage**
```bash
# Windows Task Manager: Ctrl+Shift+Esc → Performance → Memory
# Linux: watch -n 1 free -h
# Python: pip install memory-profiler
```

**Step 6: Increase Docker memory limit (if Qdrant crashes)**
```bash
# In Docker Desktop: Settings → Resources → Memory → 8GB+
docker update --memory 8g qdrant
```

#### 🛡️ Prevention
- Split large ingestion jobs into batches of 100-200 books
- Add memory profiling: `@profile` decorator
- Use `gc.collect()` after processing each book
- Add file size check before ingestion: skip files > 200MB
- Use streaming APIs instead of loading entire files
- Upgrade system RAM (16GB+ recommended for large libraries)

---

### 7. Calibre DB Connection Failures

#### 🔴 Symptoms
```
sqlite3.OperationalError: database is locked
FileNotFoundError: [Errno 2] No such file or directory: 'metadata.db'
sqlite3.DatabaseError: file is not a database
```

#### 🔍 Cause
1. Calibre desktop app has database file open (locked)
2. Wrong path to Calibre library folder
3. Corrupted Calibre database
4. Network drive with Calibre library disconnected

#### ✅ Solution

**Step 1: Close Calibre desktop app**
```bash
# Close Calibre completely (not just minimize)
# Windows: Task Manager → End Task
# Linux: killall calibre
```

**Step 2: Verify Calibre library path**
```bash
# Check for metadata.db file
dir "C:\Users\goran\Calibre Library\metadata.db"

# Update ingest_books.py with correct path
CALIBRE_LIBRARY = r"C:\Users\goran\Calibre Library"
```

**Step 3: Repair corrupted database**
```bash
# Backup database first
copy "C:\Users\goran\Calibre Library\metadata.db" metadata.db.backup

# Open Calibre → Library Maintenance → Check Library
# Or use calibredb CLI
calibredb check_library --library-path "C:\Users\goran\Calibre Library"
```

**Step 4: Read-only mode**
```python
# In calibre_utils.py, use read-only connection
import sqlite3
conn = sqlite3.connect('file:metadata.db?mode=ro', uri=True)
```

**Step 5: Export metadata instead of direct DB access**
```bash
# Export Calibre metadata to JSON
calibredb list --for-machine --library-path "C:\Users\goran\Calibre Library" > calibre_export.json

# Parse JSON instead of SQLite
python parse_calibre_json.py calibre_export.json
```

#### 🛡️ Prevention
- Always close Calibre before running batch ingestion
- Use Calibre Content Server API instead of direct DB access
- Add database lock detection: retry with exponential backoff
- Store Calibre library on local disk (not network drive)
- Regular backups: `copy metadata.db metadata.db.$(date +%Y%m%d)`

---

### 8. File Permission Errors

#### 🔴 Symptoms
```
PermissionError: [Errno 13] Permission denied: 'book.epub'
OSError: [Errno 30] Read-only file system
FileNotFoundError: [Errno 2] No such file or directory
```

#### 🔍 Cause
1. File is read-only or locked by another process
2. Script running without sufficient permissions
3. File on network drive that's disconnected
4. Antivirus software blocking file access

#### ✅ Solution

**Step 1: Check file permissions**
```bash
# Windows: Right-click file → Properties → Security
# Linux: ls -la book.epub

# Remove read-only attribute (Windows)
attrib -r "path\to\book.epub"

# Change permissions (Linux)
chmod 644 book.epub
```

**Step 2: Check if file is locked**
```bash
# Windows: Use Process Explorer (Sysinternals)
# Find which process has file handle open

# Linux: lsof | grep book.epub
```

**Step 3: Run script as Administrator (Windows)**
```bash
# Right-click PowerShell → Run as Administrator
cd C:\Users\goran\source\repos\Temenos\Akademija\Alexandria\scripts
python batch_ingest.py --directory ../ingest --domain technical
```

**Step 4: Copy files to local drive**
```bash
# If files are on network drive, copy to local first
robocopy "\\network\share\books" "C:\ingest" /E

python batch_ingest.py --directory C:\ingest --domain technical
```

**Step 5: Check antivirus exclusions**
```bash
# Add Alexandria folder to Windows Defender exclusions:
# Settings → Virus & Threat Protection → Exclusions → Add Folder
# Add: C:\Users\goran\source\repos\Temenos\Akademija\Alexandria
```

#### 🛡️ Prevention
- Store book files on local drive with full permissions
- Add Alexandria folder to antivirus exclusions
- Close all programs that might lock files (Adobe Reader, Calibre)
- Use `--resume` flag to skip locked files and continue
- Log permission errors to `logs/permission_errors.txt`

---

### 9. Unsupported File Format Errors

#### 🔴 Symptoms
```
ValueError: Unsupported file format: .mobi
Exception: Cannot extract text from .azw3 file
KeyError: No extractor found for format: cbr
```

#### 🔍 Cause
Alexandria currently supports: `.epub`, `.pdf`, `.txt`, `.md`

Unsupported formats include:
- `.mobi`, `.azw`, `.azw3` (Kindle formats)
- `.cbr`, `.cbz` (Comic book archives)
- `.djvu` (DjVu documents)
- `.fb2` (FictionBook)

#### ✅ Solution

**Option A: Convert files to supported format**
```bash
# Install Calibre CLI tools
# Convert MOBI to EPUB
ebook-convert book.mobi book.epub

# Batch convert entire folder
for file in *.mobi; do
    ebook-convert "$file" "${file%.mobi}.epub"
done

# Then ingest converted files
python batch_ingest.py --directory ../ingest --domain technical --formats epub,pdf
```

**Option B: Add support for new format**
```python
# In ingest_books.py, add extractor function
def extract_text_from_mobi(file_path):
    # Use mobi library
    import mobi
    tempdir, filepath = mobi.extract(file_path)
    # ... extract text
    return text

# Register in EXTRACTORS dict
EXTRACTORS = {
    '.epub': extract_text_from_epub,
    '.pdf': extract_text_from_pdf,
    '.mobi': extract_text_from_mobi,  # New
    # ...
}
```

**Option C: Filter files by extension**
```bash
# Only ingest supported formats
python batch_ingest.py --directory ../ingest --domain technical --formats epub,pdf,txt,md
```

**Option D: Skip unsupported files automatically**
```python
# batch_ingest.py already logs unsupported formats
# Check logs/batch_ingest_progress.json for failed files
type batch_ingest_progress.json | findstr "failed"
```

#### 🛡️ Prevention
- Convert all books to EPUB/PDF before ingestion
- Use Calibre to manage library and auto-convert formats
- Add format detection: `python validate_formats.py --directory ../ingest`
- Document supported formats in README
- Add `--skip-unsupported` flag to batch_ingest.py

---

### 10. Batch Ingestion Resume Failures

#### 🔴 Symptoms
```
--resume flag skips wrong files
All files re-ingested despite using --resume
batch_ingest_progress.json shows incorrect status
Duplicate chunks in Qdrant
```

#### 🔍 Cause
1. `batch_ingest_progress.json` corrupted or deleted
2. File paths changed (files moved between runs)
3. Resume logic compares wrong file attributes
4. Collection was deleted but progress file still exists

#### ✅ Solution

**Step 1: Check progress file integrity**
```bash
# View progress file
type scripts\batch_ingest_progress.json

# Validate JSON syntax
python -m json.tool scripts\batch_ingest_progress.json
```

**Step 2: Verify file paths match**
```bash
# Progress file stores absolute paths - ensure files haven't moved
# If files moved, update progress file or delete and restart
```

**Step 3: Reset progress file**
```bash
# Delete progress file to start fresh
del scripts\batch_ingest_progress.json

# Re-run batch ingestion without --resume
python batch_ingest.py --directory ../ingest --domain technical
```

**Step 4: Check collection manifest**
```bash
# Verify what's actually in Qdrant
python collection_manifest.py show alexandria

# Compare with progress file
# If mismatch, rebuild manifest
python collection_manifest.py sync alexandria
```

**Step 5: Manual deduplication**
```bash
# If duplicates were created, delete collection and re-ingest
python qdrant_utils.py delete alexandria --confirm
python batch_ingest.py --directory ../ingest --domain technical
```

#### 🛡️ Prevention
- Always use `--resume` when re-running batch ingestion
- Don't move files while ingestion is in progress
- Backup `batch_ingest_progress.json` before manual edits
- Add file hash comparison in resume logic (not just path)
- Add `--force` flag to ignore progress and re-ingest all files
- Use collection manifest as source of truth: `collection_manifest.py show alexandria`

---

### 11. Chunk Size Configuration Issues

#### 🔴 Symptoms
```
Retrieval returns irrelevant results
Chunks are too small (< 500 characters)
Chunks are too large (> 5000 characters)
Context window exceeded in LLM
Poor semantic search quality
```

#### 🔍 Cause
1. Wrong chunk size for content type (code vs prose)
2. Overlap too small (context lost between chunks)
3. Chunk strategy doesn't match domain
4. Sentence splitting breaks code blocks

#### ✅ Solution

**Step 1: Understand current chunking**
```bash
# Experiment with different strategies
python experiment_chunking.py --file "../ingest/book.epub" --strategies small,medium,large

# View results in experiments/ folder
```

**Step 2: Adjust domain-specific chunk sizes**
```python
# In ingest_books.py, tune DOMAIN_CHUNK_SIZES
DOMAIN_CHUNK_SIZES = {
    'technical': {'min': 1500, 'max': 2000, 'overlap': 200},  # Code examples need larger chunks
    'psychology': {'min': 800, 'max': 1200, 'overlap': 150},  # Narrative text, smaller chunks
    'philosophy': {'min': 1000, 'max': 1500, 'overlap': 150},
    'history': {'min': 1000, 'max': 1500, 'overlap': 200},
}
```

**Step 3: Increase overlap for better context**
```python
# Increase overlap to reduce context loss
'technical': {'min': 1500, 'max': 2000, 'overlap': 300},  # 300 char overlap
```

**Step 4: Test retrieval quality**
```bash
# Query and examine returned chunks
python rag_query.py "your test question" --collection alexandria_test --limit 5

# Check chunk sizes
python qdrant_utils.py search alexandria_test "query" --limit 10 | grep -o "chunk_size: [0-9]*"
```

**Step 5: Re-ingest with new settings**
```bash
# Delete test collection
python qdrant_utils.py delete alexandria_test --confirm

# Re-ingest with new chunk sizes
python ingest_books.py --file "../ingest/book.epub" --domain technical --collection alexandria_test

# Verify improvement
python rag_query.py "same test question" --collection alexandria_test --limit 5
```

#### 🛡️ Prevention
- Start with conservative chunk sizes (1000-1500 chars)
- Test retrieval quality before ingesting entire library
- Document chunk size rationale in DOMAIN_CHUNK_SIZES comments
- Use `experiment_chunking.py` before production ingestion
- Track retrieval metrics: precision, recall, relevance scores
- Different collections for different chunk strategies (compare side-by-side)

---

### 12. Network and Firewall Issues

#### 🔴 Symptoms
```
requests.exceptions.ConnectionError: ('Connection aborted.', ConnectionResetError(10054, ...))
urllib3.exceptions.NewConnectionError: Failed to establish a new connection
Timeout connecting to 192.168.0.151:6333
```

#### 🔍 Cause
1. Firewall blocking Qdrant port (6333)
2. Network changed (VPN disconnected, Wi-Fi changed)
3. Qdrant server on different machine (192.168.x.x) unreachable
4. Router configuration blocking internal traffic

#### ✅ Solution

**Step 1: Check network connectivity**
```bash
# Ping Qdrant server
ping 192.168.0.151

# Test port connectivity (Windows)
Test-NetConnection -ComputerName 192.168.0.151 -Port 6333

# Test port connectivity (Linux)
nc -zv 192.168.0.151 6333
```

**Step 2: Check Windows Firewall**
```bash
# Allow port 6333 inbound (on Qdrant server machine)
New-NetFirewallRule -DisplayName "Qdrant" -Direction Inbound -Protocol TCP -LocalPort 6333 -Action Allow

# Or disable firewall temporarily for testing (NOT recommended)
Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled False
```

**Step 3: Check Docker network**
```bash
# Verify Qdrant container port mapping
docker ps | grep qdrant
# Should show: 0.0.0.0:6333->6333/tcp

# If not exposed, recreate container with port mapping
docker run -d -p 6333:6333 -v qdrant_storage:/qdrant/storage qdrant/qdrant
```

**Step 4: Use localhost if Qdrant is local**
```bash
# If Qdrant is on same machine, use localhost
python ingest_books.py --file book.epub --domain technical --host localhost --port 6333
```

**Step 5: Check VPN/network configuration**
```bash
# If on VPN, check split tunneling settings
# Try disconnecting VPN and using localhost
# Or add 192.168.x.x subnet to VPN split tunnel
```

**Step 6: Update Qdrant host in scripts**
```python
# In scripts that hardcode host, update to correct IP
# qdrant_utils.py, ingest_books.py, batch_ingest.py
DEFAULT_HOST = "192.168.0.151"  # Update to correct IP
```

#### 🛡️ Prevention
- Use Docker Compose with predictable networking
- Add connection retry logic with exponential backoff
- Document Qdrant server IP in README
- Use environment variable for host: `QDRANT_HOST=192.168.0.151`
- Add health check endpoint: `curl http://192.168.0.151:6333/healthz`
- Set up local Qdrant for development: `docker run -p 6333:6333 qdrant/qdrant`

---

## Common Error Patterns

### Pattern: "Works on first run, fails on second run"
**Likely Causes:**
- Duplicate ingestion (didn't use `--resume`)
- Port conflict (Qdrant restarted on different port)
- Disk space full (Qdrant storage full)

**Fix:**
```bash
# Check Qdrant storage size
docker exec qdrant du -sh /qdrant/storage

# Use --resume
python batch_ingest.py --directory ../ingest --domain technical --resume
```

---

### Pattern: "Works for small books, fails for large books"
**Likely Causes:**
- Memory exhaustion
- Timeout (large PDF processing takes > default timeout)
- Chunk count exceeds Qdrant batch size

**Fix:**
```bash
# Process large books individually
python ingest_books.py --file large_book.pdf --domain technical

# Increase timeout in code
qdrant_client.upsert(timeout=300)  # 5 minutes
```

---

### Pattern: "Some books ingest, some don't"
**Likely Causes:**
- Mixed file formats (unsupported formats)
- File encoding issues (some PDFs corrupted)
- Permission errors (some files locked)

**Fix:**
```bash
# Check failed files log
type batch_ingest_progress.json | findstr "failed"

# Re-try failed files individually
python ingest_books.py --file failed_book.epub --domain technical
```

---

## When to Seek Help

### ✅ Try Self-Service First
- Check this troubleshooting guide
- Review [Track Ingestion Guide](./track-ingestion.md) for logging
- Check [Common Workflows](./common-workflows.md) for commands
- Search error message in `scripts/README.md`
- Check GitHub Issues: https://github.com/your-repo/alexandria/issues

### 🆘 Get Help If:
- Error persists after trying all solutions
- System-specific issue (exotic OS, hardware)
- Security policy blocks required ports
- Data loss or corruption occurred

**How to Report:**
```bash
# Collect diagnostic info
python scripts/diagnose.py > diagnostic_report.txt

# Include:
# 1. Full error message and stack trace
# 2. Command that caused error
# 3. System info (OS, Python version)
# 4. diagnostic_report.txt
# 5. Steps already tried
```

---

## Related Documentation

### Essential Guides
- **[Track Ingestion](./track-ingestion.md)** - Collection manifest and batch progress tracking
- **[Common Workflows](./common-workflows.md)** - Quick reference for daily tasks
- **[Configure Open WebUI](./configure-open-webui.md)** - RAG integration setup

### Script Documentation
- **[scripts/README.md](../../scripts/README.md)** - Detailed script usage and basic troubleshooting

### External Resources
- **[Qdrant Documentation](https://qdrant.tech/documentation/)** - Vector database reference
- **[Sentence Transformers](https://www.sbert.net/)** - Embedding model docs
- **[PyMuPDF Documentation](https://pymupdf.readthedocs.io/)** - PDF processing reference

---

## Quick Reference Commands

```bash
# Diagnose connection issues
curl http://192.168.0.151:6333/collections

# Check what's ingested
python collection_manifest.py show alexandria

# View batch progress
type batch_ingest_progress.json

# Resume failed batch
python batch_ingest.py --directory ../ingest --domain technical --resume

# Test single file
python ingest_books.py --file book.epub --domain technical --collection test

# Verify chunking
python experiment_chunking.py --file book.epub --strategies medium

# Check Qdrant status
docker logs qdrant

# Test retrieval
python rag_query.py "test query" --collection alexandria_test --limit 5
```

---

## Summary

✅ **Quick Diagnosis** - Start with flowchart at top
✅ **12+ Error Categories** - Symptoms, cause, solution, prevention
✅ **Common Patterns** - Recognize recurring issues
✅ **Self-Service First** - Most issues solvable without external help
✅ **Comprehensive Solutions** - Step-by-step fixes with commands

**Key Takeaway:** Most ingestion errors are solvable with proper diagnosis and the solutions in this guide. Start with Quick Diagnosis, follow the relevant section, and prevent future occurrences!

---

**Last Updated:** 2026-01-28
