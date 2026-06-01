"""NCA request/response schemas."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class NcaColumns(BaseModel):
    subject: str = "subject"
    time: str = "time"
    conc: str = "conc"
    dose: str = "dose"
    route: str = "route"


class NcaOptions(BaseModel):
    auc_method: Literal["linear", "log", "linear_up_log_down"] = "linear"
    blq_method: str = "none"
    lloq: float | None = None
    steady_state: bool = False
    tau: float | None = None
    columns: NcaColumns = Field(default_factory=NcaColumns)


class SubjectProfile(BaseModel):
    subject: str
    times: list[float]
    concs: list[float]
    lambda_z_times: list[float]
    lambda_z_concs: list[float]


class NcaResponse(BaseModel):
    columns: list[str]
    subjects: list[dict[str, Any]]
    profiles: list[SubjectProfile]
    warnings: list[str]
    disclaimer: str
