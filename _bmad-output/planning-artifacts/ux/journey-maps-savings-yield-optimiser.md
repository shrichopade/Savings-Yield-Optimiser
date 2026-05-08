# Journey Maps (Retrospective) — Savings Yield Optimiser

These journeys cover the main flows in the current MVP and highlight friction points + opportunities.

---

## Journey A — Fixed Rate saver finds best 12‑month bond

### Steps (happy path)
1. **Arrive** on Fixed Rate page
2. Select **Term = 12 months**
3. Enter **Deposit (£)**
4. Toggle **Exclude restricted deals** (optional)
5. Scan ranked table by **AER**
6. Click **Source link** to verify
7. Decide shortlist

### Feelings
- Hopeful → focused → confident (when source + last checked are present)

### Pain points (today)
- “Why ranked?” not explicitly stated above the table (implicit)
- Last checked + source are present in data, but UX could emphasize them more

### Opportunities (next)
- Add “Ranked by AER for selected term + deposit” microcopy
- Surface Last checked + Source as explicit columns

---

## Journey B — ISA maximiser compares easy access vs fixed ISA

### Steps (happy path)
1. Go to **ISA** page
2. Scan **Easy Access** table (default)
3. Enter **Deposit (£)** to remove irrelevant offers
4. Toggle **Exclude restricted deals** (optional)
5. Move to **Fixed ISA** table and select a term (or All)
6. Open provider pages from sources to confirm transfer terms (future enhancement)

### Feelings
- Curious → cautious → needs reassurance

### Pain points (today)
- ISA “gotchas” (transfer rules, flexible ISA) are not yet displayed in the table

### Opportunities (next)
- Add badges/columns for transfer-in + flexible ISA when reliable data exists

---

## Journey C — Admin refreshes data after hearing “rates changed”

### Steps (happy path)
1. Open either page (Fixed Rate / ISA)
2. Click **Refresh Live Rates**
3. See loading feedback (“Refreshing…”)
4. Refresh completes; tables auto-refetch
5. Confirm **Last checked** moved forward

### Feelings
- Responsible → impatient → relief (or stress on failure)

### Pain points (today)
- Failure feedback exists, but deeper error detail is only in backend logs
- Refresh history exists in SQLite, but not yet shown in the UI

### Opportunities (next)
- Add a small “Last refresh: succeeded/failed at …” status panel using `ingestion_job_run`

---

## Journey D — Safety-first saver verifies provenance

### Steps (happy path)
1. Open a table
2. Check Last checked
3. Click Source link
4. Decide whether to trust and proceed

### Pain points (today)
- Trust signals (e.g., FSCS, provider type) are not prominent

### Opportunities (next)
- Add a “Trust” column with FSCS known/unknown and provider type (when available)

