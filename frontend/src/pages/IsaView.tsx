import { useMemo, useState } from 'react'
import { FiltersBar } from '../components/FiltersBar'
import { RatesTable } from '../components/RatesTable'
import { ADMIN_TOKEN, triggerAdminRefresh } from '../lib/api'

export function IsaView() {
  // Cash ISA page: easy access table + fixed table with term dropdown + optional refresh.
  const [fixedTermMonths, setFixedTermMonths] = useState<number | 'all'>(12)
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
            onChange={(e) =>
              setFixedTermMonths(e.target.value === 'all' ? 'all' : Number(e.target.value))
            }
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
        termMonths={fixedTermMonths === 'all' ? undefined : fixedTermMonths}
        setTermMonths={fixedTermMonths === 'all' ? undefined : setFixedTermMonths}
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
        title="Cash ISA — Easy Access"
        endpointPath="/tables/cash-isa/easy-access"
        params={{
          deposit_gbp: depositGbp.trim() ? Number(depositGbp) : undefined,
          exclude_restricted: excludeRestricted,
          // Cache-buster param to refetch after admin refresh.
          _refresh: refreshTick,
        }}
      />

      <RatesTable
        title={
          fixedTermMonths === 'all'
            ? 'Cash ISA — Fixed (All terms)'
            : `Cash ISA — Fixed (${fixedTermMonths} months)`
        }
        endpointPath="/tables/cash-isa/fixed"
        params={{
          // Backend convention: term_months=0 means “All terms”.
          term_months: fixedTermMonths === 'all' ? 0 : fixedTermMonths,
          deposit_gbp: depositGbp.trim() ? Number(depositGbp) : undefined,
          exclude_restricted: excludeRestricted,
          // Cache-buster param to refetch after admin refresh.
          _refresh: refreshTick,
        }}
      />
    </div>
  )
}

