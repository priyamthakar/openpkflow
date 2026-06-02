"""BE request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel


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
