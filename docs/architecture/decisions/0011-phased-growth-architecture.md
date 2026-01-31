# ADR-0011: Phased Growth Architecture (Personal → SaaS Evolution)

## Status
**Accepted** (2026-01-31)

**Current Phase:** Phase 1 (Personal Tool)
**Target Phase:** TBD (decided when ready to evolve)

## Date
2026-01-31

## Context

Alexandria started as a personal RAG tool for searching a 9,000-book Calibre library. Over time, architectural discussions revealed multiple potential evolution paths:

1. **Personal tool only** - Works for one user (current)
2. **Invite-only beta** - Small circle of trusted users
3. **Public beta** - Open registration with legal compliance
4. **Full SaaS** - Commercial service with multi-tenancy, payments, support

**Problem:** Without a documented growth path, architectural decisions are made in isolation. Each phase has different requirements (legal, technical, operational), and jumping directly to "SaaS" introduces massive complexity.

**Key Insight:** Alexandria should be built with **phased evolution** in mind:
- Each phase is **self-contained** (can stop here)
- Each phase **adds value** (meaningful progress)
- Architecture **enables** next phase (but doesn't force it)
- Documentation **guides** future implementers (AI agents or human developers)

**Metaphor:** "Top of mountain might be in fog, but we can see the trail." 🏔️

## Decision

**Adopt a phased growth architecture where each phase is independently valuable and architecturally prepares for (but doesn't mandate) the next phase.**

### Phase Overview

| Phase | Name | Users | Legal | Payment | Effort | Status |
|-------|------|-------|-------|---------|--------|--------|
| **1** | Personal Tool | You only | Fair use | None | 2-3 weeks | ✅ Current |
| **2** | Invite Beta | 5-10 friends | Private use | None | +1 week | 🚧 Optional |
| **3** | Public Beta | Open registration | DMCA safe harbor | Optional | +2 weeks | 🔮 Future |
| **4** | Full SaaS | Unlimited | Full compliance | Required | +1 month | 🐋 Whale Model |

---

## Phase 1: Personal Tool (Showcase-Ready)

### Goal
Build a personal RAG service with **professional architecture** that can be **demoed to employers/clients/colleagues**.

### Users
- **Primary:** You (Sabo)
- **Demo:** Show to friends/colleagues (read-only demo, not accounts)

### Features

**Core Functionality:**
- ✅ MCP Server (stdio) - Claude Code integration
- ✅ HTTP API (REST) - Web/mobile client capability
- ✅ bge-large-en-v1.5 embeddings (GPU-accelerated)
- ✅ Semantic search with context modes (precise/contextual/comprehensive)
- ✅ Hierarchical chunking (parent/child)
- ✅ Multi-format support (EPUB, PDF, TXT, MD, HTML)
- ✅ Private collection (your 9,000 books)

**Architecture:**
- ✅ Multi-tenant ready (collection isolation, even with 1 user)
- ✅ API key authentication (basic security)
- ✅ Docker deployment (docker-compose.yml)
- ✅ Hardware-agnostic (GPU on Dell, CPU on Asus)
- ✅ Documentation (Swagger/OpenAPI, architecture diagrams)

**What's NOT Needed:**
- ❌ User registration system
- ❌ Payment processing
- ❌ Terms of Service / DMCA
- ❌ Public domain collection
- ❌ Admin dashboard (you're the only admin)
- ❌ Customer support

### Legal Status
- **Personal fair use** (grey area but generally accepted)
- No public sharing of copyrighted content
- Demo is "here's how it works" not "sign up and use it"
- **Risk:** Minimal

### Tech Stack

**Backend:**
- Python 3.14+
- FastAPI (HTTP API)
- FastMCP (MCP server)
- sentence-transformers (embeddings)
- PyTorch (GPU acceleration)
- Qdrant (vector DB)

**Deployment:**
- Docker + Docker Compose
- NAS hosting (192.168.0.151)
- Environment-based config (.env)

**Frontend (Optional):**
- Swagger UI (auto-generated from FastAPI)
- Can add simple htmx UI later if needed

### Exit Criteria (Good to Stop Here If)
- ✅ You're satisfied with personal use
- ✅ Demo wows employers/clients ("look what I built!")
- ✅ No one asks "can I use this too?"
- ✅ You learn what you wanted to learn

### Effort Estimate
**2-3 weeks:**
- Week 1: MCP + HTTP API + GPU embeddings
- Week 2: Docker deployment + documentation
- Week 3: Polish, testing, demo preparation

---

## Phase 2: Invite-Only Beta (Small Circle)

### Goal
Share Alexandria with **5-10 trusted people** (friends, colleagues, family) for feedback and validation.

### Users
- **You** (admin)
- **5-10 invites** (manual approval, no self-registration)

### Features (Added from Phase 1)

**User Management:**
- ✅ User accounts (username, email, API key)
- ✅ Manual invite system (you create accounts)
- ✅ Private collections per user (user uploads their books)
- ✅ Basic admin endpoints (create user, disable user, view usage)

**Security:**
- ✅ API key per user (authentication)
- ✅ Rate limiting (1,000 queries/day per user)
- ✅ Collection isolation (users can't see each other's books)

**What's Still NOT Needed:**
- ❌ Self-registration
- ❌ Payment processing
- ❌ DMCA (private, trusted circle)
- ❌ Public domain collection (users upload their own)
- ❌ OAuth2 (API keys sufficient)

### Legal Status
- **Private use among friends** (non-commercial)
- Users upload **their own books** (they have rights)
- Small circle (5-10 people, not public)
- **Risk:** Very low (private, non-commercial, trusted users)

### Tech Stack (Added)

**Database:**
- SQLite (users table, audit log)

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    email TEXT,
    api_key TEXT UNIQUE,
    role TEXT DEFAULT 'user',  -- 'admin' or 'user'
    max_queries_per_day INTEGER DEFAULT 1000,
    queries_today INTEGER DEFAULT 0,
    created_at TEXT,
    created_by_user_id INTEGER  -- Who invited them
);
```

**Admin Tools:**
- Simple CLI script (`python admin.py create-user john@example.com`)
- Optional: Basic web admin (htmx + TailwindCSS)

### Exit Criteria (Good to Stop Here If)
- ✅ Friends/colleagues love it (validation)
- ✅ You don't want to deal with strangers
- ✅ 10 users is enough (not trying to build a business)
- ✅ Feedback gathered, lessons learned

### Effort Estimate
**+1 week from Phase 1:**
- User accounts and SQLite schema (2 days)
- Admin CLI tools (1 day)
- Collection upload API (2 days)
- Testing with 5 beta users (ongoing)

---

## Phase 3: Public Beta (Open Registration)

### Goal
Launch **public beta** with open registration, legal compliance, and optional monetization (donations or subscriptions).

### Users
- **Anyone can register** (email + password)
- **Free tier** (limited queries, no uploads)
- **Pro tier** (optional, $9/month, user uploads)

### Features (Added from Phase 2)

**User Registration:**
- ✅ Email + password signup
- ✅ Email verification (confirm account)
- ✅ Password reset flow
- ✅ OAuth2 login (Google, GitHub) - optional

**Multi-Tenancy:**
- ✅ Free tier: Read-only access to public collection
- ✅ Pro tier: Upload books to private collection
- ✅ Quotas (queries/day, storage limits)
- ✅ Usage tracking and analytics

**Public Collection:**
- ✅ **Public domain books only** (no copyright issues)
- ✅ ~600 curated public domain books (Standard Ebooks)
- ✅ Read-only for all users
- ✅ Showcase value proposition

**Legal Compliance:**
- ✅ **Terms of Service** (users warrant they have rights to uploads)
- ✅ **Privacy Policy** (GDPR-lite, data handling)
- ✅ **DMCA Safe Harbor** (takedown process for user uploads)
- ✅ **Acceptable Use Policy** (no abuse, no piracy)

**Payment (Optional):**
- ✅ Stripe integration (if monetizing)
- ✅ Pro tier: $9/month (100 book uploads, LLM answers with BYOK)
- ✅ Free tier: Search public collection only

**What's Still NOT Needed:**
- ❌ Enterprise tier (teams, SSO, SLAs)
- ❌ Customer support team (self-service)
- ❌ Marketing site (simple landing page OK)

### Legal Status
- **DMCA Safe Harbor** (17 U.S.C. § 512)
- Users upload **their own content** (warrant they have rights)
- Public collection: **Public domain only** (no copyright issues)
- **DMCA takedown process** (respond to notices within 24h)
- **Risk:** Moderate (but legally viable, many precedents)

### Tech Stack (Added)

**Backend:**
- User registration endpoints (`/register`, `/login`, `/reset-password`)
- Email service (SendGrid or AWS SES)
- Payment integration (Stripe API)

**Database (Extended):**
```sql
CREATE TABLE users (
    -- ... existing fields ...
    tier TEXT DEFAULT 'free',  -- 'free', 'pro'
    stripe_customer_id TEXT,
    subscription_status TEXT,  -- 'active', 'canceled', 'past_due'
    subscription_end_date TEXT
);

CREATE TABLE dmca_notices (
    id INTEGER PRIMARY KEY,
    timestamp TEXT,
    complainant_email TEXT,
    infringing_content TEXT,  -- collection + book_id
    status TEXT,  -- 'received', 'processed', 'counter-notice'
    removed_at TEXT
);
```

**Legal Documents:**
- `docs/legal/terms-of-service.md`
- `docs/legal/privacy-policy.md`
- `docs/legal/dmca-policy.md`
- `docs/legal/acceptable-use.md`

**Public Domain Collection:**
- Download Standard Ebooks (~600 books, high quality)
- Ingest to `public_alexandria` collection
- Mark as read-only for all users

### Exit Criteria (Good to Stop Here If)
- ✅ You have 50-100 active users (traction!)
- ✅ Feedback is positive (people love it)
- ✅ You're happy with hobby project status
- ✅ Don't want full-time business commitments

### Effort Estimate
**+2 weeks from Phase 2:**
- Week 1: User registration, email verification, OAuth2
- Week 2: Public domain collection, DMCA process, legal docs
- Ongoing: Payment integration (if monetizing)

---

## Phase 4: Full SaaS (Whale Model 🐋)

### Goal
Build a **production SaaS** with enterprise features, support team, and scalable infrastructure.

### Users
- **Thousands of users** (open registration)
- **Enterprise customers** (teams, custom contracts)
- **Resellers/partners** (white-label, API access)

### Features (Added from Phase 3)

**Enterprise Tier:**
- ✅ Team accounts (5-50 users per org)
- ✅ SSO (SAML, OIDC)
- ✅ Custom embedding models (per tenant)
- ✅ Dedicated collections (data isolation)
- ✅ SLA guarantees (99.9% uptime)
- ✅ Priority support (Slack, phone)

**Advanced Features:**
- ✅ Admin dashboard (analytics, monitoring, user management)
- ✅ Query analytics (charts, trends, popular books)
- ✅ Webhooks (event notifications)
- ✅ Public API (documented, versioned, rate-limited)
- ✅ Mobile app (iOS/Android or PWA)

**Infrastructure:**
- ✅ Load balancer (multiple API instances)
- ✅ Database replication (high availability)
- ✅ Backup/disaster recovery
- ✅ Monitoring (Prometheus + Grafana)
- ✅ Logging (centralized, searchable)
- ✅ CDN (static assets, images)

**Operational:**
- ✅ Customer support team (email, chat, phone)
- ✅ Sales team (enterprise deals)
- ✅ Marketing site (SEO, content, blog)
- ✅ Legal team (contracts, compliance)
- ✅ DevOps team (on-call, scaling)

### Legal Status
- **Full legal compliance** (ToS, Privacy, DMCA, GDPR)
- **Business entity** (LLC or corporation)
- **Insurance** (liability, E&O)
- **Contracts** (enterprise SLAs, data processing agreements)
- **Risk:** Managed (but requires legal/business infrastructure)

### Tech Stack (Added)

**Scalability:**
- Kubernetes (container orchestration)
- PostgreSQL (replicated, not SQLite)
- Redis (caching, rate limiting)
- S3 (backup storage, large files)

**Monitoring:**
- Prometheus (metrics)
- Grafana (dashboards)
- Sentry (error tracking)
- ELK Stack (logs)

**Frontend:**
- React SPA (admin dashboard)
- React Native or PWA (mobile app)
- Marketing site (Next.js or similar)

### Revenue Model

**Free Tier:**
- Search public collection (public domain books)
- 100 queries/day
- No uploads
- **Goal:** Lead generation, showcase

**Pro Tier: $9/month**
- Everything in Free
- Upload 100 books (private collection)
- LLM answers (BYOK - user pays OpenRouter)
- 1,000 queries/day
- **Goal:** Indie researchers, students, hobbyists

**Enterprise: $99-$999/month**
- Everything in Pro
- Unlimited uploads
- LLM answers included
- Team accounts (5-50 users)
- SSO, custom integrations
- Priority support
- **Goal:** Companies, universities, research labs

### Exit Criteria (Never Stop, It's a Business)
- 💼 Full-time job (you or co-founder)
- 💰 Revenue covers costs + salary
- 📈 Growing user base (MoM growth)
- 🏆 Market leader (recognized brand)

### Effort Estimate
**+1 month from Phase 3, then ongoing:**
- Month 1: Infrastructure (Kubernetes, PostgreSQL, monitoring)
- Month 2: Admin dashboard + analytics
- Month 3: Enterprise features (SSO, teams)
- Month 4+: Marketing, sales, support (ongoing)

---

## Architecture Decisions by Phase

### Cross-Phase Architectural Principles

**Always True (All Phases):**
1. ✅ Collection isolation (ADR-0006)
2. ✅ MCP-first architecture (ADR-0003)
3. ✅ Business logic in scripts/ (ADR-0003)
4. ✅ Multi-consumer ready (ADR-0008)
5. ✅ GPU-accelerated embeddings (ADR-0010)

### Phase-Specific Decisions

| Decision | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
|----------|---------|---------|---------|---------|
| **User Accounts** | ❌ | ✅ Manual | ✅ Self-reg | ✅ + SSO |
| **Collections** | 1 private | N private | Public + N private | Public + N private |
| **Authentication** | API key (admin) | API keys | API keys + OAuth2 | + SSO/SAML |
| **Payment** | ❌ | ❌ | ✅ Optional | ✅ Required |
| **Legal Docs** | ❌ | ❌ | ✅ ToS/DMCA | ✅ + Contracts |
| **Database** | SQLite | SQLite | SQLite or Postgres | Postgres (replicated) |
| **Deployment** | Docker Compose | Docker Compose | Docker Compose | Kubernetes |
| **Monitoring** | Logs only | Logs only | Basic metrics | Full stack |
| **Support** | N/A | You (informal) | You (email) | Team (24/7) |

---

## Migration Path Between Phases

### Phase 1 → Phase 2
**Effort:** 1 week

**Steps:**
1. Add SQLite users table
2. Create admin CLI for user management
3. Extend HTTP API with `/upload` endpoint
4. Implement per-user collections
5. Test with 2-3 beta users
6. Invite 5-10 friends

**No Breaking Changes:**
- Your existing collection stays intact
- MCP server unchanged
- HTTP API extended (backward compatible)

---

### Phase 2 → Phase 3
**Effort:** 2 weeks

**Steps:**
1. Add user registration endpoints (`/register`, `/login`)
2. Implement email verification (SendGrid/SES)
3. Create public domain collection (600 books from Standard Ebooks)
4. Write legal docs (ToS, Privacy, DMCA)
5. Implement DMCA takedown endpoint
6. (Optional) Add Stripe integration
7. Launch landing page

**Breaking Changes:**
- Need real email service (not localhost)
- Must serve HTTPS (SSL certificate)
- Legal docs become mandatory

---

### Phase 3 → Phase 4
**Effort:** 1 month+

**Steps:**
1. Migrate to PostgreSQL (data export from SQLite)
2. Deploy Kubernetes cluster
3. Set up monitoring (Prometheus, Grafana)
4. Build admin dashboard (React)
5. Implement enterprise features (SSO, teams)
6. Hire support team
7. Marketing and sales efforts

**Breaking Changes:**
- Infrastructure redesign (Docker Compose → Kubernetes)
- Database migration (SQLite → PostgreSQL)
- Operational complexity (DevOps, on-call)

---

## Risk Assessment by Phase

| Phase | Technical Risk | Legal Risk | Financial Risk | Time Risk |
|-------|----------------|------------|----------------|-----------|
| **1** | ⭐ Low | ⭐ Low | ⭐ Low ($0) | ⭐ Low (2-3 weeks) |
| **2** | ⭐ Low | ⭐ Low | ⭐ Low ($0) | ⭐⭐ Low-Med (+1 week) |
| **3** | ⭐⭐ Medium | ⭐⭐ Medium | ⭐⭐ Medium ($200/mo) | ⭐⭐⭐ Medium (+2 weeks) |
| **4** | ⭐⭐⭐ High | ⭐⭐⭐ High | ⭐⭐⭐⭐ High ($2K+/mo) | ⭐⭐⭐⭐ High (+months) |

---

## Consequences

### Positive

- ✅ **Incremental value:** Each phase delivers working system
- ✅ **Flexibility:** Can stop at any phase (no forced progression)
- ✅ **Risk mitigation:** Small steps reduce technical/legal/financial risk
- ✅ **Learning:** Validate assumptions before heavy investment
- ✅ **Documentation:** Future implementers know the roadmap
- ✅ **Architecture:** Designed for growth without over-engineering
- ✅ **Demo story:** "Here's the plan, here's where we are, here's what's possible"

### Negative

- ⚠️ **Planning overhead:** More documentation upfront
- ⚠️ **Delayed features:** Full SaaS features not immediate
- ⚠️ **Migration cost:** Each phase transition has effort

### Neutral

- 🔄 **Current commitment:** Phase 1 only (2-3 weeks)
- 🔄 **Future optionality:** Phases 2-4 are options, not obligations
- 🔄 **Architecture tax:** Multi-tenant ready costs ~10% extra (worth it)

---

## Implementation

### Current Phase: Phase 1 (Personal Tool)

**Active Development:**
- ADR-0010 (GPU embeddings) - In progress
- ADR-0009 (HTTP API) - Proposed
- MCP server - Already working
- Docker deployment - To do

**Immediate Next Steps:**
1. Migrate to bge-large-en-v1.5 (GPU)
2. Build HTTP API (FastAPI)
3. Create docker-compose.yml
4. Write API documentation (Swagger)
5. Polish for demo

**Phase 1 Complete When:**
- ✅ Can demo to employers/clients
- ✅ Docker one-command deployment
- ✅ Documentation complete
- ✅ You're happy with quality

---

## Alternatives Considered

### Alternative 1: Build Full SaaS Immediately
**Rejected because:**
- Massive complexity (legal, payment, ops)
- High risk (might not need it)
- Long time to value (months before usable)
- Over-engineering (building for hypothetical users)

### Alternative 2: No Phasing (Ad-Hoc Growth)
**Rejected because:**
- Architectural debt accumulates
- Each feature decision lacks context
- Migration becomes painful retrofit
- No clear stopping points

### Alternative 3: Microservices from Day 1
**Rejected because:**
- Overkill for personal tool
- Operational complexity
- Slower development
- Can add later if Phase 4 happens

---

## Related Decisions

- **ADR-0003: GUI as Thin Layer** - MCP-first supports all phases
- **ADR-0006: Collection Isolation** - Enables multi-tenancy (Phase 2+)
- **ADR-0008: Multi-Consumer Service** - Service model fits phased growth
- **ADR-0009: HTTP API Wrapper** - Needed for Phase 2+ (web clients)
- **ADR-0010: GPU Embeddings** - Quality foundation for all phases

---

## References

- **SaaS Growth Models:** "The Lean Startup" (Eric Ries)
- **DMCA Safe Harbor:** 17 U.S.C. § 512
- **Phased Delivery:** "Building Microservices" (Sam Newman)
- **Examples:** YouTube (started simple), Dropbox (MVP first), GitHub (free → paid)

---

**Author:** Winston (Architect Agent) + Sabo
**Reviewers:** Sabo (Project Owner)
**Metaphor:** "Top of mountain might be in fog, but we can see the trail 🏔️"

---

## Quick Reference: Which Phase Am I In?

**Ask yourself:**

- **Only me using it?** → Phase 1
- **5-10 friends?** → Phase 2
- **Open to public?** → Phase 3
- **Hiring a team?** → Phase 4

**Decision flowchart:**

```
Start
  ↓
Is anyone asking "can I use this?"
  ├─ No → Stay in Phase 1 ✅
  └─ Yes → Are they trusted friends?
         ├─ Yes → Phase 2 (invite-only)
         └─ No → Do you want public users?
                ├─ No → Politely decline
                └─ Yes → Phase 3 (public beta)
                        ↓
                  Growing beyond hobby?
                     ├─ No → Stay Phase 3 ✅
                     └─ Yes → Phase 4 (whale model 🐋)
```
