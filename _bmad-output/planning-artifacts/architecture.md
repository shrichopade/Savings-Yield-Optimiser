---
completedAt: 2026-05-08
project_name: Savings-Yield-Optimiser
user_name: Shri
date: 2026-05-08
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements (what we must support):**
- **Ranked tables** for:
  - Fixed Savings (by term; also supports “All”)
  - Cash ISA Easy Access
  - Cash ISA Fixed (by term; also supports “All”)
- **Filters**:
  - Deposit amount (hide offers outside min/max bounds)
  - Exclude restricted deals (MVP definition: `new_customer_only` / `new_money_required`)
  - Term selection for fixed categories
- **Transparency**:
  - Show “Last checked” (from `offer_snapshot.verified_at`)
  - Provide a source URL per row (from `snapshot_source → source.url`)
- **Admin operations**:
  - On-demand refresh (admin-only)
  - Basic job status visibility (persisted in SQLite via `ingestion_job_run`)
- **Automated data collection**:
  - Firecrawl-based scraping of UK comparison/editorial pages
  - 6-hour refresh cadence (optional scheduler) + manual refresh

**Non-Functional Requirements (constraints that shape architecture):**
- **Local-first**: SQLite is the system of record; app runs locally.
- **Auditability**: every displayed value must map to a stored field + source URL(s).
- **Operational safety**: refresh must fail gracefully and not corrupt DB.
- **Performance**: table reads should be fast (simple “current snapshot” reads; indexed).

**Scale & Complexity:**
- Primary domain: **full-stack local web app** (React + FastAPI + SQLite)
- Complexity level: **medium**
- Estimated architectural components: **5–7**
  - UI (React)
  - API (FastAPI)
  - SQLite persistence/query layer
  - Scrape/extract (Firecrawl client)
  - Refresh orchestration (scheduler + admin refresh)
  - (Optional next) job-history UI, richer ranking explanations, alerts

### Technical Constraints & Dependencies

- **Firecrawl** requires `FIRECRAWL_API_KEY` and network access.
- **Admin** endpoints require `ADMIN_TOKEN` and client-side `VITE_ADMIN_TOKEN` for the refresh button.
- **Term comparability**: fixed categories must respect term buckets; “All” is supported via `term_months=0`.
- **Data drift risk**: upstream pages change; extraction schema/prompt may require maintenance.

### Cross-Cutting Concerns Identified

- **Traceability**: source URLs and last-checked timestamps must be preserved end-to-end.
- **Idempotent ingestion**: upsert must not create duplicates or lose history.
- **Resilient refresh**: partial failures should not block all updates.
- **Security (MVP local)**: shared-secret admin token (acceptable for local dev; not production multi-user).

## Starter Template Evaluation

### Primary Technology Domain

**Full-stack local web application**:
- **Frontend**: React + TypeScript (Vite)
- **Backend**: FastAPI (Python)
- **Database**: SQLite (local-first)

### Starter Options Considered (for context)

If we were starting from scratch today, viable starters would include:
- **Vite React + TypeScript template** (simple, fast iteration) — `npm create vite@latest ... -- --template react-ts`
- **FastAPI Full Stack Template** (heavier, production-oriented scaffold)

### Selected Starter: This repository’s current baseline

We treat the current codebase as the “starter template” we standardize on.

**Rationale for selection:**
- Matches the PRD’s **local-first** and **auditability** needs with a simple, inspectable stack.
- Keeps the system easy to operate locally (no external DB required).
- Preserves the implemented conventions already relied upon by UX and API contracts:
  - `term_months=0` = “All terms”
  - “Last checked” = `offer_snapshot.verified_at`
  - Admin refresh secured via `X-Admin-Token`

**Initialization commands (what the baseline assumes):**

Frontend baseline is consistent with Vite’s React+TS creation flow:

```bash
npm create vite@latest my-app -- --template react-ts
```

