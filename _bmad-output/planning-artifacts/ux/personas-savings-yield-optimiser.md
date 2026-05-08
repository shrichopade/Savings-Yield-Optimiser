# Personas (Retrospective) — Savings Yield Optimiser

These personas are derived from the PRD user types and the product’s current MVP surfaces.

---

## Persona 1 — “Rate Optimiser”

### Snapshot
- **Who**: UK saver comparing fixed-term savings bonds
- **Goal**: Highest AER for a specific term (e.g., 12 or 24 months)
- **Context**: Checks rates during short decision windows (payday, maturity dates)

### Primary needs
- Quick **term selection**
- Clear **ranking by AER**
- Confidence that deposit constraints won’t block opening
- Proof: **Last checked** + **Source**

### Frustrations
- “Best rate” lists that ignore deposit minimums
- Hidden restrictions (“new customers only”) discovered late

### MVP tasks
- Pick term → enter deposit → exclude restricted → shortlist top 3 → click source to verify

---

## Persona 2 — “ISA Maximiser”

### Snapshot
- **Who**: UK saver optimizing Cash ISA returns
- **Goal**: Best easy access ISA or best fixed ISA for a chosen term
- **Context**: Often comparing across multiple tabs/tools; wants fast scanning

### Primary needs
- Clear separation between:
  - **Easy access ISA** table
  - **Fixed ISA** table by term
- “All terms” option for discovery
- Proof: **Last checked** + **Source**

### Frustrations
- ISA product terms are hard to interpret; comparison sites may be stale
- Confusing naming (product labels change across sources)

### MVP tasks
- Compare easy access ISA table → switch to fixed ISA table → select term → verify on provider site

---

## Persona 3 — “Safety-first Saver”

### Snapshot
- **Who**: UK saver who prioritizes safety and legitimacy over tiny rate differences
- **Goal**: Only consider reputable providers; verify claims
- **Context**: More cautious; wants signals of trust and traceability

### Primary needs
- Visible **source links**
- Visible **Last checked** timestamps (freshness)
- (Future) FSCS and provider notes surfaced cleanly

### Frustrations
- Unclear provenance of displayed rates
- Stale data presented as current

### MVP tasks
- Use table → verify source → decide whether to trust the listing

---

## Persona 4 — “Admin / Maintainer”

### Snapshot
- **Who**: the project owner/operator (local-first admin)
- **Goal**: Keep data fresh and validate scraping works
- **Context**: Debugging and operational oversight

### Primary needs
- One-click “Refresh Live Rates”
- Clear success/failure feedback
- (Future) persisted refresh history visible in the UI

### Frustrations
- Refresh fails silently
- Hard to tell whether UI is stale or scraping failed

### MVP tasks
- Trigger refresh → confirm tables updated → troubleshoot if not

