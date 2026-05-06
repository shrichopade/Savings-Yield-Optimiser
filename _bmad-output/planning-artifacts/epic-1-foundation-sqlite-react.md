# Epic 1: Foundation — SQLite database + basic React tables

## Goal
Establish a local-first foundation that can persist UK savings/ISA product data in SQLite and render basic fixed savings + Cash ISA tables in a React UI.

## Stories
### Story 1.1: Add SQLite schema + bootstrap
- Add SQLite DDL file to repo (checked-in schema)
- Create database bootstrap routine (create tables, set pragmas, schema_version)
- Provide a simple CLI command to initialise a local DB file

### Story 1.2: Python backend skeleton for local data management
- Create a minimal Python backend structure (packages/modules)
- Implement DB connection management + pragmas (foreign_keys, WAL)
- Add repository/service layers for offers and snapshots (read paths only for now)

### Story 1.3: Seed data loader (local JSON/CSV → SQLite)
- Define a canonical seed format (JSON recommended) for providers/products/offers/snapshots
- Implement `seed` CLI to load sample data into SQLite
- Ensure source URL + last checked are populated for seeded records

### Story 1.4: Table query endpoints (fixed savings + cash ISA)
- Implement read-only endpoints for:
  - fixed savings table by term
  - cash ISA easy access table
  - cash ISA fixed table by term
- Implement filtering: deposit amount + exclude restricted deals
- Implement ranking: AER desc + restriction tie-breaker

### Story 1.5: React app scaffold + routing
- Create React app scaffold
- Add routes/pages for:
  - Fixed Savings Table
  - Cash ISA (Easy Access) Table
  - Cash ISA (Fixed) Table

### Story 1.6: React table UI (MVP fields)
- Render basic table columns per PRD (Provider, Product, AER, term, min/max, last checked, source link)
- Add “Gotchas” badges column (bonus/penalty/eligibility/transfer/flexible flags)
- Add row expand/details panel (lightweight)

### Story 1.7: Filters UI + API wiring
- Add deposit amount input and “exclude restricted deals” toggle
- Wire filters to backend endpoints (or mocked API client if backend not running yet)
- Display exclusions summary (“excluded N due to min deposit…”)

### Story 1.8: Basic styling + accessibility pass
- Sticky table header, keyboard navigation
- Ensure readable “Why ranked?” text and last-updated indicators

