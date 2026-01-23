# Structurizr Lite - Interactive Architecture Diagrams

Alexandria uses **Structurizr Lite** to visualize C4 architecture diagrams interactively.

---

## Quick Start

### Start Structurizr Lite
```bash
scripts/start-structurizr.bat
```

**Opens:** http://localhost:8081

**What it does:**
- Creates/starts Docker container: `alexandria-structurizr`
- Mounts `docs/architecture/` folder to container
- Exposes on port 8081 (port 8080 used by WBF2)
- Runs in background (daemon mode)

### Stop Structurizr Lite
```bash
scripts/stop-structurizr.bat
```

---

## Docker Image Info

**Image:** `structurizr/lite:latest`
**Size:** ~100MB
**License:** MIT
**Documentation:** https://github.com/structurizr/lite

---

## Container Management

### Check Status
```bash
docker ps | grep alexandria-structurizr
```

**Expected output:**
```
alexandria-structurizr   Up X minutes (healthy)   0.0.0.0:8081->8080/tcp
```

### View Logs
```bash
docker logs alexandria-structurizr
```

### Restart Container
```bash
docker restart alexandria-structurizr
```

### Remove Container (full cleanup)
```bash
docker stop alexandria-structurizr
docker rm alexandria-structurizr
```

Next run of `start-structurizr.bat` will create fresh container.

---

## Workspace File

**Location:** `docs/architecture/workspace.dsl`

**Format:** Structurizr DSL (Domain-Specific Language)

**Hot Reload:** Changes to `workspace.dsl` are automatically detected by Structurizr Lite (refresh browser to see updates).

---

## Available Views

Once Structurizr Lite is running, you can view:

### 1. System Context (Level 1)
- Shows Alexandria in broader ecosystem
- External systems: Qdrant, OpenRouter
- Users: Developer/Researcher

### 2. Containers (Level 2)
- Shows major components:
  - Streamlit GUI
  - Scripts Package
  - File System
  - Calibre Database

### 3. Components (Level 3)
- Shows internal Scripts Package structure:
  - Ingestion Engine
  - Chunking Strategies
  - RAG Query Engine
  - Collection Management
  - Calibre Integration

### 4. Dynamic Views
- **Book Ingestion Flow** - Step-by-step ingestion process
- **RAG Query Flow** - Query execution flow

---

## Troubleshooting

### Container Won't Start
**Check if port 8081 is available:**
```bash
netstat -ano | findstr :8081
```

**If port is in use, change port in `start-structurizr.bat`:**
```batch
docker run -d ... -p 8082:8080 ...
```

### Workspace Not Loading
**Check logs:**
```bash
docker logs alexandria-structurizr | grep -i error
```

**Verify DSL syntax:**
```bash
# Validate workspace.dsl locally
docker run --rm -v "%cd%\docs\architecture:/usr/local/structurizr" structurizr/cli validate
```

### Container Exists But Won't Start
**Remove and recreate:**
```bash
docker rm -f alexandria-structurizr
scripts/start-structurizr.bat
```

### Changes Not Visible
1. Save `workspace.dsl`
2. Wait 5 seconds (auto-reload)
3. Refresh browser (F5)

If still not visible, restart container:
```bash
docker restart alexandria-structurizr
```

---

## Multiple Structurizr Instances

Alexandria uses **port 8081** to avoid conflict with WBF2 on port 8080.

**If you need both running:**
- WBF2 Structurizr: http://localhost:8080
- Alexandria Structurizr: http://localhost:8081

**Container names:**
- WBF2: (check in WBF2 project)
- Alexandria: `alexandria-structurizr`

---

## Exporting Diagrams

### Export PNG/SVG (Using Structurizr CLI)

```bash
# Pull CLI image (if not already pulled)
docker pull structurizr/cli

# Export all diagrams as PNG
docker run --rm -v "%cd%\docs\architecture:/usr/local/structurizr" ^
  structurizr/cli export -workspace workspace.dsl -format png -output diagrams

# Export as SVG
docker run --rm -v "%cd%\docs\architecture:/usr/local/structurizr" ^
  structurizr/cli export -workspace workspace.dsl -format svg -output diagrams
```

**Output:** `docs/architecture/diagrams/*.png` (or `*.svg`)

### Export from Browser
1. Open view in Structurizr Lite
2. Click "Export" button
3. Choose PNG or SVG
4. Save to `docs/architecture/diagrams/`

---

## DSL Syntax Reference

**Official Documentation:**
https://github.com/structurizr/dsl/blob/master/docs/language-reference.md

**Key Elements:**

```dsl
workspace "Name" "Description" {
    model {
        user = person "Name" "Description"
        system = softwareSystem "Name" "Description" {
            container = container "Name" "Description" "Technology"
        }
        user -> system "Interaction"
    }

    views {
        systemContext system "ViewKey" {
            include *
            autolayout
        }
    }

    styles {
        element "Person" {
            background #08427b
            color #ffffff
        }
    }
}
```

---

## Related Documentation

- **[Architecture Overview](README.md)** - Main architecture documentation
- **[C4 Model Docs](c4/)** - Detailed explanations of each diagram level
- **[workspace.dsl](workspace.dsl)** - Source file for diagrams

---

**Last Updated:** 2026-01-23
