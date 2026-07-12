import type { Breakdown, DatasetMeta, Summary, Trends, User } from './types'

const API_URL = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, '') || ''

function authHeaders(token: string): HeadersInit {
  return { Authorization: `Bearer ${token}` }
}

async function parseError(res: Response): Promise<string> {
  try {
    const data = await res.json()
    if (typeof data.detail === 'string') return data.detail
    return JSON.stringify(data.detail ?? data)
  } catch {
    return res.statusText || 'Request failed'
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, init)
  if (!res.ok) throw new Error(await parseError(res))
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export const api = {
  googleLoginUrl: `${API_URL}/api/auth/google/login`,

  async devLogin(email: string, fullName: string) {
    return request<{ access_token: string; token_type: string }>('/api/auth/dev-login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, full_name: fullName }),
    })
  },

  async me(token: string) {
    return request<User>('/api/auth/me', { headers: authHeaders(token) })
  },

  async listDatasets(token: string) {
    return request<DatasetMeta[]>('/api/datasets', { headers: authHeaders(token) })
  },

  async loadSample(token: string) {
    return request<DatasetMeta>('/api/datasets/sample', {
      method: 'POST',
      headers: authHeaders(token),
    })
  },

  async uploadCsv(token: string, file: File, name?: string) {
    const body = new FormData()
    body.append('file', file)
    if (name) body.append('name', name)
    return request<DatasetMeta>('/api/datasets/upload', {
      method: 'POST',
      headers: authHeaders(token),
      body,
    })
  },

  async summary(
    token: string,
    datasetId: number,
    params: { date_from?: string; date_to?: string; category?: string },
  ) {
    const q = new URLSearchParams()
    if (params.date_from) q.set('date_from', params.date_from)
    if (params.date_to) q.set('date_to', params.date_to)
    if (params.category) q.set('category', params.category)
    const qs = q.toString()
    return request<Summary>(`/api/data/${datasetId}/summary${qs ? `?${qs}` : ''}`, {
      headers: authHeaders(token),
    })
  },

  async trends(
    token: string,
    datasetId: number,
    params: { date_from?: string; date_to?: string; category?: string },
  ) {
    const q = new URLSearchParams()
    if (params.date_from) q.set('date_from', params.date_from)
    if (params.date_to) q.set('date_to', params.date_to)
    if (params.category) q.set('category', params.category)
    const qs = q.toString()
    return request<Trends>(`/api/data/${datasetId}/trends${qs ? `?${qs}` : ''}`, {
      headers: authHeaders(token),
    })
  },

  async breakdown(
    token: string,
    datasetId: number,
    params: { date_from?: string; date_to?: string; category?: string; group_by?: string },
  ) {
    const q = new URLSearchParams()
    if (params.date_from) q.set('date_from', params.date_from)
    if (params.date_to) q.set('date_to', params.date_to)
    if (params.category) q.set('category', params.category)
    if (params.group_by) q.set('group_by', params.group_by)
    const qs = q.toString()
    return request<Breakdown>(`/api/data/${datasetId}/breakdown${qs ? `?${qs}` : ''}`, {
      headers: authHeaders(token),
    })
  },
}
