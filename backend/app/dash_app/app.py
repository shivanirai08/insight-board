"""
Dash analyst frontend — denser view of the same datasets.

Mounted at /analytics on the FastAPI process (WSGIMiddleware).
Callbacks load data via JWT + SQLAlchemy + analytics services (same logic
as the REST API, so React and Dash never disagree).
"""

from __future__ import annotations

from dash import Dash, Input, Output, State, dash_table, dcc, html
import plotly.express as px
from sqlalchemy import select

from app.core.security import decode_access_token
from app.db.session import SessionLocal
from app.models.dataset import Dataset
from app.models.user import User
from app.services import analytics as analytics_service
from app.services.csv_processing import dataframe_from_dataset_rows


def create_dash_app() -> Dash:
    dash_app = Dash(
        __name__,
        requests_pathname_prefix="/analytics/",
        title="InsightBoard Analyst",
        suppress_callback_exceptions=True,
    )

    dash_app.layout = html.Div(
        className="ib-shell",
        children=[
            dcc.Store(id="auth-token"),
            html.Header(
                className="ib-header",
                children=[
                    html.Div(
                        [
                            html.P("InsightBoard", className="ib-brand"),
                            html.H1("Analyst workspace"),
                            html.P(
                                "Dense Plotly view — same datasets as the React dashboard.",
                                className="ib-lede",
                            ),
                        ]
                    ),
                    html.Div(
                        className="ib-auth",
                        children=[
                            dcc.Input(
                                id="token-input",
                                type="password",
                                placeholder="Paste JWT from Dev login / React",
                                className="ib-input",
                                style={"width": "320px"},
                            ),
                            html.Button("Connect", id="connect-btn", n_clicks=0, className="ib-btn"),
                            html.Span(id="auth-status", className="ib-status"),
                        ],
                    ),
                ],
            ),
            html.Div(
                className="ib-controls",
                children=[
                    html.Div(
                        [
                            html.Label("Dataset"),
                            dcc.Dropdown(id="dataset-dropdown", placeholder="Connect with a token first"),
                        ],
                        className="ib-control",
                    ),
                    html.Div(
                        [
                            html.Label("Category"),
                            dcc.Dropdown(id="category-dropdown", placeholder="All categories"),
                        ],
                        className="ib-control",
                    ),
                    html.Div(
                        [
                            html.Label("Breakdown by"),
                            dcc.Dropdown(
                                id="groupby-dropdown",
                                options=[
                                    {"label": "region", "value": "region"},
                                    {"label": "category", "value": "category"},
                                    {"label": "product", "value": "product"},
                                ],
                                value="region",
                                clearable=False,
                            ),
                        ],
                        className="ib-control",
                    ),
                    html.Div(
                        [
                            html.Label("Date from"),
                            dcc.Input(id="date-from", type="text", placeholder="YYYY-MM-DD", className="ib-input"),
                        ],
                        className="ib-control",
                    ),
                    html.Div(
                        [
                            html.Label("Date to"),
                            dcc.Input(id="date-to", type="text", placeholder="YYYY-MM-DD", className="ib-input"),
                        ],
                        className="ib-control",
                    ),
                ],
            ),
            html.Div(id="kpi-row", className="ib-kpis"),
            html.Div(
                className="ib-charts",
                children=[
                    dcc.Graph(id="trends-graph", className="ib-graph"),
                    dcc.Graph(id="breakdown-graph", className="ib-graph"),
                ],
            ),
            html.Div(
                [
                    html.H2("Data table"),
                    dash_table.DataTable(
                        id="data-table",
                        page_size=12,
                        style_table={"overflowX": "auto"},
                        style_header={
                            "backgroundColor": "#0d4f4a",
                            "color": "#f7fbfa",
                            "fontWeight": "600",
                        },
                        style_cell={
                            "fontFamily": "Figtree, Segoe UI, sans-serif",
                            "fontSize": "13px",
                            "padding": "8px 10px",
                            "border": "1px solid #d7e2df",
                        },
                        style_data_conditional=[
                            {"if": {"row_index": "odd"}, "backgroundColor": "#f3f7f5"},
                        ],
                    ),
                ],
                className="ib-table-wrap",
            ),
        ],
    )

    dash_app.index_string = INDEX_STRING

    @dash_app.callback(
        Output("auth-token", "data"),
        Output("auth-status", "children"),
        Output("dataset-dropdown", "options"),
        Output("dataset-dropdown", "value"),
        Input("connect-btn", "n_clicks"),
        State("token-input", "value"),
        prevent_initial_call=True,
    )
    def connect(n_clicks: int, token: str | None):
        if not token or not token.strip():
            return None, "Paste a JWT first", [], None
        try:
            payload = decode_access_token(token.strip())
            user_id = int(payload["sub"])
        except Exception:  # noqa: BLE001 — surface auth errors in the UI
            return None, "Invalid or expired token", [], None

        db = SessionLocal()
        try:
            user = db.get(User, user_id)
            if user is None:
                return None, "User not found", [], None
            datasets = list(
                db.scalars(
                    select(Dataset).where(Dataset.owner_id == user.id).order_by(Dataset.created_at.desc())
                )
            )
            options = [{"label": f"{d.name} ({d.row_count} rows)", "value": d.id} for d in datasets]
            value = options[0]["value"] if options else None
            status = f"Connected as {user.email} · {len(datasets)} dataset(s)"
            return token.strip(), status, options, value
        finally:
            db.close()

    @dash_app.callback(
        Output("category-dropdown", "options"),
        Output("category-dropdown", "value"),
        Output("groupby-dropdown", "options"),
        Input("dataset-dropdown", "value"),
        State("auth-token", "data"),
    )
    def sync_filters(dataset_id: int | None, token: str | None):
        if not dataset_id or not token:
            return [], None, [
                {"label": "region", "value": "region"},
                {"label": "category", "value": "category"},
                {"label": "product", "value": "product"},
            ]
        dataset = _load_dataset(token, dataset_id)
        if dataset is None:
            return [], None, []
        summary = analytics_service.build_summary(list(dataset.columns or []), list(dataset.rows or []))
        categories = [{"label": c, "value": c} for c in summary["filter_options"]["categories"]]
        group_opts = [{"label": c, "value": c} for c in (dataset.columns or [])]
        return categories, None, group_opts or [{"label": "category", "value": "category"}]

    @dash_app.callback(
        Output("kpi-row", "children"),
        Output("trends-graph", "figure"),
        Output("breakdown-graph", "figure"),
        Output("data-table", "columns"),
        Output("data-table", "data"),
        Input("dataset-dropdown", "value"),
        Input("category-dropdown", "value"),
        Input("groupby-dropdown", "value"),
        Input("date-from", "value"),
        Input("date-to", "value"),
        State("auth-token", "data"),
    )
    def refresh_analytics(
        dataset_id: int | None,
        category: str | None,
        group_by: str | None,
        date_from: str | None,
        date_to: str | None,
        token: str | None,
    ):
        empty_fig = {"data": [], "layout": {"paper_bgcolor": "rgba(0,0,0,0)", "plot_bgcolor": "rgba(0,0,0,0)"}}
        if not dataset_id or not token:
            return (
                [html.P("Connect and choose a dataset to see KPIs.")],
                empty_fig,
                empty_fig,
                [],
                [],
            )

        dataset = _load_dataset(token, dataset_id)
        if dataset is None:
            return [html.P("Dataset not found for this user.")], empty_fig, empty_fig, [], []

        columns = list(dataset.columns or [])
        rows = list(dataset.rows or [])
        summary = analytics_service.build_summary(
            columns, rows, date_from=date_from or None, date_to=date_to or None, category=category or None
        )
        trends = analytics_service.build_trends(
            columns, rows, date_from=date_from or None, date_to=date_to or None, category=category or None
        )
        breakdown = analytics_service.build_breakdown(
            columns,
            rows,
            group_by=group_by or None,
            date_from=date_from or None,
            date_to=date_to or None,
            category=category or None,
        )

        kpis = html.Div(
            className="ib-kpi-grid",
            children=[
                _kpi("Total revenue", f"${summary['total_revenue']:,.0f}"),
                _kpi("Units", f"{summary['total_units']:,.0f}"),
                _kpi("Avg revenue", f"${summary['avg_revenue']:,.0f}"),
                _kpi(
                    "Growth",
                    "—"
                    if summary["growth_pct"] is None
                    else f"{summary['growth_pct']:+.1f}%",
                ),
                _kpi("Rows", f"{summary['row_count']}"),
            ],
        )

        trend_fig = px.line(
            trends["points"],
            x="date",
            y="value",
            markers=True,
            title="Revenue over time",
        )
        trend_fig.update_layout(
            margin=dict(l=40, r=20, t=48, b=40),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(243,247,245,0.7)",
            font_family="Figtree, sans-serif",
            title_font_family="Syne, sans-serif",
        )
        trend_fig.update_traces(line_color="#0d4f4a")

        break_fig = px.bar(
            breakdown["items"],
            x="label",
            y="value",
            title=f"Breakdown by {breakdown['group_by'] or 'n/a'}",
        )
        break_fig.update_layout(
            margin=dict(l=40, r=20, t=48, b=40),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(243,247,245,0.7)",
            font_family="Figtree, sans-serif",
            title_font_family="Syne, sans-serif",
        )
        break_fig.update_traces(marker_color="#e05a33")

        df = dataframe_from_dataset_rows(columns, rows)
        if category and "category" in df.columns:
            df = df[df["category"].astype(str) == category]
        if date_from and "date" in df.columns:
            df = df[df["date"].astype(str) >= date_from]
        if date_to and "date" in df.columns:
            df = df[df["date"].astype(str) <= date_to]

        table_cols = [{"name": c, "id": c} for c in df.columns]
        table_data = df.to_dict("records")
        return kpis, trend_fig, break_fig, table_cols, table_data

    return dash_app


