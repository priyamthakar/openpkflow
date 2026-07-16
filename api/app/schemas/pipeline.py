"""Study-pipeline request and response schemas."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel


class PipelineOptions(BaseModel):
    title: str = "OpenPKFlow Study Report"
    dissolution_reference: str | None = None
    dissolution_test: str | None = None
    nca_auc_method: Literal["linear", "log", "linear_up_log_down"] | None = None
    nca_blq_method: Literal["none", "drop", "zero", "half_lloq", "lloq", "m1", "m2"] | None = None
    be_parameter: str = "AUCinf"
    be_reference_col: str = "reference"
    be_test_col: str = "test"
    be_subject_col: str = "subject"
    be_sequence_col: str | None = "sequence"
    be_lower: float = 0.80
    be_upper: float = 1.25


class PipelineResponse(BaseModel):
    metadata: dict[str, Any]
    dissolution: dict[str, Any] | None
    nca: dict[str, Any] | None
    be: dict[str, Any] | None
    disclaimer: str
