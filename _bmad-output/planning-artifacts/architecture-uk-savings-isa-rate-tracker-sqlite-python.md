# Architecture — UK Savings & Cash ISA Rate Tracker (SQLite + Python, Local-first)

## 1) Architecture goals (from PRD)
- **Local-first**: all data stored and queried locally using SQLite.
- **Trust & auditability**: every displayed field must map to a stored field with **source URL(s)** and **last verified** timestamps.
- **Honest comparisons**: enforce **comparability sets** (category + term bucket) and apply eligibility/deposit filters deterministically.
- **Change awareness**: store **history** of rates/terms to support “changed/withdrawn” handling and future alerts.

## 2) High-level system shape
### 2.1 Components
- **Scraper service** (Firecrawl-powered ingestion): fetch + extract content from approved UK financial comparison/editorial-aggregation pages (e.g., Moneyfacts, MoneySavingExpert) and (where feasible) provider product pages, normalize into “offer observations”, validate, then upsert into SQLite.
- **Query API** (local Python backend): read-only endpoints for:
  - fixed savings table (by term bucket)
  - easy access cash ISA table
  - fixed cash ISA table (by term bucket)
  - product details (includes sources + history)
- **Ranking service**: implements comparability and tie-breakers; produces “why ranked” metadata.
- **Alert evaluator** (phase 1-lite): runs after ingestion to detect “better rate appeared” or watched product changed.
- **Scheduler / job runner**: a background process that runs the refresh cadence (every 6 hours + daily full refresh) and records job status.

### 2.2 Data flow
1. Scraper service uses **Firecrawl** to retrieve and extract content for monitored pages.
2. Scraper service produces an **Observation** for a product offer at time \(t\).
2. Observation is persisted as an immutable **offer_snapshot** row.
3. A **product_offer.current_snapshot_id** pointer is updated to the latest valid snapshot.
4. Query layer reads **current snapshots** (or historical snapshots when requested), applies filters + ranking, returns table rows.

## 3) SQLite schema (DDL)
The schema is designed around:
- **provider** → brands/institutions
- **product** → marketing-level product (name/type)
- **product_offer** → a specific offer variant (term bucket, ISA subtype, etc.)
- **offer_snapshot** → time-versioned facts (AER, bonuses, eligibility flags, limits, etc.)
- **source** + **snapshot_source** → traceability

Reference implementation DDL: `sqlite-schema-uk-savings-isa.sql` (generated in this repo’s planning artifacts).

### 3.1 Key modelling decisions
- **Offer vs snapshot**:
  - `product_offer` is the stable “thing you rank” (e.g., “Provider X 1-year fixed bond”, or “Provider Y easy access cash ISA”).
  - `offer_snapshot` captures time-varying details (rates, limits, terms text-derived flags) and supports change history.
- **Eligibility and constraints** stored as structured fields**:
  - Enables deterministic filtering and reproducible ranking.
- **Unknowns are first-class**:
  - many fields can be `NULL` (“unknown”), and the UI should display “Unknown” rather than guessing.

### 3.2 Indexing strategy (for table performance)
Primary table queries are “top list” reads; indexes support:
- Fast retrieval of active offers in a given comparability set.
- Sorting by AER and filtering by deposit min/max.
- Filtering on eligibility restriction flags.

## 4) Query & ranking approach
### 4.1 Comparability sets (PRD FR6)
Tables are defined by:
- **category**:
  - `fixed_savings`
  - `cash_isa_easy_access`
  - `cash_isa_fixed`
  - (phase 2) `cash_isa_notice`
- **term_bucket_months** (only for fixed categories)

Implementation:
- Each `product_offer` stores `category` and optional `term_months`.
- Query endpoints always scope to a single category (+ term when applicable).

### 4.2 Filtering (PRD FR4)
Applied in this order (recommended):
1. **Status**: exclude withdrawn/inactive offers.
2. **Deposit filter**: if user provides deposit amount \(D\), require:
   - `min_opening_deposit_gbp <= D` (or `NULL` treated as “no minimum known”, optionally include but flag)
   - `max_balance_gbp >= D` (or `NULL` treated as “no maximum known”)
