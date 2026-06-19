# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

CSV → Insights Dashboard. A user uploads a CSV; the backend extracts column metadata, an LLM
(Groq `llama-3.3-70b-versatile`) reasons over it and returns strict JSON describing recommended
charts + plain-English insights; the React frontend renders charts and insight cards.

## Single source of truth

`inference-rules.md` (repo root) governs ALL CSV reasoning: column classification, chart
selection, how many charts, insight style, and the exact output JSON schema. The backend loads
it verbatim as the Groq system prompt (`backend/groq_client.py`). **When changing how data is
analyzed or how output is shaped, edit `inference-rules.md` — do not hardcode reasoning rules in
Python or JS.** Follow the same rules yourself when analyzing CSVs via the `/analyze` command.

## Architecture

Two **independent** execution paths — do not conflate them:

- **Runtime (serves users):** browser → multipart POST `/api/analyze` → FastAPI reads bytes with
  pandas → Groq (JSON mode) → backend builds chart data → JSON → Recharts. **No MCP here.**
- **Dev-time (Claude Code only):** `.mcp.json` runs a filesystem MCP rooted at `./data` and
  `./sample_data`, letting Claude Code read CSVs (uploaded *and* bundled samples) to test rules /
  debug. Never in the request path.

Backend pipeline is layered into small single-purpose modules — keep them separate:
`analyzer.py` (parse + per-column type inference) → `groq_client.py` (load rules, call Groq) →
`chart_builder.py` (aggregate the DataFrame into Recharts-ready `data`) → `main.py` (routes/CORS).

**Key contract detail:** Groq returns chart *specs* only (`type`, `title`, `x`, `y`, `insight`) —
**not** the data arrays. `chart_builder.py` fills each chart's `data` from the parsed DataFrame
afterward (bar/pie = group by `x` aggregate `y`; line = sort by `x`; scatter = sampled pairs).
The `data` object keys equal the `x` and `y` column names.

Uploaded CSVs are saved into `./data` so the filesystem MCP can later inspect them.

## API contract

`POST /api/analyze` (multipart, field `file`) → `{ summary, charts, insights }`:
- `summary`: `rowCount`, `columnCount`, `description`, `columns[]` (`name`, `type`, `uniqueCount`, `nullCount`, `sampleValues`)
- `charts[]` (2–4): `type` ∈ `bar|line|pie|scatter`, `title`, `x`, `y`, `insight`, `data[]`
- `insights[]`: 3–4 plain-English strings

Errors → `{ "error": "..." }` (400 bad/empty CSV, 500 Groq/parse failure). `GET /api/health` → `{ "status": "ok" }`.

## Commands

Backend: `cd backend && pip install -r requirements.txt && uvicorn main:app --reload` (port 8000)
Frontend: `cd frontend && npm install && npm run dev` (port 3000)
Smoke test API: `curl -F "file=@data/sample_sales.csv" localhost:8000/api/analyze`
Requires `GROQ_API_KEY` in `backend/.env` (copy `backend/.env.example`, add key).
Claude Code MCP: `.mcp.json` (filesystem, rooted at `./data` and `./sample_data` — dev only, not in request path).

## Conventions

- Python 3, keep functions small and single-purpose; respect the parse → groq → build layering.
- All Groq calls go through `groq_client.py` only; all CSV parsing through `analyzer.py` only.
- Backend is stdlib + pandas + groq + fastapi only. Never invent CSV column names in any output.
- `vite.config.js` proxies `/api` to `:8000` — use relative `/api/...` paths in `api.js`, never hardcode `localhost:8000`.
- Run the affected path end-to-end after changes (upload a CSV, or `curl` the endpoint) before
  considering a task done.