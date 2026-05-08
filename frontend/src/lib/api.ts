// api.ts — small helpers for calling the FastAPI backend from the frontend
// This file keeps all HTTP request code in one place.

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'
export const ADMIN_TOKEN = import.meta.env.VITE_ADMIN_TOKEN as string | undefined

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
  // Build a URL like: http://127.0.0.1:8000/tables/fixed-savings?term_months=12
  // Inputs: endpoint path and query params.
  // Returns: an array of TableRow objects.
  const url = new URL(`${API_BASE_URL}${path}`)
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined) continue
    url.searchParams.set(k, String(v))
  }

  // Call the backend and fail loudly if we get a non-200 response.
  const res = await fetch(url.toString())
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`HTTP ${res.status} ${res.statusText}${text ? `: ${text}` : ''}`)
  }
  const json = (await res.json()) as { items: TableRow[] }
  return json.items
}

export type RefreshResponse = {
  job_id: string
  status: string
  message?: string
}

export async function triggerAdminRefresh(): Promise<RefreshResponse> {
  // Trigger the backend’s admin-only refresh endpoint.
  // Requires: VITE_ADMIN_TOKEN set in `frontend/.env` (must match backend ADMIN_TOKEN).
  // Returns: {job_id, status, message} from the backend.
  if (!ADMIN_TOKEN) {
    throw new Error('Missing VITE_ADMIN_TOKEN in frontend env')
  }

  const url = new URL(`${API_BASE_URL}/admin/refresh`)
  url.searchParams.set('wait', 'true')

  // We send the shared secret in a header so normal users cannot trigger refresh.
  const res = await fetch(url.toString(), {
    method: 'POST',
    headers: {
      'X-Admin-Token': ADMIN_TOKEN,
    },
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`HTTP ${res.status} ${res.statusText}${text ? `: ${text}` : ''}`)
  }
  return (await res.json()) as RefreshResponse
}

