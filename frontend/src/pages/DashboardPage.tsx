import { useEffect, useMemo, useState } from 'react'
import type { ChangeEvent } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { api } from '../api'
import { useAuth } from '../auth'
import type { Breakdown, DatasetMeta, Filters, Summary, Trends } from '../types'

const emptyFilters: Filters = {
  date_from: '',
  date_to: '',
  category: '',
  group_by: 'region',
}

function money(n: number) {
  return n.toLocaleString(undefined, { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })
}

export function DashboardPage() {
  const { token, user, logout } = useAuth()
  const [datasets, setDatasets] = useState<DatasetMeta[]>([])
  const [datasetId, setDatasetId] = useState<number | null>(null)
  const [filters, setFilters] = useState<Filters>(emptyFilters)
  const [summary, setSummary] = useState<Summary | null>(null)
  const [trends, setTrends] = useState<Trends | null>(null)
  const [breakdown, setBreakdown] = useState<Breakdown | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const query = useMemo(
    () => ({
      date_from: filters.date_from || undefined,
      date_to: filters.date_to || undefined,
      category: filters.category || undefined,
      group_by: filters.group_by || undefined,
    }),
    [filters],
  )

  async function refreshDatasets(selectId?: number) {
    if (!token) return
    const list = await api.listDatasets(token)
    setDatasets(list)
    setDatasetId((prev) => selectId ?? prev ?? list[0]?.id ?? null)
  }

  useEffect(() => {
    if (!token) return
    void refreshDatasets().catch((err: unknown) =>
      setError(err instanceof Error ? err.message : 'Failed to load datasets'),
    )
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token])

  useEffect(() => {
    if (!token || !datasetId) {
      setSummary(null)
      setTrends(null)
      setBreakdown(null)
      return
    }
    let cancelled = false
    async function load() {
      setBusy(true)
      setError(null)
      try {
        const [s, t, b] = await Promise.all([
          api.summary(token!, datasetId!, query),
          api.trends(token!, datasetId!, query),
          api.breakdown(token!, datasetId!, query),
        ])
        if (!cancelled) {
          setSummary(s)
          setTrends(t)
          setBreakdown(b)
        }
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Failed to load analytics')
      } finally {
        if (!cancelled) setBusy(false)
      }
    }
    void load()
    return () => {
      cancelled = true
    }
  }, [token, datasetId, query])

  async function onSample() {
    if (!token) return
    setBusy(true)
    setError(null)
    try {
      const ds = await api.loadSample(token)
      await refreshDatasets(ds.id)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sample load failed')
    } finally {
      setBusy(false)
    }
  }

  async function onUpload(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (!file || !token) return
    setBusy(true)
    setError(null)
    try {
      const ds = await api.uploadCsv(token, file)
      await refreshDatasets(ds.id)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setBusy(false)
    }
  }

  const categories = summary?.filter_options.categories ?? []
  const groupOptions = datasets.find((d) => d.id === datasetId)?.columns ?? ['region', 'category', 'product']

  return (
    <div className="dash-shell">
      <header className="dash-top">
        <div>
          <p className="brand-mark">InsightBoard</p>
          <p className="subtle">Customer analytics</p>
        </div>
        <div className="dash-user">
          <a className="btn btn-ghost" href={import.meta.env.VITE_ANALYTICS_URL || 'http://localhost:8000/analytics/'} target="_blank" rel="noreferrer">
            Analyst view
          </a>
          <span>{user?.full_name || user?.email}</span>
          <button type="button" className="btn btn-ghost" onClick={logout}>
            Log out
          </button>
        </div>
      </header>

      <div className="dash-layout">
        <aside className="dash-side">
          <h2>Data</h2>
          <label>
            Dataset
            <select
              value={datasetId ?? ''}
              onChange={(e) => setDatasetId(e.target.value ? Number(e.target.value) : null)}
            >
              {datasets.length === 0 ? <option value="">No datasets yet</option> : null}
              {datasets.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} ({d.row_count} rows)
                </option>
              ))}
            </select>
          </label>

          <div className="side-actions">
            <button type="button" className="btn btn-secondary btn-block" onClick={onSample} disabled={busy}>
              Load sample sales
            </button>
            <label className="btn btn-primary btn-block file-btn">
              Upload CSV
              <input type="file" accept=".csv,text/csv" onChange={onUpload} hidden />
            </label>
          </div>

          <h2>Filters</h2>
          <label>
            From
            <input
              type="date"
              value={filters.date_from}
              onChange={(e) => setFilters((f) => ({ ...f, date_from: e.target.value }))}
            />
          </label>
          <label>
            To
            <input
              type="date"
              value={filters.date_to}
              onChange={(e) => setFilters((f) => ({ ...f, date_to: e.target.value }))}
            />
          </label>
          <label>
            Category
            <select
              value={filters.category}
              onChange={(e) => setFilters((f) => ({ ...f, category: e.target.value }))}
            >
              <option value="">All</option>
              {categories.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </label>
          <label>
            Breakdown by
            <select
              value={filters.group_by}
              onChange={(e) => setFilters((f) => ({ ...f, group_by: e.target.value }))}
            >
              {groupOptions.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </label>
        </aside>

        <main className="dash-main">
          {error ? <p className="error banner">{error}</p> : null}
          {!datasetId ? (
            <div className="empty-state">
              <h1>No dataset selected</h1>
              <p>Load the sample sales CSV or upload your own to see KPIs and charts.</p>
            </div>
          ) : (
            <>
              <section className="kpi-row" aria-busy={busy}>
                <article className="kpi">
                  <p>Total revenue</p>
                  <strong>{summary ? money(summary.total_revenue) : '—'}</strong>
                </article>
                <article className="kpi">
                  <p>Units sold</p>
                  <strong>{summary ? summary.total_units.toLocaleString() : '—'}</strong>
                </article>
                <article className="kpi">
                  <p>Avg order</p>
                  <strong>{summary ? money(summary.avg_revenue) : '—'}</strong>
                </article>
                <article className="kpi">
                  <p>Growth</p>
                  <strong>
                    {summary?.growth_pct == null ? '—' : `${summary.growth_pct > 0 ? '+' : ''}${summary.growth_pct}%`}
                  </strong>
                </article>
              </section>

              <section className="chart-grid">
                <article className="chart-panel">
                  <header>
                    <h2>Revenue over time</h2>
                    <p>From `/api/data/{'{id}'}/trends`</p>
                  </header>
                  <div className="chart-body">
                    <ResponsiveContainer width="100%" height={280}>
                      <LineChart data={trends?.points ?? []}>
                        <CartesianGrid stroke="rgba(13,79,74,0.12)" strokeDasharray="4 6" />
                        <XAxis dataKey="date" tick={{ fontSize: 11 }} minTickGap={24} />
                        <YAxis tick={{ fontSize: 11 }} width={56} />
                        <Tooltip formatter={(v) => money(Number(v))} />
                        <Line
                          type="monotone"
                          dataKey="value"
                          stroke="#0d4f4a"
                          strokeWidth={2.5}
                          dot={false}
                          animationDuration={700}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </article>

                <article className="chart-panel">
                  <header>
                    <h2>Breakdown</h2>
                    <p>Grouped by {breakdown?.group_by ?? '…'}</p>
                  </header>
                  <div className="chart-body">
                    <ResponsiveContainer width="100%" height={280}>
                      <BarChart data={breakdown?.items ?? []}>
                        <CartesianGrid stroke="rgba(13,79,74,0.12)" strokeDasharray="4 6" />
                        <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                        <YAxis tick={{ fontSize: 11 }} width={56} />
                        <Tooltip formatter={(v) => money(Number(v))} />
                        <Bar dataKey="value" fill="#e05a33" radius={[6, 6, 0, 0]} animationDuration={700} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </article>
              </section>
            </>
          )}
        </main>
      </div>
    </div>
  )
}
