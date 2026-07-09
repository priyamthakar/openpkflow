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
