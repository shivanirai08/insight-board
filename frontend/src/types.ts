export type User = {
  id: number
  email: string
  full_name: string | null
  picture_url: string | null
}

export type DatasetMeta = {
  id: number
  name: string
  original_filename: string | null
  source: string
  row_count: number
  columns: string[]
  notes: string | null
  created_at: string
}

export type Summary = {
  dataset_id: number
  row_count: number
  total_revenue: number
  total_units: number
  avg_revenue: number
  growth_pct: number | null
  metrics_available: Record<string, string | null>
  filter_options: { categories: string[] }
}

export type Trends = {
  dataset_id: number
  date_column: string | null
  value_column: string | null
  points: { date: string; value: number }[]
}

export type Breakdown = {
  dataset_id: number
  group_by: string | null
  value_column: string | null
  items: { label: string; value: number }[]
}

export type Filters = {
  date_from: string
  date_to: string
  category: string
  group_by: string
}