Backend baseline is a standard FastAPI app served by Uvicorn (and optionally `fastapi dev` in newer setups).

**Architectural decisions provided by this baseline:**
- **Language & runtime**:
  - Frontend: TypeScript + React
  - Backend: Python + FastAPI
- **Styling**:
  - Tailwind-based styling in the current UI (as implemented)
- **Build tooling**:
  - Vite for frontend build + dev server
- **Data**:
  - SQLite as system of record; current-snapshot pointer pattern for fast table reads
- **Refresh & ingestion**:
  - Firecrawl extraction → upsert pipeline → snapshot/history model
  - Scheduler optional via APScheduler; admin refresh available when token is set

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
- **System of record**: SQLite local DB (`data/app.db`)
- **Offer model**: stable offer (`product_offer`) + immutable observation (`offer_snapshot`) + source traceability (`source`/`snapshot_source`)
- **Freshness model**:
  - scheduled refresh (optional) + admin on-demand refresh
  - persisted job history in SQLite (`ingestion_job_run`)
- **API contract**:
  - `term_months=0` means “All terms”
  - “Last checked” = `offer_snapshot.verified_at`
- **Admin access**: shared secret token header (`X-Admin-Token`) (local-first MVP)

**Important Decisions (Shape Architecture):**
- **Scraping approach**: Firecrawl JSON extraction with a schema + prompt
- **Ingestion**: idempotent upsert pipeline; update `current_snapshot_id` pointer
- **Failure behavior**: per-target/per-offer errors logged; refresh continues best-effort
- **Frontend refresh UX**: optional “Refresh Live Rates” button when `VITE_ADMIN_TOKEN` is configured

**Deferred Decisions (Post-MVP):**
- Full auth/roles (beyond shared token)
- Provider-page “source of truth” reconciliation (follow `provider_product_url` to confirm terms)
- CI fixtures for scraping drift and richer “gotchas” UX (bonus/penalty/transfer rules)

### Data Architecture

- **Database**: SQLite (local-first)
- **Schema strategy**: checked-in DDL (`backend/sql/schema.sql`) + bootstrap init
- **Query strategy**: read via `product_offer.current_snapshot_id` for fast “current tables”
- **Job tracking**: `ingestion_job_run` persists refresh run status

### Authentication & Security

- **MVP auth**: shared secret header `X-Admin-Token` for `/admin/*`
- **Frontend secret handling**: `VITE_ADMIN_TOKEN` is build-time exposed (acceptable for local; not production)
- **Production note** (deferred): replace with proper auth (sessions/JWT) and server-side role checks

### API & Communication Patterns

- **API style**: REST (FastAPI)
- **Endpoint grouping**: public tables under `/tables/*`, admin under `/admin/*`
- **Error behavior**: table APIs return standard HTTP errors; refresh returns job id/status

### Frontend Architecture

- **Framework**: React + TypeScript
- **Data fetching**: `fetchTable()` helper; table component fetches on param changes
- **Refresh refetch**: `_refresh` param tick acts as a cache-buster to trigger re-fetch

### Infrastructure & Deployment

- **Local dev**: run backend with uvicorn, frontend with Vite dev server
- **Scheduler**: in-process APScheduler is optional and controlled via env
- **Ports**: backend default `8000`, frontend dev default `5173`

### Decision Impact Analysis

**Implementation sequence (already followed by repo):**
1. SQLite schema + bootstrap init
2. Public table APIs reading “current snapshot” rows
3. Firecrawl extraction + ingestion upsert
4. Scheduler + admin refresh endpoints + persisted job history
5. Frontend tables + admin refresh UX

**Cross-component dependencies:**
- Refresh pipeline ↔ DB schema (snapshot/source/job-run tables)
- UI “All terms” ↔ API `term_months=0` convention
- Admin refresh UI ↔ `ADMIN_TOKEN` / `VITE_ADMIN_TOKEN` configuration

## Implementation Patterns & Consistency Rules

### Pattern Categories Defined

