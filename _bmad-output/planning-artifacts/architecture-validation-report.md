## Architecture Validation Report — Savings Yield Optimiser

This report validates the project’s architecture against:
- PRD: `_bmad-output/planning-artifacts/prd-uk-savings-isa-rate-tracker.md`
- Project Brief: `_bmad-output/planning-artifacts/project-brief-uk-savings-isa-rate-tracker.md`
- Architecture: `_bmad-output/planning-artifacts/architecture.md`
- Implemented constraints and risks summarized in `docs/system-overview.md`

Date: 2026-05-08

---

## 1) Executive summary

**Overall status:** ✅ **Meets MVP requirements with documented deferrals**

The current architecture is coherent, implementable, and aligns strongly with the core goals:
- local-first, auditability, and honest comparability
- agentic freshness via refresh pipeline (scheduler + admin)
- stable API contracts used by the frontend

The main gaps are **explicitly deferred** (not architectural contradictions):
- daily “full refresh” / withdrawal detection policy (PRD FR10)
- richer “gotchas” capture and UI detail view (FR5/FR7)
- alerting (FR9)
- provider-source-of-truth reconciliation beyond capturing `provider_product_url` (FR10)

---

## 2) Requirements coverage (PRD / Brief → Architecture)

### 2.1 Core tables and filters

- **Ranked tables (FR1/FR2/FR3)**: ✅ Covered
  - Separate table categories are modeled via `product_offer.category` (+ term where applicable).
  - Ranking is driven by `aer_percent` with stable sorting rules.

- **Filters (FR4)**: ✅ Covered (MVP subset)
  - Deposit bounds and “restricted deals” toggle are supported.
  - Term selection exists for fixed categories, including the “All” sentinel.

**Note:** payout frequency filter is not implemented; architecture allows it since the schema includes `payout_frequency`.

### 2.2 Transparency, freshness, and provenance (FR8)

- **Last checked**: ✅ Covered
  - Mapped to `offer_snapshot.verified_at` and returned by APIs.
- **Source URL**: ✅ Covered
  - Stored in `source` and linked via `snapshot_source`; table query returns a representative `source_url`.

### 2.3 Automated data collection + refresh controls (FR10)

- **Firecrawl scraping**: ✅ Covered
  - Firecrawl client wrapper provides JSON extraction via schema + prompt.
- **6-hour cadence**: ✅ Covered (optional scheduler)
  - Scheduler can be enabled by env vars.
- **Admin on-demand refresh**: ✅ Covered
  - Token-protected admin endpoints trigger refresh and persist history.
- **Persisted job status**: ✅ Covered
  - `ingestion_job_run` persists runs and `/admin/refresh-history` exposes them.

**Important gap vs PRD FR10:** daily “full refresh” job for withdrawal detection is **not implemented** (documented as deferred).

### 2.4 “Gotchas” + detail view (FR5/FR7)

- **Schema capability**: ✅ Largely supported
  - `offer_snapshot` has fields for many of the “gotchas” categories.
- **UI/detail view**: ⚠️ Not implemented (deferred)
  - Architecture explicitly calls out richer gotchas UX and detail panels as post-MVP.

### 2.5 Alerts (FR9)

- ⚠️ Not implemented (deferred)
  - Architecture lists alerts as optional next steps; no blocking architectural conflict.

---

## 3) Non-functional requirements validation

### 3.1 Local-first constraint

- ✅ Architecture aligns: SQLite is the system of record; services run locally.

### 3.2 Auditability

- ✅ Architecture aligns: table rows map to stored fields and include provenance (`source_url`) and observation time (`verified_at`).

### 3.3 Operational safety

- ✅ Architecture aligns: refresh runs are isolated from the request path; errors are handled so one failed target/offer doesn’t crash the API.
- ⚠️ Improvement opportunity: add rate limiting/backoff strategy for Firecrawl calls (not currently specified as a concrete policy).

### 3.4 Performance

- ✅ Architecture aligns: “current snapshot pointer” design supports fast reads; schema includes relevant indexes for table reads.

### 3.5 Security (MVP local)

- ✅ Architecture aligns with stated constraint: admin endpoints are protected by shared secret header `X-Admin-Token`.
- ⚠️ Explicit limitation: `VITE_ADMIN_TOKEN` is build-time exposed (acceptable for local/dev, not for hosted multi-user).

---

## 4) Constraint & risk checks (from Brief + PRD)

### 4.1 Scrape drift risk

- ✅ Addressed: schema+prompt extraction, error isolation, and an explicit risk note in architecture/system overview.
- ⚠️ Recommended follow-up: fixture-based regression tests for extraction results per target URL.

### 4.2 Source-of-truth hierarchy (comparison vs provider)

- ⚠️ Partially addressed:
  - The system stores provenance and supports provider URLs (when present), but does not enforce “provider authoritative” reconciliation yet.
  - This is documented as deferred in architecture and system overview.

### 4.3 Withdrawal detection / “daily full refresh”

- ⚠️ Not implemented:
  - PRD FR10 expects a daily full refresh and marking withdrawn/removed items.
  - Architecture acknowledges withdrawal handling conceptually but does not define a concrete daily sweep implementation.

---

## 5) Architectural coherency & consistency rules

### 5.1 Contract coherency

✅ The architecture documents and the codebase align on:
- `{ items: [...] }` response wrapper for tables
- `snake_case` response fields
- `term_months=0` sentinel for “All terms”
- “Last checked” meaning `offer_snapshot.verified_at`

### 5.2 Boundary coherency

✅ The “thin routes, logic in services/repositories” boundary is consistent across modules.

---

## 6) Gaps / recommendations (prioritized)

### P0 (Next to implement if targeting PRD completeness)

- Add a **daily full refresh / withdrawal detection** workflow:
  - mark offers withdrawn/unknown when they disappear
  - ensure UI/table queries exclude withdrawn by default (already filter on `status='active'`)

### P1 (High-value stability)

- Add **fixture-based ingestion regression tests** for each RefreshTarget kind:
  - protect against schema/prompt drift and routing mistakes

### P2 (User trust / UX completeness)

- Implement row expand / detail surface for “gotchas” (FR5/FR7), using the already-present snapshot fields.

### P3 (Future scale)

- Replace shared-secret admin token with real auth if moving beyond local/dev usage.

