# Project Brief — UK Savings & ISA Rate Tracker

## 1) Purpose / one-liner
Build a trustworthy tracker that helps UK consumers quickly find and compare the **best fixed savings rates** and **best cash ISA rates** from UK banks and building societies, based on *their* deposit size, term, access needs, and eligibility.

## 2) Problem statement
UK savings products are hard to compare because:
- Rates change frequently and providers launch/withdraw products with little notice.
- “Best rate” depends on constraints (term, min deposit, access, ISA rules, bonus periods, eligibility, payout frequency).
- Product pages bury critical terms (withdrawal penalties, maturity handling, transfer-in rules, restrictions on new vs existing customers).

## 3) Target users
- **Rate optimisers**: want the highest AER for a specific term (e.g., 1-year fixed).
- **ISA maximisers**: want best Cash ISA AER with clear transfer-in, flexible ISA, and access rules.
- **Safety-first savers**: care about FSCS protection and institution type.
- **Busy comparers**: want quick “top 5” with the key gotchas surfaced.

## 4) Scope (MVP)
### 4.1 Core product coverage
- **Fixed savings accounts** (fixed-rate bonds): common terms (e.g., 3/6/9/12/18/24/36/60 months).
- **Cash ISAs**:
  - Easy access Cash ISA
  - Fixed-rate Cash ISA
  - Notice Cash ISA (if feasible in MVP, otherwise phase 2)

### 4.2 Key outcome
Show the user **ranked lists** of products that are *actually comparable*, with enough terms/eligibility information to make a confident shortlist.

## 5) Key features (what we must build to “show the best rates”)
### 5.1 Rate discovery & catalog
- **Product database**: structured records per product with full terms metadata (see Section 7).
- **Source traceability**: store source URL(s), last-checked timestamp, and change history for each product/rate.
- **Automated data collection (agentic freshness)**:
  - **Primary targets (phase 1)**: UK savings comparison / editorial-aggregation sites such as **Moneyfacts** and **MoneySavingExpert** (and similar), used to discover and monitor rate movements quickly.
  - **Source-of-truth policy**: comparison sites are used for *discovery + monitoring*; whenever feasible, persist a link to the **provider’s official product page** and treat it as the authoritative reference for terms that materially affect comparability (penalties, eligibility, funding windows, transfer rules).
  - **Fetch cadence** (MVP recommendation):
    - Run a scheduled scrape **every 6 hours** (4×/day) for target comparison pages (keeps the app “agentic” without over-polling).
    - Add a **daily** (1×/day) “full refresh” job that re-validates active products and marks withdrawn/removed items.
    - Allow an **on-demand** manual refresh (admin-only) for debugging and rapid verification after schema or parser changes.
  - **Freshness SLA surfaced in UI**:
    - Show “Last checked” timestamps per table/category.
    - Target **median freshness ≤ 6 hours** for tracked categories; flag if last check exceeds **24 hours**.
- **Update workflow**:
  - Detect changes (rate/terms) and mark products as updated.
  - Handle withdrawals/closures: preserve history; mark as unavailable.

### 5.2 Comparison & ranking UX
- **Top lists by category**:
  - Fixed savings (by term)
  - Cash ISA easy access
  - Cash ISA fixed (by term)
- **Filter controls** (minimum set):
  - Deposit amount (min/max eligibility)
  - Term (for fixed)
  - Access type (easy access vs notice vs fixed)
  - Payout frequency (monthly/annual; if it affects suitability)
  - Provider type (bank/building society) and/or FSCS notes (where known)
  - Customer eligibility (e.g., new customers only) — at least a toggle to include/exclude restricted deals
- **Comparison view**:
  - “Why this is ranked here” explainer: highlights the AER and any ranking-adjusting constraints (bonus expiry, penalties, min deposit).
  - Side-by-side key fields (AER, term, min deposit, withdrawals/penalties, payout, eligibility, opening method).

### 5.3 “Gotchas” surfaced prominently
To avoid misleading “best rate” lists, each result card should clearly surface:
- **Bonus/intro rate**: amount and duration; what happens after expiry (reversion rate).
- **Withdrawal penalties / restrictions**: allowed withdrawals, penalty formula, loss of interest, account closure risk.
- **Eligibility restrictions**: residency, age, “new money”, existing customer restrictions, bundle requirements.
- **ISA transfer rules** (for ISAs): transfer-in supported? partial transfers? time to transfer? flexible ISA?
- **Deposit constraints**: min initial, min ongoing, max balance, funding window.

### 5.4 Alerts & monitoring (MVP-light)
- **Rate change alerts**: user can watch a product or category/term and get notified when a better rate appears or a watched product changes/withdraws.
- Start with **email** or **in-app list**; allow multiple alert rules later.

### 5.5 Provider pages (trust and navigation)
For each provider/institution:
- List active products, recent changes, and any notable constraints.
- Link to official product pages and source references.

## 6) Out of scope (initially)
- Stocks & Shares ISAs / Lifetime ISAs
- Personalised financial advice or suitability scoring beyond rule-based constraints
- Full application journey (we link out; we do not open accounts)
- Open Banking integrations