3. **Eligibility toggle**:
   - when “exclude restricted deals” is on, remove offers where snapshot indicates restrictions (new customer only / membership / other gating).
4. Optional payout frequency, conditional rate inclusion, etc.

### 4.3 Ranking & tie-breakers (PRD)
Default sort:
1. `aer_percent` DESC (NULLS LAST)
2. Fewer restrictions (computed `restriction_score` ASC)
3. Access friendliness (for access-focused views; phase 1 optional)
4. Payout preference match (optional)

Return additional metadata per row:
- `rank_basis`: e.g., “AER desc within 12‑month fixed savings”
- `excluded_reason_counts`: used to render exclusions messaging
- `badges`: bonus/conditional/penalty/transfer/flexible flags

## 5) Python backend structure (local data management)
Keep it boring: a small FastAPI app + SQLAlchemy (or sqlite3) + a CLI for ingestion.

### 5.1 Suggested repository layout
```
backend/
  app/
    __init__.py
    main.py                 # FastAPI app, routes wiring
    settings.py             # paths, environment config (db path, etc.)
    db/
      __init__.py
      engine.py             # create_engine(sqlite:///...), pragmas
      session.py            # session maker / connection helpers
      migrations/           # optional (Alembic) or simple schema bootstrap
    models/
      __init__.py
      orm.py                # SQLAlchemy ORM models (provider/product/offer/snapshot/source)
      enums.py              # category constants, payout frequency, etc.
    schemas/
      __init__.py
      api.py                # Pydantic response/request models for tables + details
    repositories/
      offers.py             # query helpers (current offers, by category/term)
      snapshots.py          # snapshot CRUD + history reads
      sources.py            # source linking + traceability
    services/
      ranking.py            # apply filters + sort + produce “why ranked”
      exclusions.py         # compute excluded counts + messages
      validation.py         # validate ingestion output before persist
    routes/
      fixed_savings.py      # /tables/fixed-savings?term=12&deposit=...
      cash_isa.py           # /tables/cash-isa/easy-access, /tables/cash-isa/fixed
      products.py           # /products/{offer_id}
    cli/
      ingest.py             # run ingestion pipeline locally
      export.py             # optional: export CSV for debugging
  ingestors/
    __init__.py
    base.py                 # interface for ingestors
    provider_x.py           # per-provider parser (incrementally added)
  sql/
    schema.sql              # SQLite DDL snapshot (checked in)
```

### 5.2 SQLite operational practices
Set SQLite pragmas on connect:
- `PRAGMA foreign_keys = ON;`
- `PRAGMA journal_mode = WAL;` (better concurrent reads during ingestion)
- `PRAGMA synchronous = NORMAL;` (reasonable for local)

### 5.3 Ingestion workflow (local)
1. Fetch HTML (or API payload) for a provider product page.
2. Parse into a canonical “offer observation” object.
3. Validate:
   - required identifiers present
   - numeric fields in bounds (AER 0–100, deposits non-negative)
   - term months set when category requires it
4. Upsert `provider` + `product`.
5. Upsert `product_offer` (stable key: provider + product + category + term + subtype).
6. Insert immutable `offer_snapshot` row with `verified_at`.
7. Link `snapshot_source` rows with URL(s).
8. Update `product_offer.current_snapshot_id` to this snapshot (if snapshot passes validation).

### 5.4 Query endpoints (MVP)
- `GET /tables/fixed-savings?term_months=12&deposit_gbp=5000&exclude_restricted=true`
- `GET /tables/cash-isa/easy-access?deposit_gbp=2000&exclude_restricted=true`
- `GET /tables/cash-isa/fixed?term_months=12&deposit_gbp=2000&exclude_restricted=true`
- `GET /offers/{offer_id}` (current snapshot + sources + (optional) history)

### 5.5 Scraper service (Firecrawl) — design
#### 5.5.1 Responsibilities
- **Target selection**:
  - Phase 1: monitor a small set of comparison/editorial-aggregation pages for each table category/term bucket.
  - When feasible, also capture and persist **provider product page URLs** for authoritative terms.
- **Extraction**:
  - Use **Firecrawl** for retrieval + extraction (HTML → structured content).
  - Parse extracted content into the canonical observation model used by the existing ingestion pipeline.
