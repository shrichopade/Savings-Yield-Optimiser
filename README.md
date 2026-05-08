## Savings Yield Optimiser

Local-first UK **Savings + Cash ISA rate tracker**.

This project is designed to:
- Keep a local SQLite database of rate offers and historical snapshots
- Scrape / refresh live rates periodically (Firecrawl) and on-demand (Admin refresh)
- Present tables and filters in a React UI

---

## What you get

- **Frontend**: React + TypeScript (Vite) dashboard with tables and filters.
- **Backend**: FastAPI providing table APIs and admin refresh endpoints.
- **Database**: SQLite (`data/app.db`) with stable “offers” + immutable “snapshots”.
- **Scraping / ingestion**: Firecrawl JSON extraction + upsert pipeline into SQLite.
- **Refresh**:
  - Scheduled refresh via APScheduler (configurable)
  - Admin-triggered on-demand refresh (button in UI + API)
  - Persisted refresh history in SQLite (`ingestion_job_run`)

---

## Repository layout

- **`frontend/`**: UI (Vite/React/TS)
- **`backend/`**: API + scraping/ingestion services
  - **`backend/app/main.py`**: FastAPI app factory + routes + scheduler startup
  - **`backend/app/routes/tables.py`**: table endpoints (`/fixed-savings`, `/cash-isa/*`)
  - **`backend/app/routes/admin_refresh.py`**: admin refresh endpoints (`/admin/*`)
  - **`backend/app/services/refresh_scheduler.py`**: APScheduler + refresh orchestration
  - **`backend/app/services/scraped_rate_ingestion.py`**: SQLite upsert pipeline
  - **`backend/sql/schema.sql`**: SQLite schema
- **`data/`**: local SQLite database lives here (created at runtime)
- **`_bmad-output/`**: planning artifacts (Project Brief, PRD, Architecture, sprint status)

---

## Prerequisites

- **Python**: 3.11+ recommended
- **Node.js**: 18+ (or newer)

---

## Quick start (Windows / PowerShell)

From the repo root:

### 1) Create a Python venv + install backend deps

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r backend\requirements.txt
```

Optional dev deps (tests):

```powershell
.\.venv\Scripts\python -m pip install -r backend\requirements-dev.txt
```

### 2) Configure environment variables

Create or edit **repo root** `.env`:

```env
# Firecrawl (required for live scraping)
FIRECRAWL_API_KEY=...

# Enable periodic refresh job (optional)
REFRESH_SCHEDULER_ENABLED=0
REFRESH_INTERVAL_HOURS=6

# Admin endpoints protection (required for /admin/*)
ADMIN_TOKEN=some-long-random-string
```

Notes:
- **`ADMIN_TOKEN`** can be any long random string you choose (keep it private).
- If `ADMIN_TOKEN` is missing, `/admin/*` returns `503 Admin token not configured on server.`

### 3) Initialise the SQLite database

```powershell
.\.venv\Scripts\python -m backend.app.cli.init_db
```

Optional (MVP seed data):

```powershell
.\.venv\Scripts\python -m backend.app.cli.seed_db
```

### 4) Run the backend API

```powershell
.\.venv\Scripts\python -m uvicorn backend.app.main:app --reload
```

Backend docs:
- Swagger: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/health`

### 5) Run the frontend

```powershell
cd frontend
npm install
npm run dev
```

Open the UI at the Vite URL (usually `http://127.0.0.1:5173`).

---

## Admin refresh (API)

Admin endpoints are under **`/admin`** and require header:
- **`X-Admin-Token: <ADMIN_TOKEN>`**

### Trigger a refresh

Synchronous (wait until complete):

```powershell
$token = "<your ADMIN_TOKEN>"
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/admin/refresh?wait=true" -Headers @{ "X-Admin-Token" = $token }
```

Async (returns immediately with a `job_id`):

```powershell
$token = "<your ADMIN_TOKEN>"
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/admin/refresh?wait=false" -Headers @{ "X-Admin-Token" = $token }
```

### Check job status (in-memory; current process only)

```powershell
$token = "<your ADMIN_TOKEN>"
Invoke-RestMethod -Uri "http://127.0.0.1:8000/admin/refresh/<job_id>" -Headers @{ "X-Admin-Token" = $token }
```

### View refresh history (persisted in SQLite; survives restarts)

```powershell
$token = "<your ADMIN_TOKEN>"
Invoke-RestMethod -Uri "http://127.0.0.1:8000/admin/refresh-history?limit=25" -Headers @{ "X-Admin-Token" = $token }
```

---

## Refresh scheduler (6-hour cadence)

The scheduler is started on FastAPI startup if enabled:
- `REFRESH_SCHEDULER_ENABLED=1`
- `REFRESH_INTERVAL_HOURS=6`

If you want to customize scrape targets, set `REFRESH_TARGETS_JSON` to a JSON array of targets (advanced).

---

## Frontend admin refresh button

The UI includes a **“Refresh Live Rates”** button. For it to work:
- Backend must have `ADMIN_TOKEN` configured
- Frontend must have `VITE_ADMIN_TOKEN` configured

Add to `frontend/.env`:

```env
VITE_ADMIN_TOKEN=the-same-value-as-ADMIN_TOKEN
```

Restart the frontend dev server after editing `frontend/.env`.

---

## Running tests

```powershell
.\.venv\Scripts\python -m pip install -r backend\requirements-dev.txt
.\.venv\Scripts\python -m pytest -q
```

---

## Troubleshooting

### “Admin token not configured on server.”
- Set `ADMIN_TOKEN` in the **repo root** `.env`
- Restart the backend

### Frontend tables are empty
Check these in order:
- Backend running: `GET http://127.0.0.1:8000/health`
- API tables return rows:
  - `GET http://127.0.0.1:8000/fixed-savings?term_months=0`
  - `GET http://127.0.0.1:8000/cash-isa/fixed?term_months=0`
- Ensure your refresh ran (admin refresh or scheduler)

### PowerShell encoding / JSON piping issues
If you run CLI scripts that print Unicode/JSON and see encoding problems, use:

```powershell
$env:PYTHONUTF8=1
$OutputEncoding=[Console]::OutputEncoding=[Text.UTF8Encoding]::new()
```

---

## Development notes (high level)

The data model is designed around:
- **Stable offer identity**: `product_offer` represents a comparable offer variant
- **Immutable observations**: `offer_snapshot` records facts “as verified at” a point in time
- **Traceability**: `snapshot_source` links a snapshot to the `source.url` it came from

---

## License

TBD (add a license if/when you’re ready to open source this).

