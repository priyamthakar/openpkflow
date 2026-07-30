"""Dissolution request/response schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


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


class WorkbenchConfigRequest(BaseModel):
    reference_label: str = Field(..., min_length=1)
    test_label: str = Field(..., min_length=1)
    f2_method: Literal["regulatory", "all_points"] = "regulatory"
    bootstrap_replicates: int = Field(default=5000, ge=100, le=100_000)
    confidence_level: float = Field(default=0.90, gt=0.0, lt=1.0)
    seed: int | None = 2026
    model_comparison_model: Literal[
        "zero_order",
        "first_order",
        "higuchi",
        "korsmeyer_peppas",
        "weibull",
    ] = "weibull"
    model_comparison_param_index: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def labels_are_distinct(self) -> WorkbenchConfigRequest:
        if self.reference_label == self.test_label:
            raise ValueError("reference_label and test_label must be different.")
        return self


class WorkbenchRequest(BaseModel):
    rows: list[DissolutionRow] = Field(..., min_length=1)
    config: WorkbenchConfigRequest


class WorkbenchMetadataResponse(BaseModel):
    openpkflow_version: str
    generated_at_utc: str
    workflow: str


class VesselProfileResponse(BaseModel):
    formulation: str
    vessel_id: str
    time_points: list[float]
    percent_released: list[float]


class WorkbenchVesselProfilesResponse(BaseModel):
    reference: list[VesselProfileResponse]
    test: list[VesselProfileResponse]


class WorkbenchSimilarityResponse(BaseModel):
    reference_label: str
    test_label: str
    f1_value: float
    f2_value: float
    n_timepoints: int
    reference_mean: list[float]
    test_mean: list[float]
    time_points: list[float]
    f2_method: Literal["regulatory", "all_points"]
    similar: bool
    warnings: list[str]


class WorkbenchBootstrapResponse(BaseModel):
    f2_observed: float
    ci_lower: float
    ci_upper: float
    confidence_level: float
    n_replicates: int
    n_timepoints: int
    n_reference_vessels: int
    n_test_vessels: int
    is_similar: bool
    method: Literal["all_points"]


class WorkbenchModelFitResponse(BaseModel):
    model_name: str
    params: dict[str, float]
    r_squared: float | None
    aic: float | None
    aicc: float | None
    bic: float | None
    n_points: int
    n_params: int
    converged: bool
    fitted_values: list[float]
    time_points: list[float]


class WorkbenchFormulationModelsResponse(BaseModel):
    formulation_label: str
    time_points: list[float]
    observed_mean: list[float]
    best_model: str
    fits: list[WorkbenchModelFitResponse]


class WorkbenchModelsResponse(BaseModel):
    reference: WorkbenchFormulationModelsResponse
    test: WorkbenchFormulationModelsResponse


class WorkbenchModelComparisonResponse(BaseModel):
    model_name: str
    param_name: str
    ref_value: float
    test_value: float
    se_diff: float
    ratio_pct: float
    ci_lo: float
    ci_hi: float
    is_similar: bool


class WorkbenchAlternativesResponse(BaseModel):
    maximum_deviation: float
    msd: float
    msd_squared: float
    chi2_05_critical: float
    n_timepoints: int
    msd_is_similar: bool


class WorkbenchResponse(BaseModel):
    metadata: WorkbenchMetadataResponse
    config: WorkbenchConfigRequest
    normalized_rows: list[DissolutionRow]
    vessel_profiles: WorkbenchVesselProfilesResponse
    similarity: WorkbenchSimilarityResponse
    bootstrap_f2: WorkbenchBootstrapResponse
    model_fits: WorkbenchModelsResponse
    model_comparison: WorkbenchModelComparisonResponse
    alternatives: WorkbenchAlternativesResponse
    warnings: list[str]
    disclaimer: str
