---
epic: 7
title: "Audit Logging & Monitoring"
status: pending
priority: P2
estimated_stories: 3
---

# Epic 7: Audit Logging & Monitoring

Implement comprehensive audit logging and observability stack for compliance, debugging, and operations.

**User Outcome:** System events are logged to SQLite for audit trails, and monitored via Grafana dashboards for health and performance oversight.

**FRs Covered:** NFR-003 (reliability), NFR-004 (maintainability via observability), NFR-005 (scalability monitoring)

**ADR References:** ADR-0011 (Phase 2+ requirements), project-context.md (logging patterns)

**Current State:**
- ✅ Application logging (logger.info/error/debug) exists
- ❌ No business audit logging (who did what, when)
- ❌ No SQLite audit database
- ❌ No monitoring dashboards (Grafana)
- ❌ No user activity tracking (privacy-sensitive)

**Target State:**
- SQLite audit.db for all business events
- System events always logged (errors, admin actions, ingestion)
- User activity opt-in with GDPR compliance (Personal Journaling Mode)
- Grafana monitoring stack (Prometheus, Alertmanager, Loki)
- Compliance reporting (audit exports, GDPR data access)

---

## Stories

### Story 7.1: SQLite Audit Logging (System Events)

**Status:** ⏳ PENDING

As a **system administrator**,
I want **all system events logged to SQLite**,
So that **I have audit trail for compliance and debugging**.

**Acceptance Criteria:**

**Given** a system event occurs (error, ingestion, admin action)
**When** the event is logged
**Then** it is stored in `data/audit.db` with:
  - Timestamp
  - Event type (error, ingestion, admin_action, access_control)
  - User ID (if applicable)
  - Details (JSON payload)
  - Severity (info, warning, error, critical)

**Given** I query audit logs
**When** I run `python scripts/audit_report.py --event-type ingestion --last 7d`
**Then** I see all ingestion events from last 7 days
**And** results are exportable to CSV/JSON

**Technical Tasks:**

- [ ] Create SQLite audit database: `data/audit.db`
  ```sql
  CREATE TABLE audit_log (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      event_type TEXT NOT NULL,  -- error, ingestion, admin_action, access_control, compliance
      user_id TEXT,  -- NULL for system events
      severity TEXT,  -- info, warning, error, critical
      details TEXT,  -- JSON payload
      ip_address TEXT,
      endpoint TEXT  -- API endpoint (if applicable)
  );

  CREATE INDEX idx_event_type ON audit_log(event_type);
  CREATE INDEX idx_timestamp ON audit_log(timestamp);
  CREATE INDEX idx_user_id ON audit_log(user_id);
  ```
- [ ] Create audit logging module: `scripts/audit.py`
  ```python
  import sqlite3
  import json
  from datetime import datetime

  class AuditLogger:
      def __init__(self, db_path="data/audit.db"):
          self.db_path = db_path
          self._ensure_schema()

      def log_event(
          self,
          event_type: str,
          details: dict,
          user_id: str = None,
          severity: str = "info",
          ip_address: str = None,
          endpoint: str = None
      ):
          conn = sqlite3.connect(self.db_path)
          cursor = conn.cursor()
          cursor.execute(
              """
              INSERT INTO audit_log (event_type, user_id, severity, details, ip_address, endpoint)
              VALUES (?, ?, ?, ?, ?, ?)
              """,
              (event_type, user_id, severity, json.dumps(details), ip_address, endpoint)
          )
          conn.commit()
          conn.close()

      def query_events(
          self,
          event_type: str = None,
          user_id: str = None,
          since: datetime = None
      ) -> list:
          # Query audit log with filters
          pass
  ```
- [ ] Integrate audit logging:
  - Ingestion events: book uploaded, chunks created, errors
  - Admin actions: user created, settings changed, collection deleted
  - Access control: permission denied, quota exceeded
  - Compliance: DMCA takedown, privacy request (Phase 3+)
- [ ] Create audit report script: `scripts/audit_report.py`

**Files Modified:**
- `scripts/audit.py` (new)
- `data/audit.db` (new SQLite database)
- `scripts/audit_report.py` (new)
- `scripts/ingest_books.py` (add audit logging)
- `scripts/api_server.py` (add audit logging)

**Definition of Done:**
- Audit database created
- System events logged automatically
- Query and export tools working
- All critical events captured

---

### Story 7.2: User Activity Logging with Privacy Controls (Opt-In)

**Status:** ⏳ PENDING

As a **user**,
I want **opt-in activity tracking for personal journaling**,
So that **I can track my learning journey while maintaining privacy control**.

**Acceptance Criteria:**

**Given** I enable Personal Journaling Mode
**When** I consent to activity tracking
**Then** my searches, books read, and timestamps are logged
**And** I can export my journal as JSON/CSV
**And** I can delete all my activity data anytime
**And** I can revoke consent with one click

**Given** I do NOT enable Personal Journaling Mode
**When** I use Alexandria
**Then** ZERO user activity is logged (only system events)
**And** my queries remain private

**Technical Tasks:**

