# Glance — CSV → Insights Dashboard

Upload a CSV, get auto-generated charts and plain-English insights. Built for a hackathon.

## Stack
- **Frontend:** React + Recharts + Tailwind (Vite, single page)
- **Backend:** FastAPI + pandas
- **LLM:** Groq `llama-3.3-70b-versatile` (JSON mode)
- **Rules:** `inference-rules.md` — single source of truth for all CSV reasoning
- **Claude Code:** `CLAUDE.md`, `/analyze` slash command, `chart-picker` skill, filesystem MCP

## Run

Backend:
```bash
cd backend
pip install -r requirements.txt
cp ../.env.example .env   # then add your GROQ_API_KEY
uvicorn main:app --reload
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000. The dev server proxies `/api` → `:8000`.

## Smoke test
```bash
curl -F "file=@data/sample_sales.csv" localhost:8000/api/analyze
```

## How it works
1. Browser uploads a CSV to `POST /api/analyze` (multipart).
2. Backend parses it with pandas, infers column types, saves the file to `data/`.
3. Backend sends column metadata + sample rows to Groq, with `inference-rules.md` as the system prompt.
4. Groq returns strict JSON: chart specs + insights + summary.
5. Backend fills each chart's `data` from the DataFrame; frontend renders charts + insight cards.

## Claude Code verifiability
Run `/analyze sample_sales.csv` inside Claude Code — it reads the CSV from `data/` via the
filesystem MCP and applies the **same** `inference-rules.md` the backend uses, so its output
should match the live API.
