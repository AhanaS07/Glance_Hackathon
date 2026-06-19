---
description: Analyze a CSV in ./data and output chart + insight JSON using inference-rules.md
argument-hint: <filename.csv>
---

Analyze the CSV file `$ARGUMENTS` located in the `./data` directory.

Steps:
1. Read the file `data/$ARGUMENTS` using the filesystem MCP server.
2. Read `inference-rules.md` from the repo root. Treat it as the **single source of truth** —
   follow its column-classification, chart-selection, insight, and output-format rules exactly.
3. Inspect the columns: infer each column's type (numeric / categorical / datetime / identifier),
   note cardinality, null counts, and a few sample values.
4. Produce the strict JSON object defined in `inference-rules.md` (`summary`, `charts`, `insights`)
   — chart specs only, no data arrays.

Output **only** the JSON, no surrounding prose. This should match what the backend's
`POST /api/analyze` endpoint would return (before the backend fills in each chart's `data`),
so it can be used to verify the live API.
