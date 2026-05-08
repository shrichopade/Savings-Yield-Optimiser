## Solution Design — Savings Yield Optimiser

This document describes the implemented solution (MVP + Epic 2) for a local-first UK Savings + Cash ISA rate tracker, including ingestion (Firecrawl), SQLite persistence, FastAPI APIs, and a React dashboard.

---

## 1) Goals and non-goals

### 1.1 Goals
- **Local-first**: everything runs locally; data stored in SQLite.
- **Trust & auditability**: every displayed row has **source URL(s)** and **Last checked** timestamps.
- **Honest comparisons**: only rank within comparable sets (category + term where applicable).
- **Agentic freshness**:
  - automated refresh (target cadence: **6 hours**)
  - admin-triggered on-demand refresh

### 1.2 Non-goals (MVP)
- Financial advice, account opening flows, Stocks & Shares/Lifetime ISAs.
- Full authentication/role system (admin is a shared-secret token for local use).

---

## 2) High-level architecture

### 2.1 Components
- **Frontend (React + TypeScript / Vite)**:
  - tables for Fixed Savings and Cash ISAs
  - filters (deposit, eligibility, term selection with “All”)
  - admin “Refresh Live Rates” button (optional; token-gated)
- **Backend (FastAPI)**:
  - read-only table endpoints
  - admin refresh endpoints (manual refresh + job status)
  - optional background refresh scheduler (APScheduler)
- **Ingestion pipeline**:
  - Firecrawl JSON extraction from target pages
  - normalization into `ScrapedRate` items
  - idempotent **upsert** into SQLite (stable offers + immutable snapshots)
- **SQLite database**:
  - stable entities: provider/product/offer
  - immutable observations: offer snapshots
  - traceability: snapshot ↔ sources
  - job history: refresh runs persisted for visibility across restarts

### 2.2 Data flow (end-to-end)
1. A refresh run (scheduler or admin) selects a set of target URLs.
2. Firecrawl extracts a list of “offers” for each URL into structured JSON.
3. Each extracted offer is normalized and routed to a category/term/subtype.
4. The ingestion service upserts:
   - provider
   - product
   - product_offer (stable identity)
   - offer_snapshot (immutable point-in-time facts; includes `verified_at`)
   - source + snapshot_source (traceability)
5. Table endpoints read current snapshots and return ranked rows to the UI.

---

## 3) Data model (SQLite)

### 3.1 Core tables
- **`provider`**: provider identity (e.g., Santander).
- **`product`**: marketing-level product under a provider.
- **`product_offer`**: a stable offer variant within a comparable set.
  - key fields: `category`, `term_months`, `isa_subtype`
  - pointer: `current_snapshot_id`
- **`offer_snapshot`**: immutable observation for an offer at a `verified_at` time.
- **`source`** and **`snapshot_source`**: source URL(s) for traceability.

### 3.2 Job history
- **`ingestion_job_run`**: persisted refresh run history.
  - `job_run_id` (text id), `job_type` (`scheduler`/`admin`), `status`
  - `started_at`, `finished_at`, `error`

### 3.3 “Last checked” mapping
- The UI’s “Last checked” should come from **`offer_snapshot.verified_at`** for the offer’s current snapshot.

---

## 4) Backend APIs

### 4.1 Table endpoints (public)
These return table rows from the current snapshot set.

- **`GET /fixed-savings`**
  - `term_months=0` means “All terms”
- **`GET /cash-isa/easy-access`**
- **`GET /cash-isa/fixed`**
  - `term_months=0` means “All terms”

### 4.2 Admin endpoints (token protected)
All `/admin/*` endpoints require header:
- `X-Admin-Token: <ADMIN_TOKEN>`

- **`POST /admin/refresh?wait=true|false`**
  - triggers a refresh run (same pipeline as scheduler)
  - returns `{job_id, status, message}`
- **`GET /admin/refresh/{job_id}`**
  - in-memory job state (for current process)
- **`GET /admin/refresh-history?limit=25`**
  - returns persisted job history from SQLite (survives restarts)

---

## 5) Refresh orchestration

### 5.1 Scheduler refresh (6-hour cadence)
- Implemented using **APScheduler** inside the FastAPI process on startup (configurable).
- Controlled by environment variables:
  - `REFRESH_SCHEDULER_ENABLED=1|0`
  - `REFRESH_INTERVAL_HOURS=6`

### 5.2 Manual refresh (admin)
- Exposed via `POST /admin/refresh`
- Executes the same `run_refresh_once()` orchestration.
- Records job status to SQLite (`ingestion_job_run`) so refresh visibility survives restarts.

### 5.3 Failure behavior
- Per-target and per-offer errors are logged and do not crash the API process.
- The refresh run record is marked `failed` with an error message if an unhandled exception escapes.

---

## 6) Scraping and ingestion design

### 6.1 Firecrawl extraction
- Firecrawl is used to extract a small list of offers from a target URL into JSON.
- Each offer attempts to capture:
  - `bank_name`
  - `product_name`
  - `interest_rate` (string as displayed)
  - `aer_percent` (numeric if possible)
  - `provider_product_url` (best-effort)

### 6.2 Routing and normalization
- Each scraped offer is routed into:
  - `category` (e.g., `fixed_savings`, `cash_isa_easy_access`, `cash_isa_fixed`)
  - `term_months` (inferred when needed)
  - `isa_subtype` (e.g., `easy_access`, `fixed`)
- Example: Santander’s “savings-and-isas” page mixes products, so routing is based on `product_name` keywords and term inference from URL text.

### 6.3 Upsert strategy
- Identity is stable at the **offer** level (provider/product + category + term + subtype).
- Snapshots are append-only and represent what we observed at a time.
- The current snapshot pointer is updated after insertion so table reads are simple.

---

## 7) Frontend integration

### 7.1 Data fetching
- The UI fetches data from backend table endpoints.
- “All” term selection maps to `term_months=0` on the API.

### 7.2 Admin refresh button
- The UI calls the admin refresh endpoint and then refetches tables on success.
- Frontend configuration:
  - `VITE_ADMIN_TOKEN` must match backend `ADMIN_TOKEN`.

---

## 8) Operational configuration

### 8.1 Environment variables (repo root `.env`)
- `FIRECRAWL_API_KEY`: required for live scraping.
- `ADMIN_TOKEN`: required for admin endpoints.
- `REFRESH_SCHEDULER_ENABLED`: enable/disable periodic refresh.
- `REFRESH_INTERVAL_HOURS`: cadence (default 6).
- `REFRESH_TARGETS_JSON` (optional): override default refresh targets.

### 8.2 Local data location
- SQLite database path is configured in backend settings; default is `data/app.db`.

---

## 9) Testing strategy (current)

### 9.1 Unit tests
- `pytest` tests cover:
  - term inference from product names/URLs
  - routing logic for mixed-category pages (e.g., Santander)

### 9.2 Future testing (recommended)
- Add sanitized fixtures per source URL (captured “offers” JSON) and validate ingestion deterministically in CI.
- Add an integration test that triggers refresh against fixtures and validates resulting SQLite rows.

---

## 10) Known limitations and next refinements

- **Admin auth** is a shared token (fine for local dev; not for multi-user production).
- **Provider source-of-truth**: currently best-effort; next phase can follow `provider_product_url` and scrape provider pages for authoritative terms.
- **Offer identity**: current model is stable but can be made more deterministic with an explicit offer-key strategy for edge cases.