- **Validation & persistence**:
  - Perform strict validation before DB write (bounds checks, term/category required fields).
  - Upsert offer identity (`provider` / `product` / `product_offer`) and insert immutable `offer_snapshot` rows.

#### 5.5.2 Source-of-truth hierarchy (how we store Last Checked + Source URLs)
The current schema already supports this requirement:
- **“Last Checked”**:
  - Stored as `offer_snapshot.verified_at` (ISO timestamp).
  - The UI’s “Last checked” for a row is derived from the **current snapshot’s** `verified_at`.
- **Source URL(s)**:
  - Stored in `source.url`, linked to snapshots via `snapshot_source`.
  - `source.source_type` should be extended/used to distinguish origins:
    - `comparison_site` (or similar) for Moneyfacts/MoneySavingExpert pages
    - `provider_page` for bank/building society product pages
    - `other`/`fca_register` as needed

Schema note (recommended small tweak, optional): update the allowed values comment for `source.source_type` to include `comparison_site`, but no structural change is required because it’s already a free-text field.

### 5.6 Scheduler / background jobs (6-hour cadence)
We want “agentic freshness” without coupling refresh to user requests.

#### 5.6.1 Execution model (local-first)
Choose one of these “boring” options (both work locally):
- **External scheduler**: run `python -m backend.app.cli.refresh_rates` via cron/Windows Task Scheduler every 6 hours (+ a daily full refresh job).
- **In-process scheduler**: run APScheduler (or similar) in a dedicated process started alongside the API (recommended only if you control deployment and avoid multi-worker duplication).

#### 5.6.2 Job semantics
- **6-hour incremental refresh**:
  - Scrape monitored comparison pages for each category/term bucket.
  - Upsert offers and write new snapshots where changes are detected.
- **Daily full refresh**:
  - Re-validate the active set, mark withdrawn/removed items, and ensure “last checked” updates even when rates are unchanged (optional).
- **Idempotency & locking**:
  - Ensure only one refresh runs at a time (process lock / DB lock row / file lock).
  - If a job fails mid-run, partial progress is acceptable as long as the DB is never left inconsistent (snapshots are append-only; offer pointers update only after validation).

#### 5.6.3 Minimal job status tracking (recommended)
To support the admin UI, expose job state via a lightweight mechanism:
- Minimal approach: log to disk + keep last-run timestamps in memory (quick but not queryable after restart).
- Better approach (recommended): add a small `ingestion_job_run` table in SQLite:
  - `job_run_id`, `job_type` (six_hour/daily/manual), `status` (queued/running/succeeded/failed), `started_at`, `finished_at`, `error_summary`
  - This keeps job state queryable and survives restarts.

### 5.7 Admin on-demand refresh (Frontend → FastAPI → job runner)
#### 5.7.1 API endpoints
Add admin endpoints (exact routing is flexible):
- `POST /admin/refresh`:
  - Enqueues (or starts) a **manual refresh** run.
  - Returns `{ job_run_id, status }`.
- `GET /admin/refresh/{job_run_id}`:
  - Returns job status + timestamps + a short error summary (if failed).

#### 5.7.2 Frontend flow
- The React UI shows an **Admin-only** “Refresh rates now” button.
- On click:
  1. Call `POST /admin/refresh`.
  2. Show immediate feedback (“Refresh started”) and poll `GET /admin/refresh/{job_run_id}` until terminal state.
  3. On success, refetch the active table endpoints so updated “Last checked” timestamps appear.

#### 5.7.3 Authorization (local-first)
For MVP/local use, keep it simple:
- Gate the admin control behind a simple config flag or shared secret header.
- Ensure non-admin users cannot trigger refresh (even if they discover the endpoint).

## 6) Migration strategy
For SQLite, simplest is:
- Check in `schema.sql`.
- On startup (or CLI), run a **bootstrap** that:
  - creates tables if missing
  - writes a `schema_version` row
Later, if needed:
- adopt Alembic migrations (still SQLite-compatible) once schema changes become frequent.

## 7) Security, compliance, and disclaimers (local-first)
- Treat the DB as local user data; store it under a predictable app data directory.
- Keep “not financial advice” disclaimers in the UI layer; backend should return rank basis and sources to support transparency.

