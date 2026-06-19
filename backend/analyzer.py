"""CSV parsing + per-column type inference.

Bottom of the pipeline: analyzer -> groq_client -> chart_builder -> main.
This module imports NOTHING from the other pipeline modules. It is the only
place CSV bytes are parsed. All reasoning about *charts* lives in
inference-rules.md (loaded by groq_client); this module only classifies column
types deterministically so that metadata can be handed to the LLM.
"""

import io
import re
import warnings

import pandas as pd

# pandas emits a UserWarning when it falls back to dateutil for mixed/ambiguous
# date strings; that is expected during type probing, so keep it out of the logs.
warnings.filterwarnings("ignore", message="Could not infer format", category=UserWarning)

# Type inference thresholds (mirrors inference-rules.md).
_PARSE_RATE = 0.80          # >80% of non-null values must parse for datetime/numeric
_LOW_DISTINCT_NUMERIC = 6   # numeric with <= this many uniques -> categorical
_HIGH_CARDINALITY = 15      # categorical with > this many uniques -> high_cardinality
_BOOL_TOKENS = {"true", "false", "yes", "no", "0", "1"}
_SAMPLE_VALUES = 5
_SAMPLE_ROWS = 15
_MAX_ALL_ROWS = 300

# Identifier columns are unique-per-row KEYS (inference-rules.md: "id, uuid,
# email"). We require an id-like NAME as well as uniqueness, so a genuine
# measure that happens to be all-distinct on a small dataset (e.g. age, score)
# is NOT mistaken for an ID. Works for text keys (Loan_ID) and numeric keys.
_ID_NAME = re.compile(r"(?:^|[_\s])(?:id|uuid|guid|key|email)s?$", re.IGNORECASE)
_ID_EXACT = {"id", "uuid", "guid", "key", "email"}


def _looks_like_id(name: str) -> bool:
    n = str(name).strip()
    return n.lower() in _ID_EXACT or bool(_ID_NAME.search(n))


def _read_dataframe(file_bytes: bytes) -> pd.DataFrame:
    """Decode bytes to a DataFrame, trying utf-8 then latin-1."""
    if not file_bytes or not file_bytes.strip():
        raise ValueError("Uploaded file is empty.")

    last_err = None
    for encoding in ("utf-8", "latin-1"):
        try:
            return pd.read_csv(io.BytesIO(file_bytes), encoding=encoding)
        except pd.errors.EmptyDataError:
            raise ValueError("Uploaded file is empty.")
        except (UnicodeDecodeError, pd.errors.ParserError) as exc:
            last_err = exc
            continue
        except Exception as exc:  # noqa: BLE001 - never leak pandas internals
            last_err = exc
            continue
    raise ValueError("Could not decode CSV. Try saving as UTF-8.") from last_err


def _is_datetime(series: pd.Series) -> bool:
    """True if >80% of non-null values parse as dates."""
    non_null = series.dropna()
    if non_null.empty:
        return False
    # Pure-numeric columns (e.g. 1,2,3) should not be coerced into dates.
    if pd.api.types.is_numeric_dtype(non_null):
        return False
    parsed = pd.to_datetime(non_null, errors="coerce")
    return (parsed.notna().sum() / len(non_null)) > _PARSE_RATE


def _is_numeric(series: pd.Series) -> bool:
    """True if already numeric dtype, or >80% of non-null values coerce to numeric."""
    non_null = series.dropna()
    if non_null.empty:
        return False
    if pd.api.types.is_numeric_dtype(non_null):
        return True
    parsed = pd.to_numeric(non_null, errors="coerce")
    return (parsed.notna().sum() / len(non_null)) > _PARSE_RATE


def _is_boolean(series: pd.Series) -> bool:
    """True if every non-null value (lowered/stripped) is a boolean token."""
    non_null = series.dropna()
    if non_null.empty:
        return False
    tokens = {str(v).strip().lower() for v in non_null.unique()}
    return tokens.issubset(_BOOL_TOKENS)


