import { useState } from 'react'
import { FiltersBar } from '../components/FiltersBar'
import { RatesTable } from '../components/RatesTable'

export function FixedRateView() {
  const [termMonths, setTermMonths] = useState(12)
  const [depositGbp, setDepositGbp] = useState('')
  const [excludeRestricted, setExcludeRestricted] = useState(false)

  return (
    <div className="space-y-4">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold">Fixed Rate</h1>
          <p className="mt-1 text-sm text-slate-300">
            Fixed savings products ranked by AER (sample dataset).
          </p>
        </div>

        <label className="text-sm text-slate-200">
          Term
          <select
            className="ml-2 rounded-md border border-slate-800 bg-slate-950 px-3 py-1.5 text-sm text-slate-100"
            value={termMonths}
            onChange={(e) => setTermMonths(Number(e.target.value))}
          >
            {[3, 6, 9, 12, 18, 24, 36, 60].map((m) => (
              <option key={m} value={m}>
                {m} months
              </option>
            ))}
          </select>
        </label>
      </header>

      <FiltersBar
        label="Filters"
        termMonths={termMonths}
        setTermMonths={setTermMonths}
        termPresets={[12, 24]}
        depositGbp={depositGbp}
        setDepositGbp={setDepositGbp}
        excludeRestricted={excludeRestricted}
        setExcludeRestricted={setExcludeRestricted}
      />

      <RatesTable
        title={`Fixed Savings — ${termMonths} months`}
        endpointPath="/tables/fixed-savings"
        params={{
          term_months: termMonths,
          deposit_gbp: depositGbp.trim() ? Number(depositGbp) : undefined,
          exclude_restricted: excludeRestricted,
        }}
      />
    </div>
  )
}