def _kpi(label: str, value: str) -> html.Div:
    return html.Div([html.P(label), html.Strong(value)], className="ib-kpi")


def _load_dataset(token: str, dataset_id: int) -> Dataset | None:
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except Exception:  # noqa: BLE001
        return None
    db = SessionLocal()
    try:
        return db.scalar(
            select(Dataset).where(Dataset.id == dataset_id, Dataset.owner_id == user_id)
        )
    finally:
        db.close()


INDEX_STRING = """
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
        <link href="https://fonts.googleapis.com/css2?family=Figtree:wght@400;600;700&family=Syne:wght@700;800&display=swap" rel="stylesheet" />
        <style>
            body {
                margin: 0;
                font-family: Figtree, sans-serif;
                color: #14201e;
                background:
                  radial-gradient(900px 420px at 0% 0%, rgba(224,90,51,0.14), transparent 55%),
                  linear-gradient(165deg, #e7f0ed, #f4efe6 55%, #e9ebe4);
            }
            .ib-shell { max-width: 1200px; margin: 0 auto; padding: 1.25rem 1rem 2.5rem; }
            .ib-header { display:flex; justify-content:space-between; gap:1rem; flex-wrap:wrap; margin-bottom:1rem; }
            .ib-brand { margin:0; font-family:Syne,sans-serif; font-weight:800; color:#0d4f4a; }
            .ib-header h1 { margin:0.15rem 0; font-family:Syne,sans-serif; letter-spacing:-0.03em; }
            .ib-lede { margin:0; color:#5b6b67; }
            .ib-auth { display:flex; gap:0.5rem; align-items:center; flex-wrap:wrap; }
            .ib-input { border:1px solid rgba(13,79,74,0.18); border-radius:10px; padding:0.55rem 0.75rem; background:rgba(255,252,248,0.85); }
            .ib-btn { border:none; border-radius:999px; padding:0.6rem 1rem; background:#0d4f4a; color:#f7fbfa; font-weight:600; cursor:pointer; }
            .ib-status { color:#5b6b67; font-size:0.9rem; }
            .ib-controls { display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:0.75rem; margin-bottom:1rem; }
            .ib-control { background:rgba(255,252,248,0.82); border:1px solid rgba(255,255,255,0.55); border-radius:14px; padding:0.75rem; box-shadow:0 10px 30px rgba(20,32,30,0.08); }
            .ib-control label { display:block; font-size:0.85rem; color:#5b6b67; margin-bottom:0.35rem; }
            .ib-kpis { margin-bottom:1rem; }
            .ib-kpi-grid { display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:0.75rem; }
            .ib-kpi { background:rgba(255,252,248,0.82); border-radius:14px; padding:0.9rem 1rem; box-shadow:0 10px 30px rgba(20,32,30,0.08); }
            .ib-kpi p { margin:0 0 0.25rem; color:#5b6b67; font-size:0.85rem; }
            .ib-kpi strong { font-family:Syne,sans-serif; font-size:1.35rem; }
            .ib-charts { display:grid; grid-template-columns:1.2fr 1fr; gap:0.75rem; margin-bottom:1rem; }
            .ib-graph, .ib-table-wrap { background:rgba(255,252,248,0.82); border-radius:14px; padding:0.5rem 0.75rem 0.75rem; box-shadow:0 10px 30px rgba(20,32,30,0.08); }
            .ib-table-wrap h2 { font-family:Syne,sans-serif; font-size:1.05rem; margin:0.4rem 0 0.75rem; }
            @media (max-width: 900px) {
              .ib-controls, .ib-kpi-grid, .ib-charts { grid-template-columns:1fr; }
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
"""
