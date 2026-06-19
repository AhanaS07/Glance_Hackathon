"""FastAPI app: routes, CORS, error envelopes.

Top of the pipeline: imports analyzer, groq_client, chart_builder, models and
orchestrates them. Contains NO reasoning logic and NO CSV parsing of its own —
it only wires the layers together and shapes HTTP responses.
"""

import os
import traceback

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import analyzer
import chart_builder
import groq_client
from models import AnalyzeResponse, ColumnMeta, SummaryBlock

app = FastAPI(title="CSV → Insights Dashboard")

app.add_middleware(
    CORSMiddleware,
    # 3000 is the documented dev port (CLAUDE.md); 5173 is Vite's default, kept
    # as a safety net for a direct browser -> :8000 hit that bypasses the proxy.
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Uploaded CSVs are saved here so the filesystem MCP can later inspect them.
_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _error(status: int, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": message})


@app.exception_handler(Exception)
async def _unhandled(request, exc):  # noqa: ANN001
    print(f"[main] unhandled error: {exc}")
    traceback.print_exc()
    return _error(500, "Unexpected server error. Check backend logs.")


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/analyze")
async def analyze(file: UploadFile = File(...)):
    # 1-2. Reject non-CSV extensions / obviously empty uploads immediately.
    filename = file.filename or ""
    if not filename.lower().endswith(".csv"):
        return _error(400, "Please upload a .csv file.")

    file_bytes = await file.read()
    if not file_bytes:
        return _error(400, "Uploaded file is empty.")

    # 4. Parse + infer column types.
    try:
        parsed = analyzer.parse_csv(file_bytes)
    except ValueError as exc:
        return _error(400, str(exc))

    # 5. Persist the upload into ./data (best-effort; never fail the request on this).
    try:
        os.makedirs(_DATA_DIR, exist_ok=True)
        with open(os.path.join(_DATA_DIR, os.path.basename(filename)), "wb") as fh:
            fh.write(file_bytes)
    except OSError as exc:
        print(f"[main] could not save upload: {exc}")

    # 6. Groq reasoning -> chart specs + insights + summary.
    try:
        insights = groq_client.get_insights(parsed)
    except RuntimeError as exc:
        return _error(500, str(exc))

    # 7. Fill chart data arrays from the parsed rows.
    try:
        charts = chart_builder.build_charts(
            insights["charts"], parsed["all_rows"], parsed["columns"]
        )
    except RuntimeError as exc:
        return _error(500, str(exc))

    # 8. Assemble and validate the response against the API contract.
    summary = SummaryBlock(
        rowCount=parsed["rowCount"],
        columnCount=parsed["columnCount"],
        description=insights["summary"]["description"],
        columns=[ColumnMeta(**c) for c in parsed["columns"]],
    )
    response = AnalyzeResponse(summary=summary, charts=charts, insights=insights["insights"])
    return response.model_dump()