## 7) Data model — minimum fields required to rank and compare correctly
### 7.1 Common fields (all products)
- **Provider**: name, brand, legal entity (if known), type (bank/building society)
- **Product identifiers**: internal id, product name, product type (fixed savings / cash ISA), variant tags (easy access / notice / fixed ISA)
- **Rate fields**:
  - AER (%)
  - Gross rate (%), if published
  - Rate structure: fixed / variable / tracker-like
  - Bonus/intro: bonus amount, start/end conditions, expiry date/duration, post-bonus reversion rate
- **Interest mechanics**:
  - Interest payment frequency (monthly/annual/at maturity)
  - Compounding assumptions (where relevant)
- **Balances & funding**:
  - Minimum opening deposit
  - Minimum ongoing balance (if any)
  - Maximum balance
  - Funding window (e.g., “must fund within 14 days”)
- **Access & penalties**:
  - Withdrawals allowed? (Y/N/limited)
  - Notice period (if notice product)
  - Penalty model (e.g., X days’ interest; loss of interest; forfeiture rules)
  - Early closure allowed? (Y/N)
- **Eligibility**:
  - UK residency requirement (Y/N/unknown)
  - Age constraints
  - New customer only (Y/N)
  - “New money” requirement (Y/N)
  - Other gating requirements (current account needed, membership, postcode, etc.)
- **Channels**:
  - Open method (online/app/branch/post)
  - Managed via (online/app/branch)
- **Safety / trust**:
  - FSCS protected? (Y/N/unknown)
  - FSCS license grouping notes (where known)
- **Operational metadata**:
  - Source URL(s)
  - Last verified timestamp
  - Status (active / withdrawn / unknown)

### 7.2 Fixed savings-specific fields
- **Term length** (months)
- **Maturity handling**:
  - At maturity options (auto-renew / move to easy access / pay out)
  - Grace period length (if known)
- **Deposits during term**: allowed (Y/N)

### 7.3 Cash ISA-specific fields
- **ISA subtype**: easy access / fixed / notice
- **Flexible ISA**: Y/N
- **Transfers in**:
  - Transfer-in supported (Y/N)
  - Partial transfers allowed (Y/N)
  - Transfer-out restrictions (if any)
- **Subscriptions**:
  - Pay in by debit card/bank transfer/standing order (where relevant)
  - Funding window for fixed ISA

## 8) Ranking logic (how we define “best”)
### 8.1 Primary sorting
- Default ranking within a comparable set uses **highest AER** first.

### 8.2 Comparability rules (to keep lists honest)
Products should only be ranked together when core constraints match:
- Fixed savings: same **term bucket** (e.g., 12-month fixed vs 24-month fixed).
- Fixed cash ISA: same **term bucket**.
- Easy access cash ISA: grouped separately from fixed/notice.

### 8.3 Ranking adjustments (MVP rules)
Apply consistent, transparent tie-breakers:
- Exclude products that **do not accept the user’s deposit amount** (min/max).
- Prefer products with **no bonus** over bonus-driven rates when the user selects “long-term rate stability” (optional toggle).
- Where a rate is “up to” or conditional, mark as conditional and rank below unconditional rates unless the condition can be verified by the user via an explicit filter.
- Tie-breakers (in order, suggested):
  1. Higher AER
  2. Fewer eligibility restrictions
  3. Better access terms (for “access-friendly” views)
  4. Better interest payout preference match (monthly vs annual)

### 8.4 Transparency requirement
Every ranked list must show:
- **Basis**: “Ranked by AER for your selected term and deposit.”
- **Exclusions**: a clear explanation when items are hidden due to deposit/eligibility filters.

## 9) Trust, compliance, and disclaimers (non-negotiable)
- Clearly state this is **information and comparison**, **not financial advice**.
- Show **last updated** times and sources.
- Avoid misleading “best” claims without context; always qualify by the chosen filters (term, deposit, ISA type).

## 10) Success metrics
- **Coverage**: % of top providers/products in target categories captured.
- **Freshness**: median time from change detected on monitored sources → tracker update (target ≤ 6 hours).
- **User utility**: clicks to provider, shortlist creation, alert subscriptions.
- **Accuracy**: low rate of user-reported incorrect terms; audit pass rate.

## 11) Risks & open questions
- **Data accuracy & maintenance**: rate pages change formats; need robust monitoring and verification.
- **Scraping reliability & compliance**: robots.txt / ToS constraints, rate limits, and page format drift require resilient extraction and fallbacks.
- **Aggregator vs provider mismatch**: comparison sites may lag or simplify terms; need an explicit policy for reconciling conflicts and marking uncertain fields as “unknown” rather than guessing.
- **FSCS grouping complexity**: brands share licenses; may require curated mapping.
- **ISA rule nuance**: transfer/partial transfer rules vary and can be confusing; must be carefully sourced.
- Open questions to resolve early:
  - Primary sources: provider websites only, or also FCA register / trusted aggregators?
  - Update cadence SLA (hourly/daily) for “best rate” credibility.
  - How to handle “exclusive”/member-only deals (include with eligibility filters?).

## 12) Next steps (recommended)
- Finalise MVP categories and comparability rules (Section 8).
- Define canonical term buckets and filtering UX.
- Implement the product schema and ingestion/update pipeline.
- Build ranking endpoints + “why ranked” explanations in the UI.