- [ ] Extend audit.db schema for user activity:
  ```sql
  CREATE TABLE user_activity (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id TEXT NOT NULL,
      timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      activity_type TEXT,  -- search, read, bookmark, note
      query TEXT,  -- Search query (if activity_type=search)
      book_id TEXT,
      collection_name TEXT,
      consent_id TEXT  -- Links to consent record
  );

  CREATE TABLE user_consent (
      consent_id TEXT PRIMARY KEY,
      user_id TEXT NOT NULL,
      consent_type TEXT,  -- personal_diary, system_improvement
      granted_at TIMESTAMP,
      revoked_at TIMESTAMP,
      ip_address TEXT
  );
  ```
- [ ] Add consent UI in Settings:
  - Checkbox: "Track my activity for personal journal"
  - Clear explanation of what's logged
  - Easy revoke button
- [ ] Add user activity logging:
  ```python
  def log_user_activity(user_id, activity_type, details):
      # Check consent first
      if not has_consent(user_id, "personal_diary"):
          return  # Do not log

      audit_logger.log_user_activity(user_id, activity_type, details)
  ```
- [ ] Add data export: `scripts/export_user_journal.py`
  ```bash
  python scripts/export_user_journal.py --user sabo --format json > my_journal.json
  ```
- [ ] Add data deletion: `scripts/delete_user_data.py`
  ```bash
  python scripts/delete_user_data.py --user sabo --confirm
  ```
- [ ] GDPR compliance:
  - Article 6(1)(a): Consent
  - Article 6(1)(f): Legitimate Interest (personal journaling)
  - Right to access (export)
  - Right to erasure (delete)

**Files Modified:**
- `data/audit.db` (extend schema)
- `scripts/audit.py` (add user activity methods)
- `scripts/export_user_journal.py` (new)
- `scripts/delete_user_data.py` (new)
- `alexandria_app.py` (add consent UI)

**Definition of Done:**
- Opt-in consent mechanism working
- User activity logged ONLY with consent
- Export and delete tools functional
- GDPR compliance documented

---

### Story 7.3: Grafana Monitoring Stack

**Status:** ⏳ PENDING

As a **DevOps engineer**,
I want **Grafana dashboards for system health and performance**,
So that **I can monitor Alexandria in real-time and detect issues proactively**.

**Acceptance Criteria:**

**Given** Grafana is configured
**When** I open the Alexandria dashboard
**Then** I see metrics:
  - Query latency (p50, p95, p99)
  - Ingestion throughput (books/hour)
  - Error rates (per endpoint)
  - Active users (Phase 2+)
  - Qdrant collection size (chunks, storage MB)
  - API request rate (per minute)

**Given** a threshold is breached (e.g., query latency >500ms)
**When** Alertmanager detects the issue
**Then** an alert is sent (email, Slack, PagerDuty)
**And** the alert includes context (query details, timestamp, severity)

**Technical Tasks:**

- [ ] Set up Prometheus metrics exporter:
  ```python
  from prometheus_client import Counter, Histogram, Gauge, start_http_server

  # Metrics
  query_latency = Histogram('alexandria_query_latency_seconds', 'Query latency')
  query_count = Counter('alexandria_queries_total', 'Total queries')
  error_count = Counter('alexandria_errors_total', 'Total errors', ['endpoint'])
  collection_size = Gauge('alexandria_collection_chunks', 'Total chunks in collection')

  # Export metrics on :9090
  start_http_server(9090)
  ```
- [ ] Configure Prometheus scraping:
  ```yaml
  # prometheus.yml
  scrape_configs:
    - job_name: 'alexandria'
      static_configs:
        - targets: ['localhost:9090']
  ```
- [ ] Create Grafana dashboards:
  - System health dashboard (uptime, errors, latency)
  - Performance dashboard (query times, ingestion throughput)
  - Usage dashboard (queries per user, popular books)
- [ ] Configure Alertmanager:
  ```yaml
  # alerts.yml
  - alert: HighQueryLatency
    expr: histogram_quantile(0.95, alexandria_query_latency_seconds) > 0.5
    for: 5m
    annotations:
      summary: "High query latency detected"
  ```
- [ ] Add log aggregation (Loki or ELK):
  - Centralize logs from all components
  - Full-text search across logs
  - Correlation with metrics

**Files Modified:**
- `scripts/metrics.py` (new Prometheus exporter)
- `docker-compose.yml` (add Prometheus, Grafana, Alertmanager)
- `grafana/dashboards/` (new dashboard configs)
- `docs/deployment/monitoring.md` (new deployment guide)

**Definition of Done:**
- Prometheus collecting metrics
- Grafana dashboards functional
- Alertmanager configured
- Log aggregation working
- Documentation complete

---

## Epic Summary

**Total Stories:** 3
**Status:** ⏳ PENDING

**Completed Features:**
- ✅ Application logging (logger.info/error/debug)

**Pending Features:**
- ⏳ SQLite audit logging (system events)
- ⏳ User activity logging (opt-in, GDPR compliant)
- ⏳ Grafana monitoring stack

**Dependencies:**
- Epic 6 (user accounts for activity tracking)

**Success Metrics:**
- All system events logged to audit.db
- User activity opt-in rate >30% (if feature is valuable)
- 0% GDPR violations (proper consent, export, delete)
- Grafana dashboards operational
- Alerts working (no false positives)
