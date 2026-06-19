"""Pydantic v2 models matching the POST /api/analyze contract exactly.

Leaf module: imports nothing from the analyzer -> groq_client -> chart_builder ->
main pipeline. Used by main.py only to validate / serialize the response.
"""

from typing import Literal

from pydantic import BaseModel


class ColumnMeta(BaseModel):
    name: str
    type: str
    uniqueCount: int
    nullCount: int
    sampleValues: list


class ChartSpec(BaseModel):
    type: Literal["bar", "line", "pie", "scatter"]
    title: str
    x: str
    y: str
    insight: str
    data: list[dict]


class SummaryBlock(BaseModel):
    rowCount: int
    columnCount: int
    description: str
    columns: list[ColumnMeta]


class AnalyzeResponse(BaseModel):
    summary: SummaryBlock
    charts: list[ChartSpec]
    insights: list[str]


class ErrorResponse(BaseModel):
    error: str
