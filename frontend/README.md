# CSV Insights Dashboard — Frontend

A clean, dark-themed React dashboard that uploads a CSV, sends it to a FastAPI
backend for analysis, and renders charts + AI-generated insights.

## Tech Stack

- React (Vite)
- Tailwind CSS
- Recharts
- lucide-react

## Getting Started

```bash
cd frontend
npm install
npm run dev
```

The app runs at http://localhost:5173 and talks to the backend at
http://localhost:8000.

## Expected API Response (`POST /analyze`)

```json
{
  "summary": "Short description of the dataset.",
  "total_rows": 1000,
  "total_columns": 8,
  "data": [{ "col_a": "x", "col_b": 12 }],
  "charts": [
    { "type": "bar", "title": "Sales by Region", "x": "region", "y": "sales", "insight": "North leads." }
  ],
  "insights": ["Revenue grew 12% month over month."]
}
```

`type` may be one of `bar`, `line`, `scatter`, or `pie`.
The raw rows used to build charts are read from `data` (falls back to `rows` /
`raw_data`).
