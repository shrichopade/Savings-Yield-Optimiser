## Solution Architecture — Savings Yield Optimiser

Audience: **engineers** implementing/maintaining the system and **stakeholders** reviewing scope, risks, and operating model.

---

## 1) Overview

Savings Yield Optimiser is a **local-first** UK savings + Cash ISA rate tracker.

It combines:
- A **React (Vite) UI** for browsing ranked tables of offers with filters
- A **FastAPI backend** for serving tables and running refresh jobs
- A local **SQLite database** as the system of record
- A **scrape → extract → upsert** pipeline powered by **Firecrawl**
- An **optional scheduler** (6-hour cadence) plus an **admin on-demand refresh**

Key design goals:
- **Auditability**: every displayed row is backed by stored data and a **source URL**
- **Freshness**: rates can be refreshed automatically (scheduler) and manually (admin)
- **Honest comparisons**: ranking is done within comparable sets (category + term where applicable)

---

## 2) Architecture at a glance

### 2.1 Component diagram

```mermaid
flowchart LR
  UI[React UI\n(frontend)] -->|HTTP| API[FastAPI\n(backend)]

  API -->|read current rows| DB[(SQLite\n data/app.db)]

  subgraph Refresh["Refresh pipeline"]
    SCHED[Scheduler (optional)\nAPScheduler] --> RUN[run_refresh_once()]
    ADMIN[Admin refresh API\nPOST /admin/refresh] --> RUN
    RUN --> FC[Firecrawl API\nscrape + extract JSON]
    RUN -->|upsert| DB
  end
```

### 2.2 Responsibility boundaries (what goes where)

- **Frontend**: UI state, filters, table rendering, optional admin refresh button
- **Backend routes**: HTTP parsing/validation + stable response shapes
- **Backend services**: orchestration (refresh), ingestion/upsert, Firecrawl integration
- **Backend repositories**: SQL reads for table endpoints (current snapshot queries)
- **SQLite**: system of record for offers, snapshots, sources, and refresh job history

---

## 3) Primary flows

### 3.1 Read flow (normal user)

1. User adjusts filters in the UI (deposit, restrictions, term buckets).
2. UI calls public table endpoints on FastAPI.
3. Backend executes a “current snapshot” read query in SQLite.
4. Backend returns `{ "items": [...] }` where items are `snake_case` row objects.
5. UI renders ranked results.

### 3.2 Refresh flow (scheduled)

1. FastAPI starts APScheduler on startup when enabled.
2. Every 6 hours (configurable), the scheduler triggers a refresh run.
3. The refresh orchestrator scrapes configured targets via Firecrawl, normalizes offers, and upserts into SQLite.
4. The table endpoints immediately reflect new “current snapshot” pointers.

### 3.3 Refresh flow (admin on-demand)

1. UI (optional) displays “Refresh Live Rates” when `VITE_ADMIN_TOKEN` is configured.
2. UI calls `POST /admin/refresh?wait=true|false` with header `X-Admin-Token`.
3. Backend runs the same refresh pipeline as the scheduler.
4. UI forces table refetch via a `_refresh` cache-buster parameter.

---

## 4) Key contracts (stability rules)

### 4.1 Public table APIs (read-only)

All table endpoints:
- Return a wrapper object: **`{ "items": [...] }`**
- Use **`snake_case`** field names (match backend models)

Term filtering convention:
- **`term_months=0` means “All terms”** (sentinel value; stable contract)

### 4.2 Admin APIs (token-protected)

Admin endpoints require:
- Header: **`X-Admin-Token: <ADMIN_TOKEN>`**

Admin endpoints:
- `POST /admin/refresh?wait=true|false` (trigger refresh)
- `GET /admin/refresh-history?limit=N` (persisted job history)
- `GET /admin/refresh/{job_id}` (in-memory status for current process)

---

## 5) Data architecture (why snapshots)

The database separates:
- **Stable identities** (provider/product/offer) from
- **Point-in-time observations** (snapshots)

Key mapping:
- “Last checked” in the UI corresponds to `offer_snapshot.verified_at` (current snapshot).
- “Source URL” is recorded via `snapshot_source → source.url`.

Refresh job visibility:
- Refresh runs are persisted in `ingestion_job_run` (survives restarts).

---

## 6) Configuration & operational model

### 6.1 Required secrets (local-first)

- `FIRECRAWL_API_KEY` (live scraping)
- `ADMIN_TOKEN` (protects `/admin/*`)

Frontend uses:
- `VITE_ADMIN_TOKEN` to enable the refresh button (should match backend `ADMIN_TOKEN`)

### 6.2 Refresh scheduler configuration

- `REFRESH_SCHEDULER_ENABLED=1|0`
- `REFRESH_INTERVAL_HOURS=6` (default target)
- `REFRESH_TARGETS_JSON` (optional override for targets list)

---

## 7) Security posture (current scope)

This MVP assumes **local/dev operation**:
- Admin auth is a shared secret token (sufficient for local use; not a multi-user production model).
- Firecrawl key and admin token must **not** be committed to git.

If evolving toward hosted multi-user usage, the first architectural upgrade would be:
- proper auth (OIDC/session/JWT), role-based access, and secret management.

---

## 8) Risks and mitigation (architecture-level)

- **Scrape stability risk**: upstream pages change.
  - Mitigation: keep extraction schemas/prompts centralized; add fixture-based regression tests per target.
- **Aggregator vs provider discrepancies**: comparison sites can lag provider pages.
  - Mitigation: record provenance; optionally add provider-source reconciliation as a follow-up epic.
- **Token-based admin security**: simple shared secret.
  - Mitigation: keep local-only; upgrade auth before hosting.

---

## 9) Handoff notes (for future work)

When adding new features, keep these boundaries stable:
- Routes stay thin; orchestration belongs in services.
- Table API contracts are stable (snake_case, `{items:[...]}`, `term_months=0`).
- Every new ingestion path must preserve `verified_at` + `source_url`.

