# UX Specs — Savings Yield Optimiser

Status: reflects the current implemented UI + intended UX direction.

---

## 1) Product promise (what the UX must deliver)

Users come here to answer: **“What’s the best rate I can realistically get, given my term, deposit, and restrictions?”**

The UX must feel:
- **Fast**: the “best” offers are visible immediately
- **Trustworthy**: show *Last checked* + *Source link* for every row
- **Honest**: never compare apples to oranges (term bucket + category comparability)
- **Actionable**: filters match user intent (deposit bounds, restricted-deals toggle)

---

## 2) Information architecture (current MVP)

### 2.1 Primary navigation
- **Fixed Rate**
- **ISA**

### 2.2 Pages and core content blocks

#### Fixed Rate page
- Header: page title + **Term selector** (including **All**)
- Filters bar:
  - Deposit (£)
  - Exclude restricted deals (checkbox)
  - (Admin-only) Refresh Live Rates button + status text
- Table: Fixed savings offers, ranked by AER

#### ISA page
- Header: page title + **Fixed ISA term selector** (including **All**)
- Filters bar:
  - Deposit (£)
  - Exclude restricted deals (checkbox)
  - (Admin-only) Refresh Live Rates button + status text
- Table A: Easy Access Cash ISA offers
- Table B: Fixed Cash ISA offers (term-filtered)

---

## 3) Core UX behaviors (MVP)

### 3.1 Ranking model (user-facing)
The UI should communicate:
- **Ranked by AER** within the selected comparable set (category + term)
- **Restricted deals** can be excluded via a toggle

### 3.2 “All terms” behavior
When a user selects **All**:
- We show mixed-term offers in one table.
- The **Term** column becomes crucial (so users can still interpret results).
- Backend convention: `term_months=0` means **no term filter**.

### 3.3 Deposit filter
Deposit is entered as free text, but should be treated as:
- A number in GBP
- Used to filter out offers where min/max balance excludes the deposit

UX notes:
- If deposit is blank → no deposit filtering
- If deposit is invalid (non-numeric) → treat as blank and show a gentle message (future enhancement)

### 3.4 Exclude restricted deals
Interpretation (MVP):
- Exclude offers flagged as `new_customer_only` or `new_money_required`

UX notes:
- Toggle must be visible and understandable
- “Restricted” should be defined in help text in a future iteration

---

## 4) Admin refresh UX (MVP)

### 4.1 Visibility rule
- The refresh button is shown **only** when a frontend admin token is configured.

### 4.2 Interaction
On click:
- Show a loading state: “Refreshing…”
- When complete:
  - show “Live rates refreshed.”
  - refresh tables automatically
- On failure:
  - show “Refresh failed…”

### 4.3 Success criteria (user perception)
- Users see “Last checked” update quickly after refresh
- Tables re-render without manual reload

---

## 5) States & edge cases (what the UI must handle)

### 5.1 Loading
- Each table shows “Loading…” while fetching.

### 5.2 Empty results
- “No results.”
  - Common causes: deposit filter too strict, restricted toggle on, no scraped data yet

### 5.3 Errors
- Show the error message in the table area
- Recommend checking backend health + admin token config (future improvement: link to docs)

---

## 6) Accessibility & content guidelines

### 6.1 Accessibility
- Inputs have labels
- Term controls should be keyboard reachable
- Tables use `<th scope="col">` and a screen-reader caption

### 6.2 Plain language
Use wording that matches how people think:
- “Deposit (£)” (not “deposit_gbp”)
- “Exclude restricted deals” (define later)
- “Last checked” (not “verified_at”)

---

## 7) Next UX improvements (recommended)

High-impact improvements that align with the PRD:
- Add a small **“Why ranked?”** explainer above each table
- Display **Last checked** and **Source** columns explicitly (not only stored)
- Add “Gotchas” badges (bonus/conditional/withdrawal restrictions) when data quality allows
- Add a compact **admin refresh history** view (from `ingestion_job_run`)

