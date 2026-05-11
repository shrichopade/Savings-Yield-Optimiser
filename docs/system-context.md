## System Context — Savings Yield Optimiser (current implementation)

This document answers: **who uses the system**, **what it depends on**, and **what sits outside the system boundary**.

---

## 1) System boundary

**Savings Yield Optimiser** is a local-first application consisting of:
- **React UI** (`frontend/`)
- **FastAPI backend** (`backend/`)
- **SQLite database** (`data/app.db`)
- **Refresh pipeline** (scheduler + admin-triggered) inside the backend process

Everything above runs on a single machine for MVP usage.

---

## 2) People (actors)

- **Saver (end user)**: browses ranked tables and applies filters (deposit, restrictions, term).
- **Admin / Maintainer**: triggers on-demand refresh and inspects refresh history when needed.

---

## 3) External systems and dependencies

- **Firecrawl API**: external scraping/extraction service.
  - Used by the backend refresh pipeline to extract structured JSON from target pages.
  - Requires `FIRECRAWL_API_KEY`.

- **UK financial websites (targets)**: external pages that act as sources for offers.
  - Examples used in the current refresh targets include comparison/editorial sites and provider pages.
  - These are not controlled by us and can change frequently (scrape drift risk).

---

## 4) Context diagram (C4-style)

```mermaid
flowchart LR
  Saver[Saver\n(end user)]
  Admin[Admin / Maintainer]

  subgraph SYO["Savings Yield Optimiser (System)"]
    UI[React UI\n(Vite + TypeScript)]
    API[FastAPI Backend\n(Python)]
    DB[(SQLite DB\n data/app.db)]
    SCHED[Scheduler (optional)\nAPScheduler]
    REFRESH[Refresh orchestration\nrun_refresh_once()]
  end

  FC[Firecrawl API]
  WEB[UK financial websites\n(comparison + provider pages)]

  Saver -->|View tables, set filters| UI
  Admin -->|Trigger refresh, view history| UI

  UI -->|HTTP GET /tables/*| API
  UI -->|HTTP POST /admin/refresh*| API

  API -->|Read current snapshot rows| DB
  API -->|Persist refresh history| DB

  SCHED -->|Interval trigger| REFRESH
  API -->|Admin refresh trigger| REFRESH

  REFRESH -->|Scrape + extract JSON| FC
  FC -->|Fetch pages| WEB
  REFRESH -->|Upsert offers + snapshots + sources| DB
```

---

## 5) Interfaces (what crosses boundaries)

### 5.1 Public read API (Saver-facing)

- `GET /tables/fixed-savings`
- `GET /tables/cash-isa/easy-access`
- `GET /tables/cash-isa/fixed`

Stable convention:
- `term_months=0` means **All terms**.

### 5.2 Admin API (Maintainer-facing; token protected)

Requires header:
- `X-Admin-Token: <ADMIN_TOKEN>`

Endpoints:
- `POST /admin/refresh?wait=true|false`
- `GET /admin/refresh-history?limit=N`
- `GET /admin/refresh/{job_id}` (in-memory; current process only)

---

## 6) Key constraints implied by context

- **Local-first**: no managed DB or hosted infrastructure is assumed.
- **External dependency risk**: target pages can change; extraction needs ongoing maintenance.
- **Secrets**: `FIRECRAWL_API_KEY` and `ADMIN_TOKEN` must remain local (not committed).

