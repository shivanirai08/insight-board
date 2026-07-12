"""Analytics aggregations over a cleaned dataset (pandas → JSON for the API)."""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.services.csv_processing import dataframe_from_dataset_rows


def _pick_column(columns: list[str], candidates: list[str]) -> str | None:
    lower_map = {c.lower(): c for c in columns}
    for name in candidates:
        if name in lower_map:
            return lower_map[name]
    return None


def _apply_filters(
    df: pd.DataFrame,
    *,
    date_from: str | None,
    date_to: str | None,
    category: str | None,
    date_col: str | None,
    category_col: str | None,
) -> pd.DataFrame:
    out = df.copy()
    if date_col and date_col in out.columns:
        dates = pd.to_datetime(out[date_col], errors="coerce")
        if date_from:
            out = out[dates >= pd.to_datetime(date_from)]
        if date_to:
            out = out[dates <= pd.to_datetime(date_to)]
    if category and category_col and category_col in out.columns:
        out = out[out[category_col].astype(str) == category]
    return out


def build_summary(
    columns: list[str],
    rows: list[dict[str, Any]],
    *,
    date_from: str | None = None,
    date_to: str | None = None,
    category: str | None = None,
) -> dict[str, Any]:
    df = dataframe_from_dataset_rows(columns, rows)
    date_col = _pick_column(list(df.columns), ["date", "order_date", "sold_at", "day"])
    category_col = _pick_column(list(df.columns), ["category", "region", "product"])
    revenue_col = _pick_column(list(df.columns), ["revenue", "sales", "amount", "total"])
    units_col = _pick_column(list(df.columns), ["units_sold", "units", "quantity", "qty"])

    filtered = _apply_filters(
        df,
        date_from=date_from,
        date_to=date_to,
        category=category,
        date_col=date_col,
        category_col=category_col,
    )

    total_revenue = float(filtered[revenue_col].sum()) if revenue_col and not filtered.empty else 0.0
    total_units = float(filtered[units_col].sum()) if units_col and not filtered.empty else 0.0
    avg_revenue = float(filtered[revenue_col].mean()) if revenue_col and not filtered.empty else 0.0
    row_count = int(len(filtered))

    growth_pct: float | None = None
    if date_col and revenue_col and not filtered.empty:
        tmp = filtered.copy()
        tmp["_dt"] = pd.to_datetime(tmp[date_col], errors="coerce")
        tmp = tmp.dropna(subset=["_dt"]).sort_values("_dt")
        if len(tmp) >= 2:
            mid = tmp["_dt"].min() + (tmp["_dt"].max() - tmp["_dt"].min()) / 2
            first = float(tmp.loc[tmp["_dt"] <= mid, revenue_col].sum())
            second = float(tmp.loc[tmp["_dt"] > mid, revenue_col].sum())
            if first:
                growth_pct = round(((second - first) / first) * 100, 2)

    categories: list[str] = []
    if category_col and category_col in df.columns:
        categories = sorted({str(v) for v in df[category_col].dropna().unique()})

    return {
        "row_count": row_count,
        "total_revenue": round(total_revenue, 2),
        "total_units": round(total_units, 2),
        "avg_revenue": round(avg_revenue, 2),
        "growth_pct": growth_pct,
        "metrics_available": {
            "revenue": revenue_col,
            "units": units_col,
            "date": date_col,
            "category": category_col,
        },
        "filter_options": {"categories": categories},
    }


def build_trends(
    columns: list[str],
    rows: list[dict[str, Any]],
    *,
    date_from: str | None = None,
    date_to: str | None = None,
    category: str | None = None,
) -> dict[str, Any]:
    df = dataframe_from_dataset_rows(columns, rows)
    date_col = _pick_column(list(df.columns), ["date", "order_date", "sold_at", "day"])
    category_col = _pick_column(list(df.columns), ["category", "region", "product"])
    revenue_col = _pick_column(list(df.columns), ["revenue", "sales", "amount", "total"])

    if not date_col or not revenue_col:
        return {"points": [], "date_column": date_col, "value_column": revenue_col}

    filtered = _apply_filters(
        df,
        date_from=date_from,
        date_to=date_to,
        category=category,
        date_col=date_col,
        category_col=category_col,
    )
    if filtered.empty:
        return {"points": [], "date_column": date_col, "value_column": revenue_col}

    tmp = filtered.copy()
    tmp["_dt"] = pd.to_datetime(tmp[date_col], errors="coerce")
    tmp = tmp.dropna(subset=["_dt"])
    tmp["_day"] = tmp["_dt"].dt.strftime("%Y-%m-%d")
    grouped = tmp.groupby("_day", as_index=False)[revenue_col].sum()
    points = [
        {"date": row["_day"], "value": round(float(row[revenue_col]), 2)}
        for _, row in grouped.iterrows()
    ]
    return {"points": points, "date_column": date_col, "value_column": revenue_col}


def build_breakdown(
    columns: list[str],
    rows: list[dict[str, Any]],
    *,
    group_by: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    category: str | None = None,
) -> dict[str, Any]:
    df = dataframe_from_dataset_rows(columns, rows)
    date_col = _pick_column(list(df.columns), ["date", "order_date", "sold_at", "day"])
    default_group = _pick_column(list(df.columns), ["category", "region", "product"])
    category_col = _pick_column(list(df.columns), ["category", "region", "product"])
    revenue_col = _pick_column(list(df.columns), ["revenue", "sales", "amount", "total"])

    group_col = group_by if group_by and group_by in df.columns else default_group
    if not group_col or not revenue_col:
        return {"items": [], "group_by": group_col, "value_column": revenue_col}

    filtered = _apply_filters(
        df,
        date_from=date_from,
        date_to=date_to,
        category=category,
        date_col=date_col,
        category_col=category_col,
    )
    if filtered.empty:
        return {"items": [], "group_by": group_col, "value_column": revenue_col}

    grouped = (
        filtered.groupby(group_col, dropna=False)[revenue_col]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    items = [
        {"label": str(row[group_col]), "value": round(float(row[revenue_col]), 2)}
        for _, row in grouped.iterrows()
    ]
    return {"items": items, "group_by": group_col, "value_column": revenue_col}
