import { useEffect, useMemo, useState } from 'react'
import { fetchTable, type TableRow } from '../lib/api'

// RatesTable.tsx — reusable table component that fetches rows from the backend
// It shows loading/error states and renders a simple table of offers.

type Props = {
  title: string
  endpointPath: string
  params: Record<string, string | number | boolean | undefined>
}

const gbp = new Intl.NumberFormat('en-GB', {
  style: 'currency',
  currency: 'GBP',
  maximumFractionDigits: 0,
})

function formatAer(aer: number | null) {
  // Convert a numeric AER into user-friendly text (or a dash if unknown).
  // Inputs: aer (number or null).
  // Returns: formatted string like "4.25%".
  if (aer === null) return '—'
  return `${aer.toFixed(2)}%`
}

function formatTerm(termMonths: number | null) {
  // Convert a term in months into user-friendly text.
  // Inputs: termMonths (number or null).
  // Returns: formatted string like "12 mo" or "—".
  if (termMonths === null) return '—'
  if (termMonths === -1) return '—'
  return `${termMonths} mo`
}

function formatGbp(value: number | null | undefined) {
  // Format a number as GBP currency (or a dash if unknown).
  // Inputs: value (number, null, or undefined).
  // Returns: formatted string like "£5,000".
  if (value === null || value === undefined) return '—'
  return gbp.format(value)
}

export function RatesTable({ title, endpointPath, params }: Props) {
  // Fetch and display a rates table.
  // Inputs: endpointPath + params (used to call the backend).
  // Returns: a React component section.
  const [items, setItems] = useState<TableRow[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  const stableKey = useMemo(() => JSON.stringify({ endpointPath, params }), [
    endpointPath,
    params,
  ])

  useEffect(() => {
    // Whenever endpointPath/params change, re-fetch the table data.
    let cancelled = false
    setItems(null)
    setError(null)

    fetchTable(endpointPath, params)
      .then((rows) => {
        if (cancelled) return
        setItems(rows)
      })
      .catch((e: unknown) => {
        if (cancelled) return
        setError(e instanceof Error ? e.message : 'Failed to load')
      })

    return () => {
      // Prevent setting state if the component unmounts while the request is still in-flight.
      cancelled = true
    }
  }, [stableKey, endpointPath, params])

  return (
    <section className="rounded-xl border border-slate-800 bg-slate-900/40">
      <div className="flex items-start justify-between gap-4 border-b border-slate-800 px-5 py-4">
        <div>
          <h2 className="text-sm font-semibold">{title}</h2>
          <p className="mt-1 text-xs text-slate-400">
            Showing sample data from the local FastAPI backend.
          </p>
        </div>
      </div>

      {error ? (
        <div className="px-5 py-4 text-sm text-rose-300" role="alert">
          {error}
        </div>
      ) : items === null ? (
        <div className="px-5 py-4 text-sm text-slate-300" aria-live="polite">
          Loading…
        </div>
      ) : items.length === 0 ? (
        <div className="px-5 py-4 text-sm text-slate-300">No results.</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full border-separate border-spacing-0 text-left text-sm">
            <caption className="sr-only">{title}</caption>
            <thead className="sticky top-0 bg-slate-950/80 text-xs text-slate-300 backdrop-blur">
              <tr>
                <th scope="col" className="whitespace-nowrap px-5 py-3 font-semibold">
                  Bank / Provider
                </th>
                <th scope="col" className="whitespace-nowrap px-5 py-3 font-semibold">
                  AER
                </th>
                <th
                  scope="col"
                  className="whitespace-nowrap px-5 py-3 font-semibold"
                >
                  Term
                </th>
                <th
                  scope="col"
                  className="hidden whitespace-nowrap px-5 py-3 font-semibold sm:table-cell"
                >
                  Min deposit
                </th>
                <th
                  scope="col"
                  className="hidden whitespace-nowrap px-5 py-3 font-semibold lg:table-cell"
                >
                  Max balance
                </th>
              </tr>
            </thead>
            <tbody>
              {items.map((row) => (
                <tr
                  key={row.offer_id}
                  className="border-t border-slate-800/70 hover:bg-slate-950/35 focus-within:bg-slate-950/35"
                >
                  <td className="px-5 py-3">
                    <div className="font-medium text-slate-100">
                      {row.provider_name}
                    </div>
                    <div className="text-xs text-slate-400">{row.product_name}</div>
                  </td>
                  <td className="px-5 py-3 font-medium tabular-nums">
                    {formatAer(row.aer_percent)}
                  </td>
                  <td className="px-5 py-3 tabular-nums text-slate-200">
                    {formatTerm(row.term_months)}
                  </td>
                  <td className="hidden px-5 py-3 tabular-nums text-slate-200 sm:table-cell">
                    {formatGbp(row.min_opening_deposit_gbp)}
                  </td>
                  <td className="hidden px-5 py-3 tabular-nums text-slate-200 lg:table-cell">
                    {formatGbp(row.max_balance_gbp)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

