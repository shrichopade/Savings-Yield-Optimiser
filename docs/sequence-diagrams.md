## Sequence Diagrams — Savings Yield Optimiser

These diagrams reflect the current implementation of the **read path** (tables), the **refresh pipeline** (scheduler + admin), and the **scrape → upsert** ingestion flow.

---

## 1) Table load (Fixed Savings / Cash ISA)

```mermaid
sequenceDiagram
  autonumber
  actor User
  participant UI as React UI
  participant API as FastAPI (/tables/*)
  participant Repo as Offers repository
  participant DB as SQLite

  User->>UI: Open page / change filters
  UI->>API: GET /tables/fixed-savings?term_months=0&deposit_gbp=...&exclude_restricted=...
  API->>API: Map term_months=0 → OfferQuery.term_months=None
  API->>DB: Open connection(settings.db_path)
  API->>Repo: fetch_table_rows(conn, OfferQuery)
  Repo->>DB: SELECT ranked current snapshot rows
  DB-->>Repo: rows
  Repo-->>API: rows
  API-->>UI: { items: [...] } (snake_case)
  UI-->>User: Render ranked table
```

Notes:
- `term_months=0` is the stable **sentinel** meaning “All terms”.
- Response shape is always `{ "items": [...] }`.

---

## 2) Admin refresh (sync / wait=true)

```mermaid
sequenceDiagram
  autonumber
  actor Admin
  participant UI as React UI (optional)
  participant API as FastAPI (/admin)
  participant Refresh as run_refresh_once()
  participant FC as Firecrawl API
  participant DB as SQLite

  Admin->>UI: Click "Refresh Live Rates"
  UI->>API: POST /admin/refresh?wait=true (X-Admin-Token)
  API->>API: Validate X-Admin-Token
  API->>DB: INSERT ingestion_job_run(job_type="admin", status="running")
  API->>Refresh: run_refresh_once(settings)

  loop For each RefreshTarget
    Refresh->>FC: scrape_json(url, schema, prompt)
    FC-->>Refresh: extracted JSON { offers: [...] }
    loop For each offer
      Refresh->>DB: upsert provider/product/offer + insert snapshot + link source
    end
  end

  Refresh-->>API: success
  API->>DB: UPDATE ingestion_job_run(status="succeeded", finished_at=...)
  API-->>UI: { job_id, status:"succeeded", message:"Refresh complete" }
  UI->>API: Re-fetch tables (cache-buster _refresh tick)
  API-->>UI: { items: [...] }
```

Failure path (sync):
- If an exception escapes the refresh orchestration, the API marks the run as `failed` and returns HTTP 500.

---

## 3) Admin refresh (async / wait=false) + in-memory status

```mermaid
sequenceDiagram
  autonumber
  actor Admin
  participant UI as React UI (optional)
  participant API as FastAPI (/admin)
  participant Thread as Background thread
  participant Refresh as run_refresh_once()
  participant FC as Firecrawl API
  participant DB as SQLite

  Admin->>UI: Click "Refresh Live Rates"
  UI->>API: POST /admin/refresh?wait=false (X-Admin-Token)
  API->>API: Validate X-Admin-Token
  API->>API: Create in-memory JobState(job_id, status="queued")
  API->>DB: INSERT ingestion_job_run(job_type="admin", status="running")
  API->>Thread: start daemon thread(job_id)
  API-->>UI: { job_id, status:"queued", message:"Refresh started" }

  Thread->>API: set JobState status="running"
  Thread->>Refresh: run_refresh_once(settings)

  loop For each RefreshTarget
    Refresh->>FC: scrape_json(...)
    FC-->>Refresh: extracted JSON
    Refresh->>DB: upserts + snapshots + sources
  end

  alt success
    Thread->>DB: UPDATE ingestion_job_run(status="succeeded")
    Thread->>API: set JobState status="succeeded"
  else failure
    Thread->>DB: UPDATE ingestion_job_run(status="failed", error=...)
    Thread->>API: set JobState status="failed"
  end

  UI->>API: GET /admin/refresh/{job_id} (X-Admin-Token)
  API-->>UI: { job_id, status, started_at, finished_at, error }
```

Important behavior:
- `/admin/refresh/{job_id}` is **in-memory** (only works for the current server process).
- Persisted cross-restart visibility is provided by `/admin/refresh-history`.

---

## 4) Refresh job history (persisted)

```mermaid
sequenceDiagram
  autonumber
  actor Admin
  participant UI as React UI (or API client)
  participant API as FastAPI (/admin)
  participant DB as SQLite

  Admin->>UI: Open "Refresh history"
  UI->>API: GET /admin/refresh-history?limit=25 (X-Admin-Token)
  API->>API: Validate X-Admin-Token
  API->>DB: SELECT job_run_id, job_type, status, started_at, finished_at, error ORDER BY started_at DESC
  DB-->>API: rows
  API-->>UI: { items: [...] }
```

---

## 5) Scheduler refresh (background cadence)

```mermaid
sequenceDiagram
  autonumber
  participant App as FastAPI app startup
  participant Sched as APScheduler
  participant Refresh as run_refresh_once()
  participant FC as Firecrawl API
  participant DB as SQLite

  App->>Sched: start_scheduler(settings) (if enabled)
  Sched->>Sched: schedule interval job (every N hours)

  Note over Sched,Refresh: Every REFRESH_INTERVAL_HOURS
  Sched->>Refresh: run_refresh_once(settings)
  Refresh->>DB: INSERT ingestion_job_run(job_type="scheduler", status="running")

  loop For each RefreshTarget
    Refresh->>FC: scrape_json(...)
    FC-->>Refresh: extracted JSON
    Refresh->>DB: upserts + snapshots + sources
  end

  Refresh->>DB: UPDATE ingestion_job_run(status="succeeded" or "failed")
```

