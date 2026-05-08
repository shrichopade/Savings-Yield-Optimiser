# Wireframes (Retrospective) — Savings Yield Optimiser

These are lightweight “text wireframes” that describe layout and hierarchy for the current MVP pages.

---

## Wireframe 1 — Fixed Rate page

```text
┌───────────────────────────────────────────────────────────────────────────┐
│ Header                                                                     │
│  [Logo]  UK Savings & ISA Rate Tracker      [Fixed Rate] [ISA]            │
└───────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────┐
│ Fixed Rate                                        Term: [ All v ]          │
│ Fixed savings products ranked by AER (sample dataset).                     │
└───────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────┐
│ Filters                                                                     │
│  (Admin) [ Refresh Live Rates ]   (status text: refreshing / success / ...)│
│  Term pills (optional): [1-year] [2-year]                                   │
│  Deposit (£): [ 5000 ]   [ ] Exclude restricted deals                       │
└───────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────┐
│ Fixed Savings — {Term}                                                     │
│  Loading / Error / No results states                                        │
│                                                                           │
│  Table:                                                                     │
│   Bank/Provider | AER | Term | Min deposit | Max balance                    │
│   ... rows ...                                                               │
└───────────────────────────────────────────────────────────────────────────┘
```

Notes:
- When Term = All, the **Term** column is critical (mixed terms shown together).
- In future, add explicit columns for **Last checked** + **Source**.

---

## Wireframe 2 — ISA page

```text
┌───────────────────────────────────────────────────────────────────────────┐
│ Header                                                                     │
│  [Logo]  UK Savings & ISA Rate Tracker      [Fixed Rate] [ISA]            │
└───────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────┐
│ ISA                                             Fixed ISA term: [ All v ]  │
│ Cash ISA products (sample dataset).                                         │
└───────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────┐
│ Filters                                                                     │
│  (Admin) [ Refresh Live Rates ]   (status text)                             │
│  Term pills (optional): [1-year] [2-year]                                   │
│  Deposit (£): [ 5000 ]   [ ] Exclude restricted deals                       │
└───────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────┐
│ Cash ISA — Easy Access                                                     │
│  Table: Bank/Provider | AER | Term | Min deposit | Max balance             │
└───────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────┐
│ Cash ISA — Fixed ({Term})                                                  │
│  Table: Bank/Provider | AER | Term | Min deposit | Max balance             │
└───────────────────────────────────────────────────────────────────────────┘
```

Notes:
- The page intentionally places **Easy Access** above **Fixed** to match common intent.
- Future: add ISA-specific “gotchas” columns/badges (transfer-in, flexible ISA).