**Critical conflict points identified:** naming + formats + file placement + “what is the source of truth” for shared behaviors.

### Naming Patterns

**Database naming conventions**
- Tables/columns are **snake_case** (as already in `schema.sql`): `product_offer`, `offer_snapshot`, `term_months`.
- Primary keys: `{entity}_id` (e.g., `provider_id`, `offer_id`).
- Timestamps: `{verb}_at` in ISO strings (e.g., `verified_at`, `started_at`).

**API naming conventions**
- Endpoints use **simple path segments** and **snake_case query params**:
  - Paths: `/tables/fixed-savings`, `/tables/cash-isa/fixed`
  - Query params: `term_months`, `deposit_gbp`, `exclude_restricted`
- Sentinel values:
  - `term_months=0` means **All terms** (do not use “missing param” to mean All)

**Code naming conventions**
- Python: functions/vars **snake_case**, classes **PascalCase**.
- TypeScript/React: components **PascalCase**, variables **camelCase**.
- Shared meaning should keep the same words across layers:
  - API uses `verified_at`, frontend displays “Last checked”.

### Structure Patterns

**Backend structure**
- Routes only handle HTTP parsing/response; business logic stays in services:
  - routes: `backend/app/routes/*`
  - services: `backend/app/services/*`
  - db helpers: `backend/app/db/*`
  - repository queries: `backend/app/repositories/*`
- SQLite access pattern:
  - always use `connection(settings.db_path)` context manager

**Frontend structure**
- API calls live in `frontend/src/lib/api.ts`
- Pages in `frontend/src/pages/*`
- Reusable UI in `frontend/src/components/*`

**Tests**
- Python tests live in `backend/tests/*` and use `pytest`.

### Format Patterns

**API response wrappers**
- Table endpoints return:
  - `{ "items": [...] }`
- TableRow field names are **snake_case** (match backend):
  - `offer_id`, `provider_name`, `term_months`, `verified_at`, `source_url`

**Dates/times**
- Use ISO UTC strings with `Z` suffix for “checked”/job timestamps (e.g., `2026-05-08T10:54:24.123Z`).

**Booleans**
- SQLite stores 0/1/NULL; API exposes booleans as `true/false/null`.

### Process Patterns

**Loading / refresh**
- Tables always show: loading → results / empty → error.
- Refresh behavior:
  - after a successful refresh, force refetch by updating a `_refresh` “cache-buster” param in table fetch params.

**Error handling**
- Backend: log exceptions; do not crash the server on a single failed offer/target.
- Frontend: show a user-readable error string in the table area.

### Enforcement Guidelines (what all AI agents MUST follow)

- Keep **API param conventions** stable (`term_months=0` => All).
- Keep **response shapes stable** (`{items:[...]}`).
- Store **traceability** on every ingestion: `verified_at` + at least one `source_url`.
- Do not embed ad-hoc scraping logic in routes; keep it in services.
- Do not commit secrets (`.env` remains untracked/ignored).

### Pattern Examples

**Good examples**
- Backend table call uses:
  - `OfferQuery(term_months=None if term_months == 0 else term_months, ...)`
- Frontend “All” sends:
  - `term_months: 0`

**Anti-patterns**
- Returning table rows as a bare array (breaks contract)
- Changing query param names to camelCase
- Using “missing param” to mean “All” (inconsistent with current backend)

## Project Structure & Boundaries

### Complete Project Directory Structure

