type Props = {
  depositGbp: string
  setDepositGbp: (v: string) => void
  excludeRestricted: boolean
  setExcludeRestricted: (v: boolean) => void
  termMonths?: number
  setTermMonths?: (v: number) => void
  termPresets?: number[]
  label: string
}

function pillClass(active: boolean) {
  return [
    'rounded-full border px-3 py-1 text-xs font-medium',
    active
      ? 'border-slate-200 bg-slate-100 text-slate-900'
      : 'border-slate-800 bg-slate-950 text-slate-200 hover:bg-slate-900',
  ].join(' ')
}

export function FiltersBar({
  depositGbp,
  setDepositGbp,
  excludeRestricted,
  setExcludeRestricted,
  termMonths,
  setTermMonths,
  termPresets = [12, 24],
  label,
}: Props) {
  return (
    <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
      <div className="flex flex-wrap items-center gap-3">
        <div className="text-sm font-semibold">{label}</div>

        {typeof termMonths === 'number' && setTermMonths ? (
          <div className="flex items-center gap-2" role="group" aria-label="Term">
            <span className="text-xs text-slate-400">Term</span>
            <div className="flex flex-wrap gap-2">
              {termPresets.map((m) => (
                <button
                  key={m}
                  type="button"
                  className={pillClass(m === termMonths)}
                  aria-pressed={m === termMonths}
                  aria-label={`Set term to ${m === 12 ? '1 year' : m === 24 ? '2 years' : `${m} months`}`}
                  onClick={() => setTermMonths(m)}
                >
                  {m === 12 ? '1-year' : m === 24 ? '2-year' : `${m} mo`}
                </button>
              ))}
            </div>
          </div>
        ) : null}

        <div className="flex items-center gap-2">
          <label className="text-xs text-slate-400" htmlFor="deposit">
            Deposit (£)
          </label>
          <input
            id="deposit"
            inputMode="numeric"
            aria-label="Deposit amount in pounds"
            placeholder="e.g. 5000"
            className="w-28 rounded-md border border-slate-800 bg-slate-950 px-3 py-1.5 text-sm text-slate-100 placeholder:text-slate-500"
            value={depositGbp}
            onChange={(e) => setDepositGbp(e.target.value)}
          />
        </div>

        <label className="ml-auto flex items-center gap-2 text-sm text-slate-200">
          <input
            type="checkbox"
            className="h-4 w-4 rounded border-slate-700 bg-slate-950"
            checked={excludeRestricted}
            aria-label="Exclude restricted deals"
            onChange={(e) => setExcludeRestricted(e.target.checked)}
          />
          Exclude restricted deals
        </label>
      </div>
    </section>
  )
}