def _infer_type(series: pd.Series, name: str, unique_count: int, null_count: int, row_count: int) -> str:
    """Classify one column, applying the exact priority order + overrides.

    Priority: identifier -> datetime -> numeric -> boolean -> categorical.
    Overrides: identifier (id-like name AND unique-per-row), low-distinct
    numeric -> categorical, high-cardinality categorical -> high_cardinality.
    """
    # Identifier: an id-like NAME that is also unique per row (all present
    # values distinct). Name-gated so genuine all-distinct measures stay numeric.
    non_null = row_count - null_count
    unique_per_row = unique_count == row_count or (non_null > 0 and unique_count == non_null)
    if _looks_like_id(name) and unique_per_row:
        return "identifier"

    if _is_datetime(series):
        return "datetime"

    if _is_numeric(series):
        # Low-distinct numeric represents discrete groups, not a measure.
        if unique_count <= _LOW_DISTINCT_NUMERIC:
            return "categorical"
        return "numeric"

    if _is_boolean(series):
        # Booleans are charted like a 2-value categorical.
        return "boolean"

    # Everything else is categorical; flag high-cardinality so it's excluded.
    if unique_count > _HIGH_CARDINALITY:
        return "high_cardinality"
    return "categorical"


def _sample_values(series: pd.Series) -> list:
    """First N non-null values as JSON-friendly Python scalars."""
    vals = series.dropna().head(_SAMPLE_VALUES).tolist()
    out = []
    for v in vals:
        if isinstance(v, (int, float, str, bool)):
            out.append(v)
        else:
            out.append(str(v))
    return out


def _json_rows(df: pd.DataFrame) -> list:
    """Convert a DataFrame to a list of plain dicts (NaN -> None)."""
    return df.astype(object).where(pd.notnull(df), None).to_dict(orient="records")


def parse_csv(file_bytes: bytes) -> dict:
    """Parse CSV bytes into column metadata + sample rows for the LLM.

    Raises ValueError (human-readable) on any unusable input; never leaks a
    pandas stack trace to the caller.
    """
    df = _read_dataframe(file_bytes)

    # Reject empties / missing header.
    if df.shape[0] == 0:
        raise ValueError("Uploaded file is empty.")
    if df.shape[1] == 0:
        raise ValueError("CSV must have at least 2 columns to generate charts.")
    # An all-"Unnamed" header means pandas found no valid header row.
    if all(str(c).startswith("Unnamed") for c in df.columns):
        raise ValueError("Could not decode CSV. Try saving as UTF-8.")
    if df.shape[1] < 2:
        raise ValueError("CSV must have at least 2 columns to generate charts.")

    row_count = int(df.shape[0])
    columns = []
    try:
        for name in df.columns:
            series = df[name]
            unique_count = int(series.nunique(dropna=True))
            null_count = int(series.isna().sum())
            col_type = _infer_type(series, str(name), unique_count, null_count, row_count)
            columns.append(
                {
                    "name": str(name),
                    "type": col_type,
                    "uniqueCount": unique_count,
                    "nullCount": null_count,
                    "sampleValues": _sample_values(series),
                }
            )
    except ValueError:
        raise
    except Exception as exc:  # noqa: BLE001 - re-raise as human-readable
        raise ValueError(f"Failed to analyze CSV columns: {exc}") from exc

    # Every column is either an identifier or high-cardinality -> nothing to chart.
    chartable = [c for c in columns if c["type"] not in ("identifier", "high_cardinality")]
    if not chartable:
        raise ValueError("No chartable columns found after type inference.")

    return {
        "rowCount": row_count,
        "columnCount": int(df.shape[1]),
        "columns": columns,
        "sample_rows": _json_rows(df.head(_SAMPLE_ROWS)),
        "all_rows": _json_rows(df.head(_MAX_ALL_ROWS)),
    }