```text
Savings-Yield-Optimiser/
├── README.md
├── SOLUTION_DESIGN.md
├── solution_design.md
├── .gitignore
├── .env                       # local config (ignored by git)
├── .cursor/
│   └── rules/
│       ├── CODE_COMMENTS.mdc
│       └── PROJECT_CONTEXT.mdc
├── docs/
│   ├── system-overview.md
│   ├── bmad-prompts-epic-1.md
│   └── bmad-prompts-epic-2.md
├── _bmad-output/
│   ├── implementation-artifacts/
│   │   └── sprint-status.yaml
│   └── planning-artifacts/
│       ├── architecture.md
│       ├── architecture-uk-savings-isa-rate-tracker-sqlite-python.md
│       ├── prd-uk-savings-isa-rate-tracker.md
│       ├── project-brief-uk-savings-isa-rate-tracker.md
│       ├── epic-2-data-scrapper-agents.md
│       └── ux/
│           ├── index.md
│           ├── ux-specs-savings-yield-optimiser.md
│           ├── wireframes-savings-yield-optimiser.md
│           ├── personas-savings-yield-optimiser.md
│           └── journey-maps-savings-yield-optimiser.md
├── backend/
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── .env                   # local backend config (ignored by git)
│   ├── seed/
│   │   └── sample-uk-rates.json
│   ├── sql/
│   │   └── schema.sql
│   ├── tests/
│   │   └── test_refresh_scheduler_routing.py
│   └── app/
│       ├── main.py
│       ├── settings.py
│       ├── cli/
│       │   ├── init_db.py
│       │   ├── seed_db.py
│       │   ├── firecrawl_sample.py
│       │   ├── firecrawl_moneysupermarket.py
│       │   └── ingest_scraped_rate.py
│       ├── db/
│       │   ├── connection.py
│       │   └── bootstrap.py
│       ├── ingestion/
│       │   └── firecrawl.py
│       ├── repositories/
│       │   └── offers.py
│       ├── routes/
│       │   ├── tables.py
│       │   └── admin_refresh.py
│       ├── schemas/
│       │   └── api.py
│       └── services/
│           ├── refresh_scheduler.py
│           └── scraped_rate_ingestion.py
└── frontend/
    ├── package.json
    ├── package-lock.json
    ├── vite.config.ts
    ├── index.html
    ├── .env                   # local frontend config (ignored by git)
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── lib/
        │   └── api.ts
        ├── components/
        │   ├── FiltersBar.tsx
        │   └── RatesTable.tsx
        └── pages/
            ├── FixedRateView.tsx
            └── IsaView.tsx
```

**Runtime / generated (not part of the “source-of-truth” tree):**
- `.venv/` (Python virtual environment)
- `frontend/node_modules/`, `frontend/dist/`
- `data/app.db` (SQLite database file produced at runtime)

### Architectural Boundaries

**API boundaries (backend responsibilities)**
- **Public read API** (safe for normal users):
  - `GET /tables/fixed-savings`
  - `GET /tables/cash-isa/easy-access`
  - `GET /tables/cash-isa/fixed`
- **Admin API** (protected by `X-Admin-Token`):
  - `POST /admin/refresh`
  - `GET /admin/refresh-history`
  - `GET /admin/refresh/{job_id}` (in-memory status)

**Service boundaries (backend internal separation)**
- **Routes** (`backend/app/routes/*`): HTTP parsing + response models only
- **Repositories** (`backend/app/repositories/*`): SQL reads for tables (current snapshot queries)
- **Services** (`backend/app/services/*`):
  - refresh orchestration (targets → scrape → upsert → job tracking)
  - ingestion upsert pipeline (provider/product/offer/snapshot/source)
- **Ingestion client** (`backend/app/ingestion/*`): Firecrawl API wrapper (HTTP client + schemas)
- **DB helpers** (`backend/app/db/*`): connection + schema bootstrap

**Frontend boundaries**
- **Pages** (`frontend/src/pages/*`): page-level state (term, deposit, refresh state)
- **Components** (`frontend/src/components/*`): reusable UI blocks (filters bar, rates table)
- **API client** (`frontend/src/lib/api.ts`): all fetch calls + env config (`VITE_*`)

**Data boundaries**
- SQLite schema is owned by `backend/sql/schema.sql`
- “Current table view” is defined by `product_offer.current_snapshot_id` pointing at the current `offer_snapshot`
- Traceability links are stored via `snapshot_source → source`

