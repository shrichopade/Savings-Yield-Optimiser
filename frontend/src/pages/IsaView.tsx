import { useState } from 'react'
import { FiltersBar } from '../components/FiltersBar'
import { RatesTable } from '../components/RatesTable'

export function IsaView() {
  const [fixedTermMonths, setFixedTermMonths] = useState(12)
  const [depositGbp, setDepositGbp] = useState('')
  const [excludeRestricted, setExcludeRestricted] = useState(false)

  return (
    <div className="space-y-4">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold">ISA</h1>
          <p className="mt-1 text-sm text-slate-300">
            Cash ISA products (sample dataset).
          </p>
        </div>

        <label className="text-sm text-slate-200">
          Fixed ISA term
          <select
            className="ml-2 rounded-md border border-slate-800 bg-slate-950 px-3 py-1.5 text-sm text-slate-100"
            value={fixedTermMonths}
            onChange={(e) => setFixedTermMonths(Number(e.target.value))}
          >
            {[6, 12, 18, 24, 36, 60].map((m) => (
              <option key={m} value={m}>
                {m} months
              </option>
            ))}
          </select>
        </label>
      </header>

      <FiltersBar
        label="Filters"
        termMonths={fixedTermMonths}
        setTermMonths={setFixedTermMonths}
        termPresets={[12, 24]}
        depositGbp={depositGbp}
        setDepositGbp={setDepositGbp}
        excludeRestricted={excludeRestricted}
        setExcludeRestricted={setExcludeRestricted}
      />

      <RatesTable
        title="Cash ISA — Easy Access"
        endpointPath="/tables/cash-isa/easy-access"
        params={{
          deposit_gbp: depositGbp.trim() ? Number(depositGbp) : undefined,
          exclude_restricted: excludeRestricted,
        }}
      />

      <RatesTable
        title={`Cash ISA — Fixed (${fixedTermMonths} months)`}
        endpointPath="/tables/cash-isa/fixed"
        params={{
          term_months: fixedTermMonths,
          deposit_gbp: depositGbp.trim() ? Number(depositGbp) : undefined,
          exclude_restricted: excludeRestricted,
        }}
      />
    </div>
  )
}

