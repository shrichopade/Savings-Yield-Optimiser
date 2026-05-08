# PRD — UK Savings & Cash ISA Rate Tracker

## 1) Summary
### 1.1 One-liner
Help UK consumers find and compare the **best fixed savings rates** and **best cash ISA rates** with transparent ranking, eligibility-aware filtering, and “gotchas” surfaced.

### 1.2 Problem
Rates and terms change frequently, and “best” depends on term, deposit limits, access/penalties, and eligibility. Users need a credible, up-to-date ranked view that avoids misleading comparisons.

### 1.3 Goals
- Provide **ranked tables** for fixed-rate savings and Cash ISAs that remain honest through comparability rules.
- Enable users to **filter by deposit, term, and eligibility** so results are actionable.
- Surface critical **constraints/gotchas** (bonus expiry, penalties, ISA transfer rules) directly in the table.
- Show **sources** and “last checked” timestamps to build trust.
- Keep rates **agentically fresh** via automated scraping + a background refresh cadence, with an admin on-demand refresh for verification.

### 1.4 Non-goals (MVP)
- Stocks & Shares ISA / Lifetime ISA
- Account opening journey (link-out only)
- Personalised financial advice
- Open Banking integration

## 2) Users & use cases
### 2.1 Primary user types
- **Rate optimisers**: pick highest AER for a specific fixed term.
- **ISA maximisers**: highest Cash ISA AER with clear transfer-in/flexible rules.
- **Safety-first savers**: care about FSCS and institution credibility.
- **Busy comparers**: want top picks with key caveats up front.

### 2.2 Primary jobs-to-be-done
- “Show me the best 12‑month fixed savings rates I can actually open with £X.”
- “Show me the best easy access Cash ISA rates, and whether I can transfer in.”
- “Explain why this is ranked above that (bonus, penalties, restrictions).”

## 3) Scope
### 3.1 MVP product types
- **Fixed savings** (fixed-rate bonds) — term buckets: 3/6/9/12/18/24/36/60 months (configurable).
- **Cash ISA**:
  - Easy access Cash ISA
  - Fixed-rate Cash ISA — same term buckets as fixed savings
  - Notice Cash ISA (phase 2 unless already easy to support)

### 3.2 MVP surfaces
- **Tables** for:
  - Fixed savings (by term)
  - Cash ISA easy access
  - Cash ISA fixed (by term)
- **Product detail view** (lightweight) or expandable row details.
- **Provider view** (lightweight): provider + active products + source links.

## 4) Functional requirements
### FR1 — Fixed-rate savings table (by term)
- Users can select a **term bucket** and see a **ranked table** of fixed savings products.
- Ranking basis: **highest AER first** among comparable products in that term bucket.
- Each row shows: Provider, Product name, AER, term, min deposit, max balance, payout frequency, access/penalty indicator, eligibility indicator, last checked timestamp, source link.
- “Gotchas” shown in-table via chips/badges and expandable detail (see FR5).

### FR2 — Cash ISA easy access table
- Users can view a **ranked table** of easy access Cash ISA products.
- Ranking basis: **highest AER first**, with clear flags for conditional/bonus rates.
- Each row shows: Provider, Product name, AER, access constraints, flexible ISA (Y/N/unknown), transfer-in supported (Y/N/unknown), min/max balance, eligibility, last checked timestamp, source link.

### FR3 — Cash ISA fixed table (by term)
- Users can select a **term bucket** and see a ranked table of fixed-rate Cash ISA products.
- Each row includes: AER, term, funding window (if any), penalty model indicator, transfer-in rules indicator, flexible ISA (typically N), last checked + source.

### FR4 — Filters (apply across tables where relevant)
Minimum filters:
- **Deposit amount** (numeric input): hide products where user deposit is outside min/max constraints.
- **Eligibility toggle**: include/exclude products with restrictions (e.g., new customers only / membership).
- **Payout frequency** (optional in MVP if data reliable): monthly / annual / at maturity.
- **Access type** (for ISA scope navigation): easy access vs fixed (notice optional).
- **Provider type / FSCS notes** (display-first, filter-second): filter only if we have reliable data.

### FR5 — “Gotchas” and transparency
Each product row must expose (in-row badges + details panel):
- Bonus/intro rate and **expiry / reversion rate** (if applicable).
- **Withdrawal penalties/restrictions** (days’ interest penalty, withdrawals allowed).
- **Eligibility restrictions** (new customer only, residency, membership, “new money”).
- ISA transfer rules (transfer-in supported; partial transfers; transfer-out restrictions) for ISAs.
- Deposit constraints (min opening, max balance, funding window).

