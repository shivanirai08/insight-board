"""
CSV cleaning with pandas.

Goals:
  - Accept messy uploads (nulls, mixed types, date strings)
  - Normalize column names
  - Coerce common numeric / date columns when present
  - Return records JSON-serializable for PostgreSQL JSONB
"""

from __future__ import annotations

import io
import re
from typing import Any

import pandas as pd
from fastapi import HTTPException, status


def _normalize_column(name: str) -> str:
    cleaned = re.sub(r"[^\w]+", "_", str(name).strip().lower())
    return cleaned.strip("_") or "column"


def clean_csv_bytes(raw: bytes, *, max_rows: int = 50_000) -> tuple[list[str], list[dict[str, Any]], int]:
    """
    Parse CSV bytes → (columns, rows, row_count).

    Raises HTTPException 400 if the file is empty/invalid.
    """
    if not raw.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CSV file is empty")

    try:
        df = pd.read_csv(io.BytesIO(raw))
    except Exception as exc:  # noqa: BLE001 — surface parse errors to the client
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not parse CSV: {exc}",
        ) from exc

    if df.empty:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CSV has no data rows")

    if len(df) > max_rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"CSV has {len(df)} rows; max allowed is {max_rows}",
        )

    df.columns = [_normalize_column(c) for c in df.columns]
    # Deduplicate column names: date, date → date, date_2
    seen: dict[str, int] = {}
    new_cols: list[str] = []
    for col in df.columns:
        if col not in seen:
            seen[col] = 1
            new_cols.append(col)
        else:
            seen[col] += 1
            new_cols.append(f"{col}_{seen[col]}")
    df.columns = new_cols

    df = df.dropna(how="all")
    df = df.where(pd.notnull(df), None)

    # Best-effort date parsing for common column names
    for col in df.columns:
        if col in {"date", "order_date", "sold_at", "timestamp", "day"}:
            parsed = pd.to_datetime(df[col], errors="coerce", utc=False)
            df[col] = parsed.dt.strftime("%Y-%m-%d").where(parsed.notna(), None)

    # Coerce likely numeric columns
    for col in df.columns:
        if col in {"date"} or col.endswith("_at"):
            continue
        if df[col].dtype == object:
            numeric = pd.to_numeric(df[col], errors="coerce")
            # Only keep coercion if most values converted
            non_null = df[col].notna().sum()
            if non_null and numeric.notna().sum() / non_null >= 0.8:
                df[col] = numeric

    # Replace remaining NaN/NaT with None for JSON
    df = df.astype(object).where(pd.notnull(df), None)

    records = df.to_dict(orient="records")
    # Ensure JSON-serializable primitives
    cleaned_rows: list[dict[str, Any]] = []
    for row in records:
        cleaned_rows.append({k: _jsonable(v) for k, v in row.items()})

    columns = list(df.columns)
    return columns, cleaned_rows, len(cleaned_rows)


def _jsonable(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:  # noqa: BLE001
            return str(value)
    if isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def dataframe_from_dataset_rows(columns: list[str], rows: list[dict[str, Any]]) -> pd.DataFrame:
    """Rebuild a DataFrame from stored JSON rows for analytics."""
    if not rows:
        return pd.DataFrame(columns=columns)
    df = pd.DataFrame(rows)
    # Preserve known column order when possible
    ordered = [c for c in columns if c in df.columns]
    extras = [c for c in df.columns if c not in ordered]
    return df[ordered + extras]
