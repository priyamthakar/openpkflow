"""Dissolution request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel


class DissolutionColumns(BaseModel):
    formulation: str = "formulation"
    batch: str = "batch"
    time: str = "time"
    percent_released: str = "percent_released"


class FormulationsResponse(BaseModel):
    formulations: list[str]


class CompareResponse(BaseModel):
    reference_label: str
    test_label: str
    f1_value: float
    f2_value: float
    similar: bool
    n_timepoints: int
    time_points: list[float]
    reference_mean: list[float]
    test_mean: list[float]
    warnings: list[str]
    disclaimer: str
