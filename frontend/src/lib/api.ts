export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

export type TableRow = {
  offer_id: number
  provider_name: string
  product_name: string
  category: string
  term_months: number | null
  aer_percent: number | null
  min_opening_deposit_gbp?: number | null
  max_balance_gbp?: number | null
  verified_at: string
  source_url: string | null
}

export async function fetchTable(
  path: string,
  params: Record<string, string | number | boolean | undefined>,
): Promise<TableRow[]> {
  const url = new URL(`${API_BASE_URL}${path}`)
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined) continue
    url.searchParams.set(k, String(v))
  }

  const res = await fetch(url.toString())
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`HTTP ${res.status} ${res.statusText}${text ? `: ${text}` : ''}`)
  }
  const json = (await res.json()) as { items: TableRow[] }
  return json.items
}

