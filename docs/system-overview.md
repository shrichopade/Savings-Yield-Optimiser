## Savings Yield Optimiser — System Overview

Audience: **engineers** building/operating the system and **stakeholders** evaluating scope, risks, and roadmap.

---

## 1) Executive summary

Savings Yield Optimiser is a **local-first** UK savings + Cash ISA rate tracker.

It provides:
- A React dashboard for viewing **ranked tables** of offers (fixed savings and cash ISAs)
- A FastAPI backend that serves these tables from **SQLite**
- A refresh pipeline that scrapes target pages using **Firecrawl** and upserts observations into SQLite
- A 6-hour refresh cadence (optional scheduler) plus an **admin on-demand refresh** capability

The design prioritizes **auditability**: each table row has a **“Last checked”** timestamp and a **Source URL**.

---

## 2) What problem this solves

Rates change frequently and “best” depends on constraints (term, deposit limits, restrictions).

This system addresses that by:
- Storing offers and point-in-time snapshots in a local database
- Maintaining freshness through automated and manual refresh jobs
- Exposing a simple UI and API that keep “comparability” honest (category + term)

---

## 3) Architecture at a glance

### 3.1 Components
- **Frontend** (`frontend/`): React + TypeScript (Vite). Fetches tables and displays filters and results.
- **Backend** (`backend/`): FastAPI. Serves table endpoints and admin refresh endpoints.
- **SQLite DB** (`data/app.db`): Stores providers/products/offers/snapshots and refresh job history.
- **Scraping/ingestion**: Firecrawl extracts structured JSON from target pages; backend upserts into SQLite.

### 3.2 System diagram

```mermaid
flowchart LR
  UI[React UI\n(frontend)] -->|HTTP| API[FastAPI\n(backend)]

  API -->|read current rows| DB[(SQLite\n data/app.db)]

  subgraph Refresh["Refresh pipeline"]
    SCHED[Scheduler (optional)\nAPScheduler] --> RUN[run_refresh_once()]
    ADMIN[Admin refresh endpoint\nPOST /admin/refresh] --> RUN
    RUN --> FC[Firecrawl API\nscrape + extract JSON]
    RUN -->|upsert| DB
  end

  API -->|expose job history| DB
```

---

## 4) Data model (why “offer” vs “snapshot”)

The database is designed to keep:
- A stable identity for “the thing we rank”
- A history of observed values over time

### 4.1 Core tables
- **`provider`**: the institution name (bank/building society).
- **`product`**: a product under a provider (typed as `fixed_savings` or `cash_isa`).
- **`product_offer`**: the stable offer variant that belongs in a specific comparable set.
  - key fields: `category`, `term_months`, `isa_subtype`
  - pointer: `current_snapshot_id`
- **`offer_snapshot`**: immutable observation facts for an offer at a moment in time.
  - includes `verified_at` (“Last checked”)
- **`source`** + **`snapshot_source`**: the URLs that support traceability for the snapshot.

### 4.2 “Last checked” and “Source URL”
- **Last checked** comes from `offer_snapshot.verified_at` for the offer’s **current** snapshot.
- **Source URL** is the first linked URL for the snapshot (`snapshot_source → source.url`).

### 4.3 Refresh job history
- **`ingestion_job_run`** persists refresh runs (scheduler or admin) so status survives restarts.

---

## 5) APIs (what the frontend calls)

### 5.1 Public table endpoints
These endpoints return `{ items: [...] }` where each item is a table row.

- **Fixed savings**: `GET /tables/fixed-savings`
- **Cash ISA easy access**: `GET /tables/cash-isa/easy-access`
- **Cash ISA fixed**: `GET /tables/cash-isa/fixed`

Important convention:
- `term_months=0` means **All terms** (backend maps it to “no term filter” internally).

### 5.2 Admin refresh endpoints (token protected)
All admin endpoints require:
- Header `X-Admin-Token: <ADMIN_TOKEN>`

Endpoints:
- `POST /admin/refresh?wait=true|false` — trigger refresh run (same pipeline as scheduler)
- `GET /admin/refresh/{job_id}` — in-memory job status (only for current server process)
- `GET /admin/refresh-history?limit=25` — persisted history from SQLite (survives restarts)

---

## 6) Refresh: how “freshness” is achieved

### 6.1 Scheduler refresh (optional)
If enabled, the backend starts APScheduler on API startup.

Key environment variables:
- `REFRESH_SCHEDULER_ENABLED=1`
- `REFRESH_INTERVAL_HOURS=6`

### 6.2 Manual refresh (admin)
The UI can show a “Refresh Live Rates” button when a frontend token is configured.

It calls the backend’s admin refresh endpoint, then refetches table data.

### 6.3 Failure behavior
- Per-target and per-offer errors are logged; refresh tries to continue.
- Job status is stored as `succeeded` or `failed`, with best-effort error text.

---

## 7) Configuration and operational notes

### 7.1 Required environment variables (repo root `.env`)
- `FIRECRAWL_API_KEY` — required for live scraping.
- `ADMIN_TOKEN` — required for `/admin/*`.

Optional:
- `REFRESH_SCHEDULER_ENABLED`, `REFRESH_INTERVAL_HOURS`
- `REFRESH_TARGETS_JSON` — override default target list (advanced).

### 7.2 Frontend admin refresh configuration
To enable the refresh button from the UI:
- Set `VITE_ADMIN_TOKEN` in `frontend/.env` to the same value as backend `ADMIN_TOKEN`.

---

## 8) Key risks / limitations (MVP)

- **Admin security**: admin auth is a shared secret token; this is acceptable for local/dev but not a multi-user production setup.
- **Scrape reliability**: comparison pages can change structure; extraction may degrade and require prompt/schema tuning.
- **Aggregator vs provider mismatch**: comparison sites can lag provider pages; the system records sources but does not yet enforce a full “provider page is authoritative” reconciliation process.

---

## 9) Roadmap (pragmatic next steps)

High-value follow-ups that build on the current architecture:
- **Provider page “source of truth”**: follow `provider_product_url` and scrape provider pages for authoritative terms.
- **Offer identity hardening**: explicit deterministic offer-key strategy for edge cases.
- **Fixture-based regression tests**: store sanitized extracted JSON fixtures per target URL and validate ingestion deterministically in CI.
- **UI job history panel**: display persisted refresh history (`ingestion_job_run`) in the admin UI.