### Requirements to Structure Mapping

**FR Category → Where it lives**
- **Ranked tables (Fixed Savings / Cash ISA)**:
  - Backend: `backend/app/routes/tables.py`, `backend/app/repositories/offers.py`
  - Models: `backend/app/schemas/api.py`
  - Frontend: `frontend/src/pages/*` + `frontend/src/components/RatesTable.tsx`
- **Filters (deposit, exclude restricted, term selection)**:
  - Backend filtering: `backend/app/repositories/offers.py`
  - Frontend controls: `frontend/src/components/FiltersBar.tsx`, `frontend/src/pages/*`
- **Source traceability + last checked**:
  - DB schema: `backend/sql/schema.sql`
  - API response fields: `backend/app/schemas/api.py`
  - (UX display improvements are future): data includes `verified_at` and `source_url`
- **Automated scraping + refresh controls**:
  - Firecrawl client/schema: `backend/app/ingestion/firecrawl.py`
  - Refresh orchestration: `backend/app/services/refresh_scheduler.py`
  - Upsert pipeline: `backend/app/services/scraped_rate_ingestion.py`
  - Admin API: `backend/app/routes/admin_refresh.py`
  - UI button: `frontend/src/components/FiltersBar.tsx` + refresh calls in pages
- **Job history persistence**:
  - DB: `ingestion_job_run` in `backend/sql/schema.sql`
  - Admin history API: `backend/app/routes/admin_refresh.py`

**Cross-cutting concerns → Where it is enforced**
- **Consistency rules for AI agents**:
  - `.cursor/rules/*.mdc`
  - `_bmad-output/planning-artifacts/architecture.md` (this document)
- **Secrets handling**:
  - `.gitignore` ignores `.env` files
  - Runtime config: repo root `.env`, `backend/.env`, `frontend/.env`

### Integration Points

**Internal communication**
- Frontend ↔ backend via HTTP fetch
- Refresh “refetch” uses `_refresh` param tick to invalidate table fetch memoization

**External integrations**
- Firecrawl API (requires `FIRECRAWL_API_KEY`)

**Data flow**
- Refresh job → Firecrawl scrape → normalize offers → upsert into SQLite → table endpoints serve current snapshot rows → frontend renders

## Architecture Validation Results

### Coherence Validation ✅

**Decision Compatibility:**
- The chosen stack is internally compatible: React/Vite frontend → FastAPI backend → SQLite storage.
- Firecrawl ingestion + APScheduler refresh fits the backend runtime model and avoids coupling scraping logic to request/response paths.
- Admin refresh controls align with operational needs (manual trigger + history) and do not conflict with the scheduled cadence.

**Pattern Consistency:**
- Naming and contract conventions are consistent across layers:
  - `term_months=0` sentinel for “All terms” is documented and implemented as a stable API convention.
  - Table endpoints return `{ "items": [...] }` and use `snake_case` field names.
  - “Last checked” maps to `offer_snapshot.verified_at` consistently.

**Structure Alignment:**
- Backend responsibilities are properly separated:
  - routes = HTTP boundary
  - services = orchestration + ingestion
  - repositories = read queries
  - db helpers = connection/bootstrap
- Frontend responsibilities are properly separated:
  - pages = page state/flows
  - components = reusable UI
  - `lib/api.ts` = API calls + env handling

### Requirements Coverage Validation ✅

**Epic/Feature Coverage:**
- Epic 1 table features and Epic 2 “agentic freshness” features are supported by explicit components:
  - scrape → normalize → upsert → serve tables → render tables
  - scheduled refresh + on-demand admin refresh + job history persistence

**Functional Requirements Coverage:**
- Ranked tables, term filtering (including “All”), and basic user-facing transparency (verified timestamp + source URL in data model / API) are architecturally supported.
- Admin refresh is supported end-to-end (frontend trigger → backend admin route → service orchestration → persistence).

