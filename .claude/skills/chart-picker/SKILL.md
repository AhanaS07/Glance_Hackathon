---
name: chart-picker
description: Reasoning skill for picking the right chart type from CSV column types. Use when deciding which chart (bar/line/pie/scatter) best represents a pair of columns, or when implementing/reviewing chart-selection logic for the CSV insights dashboard.
---

# Chart Picker

Given a set of CSV columns and their inferred types, choose the chart that best tells a story.
This skill mirrors the chart-selection rules in `inference-rules.md` (the single source of truth).

## Column types
- **numeric** — quantitative, aggregatable (sales, score, units, age, price)
- **categorical** — discrete labels, low/medium cardinality (region, gender, category)
- **datetime** — dates, months, ordered time periods
- **identifier** — unique per-row keys; never chart these

## Selection rules

| Columns chosen | Chart | x | y |
|---|---|---|---|
| 1 categorical (cardinality ≤ 12) + 1 numeric | **bar** | category | numeric (sum/mean) |
| 1 datetime + 1 numeric | **line** | datetime (sorted) | numeric |
| 1 categorical (cardinality ≤ 6), share of total | **pie** | category | numeric value to sum |
| 2 numeric | **scatter** | numeric | numeric |

## Heuristics
- If a datetime/ordered-period column exists, prefer a **line** chart to show trend over time.
- Use **pie** only for small cardinality (≤ 6) and when the story is "share of a whole".
- Use **bar** for comparing a measure across categories; it's the safe default for categorical+numeric.
- Use **scatter** to show correlation between two numeric measures.
- Aim for **2–4 charts** that each tell a *distinct* story — avoid charting the same pair twice.
- Only ever reference **real column names**. Never invent columns.

## Output
When asked for chart recommendations, emit specs only — `type`, `title`, `x`, `y`, `insight` —
matching the JSON schema in `inference-rules.md`. The data arrays are computed downstream by the
backend (`backend/chart_builder.py`), not here.
