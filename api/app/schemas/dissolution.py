"""Dissolution request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


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


class DissolutionRow(BaseModel):
    formulation: str
    batch: str
    time: float
    percent_released: float


class MediaData(BaseModel):
    name: str = Field(..., min_length=1)
    rows: list[DissolutionRow] = Field(..., min_length=1)


class MultiMediaRequest(BaseModel):
    media: list[MediaData] = Field(..., min_length=2)
    reference_label: str = "reference"
    test_label: str = "test"


class MediumCompareResult(BaseModel):
    medium: str
    f1_value: float
    f2_value: float
    similar: bool
    n_timepoints: int
    time_points: list[float]
    reference_mean: list[float]
    test_mean: list[float]


class MultiMediaResponse(BaseModel):
    reference_label: str
    test_label: str
    media_names: list[str]
    f2_summary: dict[str, float]
    overall_pass: bool
    per_media: list[MediumCompareResult]
    disclaimer: str
