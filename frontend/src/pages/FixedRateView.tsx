import { useMemo, useState } from 'react'
import { FiltersBar } from '../components/FiltersBar'
import { RatesTable } from '../components/RatesTable'
import { ADMIN_TOKEN, triggerAdminRefresh } from '../lib/api'

export function FixedRateView() {
  // Fixed savings page: term dropdown + filters + table + optional admin refresh.
  const [termMonths, setTermMonths] = useState<number | 'all'>(12)
  const [depositGbp, setDepositGbp] = useState('')
  const [excludeRestricted, setExcludeRestricted] = useState(false)
  const [refreshState, setRefreshState] = useState<'idle' | 'loading' | 'success' | 'error'>('idle')
  const [refreshTick, setRefreshTick] = useState(0)

  const refreshLabel = useMemo(() => {
    // Build small helper text that appears under the filters while refreshing.
    if (!ADMIN_TOKEN) return undefined
    if (refreshState === 'loading') return 'Refreshing live rates… this can take a moment.'
    if (refreshState === 'success') return 'Live rates refreshed.'
    if (refreshState === 'error') return 'Refresh failed. Check backend logs and token configuration.'
    return undefined
  }, [refreshState])

  async function onRefresh() {
    // Call the backend admin refresh endpoint, then force the tables to refetch.
    if (!ADMIN_TOKEN) return
    setRefreshState('loading')
    try {
      await triggerAdminRefresh()
      // Changing this tick value changes the `params` object, which triggers RatesTable to refetch.
      setRefreshTick((t) => t + 1)
      setRefreshState('success')
      window.setTimeout(() => setRefreshState('idle'), 2500)
    } catch {
      setRefreshState('error')
    }
  }

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
            onChange={(e) => setTermMonths(e.target.value === 'all' ? 'all' : Number(e.target.value))}
          >
            <option value="all">All</option>
            {[12, 18, 24, 36, 60].map((m) => (
              <option key={m} value={m}>
                {m} months
              </option>
            ))}
          </select>
        </label>
      </header>

      <FiltersBar
        label="Filters"
        termMonths={termMonths === 'all' ? undefined : termMonths}
        setTermMonths={termMonths === 'all' ? undefined : setTermMonths}
        termPresets={[12, 24]}
        depositGbp={depositGbp}
        setDepositGbp={setDepositGbp}
        excludeRestricted={excludeRestricted}
        setExcludeRestricted={setExcludeRestricted}
        onRefresh={ADMIN_TOKEN ? onRefresh : undefined}
        refreshState={refreshState}
        refreshLabel={refreshLabel}
      />

      <RatesTable
        title={termMonths === 'all' ? 'Fixed Savings — All terms' : `Fixed Savings — ${termMonths} months`}
        endpointPath="/tables/fixed-savings"
        params={{
          // Backend convention: term_months=0 means “All terms”.
          term_months: termMonths === 'all' ? 0 : termMonths,
          deposit_gbp: depositGbp.trim() ? Number(depositGbp) : undefined,
          exclude_restricted: excludeRestricted,
          // This is a harmless “cache buster” param used to force refetch after refresh.
          _refresh: refreshTick,
        }}
      />
    </div>
  )
}