**Non-Functional Requirements Coverage:**
- Operational safety is addressed (background job error isolation; admin token gate).
- Data provenance is addressed via `source_url` and `verified_at`.
- Performance/scalability is acceptable for the local-first scope (SQLite + periodic refresh). (No distributed scaling decisions were required for MVP.)

### Implementation Readiness Validation ✅

**Decision Completeness:**
- Critical conventions that commonly cause regressions are clearly documented:
  - query param naming + sentinel behavior
  - response wrapper shape
  - “source of truth” for shared behaviors (services vs routes, api.ts for fetch)

**Structure Completeness:**
- Project structure is complete enough for consistent changes by future AI agents.
- Integration points are explicit: frontend fetch → backend routes; refresh orchestration → Firecrawl → SQLite.

**Pattern Completeness:**
- The doc includes enforceable “do not break these contracts” rules and concrete examples (good/anti-patterns).

### Gap Analysis Results

**Critical Gaps:**
- None identified that block implementation or maintenance.

**Important Gaps:**
- **Repo structure listing drift:** Step 6 directory tree references `solution_design.md`, but the repo contains `SOLUTION_DESIGN.md` (uppercase). This can confuse future agents on Windows vs case-sensitive environments.
- **Docs accuracy:** Step 6 structure includes some “illustrative” entries (e.g., `.env` placements) that may not exist exactly as listed, and should be treated as conceptual rather than authoritative.

**Nice-to-Have Gaps:**
- Add a short “Deployment / runbook” subsection (even for local-first) that standardizes:
  - init DB → run backend → run frontend
  - recommended way to enable/disable scheduler safely
- Add a brief note on CORS expectations (frontend dev server → backend), if not already covered elsewhere.

### Validation Issues Addressed

- Identified the `SOLUTION_DESIGN.md` vs `solution_design.md` mismatch for correction (documentation-only fix).

### Architecture Completeness Checklist

Mark each item `[x]` only if validation confirms it; leave `[ ]` if it is missing, partial, or unverified. Any unchecked item must be reflected in the Gap Analysis above and in the Overall Status below.

**Requirements Analysis**

- [x] Project context thoroughly analyzed
- [x] Scale and complexity assessed
- [x] Technical constraints identified
- [x] Cross-cutting concerns mapped

**Architectural Decisions**

- [x] Critical decisions documented with versions
- [x] Technology stack fully specified
- [x] Integration patterns defined
- [x] Performance considerations addressed

**Implementation Patterns**

- [x] Naming conventions established
- [x] Structure patterns defined
- [x] Communication patterns specified
- [x] Process patterns documented

**Project Structure**

- [ ] Complete directory structure defined
- [x] Component boundaries established
- [x] Integration points mapped
- [x] Requirements to structure mapping complete

### Architecture Readiness Assessment

**Overall Status:** READY WITH MINOR GAPS

**Confidence Level:** high

**Key Strengths:**
- Clear separation of responsibilities across routes/services/repositories and pages/components/api client
- Stable, explicit API contracts (`term_months=0`, `{items:[...]}`, snake_case)
- Traceability baked into the model (`verified_at`, `source_url`)
- Refresh orchestration designed to be robust (scheduled + on-demand + persisted job history)

**Areas for Future Enhancement:**
- Tighten the “directory structure” section to match the repo exactly (reduce confusion)
- Add a minimal local runbook + CORS note for smoother onboarding

### Implementation Handoff

**AI Agent Guidelines:**
- Follow all architectural decisions exactly as documented
- Do not change sentinel/contract behaviors (`term_months=0`, `{items:[...]}`, snake_case)
- Keep scraping/refresh logic in services; keep routes thin
- Use `frontend/src/lib/api.ts` as the single source of truth for HTTP calls

**First Implementation Priority:**
- Documentation-only cleanup: make the Step 6 “Complete Project Directory Structure” reflect the repo accurately (e.g., `SOLUTION_DESIGN.md` casing) so future agents don’t drift.