### FR6 — Comparability rules & exclusions messaging
- Only rank together products that match the table’s **category + term bucket**.
- When filters exclude items, show:
  - count excluded
  - a short explanation (e.g., “Excluded 12 products due to min deposit > £X”)
- Conditional / “up to” rates:
  - clearly labelled
  - ranked below unconditional rates unless user explicitly filters to include conditional deals.

### FR7 — Product detail / row expand
- Clicking a row opens a detail panel/page containing:
  - Full terms captured in the schema (see Section 7)
  - Source URL(s)
  - Last checked timestamp
  - Change history (phase 2 if needed, but store the data)

### FR8 — Source traceability & freshness
- Every product record stores:
  - source URL(s)
  - last verified (“last checked”) timestamp
  - status (active/withdrawn/unknown)
- UI shows **“Last checked”** per product and a page-level “data last updated”.

### FR10 — Automated data collection (Firecrawl) + refresh controls
- The system must support automated collection of rates/terms from UK financial comparison/editorial-aggregation pages using **Firecrawl** (e.g., Moneyfacts / MoneySavingExpert category pages) to discover and monitor rate movements.
- The system must maintain a **source-of-truth hierarchy**:
  - Comparison sites are used for discovery/monitoring and to link users out.
  - Whenever feasible, store and prefer the **provider’s official product page** as the authoritative source for terms that affect comparability (penalties, eligibility, funding windows, ISA transfer rules).
- The system must run a background refresh job on a **6-hour cadence** (4×/day) for monitored comparison pages.
- The system must run a **daily full refresh** job that re-validates active products and marks withdrawn/removed items.
- The UI must include an **admin-only** control to trigger an **on-demand refresh** (manual scrape run) and surface job status (started/running/succeeded/failed) at least in basic form.

### FR9 — Alerts (MVP-light)
- Users can create an alert for:
  - a **category/term** (e.g., “12‑month fixed savings”) when a higher AER appears
  - a **specific product** when its AER/terms change or it withdraws
- Alert delivery: in-app list or email (implementation choice).

## 5) Non-functional requirements
- **Accuracy first**: rankings must be reproducible from stored fields and filters.
- **Performance**: tables load in < 2s for typical usage.
- **Auditability**: each displayed data point must map to a stored field with a source reference.
- **Accessibility**: tables navigable via keyboard; screen-reader-friendly labels.
- **Operational safety**: background refresh must be idempotent, rate-limited, and resilient to source page format changes (fail gracefully; never corrupt existing known-good data).

## 6) UX requirements (table behaviours)
- Default sort: **AER desc**.
- Secondary sorting (tie-breakers, when AER equal):
  1. fewer restrictions (eligibility)
  2. better access terms (for access-focused views)
  3. payout match (if user selected)
- Table controls:
  - sticky header
  - column for “Gotchas” badges
  - “Why ranked?” tooltip or inline explanation text at top:
    - “Ranked by AER for your selected term and deposit; conditional rates labelled.”

## 7) Data requirements (minimum schema for MVP)
Store enough data to support honest ranking and comparison.

### 7.1 Common fields
- Provider: name, type (bank/building society), FSCS protected (Y/N/unknown), FSCS notes (optional)
- Product identifiers: internal id, product name, product type, variant tags
- Rate: AER, gross rate (optional), fixed/variable, conditional flag
- Bonus/intro: bonus amount, duration/expiry, reversion rate
- Interest: payout frequency, compounding assumption (if needed)
- Balances: min opening deposit, min ongoing, max balance, funding window
- Access: withdrawals allowed, notice period, penalty model, early closure allowed
- Eligibility: residency, age, new customer only, new money, other requirements
- Channels: open method, managed via
- Operational: source URLs, last verified timestamp, status

### 7.2 Fixed savings-specific
- Term length (months)
- Deposits during term allowed (Y/N)
- Maturity handling + grace period (if available)

### 7.3 Cash ISA-specific
- ISA subtype (easy access/fixed/notice)
- Flexible ISA (Y/N/unknown)
- Transfers: transfer-in supported, partial transfers allowed, transfer-out restrictions
- Subscriptions/funding window for fixed ISA

