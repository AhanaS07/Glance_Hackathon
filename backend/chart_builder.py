"""Fill chart specs with Recharts-ready data arrays.

Pipeline position: analyzer -> groq_client -> chart_builder -> main.
Takes Groq's chart SPECS (no data) plus the parsed rows and attaches each
chart's `data` array. Each data dict's keys equal the spec's exact x and y
column names. No Groq calls, no CSV parsing here.
"""

import warnings

import pandas as pd

# Same dateutil-fallback warning as analyzer.py; expected during line-chart sort.
warnings.filterwarnings("ignore", message="Could not infer format", category=UserWarning)

_BAR_TOP = 20      # bar: keep top 20 groups
_PIE_TOP = 8       # pie: keep top 8 slices, remainder -> "Other"
_LINE_MAX = 200    # line: sample down to 200 points
_SCATTER_MAX = 150  # scatter: sample up to 150 pairs


def _aggregate(df: pd.DataFrame, x: str, y: str) -> pd.DataFrame:
    """Group by x and aggregate y: sum if numeric, else count. Returns x,y frame."""
    y_numeric = pd.to_numeric(df[y], errors="coerce")
    if y_numeric.notna().sum() / max(len(df), 1) > 0.8:
        work = pd.DataFrame({x: df[x], y: y_numeric})
        grouped = work.groupby(x, dropna=True)[y].sum().reset_index()
    else:
        # y is non-numeric -> count rows per group instead.
        print(f"[chart_builder] y={y!r} not numeric; using count aggregation")
        grouped = df.groupby(x, dropna=True).size().reset_index(name=y)
    return grouped.sort_values(by=y, ascending=False)


def _build_bar(df: pd.DataFrame, x: str, y: str) -> list:
    grouped = _aggregate(df, x, y).head(_BAR_TOP)
    return [{x: _scalar(r[x]), y: _scalar(r[y])} for _, r in grouped.iterrows()]


def _build_pie(df: pd.DataFrame, x: str, y: str) -> list:
    grouped = _aggregate(df, x, y)
    if len(grouped) > _PIE_TOP:
        top = grouped.head(_PIE_TOP)
        other_total = grouped.iloc[_PIE_TOP:][y].sum()
        rows = [{x: _scalar(r[x]), y: _scalar(r[y])} for _, r in top.iterrows()]
        rows.append({x: "Other", y: _scalar(other_total)})
        return rows
    return [{x: _scalar(r[x]), y: _scalar(r[y])} for _, r in grouped.iterrows()]


def _build_line(df: pd.DataFrame, x: str, y: str) -> list:
    work = df[[x, y]].dropna()
    # Sort ascending by x (datetime-aware when possible).
    sort_key = pd.to_datetime(work[x], errors="coerce")
    if sort_key.notna().sum() / max(len(work), 1) > 0.8:
        work = work.assign(_k=sort_key).sort_values("_k").drop(columns="_k")
    else:
        work = work.sort_values(by=x)
    if len(work) > _LINE_MAX:
        step = max(len(work) // _LINE_MAX, 1)
        work = work.iloc[::step].head(_LINE_MAX)
    return [{x: _scalar(r[x]), y: _scalar(r[y])} for _, r in work.iterrows()]


def _build_scatter(df: pd.DataFrame, x: str, y: str) -> list:
    work = df[[x, y]].copy()
    work[x] = pd.to_numeric(work[x], errors="coerce")
    work[y] = pd.to_numeric(work[y], errors="coerce")
    work = work.dropna()
    if len(work) > _SCATTER_MAX:
        work = work.head(_SCATTER_MAX)
    return [{x: _scalar(r[x]), y: _scalar(r[y])} for _, r in work.iterrows()]


def _scalar(v):
    """Coerce a pandas/numpy scalar to a JSON-friendly Python value."""
    if pd.isna(v):
        return None
    if hasattr(v, "item"):
        try:
            return v.item()
        except (ValueError, AttributeError):
            pass
    if isinstance(v, (int, float, str, bool)):
        return v
    return str(v)


_BUILDERS = {
    "bar": _build_bar,
    "pie": _build_pie,
    "line": _build_line,
    "scatter": _build_scatter,
}


def build_charts(chart_specs: list, all_rows: list, columns_meta: list) -> list:
    """Attach a `data` array to each chart spec; skip any chart that can't build.

    Never crashes on a single bad chart. Raises RuntimeError only if EVERY chart
    is skipped.
    """
    df = pd.DataFrame(all_rows)
    enriched = []

    for spec in chart_specs:
        x, y, ctype = spec.get("x"), spec.get("y"), spec.get("type")

        if x not in df.columns or y not in df.columns:
            print(f"[chart_builder] skipping chart; column missing: x={x!r} y={y!r}")
            continue

        builder = _BUILDERS.get(ctype)
        if builder is None:
            print(f"[chart_builder] skipping chart with unknown type: {ctype}")
            continue

        try:
            data = builder(df, x, y)
        except Exception as exc:  # noqa: BLE001 - never crash on one bad chart
            print(f"[chart_builder] skipping chart {spec.get('title')!r}: {exc}")
            continue

        if not data:
            print(f"[chart_builder] skipping chart {spec.get('title')!r}: 0 rows after build")
            continue

        out = dict(spec)
        out["data"] = data
        enriched.append(out)

    if not enriched:
        raise RuntimeError("Could not build chart data for any chart spec.")

    return enriched
