---
description: Analyze a CSV file and generate dashboard insights end to end
argument-hint: [sample_data/file.csv]
allowed-tools: Bash(curl:*), Bash(ls:*), Bash(head:*), Read, mcp__filesystem
---

# /analyze — CSV → Dashboard insights (end to end)

The user invoked: `/analyze $ARGUMENTS`

This command exercises the **live runtime path**: it sends a CSV to the backend's
`POST /api/analyze` endpoint, which reasons over the data using `inference-rules.md` (the single
source of truth) and returns charts + insights. It therefore validates the whole pipeline
(upload → pandas → Groq → chart_builder), not just Claude's own reasoning.

> Endpoint note: per `CLAUDE.md`, the route is `/api/analyze` and the multipart field name is
> `file`. The response `summary` is an object — validate `summary.description`.

---

## Case A — no argument given (`$ARGUMENTS` is empty)

1. List the CSV files available under `sample_data/`:
   ```
   ls sample_data/*.csv
   ```
2. Print the filenames and ask the user to re-run with one of them, e.g.:
   > Re-run with one of these, for example: `/analyze sample_data/sample_sales.csv`
3. **Stop.** Do not call the backend.

---

## Case B — an argument is given (`$ARGUMENTS` is a CSV path or filename)

### 1. Resolve the path
- If `$ARGUMENTS` already contains a directory separator, use it verbatim.
- Otherwise treat it as a filename under `sample_data/` (e.g. `sample_sales.csv` →
  `sample_data/sample_sales.csv`).
- Read the file with the `filesystem` MCP server — its roots are `./data` and `./sample_data`, so
  both uploaded files and bundled samples are reachable. (The actual upload to the backend is done
  by curl below, so reading here is only to validate the file.)

### 2. Confirm it is a valid CSV
Verify all of the following; if any fails, print a clear one-line error and **stop**:
- The file exists.
- It has a header row.
- The header has **at least 2 columns** (i.e. the first line contains at least one comma).

You can inspect the header with:
```
head -n 1 <resolved-path>
```

### 3. Call the backend
```
curl -s -w "\n%{http_code}" -F "file=@<resolved-path>" http://localhost:8000/api/analyze
```

### 4. Handle backend not running
If curl cannot connect (exit code `7`, or output contains `Connection refused` / `Failed to
connect`), print **exactly** this and stop:
```
Start backend first: cd backend && uvicorn main:app --reload
```

### 5. Validate the response
The JSON body must contain:
- a non-empty **`charts`** array, and
- a **`summary`** object whose **`description`** is a non-empty string.

(Per `inference-rules.md`, Groq returns `summary` as a string, which the backend wraps into the
API's `summary.description`; the backend also fills each chart's `data[]`.)

If the body is an error envelope (`{ "error": "..." }`), the HTTP status is not `200`, or the
shape is wrong, print the error/status and **stop**.

### 6. Print a concise report
On success, print a short, human-readable summary:
- **Charts generated:** the number of items in `charts`.
- **Chart types:** the `type` of each chart, comma-separated (e.g. `bar, line, pie`).
- **Insight preview:** the first **80 characters** of `insights[0]` (fall back to the first
  chart's `insight` if the top-level `insights` array is empty).

Keep the output brief — this is a smoke test of the live dashboard pipeline, not a data dump.
