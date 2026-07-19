"""BE request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class BeOptions(BaseModel):
    parameter: str = "AUCinf"
    reference_col: str = "reference"
    test_col: str = "test"
    subject_col: str = "subject"
    sequence_col: str | None = "sequence"
    be_lower: float = 0.80
    be_upper: float = 1.25
    alpha: float = 0.05
    columns: dict[str, str] = {}


class SubjectRow(BaseModel):
    subject: str
    reference: float
    test: float
    ratio: float
    log_diff: float
    sequence: str | None = None


class BeResponse(BaseModel):
    parameter: str
    n: int
    gmr: float
    gmr_lower_90ci: float
    gmr_upper_90ci: float
    be_lower: float
    be_upper: float
    bioequivalent: bool
    cv_intra_pct: float
    subjects: list[SubjectRow]
    disclaimer: str


class FormalBeOptions(BaseModel):
    parameter: str = "AUCinf"
    value_col: str | None = None
    subject_col: str = "subject"
    sequence_col: str = "sequence"
    period_col: str = "period"
    treatment_col: str = "treatment"
    be_lower: float = Field(default=0.80, gt=0)
    be_upper: float = Field(default=1.25, gt=0)
    alpha: float = Field(default=0.05, gt=0, lt=0.5)
    columns: dict[str, str] = Field(default_factory=dict)


class FormalAnovaRow(BaseModel):
    source: str
    df: int
    sum_squares: float
    mean_square: float | None
    f_value: float | None
    p_value: float | None


class FormalBeResponse(BaseModel):
    parameter: str
    design: str
    n_subjects: int
    alpha: float
    confidence_level_pct: float
    be_lower: float
    be_upper: float
    treatment_log_lsmean: float
    reference_log_lsmean: float
    treatment_difference: float
    treatment_se: float
    residual_mse: float
    residual_df: int
    cv_intra_pct: float
    gmr: float
    gmr_lower_ci: float
    gmr_upper_ci: float
    decision: str
    anova: list[FormalAnovaRow]
    disclaimer: str


class RsabeOptions(BaseModel):
    parameter: str = "AUC"
    value_col: str | None = None
    subject_col: str = "subject"
    sequence_col: str = "sequence"
    period_col: str = "period"
    treatment_col: str = "treatment"
    alpha: float = Field(default=0.05, gt=0, lt=0.5)
    sigma_wr_floor: float = Field(default=0.25, gt=0)
    highly_variable_cv_pct: float = Field(default=30.0, gt=0)
    columns: dict[str, str] = Field(default_factory=dict)


class RsabeResponse(BaseModel):
    parameter: str
    decision: str
    design: str
    jurisdiction: str
    validation_status: str
    message: str
    n_subjects: int
    alpha: float
    confidence_level_pct: float
    delta_hat: float
    delta_ci_lower: float
    delta_ci_upper: float
    gmr: float
    gmr_ci_lower: float
    gmr_ci_upper: float
    sigma_wr: float
    sigma_wr_ci_lower: float
    sigma_wr_ci_upper: float
    cv_wr_pct: float
    highly_variable: bool
    theta: float
    aggregate_criterion_point: float
    aggregate_criterion_upper: float
    point_estimate_constraint_met: bool
    disclaimer: str


class PowerRequest(BaseModel):
    gmr: float = Field(..., gt=0, description="True geometric mean ratio (test/reference).")
    cv: float = Field(..., gt=0, description="Intra-subject CV as fraction (e.g. 0.20 for 20%).")
    n: int = Field(..., ge=3, description="Number of subjects.")
    be_lower: float = 0.80
    be_upper: float = 1.25
    alpha: float = 0.05


class PowerResponse(BaseModel):
    power: float
    gmr: float
    cv: float
    n: int
    be_lower: float
    be_upper: float
    alpha: float
    disclaimer: str


class SampleSizeRequest(BaseModel):
    gmr: float = Field(..., gt=0, description="Assumed true GMR (test/reference).")
    cv: float = Field(..., gt=0, description="Intra-subject CV as fraction (e.g. 0.20 for 20%).")
    target_power: float = Field(0.80, gt=0, lt=1)
    be_lower: float = 0.80
    be_upper: float = 1.25
    alpha: float = 0.05
    max_n: int = Field(1000, ge=4)


class SampleSizeResponse(BaseModel):
    n: int
    achieved_power: float
    gmr: float
    cv: float
    target_power: float
    be_lower: float
    be_upper: float
    alpha: float
    disclaimer: str
