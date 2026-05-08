# Epic 2: Data Scraper Agents — Firecrawl ingestion + refresh workflows

## Goal
Add an automated, “agentic” data collection capability that keeps UK savings and Cash ISA rates fresh by scraping approved UK comparison/editorial-aggregation sources (and linking to provider pages where feasible), updating SQLite on a **6-hour cadence**, and providing an **admin on-demand refresh** in the UI.

## Stories
### Story 2.1: Firecrawl integration + scraper base abstractions
- Add Firecrawl client configuration (API key via environment/config)
- Define canonical scraper interfaces:
  - fetch/extract page content
  - parse extracted content into a normalized “offer observation” model
  - emit structured outputs for persistence (provider/product/offer/snapshot + sources)
- Add a minimal “health” command to validate Firecrawl connectivity locally

### Story 2.2: Target a first UK comparison site and extract table rows (Moneyfacts or MoneySavingExpert)
- Select one initial target site/page(s) for:
  - fixed savings (by term bucket), and/or
  - cash ISA easy access, and/or
  - cash ISA fixed (by term bucket)
- Implement parser to extract:
  - provider name, product name, AER, term (if applicable), basic constraints (min/max) when present
  - at least one **source URL** (the page scraped), and a best-effort **provider product URL** if present on the page
- Add fixtures / sample captured responses (or stored HTML/text) for regression testing of parsers

### Story 2.3: SQLite upsert pipeline for scraped observations (Last Checked + source hierarchy)
- Convert parsed observations into the existing normalized schema:
  - upsert `provider` / `product` / `product_offer`
  - insert immutable `offer_snapshot` with `verified_at` as “Last Checked”
  - create `source` rows and `snapshot_source` links
- Store source-of-truth metadata via `source.source_type`:
  - `comparison_site` for aggregation pages
  - `provider_page` for provider product pages (when available)
- Ensure idempotency (re-running a scrape does not duplicate snapshots unless `verified_at` differs)

### Story 2.4: Background refresh service (6-hour cadence + daily full refresh)
- Implement a refresh runner that can be executed:
  - as a CLI command (recommended for local-first)
  - on a schedule every 6 hours
  - with a daily full refresh mode
- Add a single-run locking mechanism to prevent concurrent refresh runs
- Record refresh outcomes (at least log; preferably persist job runs for UI status)

### Story 2.5: FastAPI admin endpoints to trigger and observe refresh jobs
- Add `POST /admin/refresh` to trigger an on-demand refresh
- Add `GET /admin/refresh/{job_run_id}` to check job status
- Gate endpoints as admin-only (MVP-safe approach: shared secret header or config-gated)

### Story 2.6: Frontend admin refresh button + basic job status UI
- Add an admin-only “Refresh rates now” button
- On click:
  - call `POST /admin/refresh`
  - poll job status until complete
  - refetch table endpoints and update “Last checked” display
- Provide basic UI states: idle / running / success / error

