"""Groq inference: load inference-rules.md verbatim, call the LLM, validate.

Pipeline position: analyzer -> groq_client -> chart_builder -> main.
This is the ONLY module that talks to Groq and the ONLY place reasoning rules
live (they live in inference-rules.md, loaded here verbatim as the system
prompt). It does not parse CSVs and does not build chart data.
"""

import json
import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
_ALLOWED_TYPES = {"bar", "line", "pie", "scatter"}

# Resolve inference-rules.md at the repo root (one level above backend/).
_RULES_PATH = os.path.join(os.path.dirname(__file__), "..", "inference-rules.md")


def _load_rules() -> str:
    """Read inference-rules.md once at import time and cache it."""
    try:
        with open(os.path.abspath(_RULES_PATH), "r", encoding="utf-8") as fh:
            return fh.read()
    except FileNotFoundError as exc:
        raise RuntimeError("inference-rules.md not found. Run from repo root.") from exc


# Cache the rules at import (do not re-read per request).
_SYSTEM_PROMPT = _load_rules()


def _get_client() -> Groq:
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        raise RuntimeError(
            "GROQ_API_KEY not set. Copy backend/.env.example to backend/.env and add your key."
        )
    return Groq(api_key=key)


def _build_user_message(parsed: dict) -> str:
    return (
        "Analyze this CSV dataset and return insights.\n\n"
        f"Columns:\n{json.dumps(parsed['columns'], indent=2)}\n\n"
        f"Sample rows (first 15):\n{json.dumps(parsed['sample_rows'], indent=2)}\n\n"
        "Return only valid JSON matching the schema in your instructions."
    )


def _call_groq(client: Groq, messages: list) -> str:
    """One Groq chat completion in JSON mode; raises RuntimeError on API failure."""
    try:
        resp = client.chat.completions.create(
            model=_MODEL,
            response_format={"type": "json_object"},
            messages=messages,
            max_tokens=1500,
            temperature=0,
        )
        return resp.choices[0].message.content
    except Exception as exc:  # noqa: BLE001 - auth / rate-limit / timeout / network
        raise RuntimeError(f"Groq API error: {exc}") from exc


def _validate_shape(data: dict) -> None:
    """Validate top-level keys and types; raise RuntimeError listing what's missing."""
    if not isinstance(data, dict):
        raise RuntimeError("LLM response missing required fields: not a JSON object")

    missing = []
    charts = data.get("charts")
    insights = data.get("insights")
    summary = data.get("summary")

    if not isinstance(charts, list) or not (2 <= len(charts) <= 4):
        missing.append("charts (list of 2-4)")
    if not isinstance(insights, list) or not (3 <= len(insights) <= 4) or not all(
        isinstance(i, str) for i in insights
    ):
        missing.append("insights (list of 3-4 strings)")
    # Per inference-rules.md, Groq returns summary as a string; accept either a
    # bare string or a dict carrying a description.
    if not (isinstance(summary, str) or (isinstance(summary, dict) and "description" in summary)):
        missing.append("summary (string or object with description)")

    if missing:
        raise RuntimeError(f"LLM response missing required fields: {missing}")


def _filter_charts(charts: list, columns_meta: list) -> list:
    """Keep only well-formed charts whose x/y are real columns; drop the rest."""
    valid_names = {c["name"] for c in columns_meta}
    kept = []
    for chart in charts:
        if not isinstance(chart, dict):
            continue
        ctype = chart.get("type")
        x = chart.get("x")
        y = chart.get("y")
        if ctype not in _ALLOWED_TYPES:
            print(f"[groq_client] dropping chart with bad type: {ctype}")
            continue
        if not all(chart.get(k) for k in ("title", "insight")) or x is None or y is None:
            print(f"[groq_client] dropping chart missing required fields: {chart}")
            continue
        if x not in valid_names or y not in valid_names:
            # Column-name hallucination: warn, drop silently, continue.
            print(f"[groq_client] dropping chart with unknown column(s): x={x!r} y={y!r}")
            continue
        kept.append(
            {"type": ctype, "title": chart["title"], "x": x, "y": y, "insight": chart["insight"]}
        )
    return kept


def get_insights(parsed: dict) -> dict:
    """Run Groq over parsed metadata and return a validated insights dict.

    Returns {"charts": [...specs...], "insights": [...], "summary": <str|dict>}.
    Charts here are SPECS ONLY (no data) — chart_builder.py fills data later.
    """
    client = _get_client()
    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": _build_user_message(parsed)},
    ]

    raw = _call_groq(client, messages)
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        # Retry once with an explicit nudge to return pure JSON.
        messages.append({"role": "assistant", "content": raw or ""})
        messages.append(
            {
                "role": "user",
                "content": (
                    "Your previous response was not valid JSON. Return only the JSON "
                    "object, no markdown, no explanation."
                ),
            }
        )
        raw = _call_groq(client, messages)
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError) as exc:
            raise RuntimeError("LLM returned invalid JSON after retry.") from exc

    _validate_shape(data)

    valid_charts = _filter_charts(data["charts"], parsed["columns"])
    if len(valid_charts) < 2:
        raise RuntimeError("LLM did not return enough valid charts. Try a different CSV.")

    summary = data["summary"]
    description = summary if isinstance(summary, str) else summary.get("description", "")

    return {
        "charts": valid_charts,
        "insights": data["insights"],
        "summary": {"description": description},
    }
