---
epic: 6
title: "Multi-Tenancy & Access Control"
status: pending
priority: P3
estimated_stories: 3
---

# Epic 6: Multi-Tenancy & Access Control

Prepare architecture for Phase 2+ multi-user support with access control for content licensing.

**User Outcome:** System supports multiple users with account groups, permissions, and copyrighted/public domain content separation.

**FRs Covered:** FR-004 (collection access control), NFR-006 (multi-tenancy)

**ADR References:** ADR-0011 (Phased Growth Architecture), ADR-0006 (Collection Isolation)

**Phased Rollout:**
- **Phase 1 (Current):** Single user, all content private
- **Phase 2 (Invite-Only):** 5-10 users, private collections only
- **Phase 3 (Public Registration):** FREE tier (public domain only) + PRO tier (private collections)
- **Phase 4 (Enterprise SaaS):** Team collections, SSO, ACLs

**Current State:**
- ❌ No user accounts or authentication
- ❌ No access control (everyone sees everything)
- ❌ No copyright-based visibility rules
- ❌ No user database

**Target State:**
- SQLite user database (Phase 2+)
- Collection visibility enforcement (public/private/shared)
- Copyright-based access control (FREE tier sees only public domain)
- Account groups and permissions (Phase 4)

---

## Stories

### Story 6.1: User Account Management (Phase 2)

**Status:** ⏳ PENDING (Phase 2+)

As a **system administrator**,
I want **user account management with roles**,
So that **multiple users can access Alexandria with appropriate permissions**.

**Acceptance Criteria:**

**Given** I create a new user account
**When** the account is created
**Then** user credentials are stored in SQLite database
**And** user has assigned tier (free, pro, admin)
**And** user is assigned default collection quota

**Technical Tasks:**

- [ ] Create SQLite user database: `data/users.db`
  ```sql
  CREATE TABLE users (
      user_id TEXT PRIMARY KEY,
      email TEXT UNIQUE NOT NULL,
      password_hash TEXT NOT NULL,
      tier TEXT DEFAULT 'free',  -- free, pro, admin
      created_at TIMESTAMP,
      last_login TIMESTAMP
  );

  CREATE TABLE api_keys (
      key_hash TEXT PRIMARY KEY,
      user_id TEXT REFERENCES users(user_id),
      created_at TIMESTAMP,
      last_used TIMESTAMP,
      revoked BOOLEAN DEFAULT 0
  );

  CREATE TABLE user_collections (
      user_id TEXT REFERENCES users(user_id),
      collection_name TEXT,
      role TEXT,  -- owner, read, write
      PRIMARY KEY (user_id, collection_name)
  );
  ```
- [ ] Create user management module: `scripts/user_management.py`
- [ ] Add password hashing (bcrypt)
- [ ] Add user creation, deletion, role assignment
- [ ] Integrate with API authentication (Epic 3)

**Files Modified:**
- `scripts/user_management.py` (new)
- `data/users.db` (new SQLite database)

**Definition of Done:**
- User database created
- User CRUD operations working
- Password hashing implemented
- API key linked to user_id

---

### Story 6.2: Collection Visibility & Copyright-Based Access Control (Phase 3)

**Status:** ⏳ PENDING (Phase 3+)

As a **FREE tier user**,
I want **access to public domain content only**,
So that **I can search Standard Ebooks without subscription**.

**Acceptance Criteria:**

**Given** I am a FREE tier user
**When** I query Alexandria
**Then** I see ONLY chunks with `copyright_status: "public_domain"`
**And** I do NOT see any copyrighted or private collections
**And** I see the public_alexandria collection (~600 Standard Ebooks)

**Given** I am a PRO tier user
**When** I query Alexandria
**Then** I see public domain content (read-only)
**And** I see my private collections (read-write)
**And** I do NOT see other users' private collections

**Technical Tasks:**

- [ ] Add visibility rules to Qdrant queries:
  ```python
  def build_access_filter(user_tier: str, user_id: str) -> Filter:
      if user_tier == "free":
          # FREE tier: public domain only
          return FieldCondition(
              key="copyright_status",
              match=MatchValue(value="public_domain")
          )
      elif user_tier == "pro":
          # PRO tier: public domain + own collections
          return Filter(
              should=[
                  FieldCondition(key="copyright_status", match=MatchValue(value="public_domain")),
                  FieldCondition(key="collection_owner", match=MatchValue(value=user_id))
              ]
          )
      # Admin: see everything
      return None
  ```
- [ ] Add collection ownership to metadata:
  - `collection_owner`: user_id
  - `visibility`: "public" | "private" | "shared"
- [ ] Enforce visibility in all query endpoints (MCP, HTTP API)
- [ ] Create public_alexandria collection (~600 Standard Ebooks)
- [ ] Add DMCA takedown process documentation (Phase 3 legal compliance)

**Files Modified:**
- `scripts/rag_query.py` (add access filters)
- `scripts/api_server.py` (enforce visibility)
- `scripts/mcp_server.py` (enforce visibility)

**Definition of Done:**
- FREE tier users see only public domain content
- PRO tier users see public domain + own collections
- Collection ownership enforced
- Visibility rules tested

---

### Story 6.3: Team Collections & SSO (Phase 4)

**Status:** ⏳ PENDING (Phase 4+)

As an **enterprise admin**,
I want **team collections with SSO integration**,
So that **my organization can share book collections with controlled access**.

**Acceptance Criteria:**

**Given** I configure SSO (SAML/OIDC)
**When** users log in via SSO
**Then** users are authenticated against external identity provider
**And** user roles are synced from SSO claims
**And** access to collections is controlled by ACLs

**Technical Tasks:**

- [ ] Add SSO integration (SAML, OIDC)
- [ ] Create team/organization model:
  ```sql
  CREATE TABLE organizations (
      org_id TEXT PRIMARY KEY,
      name TEXT,
      tier TEXT
  );

  CREATE TABLE org_members (
      org_id TEXT REFERENCES organizations(org_id),
      user_id TEXT REFERENCES users(user_id),
      role TEXT  -- admin, member, read-only
  );
  ```
- [ ] Add ACL support for collections:
  - Who can read
  - Who can write
  - Who can admin
- [ ] Integrate with audit logging (Epic 7)

**Files Modified:**
- `scripts/auth/sso.py` (new)
- `data/users.db` (extend schema)

**Definition of Done:**
- SSO working (SAML/OIDC)
- Team collections supported
- ACLs enforced
- Audit logging integrated

---

## Epic Summary

**Total Stories:** 3
**Status:** ⏳ PENDING (Phase 2-4 features)

**Phase 2 (Invite-Only):**
- Story 6.1: User Account Management

**Phase 3 (Public Registration):**
- Story 6.2: Copyright-Based Access Control

**Phase 4 (Enterprise SaaS):**
- Story 6.3: Team Collections & SSO

**Success Metrics:**
- User accounts created and authenticated (Phase 2+)
- Copyright-based access enforced (Phase 3+)
- Team collections working (Phase 4+)
