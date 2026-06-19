---
name: chart-picker
description: Reasoning skill for picking the right chart type from CSV column types. Use when deciding which chart (bar/line/pie/scatter) best represents a pair of columns, or when implementing/reviewing chart-selection logic for the CSV insights dashboard.
---

# Chart Picker

Given a set of CSV columns and their inferred types, choose the chart that best tells a story,
and render it with the correct Recharts components. This skill mirrors the chart-selection rules
in `inference-rules.md` (the **single source of truth**). When the two ever disagree,
`inference-rules.md` wins — fix this file, never hardcode divergent rules.

This skill covers two jobs:
1. **Reasoning** — picking the chart `type` + `x`/`y` from column metadata (mirrors Groq's job).
2. **Rendering** — switching Recharts components by `type` in `frontend/src/components/ChartCard.jsx`.

---

## Column types

Classify each column by attempting to parse in this **exact order**, stopping at the first fit:

1. **datetime** — dates, months, timestamps, ordered time periods.
2. **numeric** — integers/floats; quantitative, aggregatable (sales, price, score, age, units).
3. **boolean** — values limited to `true`/`false`, `yes`/`no`, `1`/`0`.
4. **categorical** — discrete text labels (region, gender, category) — anything else.

`identifier` is not a parse type but a role: unique-per-row keys (`id`, `uuid`, `email`).

---

## Selection rules

| Columns chosen | Chart | x | y |
|---|---|---|---|
| 1 categorical (cardinality ≤ 15) + 1 numeric | **bar** | category | numeric (sum/mean) |
| 1 datetime + 1 numeric | **line** | datetime (sorted) | numeric |
| multiple numeric over a shared time axis | **line** (multi-line) | datetime | most important numeric |
| 2 numeric | **scatter** | numeric | numeric |
| 1 categorical (cardinality ≤ 6), share of a whole | **pie** | category | numeric value to sum |

---

## Overrides (apply BEFORE selecting a chart)

These adjust a column's effective type and must be applied first:

- **Low-distinct numeric → categorical.** A numeric column with **fewer than 6 unique values**
  represents discrete groups, not a continuous measure — treat it as categorical.
- **High-cardinality categorical → excluded.** A categorical column with **more than 15 unique
  values** cannot be meaningfully grouped — **exclude it from all charts**.
- **boolean → 2-value categorical.** Treat boolean columns like a categorical with two values.
- **identifier → never charted.** Unique-per-row keys are never an axis.
- **Pie hard cap:** never use pie for **more than 6 categories**. A category may have up to 7
  distinct values to *qualify* as parts-of-a-whole, but if it actually exceeds 6, use **bar**.

---

## Heuristics

- If a datetime/ordered-period column exists, prefer a **line** chart to show trend over time.
- Use **bar** for comparing a measure across categories — the safe default for categorical+numeric.
  **Prefer bar over pie when uncertain.**
- Use **pie** only for small cardinality (≤ 6) when the story is genuinely "share of a whole".
- Use **scatter** to show correlation between two numeric measures.
- Multi-line: the schema carries a single `x`/`y` per chart. When several numerics share one time
  axis, emit one **line** chart for the **most important** measure — never invent a composite column.
- Aim for **2–4 charts** that each tell a *distinct* story — never chart the same pair twice.
- A title must **describe the insight, not the columns** — `"Revenue by Region"`, never `"x vs y"`.
- Only ever reference **real column names**. Never invent, rename, or guess a column.

---

## Edge cases

- **All-null column** — no usable values; exclude it from every chart.
- **Single unique value** — no variation to plot (bar/pie would be one slice, scatter/line flat);
  exclude it and do not use it as an axis.
- **Mixed types in one column** — apply the parse order above; if values don't cleanly fit numeric
  or datetime, it falls through to **categorical**, then re-check the high-cardinality override.
- **Not enough chartable columns** — return **fewer** charts rather than guessing, but never fewer
  than 2 unless the dataset genuinely cannot support 2 distinct charts.

---

## Rendering — `ChartCard.jsx`

`ChartCard.jsx` switches on the chart's `type` field (`bar | line | pie | scatter`) and renders
the matching Recharts components. Each chart's `data[]` array (filled by `chart_builder.py`) has
keys equal to the chart's `x` and `y` column names — bind `dataKey` to those exact names. The card
consumes `chart.data` directly (it does **not** re-aggregate raw rows). Wrap every chart in
`<ResponsiveContainer>`.

| `type` | Recharts components |
|---|---|
| `bar` | `BarChart` containing `Bar` (`dataKey={y}`), `XAxis dataKey={x}`, `YAxis`, `CartesianGrid`, `Tooltip` |
| `line` | `LineChart` containing `Line` (`dataKey={y}`), `XAxis dataKey={x}`, `YAxis`, `CartesianGrid`, `Tooltip` |
| `scatter` | `ScatterChart` containing `Scatter`, `XAxis dataKey={x}`, `YAxis dataKey={y}`, `Tooltip` |
| `pie` | `PieChart` containing `Pie` (`dataKey={y}`, `nameKey={x}`) with a `Cell` per slice for color |

Sketch:

```jsx
switch (chart.type) {
  case 'bar':     return <BarChart data={chart.data}>…<Bar dataKey={chart.y} />…</BarChart>;
  case 'line':    return <LineChart data={chart.data}>…<Line dataKey={chart.y} />…</LineChart>;
  case 'scatter': return <ScatterChart>…<Scatter data={chart.data} />…</ScatterChart>;
  case 'pie':     return <PieChart><Pie data={chart.data} dataKey={chart.y} nameKey={chart.x}>
                           {chart.data.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                         </Pie></PieChart>;
  default:        return null; // unknown type — render nothing
}
```

---

## Output (reasoning mode)

When asked for chart recommendations, emit specs only — `type`, `title`, `x`, `y`, `insight` —
matching the JSON schema in `inference-rules.md`. The `data[]` arrays are computed downstream by the
backend (`backend/chart_builder.py`), not here.
