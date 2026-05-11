## Integration Architecture — Savings Yield Optimiser

This document describes the **integration points** between components and external systems for the current implementation, including interfaces, contracts, auth, and failure behavior.

---

## 1) Integration inventory (what talks to what)

### 1.1 Internal integrations

- **React UI → FastAPI backend**
  - Purpose: fetch ranked tables; trigger admin refresh; view refresh history.
  - Protocol: HTTP (JSON).

- **FastAPI backend → SQLite**
  - Purpose: read “current snapshot” rows for tables; upsert offers/snapshots/sources; persist refresh job runs.
  - Protocol: local file DB access (SQLite).

- **Scheduler (APScheduler) → refresh orchestration**
  - Purpose: run refresh every `REFRESH_INTERVAL_HOURS` (default 6) when enabled.
  - Protocol: in-process function invocation.

### 1.2 External integrations

- **FastAPI backend → Firecrawl API**
  - Purpose: scrape target pages and extract structured JSON.
  - Protocol: HTTPS POST to Firecrawl `/v1/scrape`.
  - Auth: `Authorization: Bearer <FIRECRAWL_API_KEY>`.

- **Firecrawl API → UK financial websites**
  - Purpose: fetch target pages (comparison/editorial sites and provider pages).
  - Notes: upstream HTML/content can change; extraction is best-effort.

---

## 2) UI ↔ API integration (HTTP contracts)

### 2.1 Public table endpoints (read-only)

Used by normal users.

- `GET /tables/fixed-savings`
- `GET /tables/cash-isa/easy-access`
- `GET /tables/cash-isa/fixed`

**Stable conventions**
- Response wrapper is always: `{ "items": [...] }`
- Field names are `snake_case`.
- `term_months=0` is a **sentinel** meaning “All terms” (backend maps it to `None` internally).

### 2.2 Admin endpoints (token protected)

Used by maintainer/admin tooling (and optionally the UI refresh button).

Required header:
- `X-Admin-Token: <ADMIN_TOKEN>`

Endpoints:
- `POST /admin/refresh?wait=true|false`
  - `wait=true`: synchronous (request returns only after refresh finishes)
  - `wait=false`: async (returns a `job_id` immediately; refresh runs in a daemon thread)
- `GET /admin/refresh-history?limit=N`
  - persisted job history from SQLite (survives restarts)
- `GET /admin/refresh/{job_id}`
  - in-memory status (only for jobs created in the current server process)

**UI enablement**
- The frontend refresh button is gated by a configured `VITE_ADMIN_TOKEN` (expected to equal backend `ADMIN_TOKEN`).

---

## 3) Backend ↔ SQLite integration (persistence contracts)

### 3.1 “Current snapshot” read model (tables)

The backend table endpoints read from the **current snapshot** pointer model:
- Stable offer identity lives in `product_offer`
- The row values shown in tables come from the offer’s `current_snapshot_id → offer_snapshot`

Key traceability mapping:
- “Last checked” == `offer_snapshot.verified_at` (current snapshot)
- “Source URL” is derived from `snapshot_source → source.url`

### 3.2 Refresh job persistence

Refresh jobs are persisted in `ingestion_job_run` so status survives restarts:
- Job types: `scheduler` and `admin`
- Status values: `running`, `succeeded`, `failed`
- Timestamps: stored as UTC ISO strings with `Z` suffix

---

## 4) Backend ↔ Firecrawl integration

### 4.1 Transport and authentication

- Endpoint: Firecrawl `POST {base_url}/scrape` (default base: `https://api.firecrawl.dev/v1`)
- Headers:
  - `Authorization: Bearer <FIRECRAWL_API_KEY>`
  - `Content-Type: application/json`
- Timeout: 60 seconds (current client default)

### 4.2 Extraction contract (schema + prompt)

The backend supplies:
- A JSON Schema (e.g., `build_rates_list_schema(limit=N)`)
- An optional prompt to steer extraction

Expected shape (top-level):
- `{ "offers": [ ... ] }`

Offer item shape (minimum):
- `bank_name` (required)
- `interest_rate` (required)

Optional fields:
- `product_name`, `aer_percent`, `provider_product_url`

### 4.3 Failure behavior

- Firecrawl HTTP \(≥ 400\) or `success=false` raises `FirecrawlError`.
- Refresh orchestration is designed to continue best-effort across targets/offers where possible.
- Admin refresh persists `failed` status and stores an error string for later inspection.

---

## 5) Refresh pipeline integrations

### 5.1 Triggers

- **Scheduler trigger** (optional):
  - APScheduler runs `run_refresh_once(settings)` on an interval.
- **Admin trigger**:
  - `POST /admin/refresh` runs the same orchestration (sync or async).

### 5.2 Data flow (integration-centric)

1. Select refresh targets (defaults or `REFRESH_TARGETS_JSON` override).
2. For each target, call Firecrawl scrape/extract.
3. Normalize each extracted offer into internal `ScrapedRate`.
4. Route into a comparable bucket: `(category, term_months, isa_subtype)`.
5. Upsert into SQLite:
   - stable entities (provider/product/offer)
   - immutable observation (snapshot) with `verified_at`
   - provenance linkage (source URL)
6. Update job run record status (`succeeded`/`failed`).

---

## 6) Configuration points (integration-relevant)

Repo root `.env` (backend reads settings from environment):
- `FIRECRAWL_API_KEY` (required for live scraping)
- `ADMIN_TOKEN` (required for `/admin/*`)
- `REFRESH_SCHEDULER_ENABLED=0|1`
- `REFRESH_INTERVAL_HOURS` (default `6`)
- `REFRESH_TARGETS_JSON` (optional override targets list)

Frontend:
- `VITE_ADMIN_TOKEN` (optional; enables refresh button)

---

## 7) Operational considerations

- **Secrets hygiene**: keys/tokens must remain local; do not commit `.env`.
- **Idempotency**: ingestion is “upsert-first” to avoid duplicate stable offers.
- **Scrape drift**: upstream page changes are expected; keep extraction schemas/prompts centralized and add fixture-based tests as follow-up.