## 8) User stories (focus: viewing fixed-rate and ISA tables)
### 8.1 Fixed-rate savings table stories
- **US-FIXED-01 (View table)**: As a saver, I want to view a table of fixed-rate savings products for a chosen term so I can see the top rates quickly.
  - Acceptance:
    - Term selector changes the comparable set and refreshes the table.
    - Table is sorted by AER descending by default.
- **US-FIXED-02 (Deposit filter)**: As a saver, I want to enter my deposit amount so I only see products I’m eligible for based on min/max balance rules.
  - Acceptance:
    - Products outside min/max are hidden.
    - Exclusions message shows how many were removed and why.
- **US-FIXED-03 (Eligibility toggle)**: As a saver, I want to exclude “restricted” deals (e.g., new customers only) so I only see broadly available products.
  - Acceptance:
    - Toggle updates results immediately.
    - Restricted products are clearly flagged when included.
- **US-FIXED-04 (Gotchas visibility)**: As a saver, I want to see key penalties and bonus details without leaving the table so I don’t pick a misleading “best” rate.
  - Acceptance:
    - Bonus and penalty indicators appear on each row when applicable.
    - Expanding a row shows bonus expiry/reversion and penalty model details (when known).
- **US-FIXED-05 (Source & freshness)**: As a saver, I want to see when a product was last checked and the source link so I can trust and verify the information.
  - Acceptance:
    - Each row shows last checked date/time.
    - Each row has at least one source link.

### 8.2 Cash ISA tables stories (easy access + fixed)
- **US-ISA-01 (View easy access ISA table)**: As an ISA saver, I want a table of easy access Cash ISAs ranked by AER so I can quickly shortlist options.
  - Acceptance:
    - Easy access ISA table is separate from fixed ISA tables.
    - Conditional/bonus rates are labelled.
- **US-ISA-02 (View fixed ISA by term)**: As an ISA saver, I want to choose a fixed ISA term and see a ranked table so I can match my time horizon.
  - Acceptance:
    - Term selection changes comparable set.
    - Fixed ISA table displays term and penalty indicator.
- **US-ISA-03 (Transfer-in clarity)**: As an ISA saver, I want to see transfer-in support and partial transfer rules so I can understand if I can move my existing ISA.
  - Acceptance:
    - Row shows transfer-in supported (Y/N/unknown) and partial transfer allowed (Y/N/unknown) when available.
    - Details view links to source text where possible.
- **US-ISA-04 (Flexible ISA flag)**: As an ISA saver, I want to know if an ISA is flexible so I can withdraw and replace funds correctly (when applicable).
  - Acceptance:
    - Row displays flexible ISA status (Y/N/unknown).
- **US-ISA-05 (Deposit + eligibility filters)**: As an ISA saver, I want the same deposit/eligibility filtering controls so the ranked table reflects what I can open.
  - Acceptance:
    - Deposit filter excludes min/max mismatches.
    - Eligibility toggle excludes restricted deals.

### 8.3 Cross-table stories
- **US-TABLE-01 (Sort control, optional MVP)**: As a user, I want to sort by AER or provider name so I can scan results my way.
  - Acceptance:
    - Default is AER desc; user can change sort and revert.
- **US-TABLE-02 (Why ranked)**: As a user, I want a short explanation of how ranking works so I understand what “best” means on this page.
  - Acceptance:
    - A visible statement explains ranking basis and comparability constraints.

### 8.4 Admin stories (Epic 2 enablement)
- **US-ADMIN-01 (On-demand refresh)**: As an admin, I want a button to trigger an on-demand refresh so I can validate new parsers/sources and force an update after known rate moves.
  - Acceptance:
    - Control is not visible to non-admin users.
    - Trigger returns an acknowledgement and basic job status (e.g., queued/running/succeeded/failed).
    - A subsequent table visit reflects updated “last checked” timestamps after a successful run.

## 9) Assumptions
- Automated scraping will use **Firecrawl** for monitored comparison/editorial-aggregation pages.
- Source-of-truth preference is **provider product pages** (when available), with comparison sites used for discovery/monitoring and link-out.
- All displayed values must link back to at least one stored source URL.
- MVP can start with a limited provider set as long as the schema + ranking logic are correct.

## 10) Open questions
- Do we include notice ISAs in MVP or phase 2?
- Do we support payout frequency filtering in MVP (depends on data availability)?

## 11) Milestones (suggested)
- M1: Schema + ingestion + “last checked” + source links
- M2: Fixed savings table + filters + gotchas + comparability rules
- M3: Cash ISA tables (easy access + fixed) + transfer/flexible flags
- M4: Alerts (category + product)

