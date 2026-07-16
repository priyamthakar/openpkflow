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


class SparseNcaRequest(BaseModel):
    subject: str = ""
    times: list[float] = Field(min_length=3)
    concentrations: list[float] = Field(min_length=3)
    dose: float = Field(gt=0)


class SparseNcaResponse(BaseModel):
    subject: str
    dose: float
    route: Literal["oral"]
    n_samples: int
    converged: bool
    CL_F: float
    Vz_F: float
    ka: float
    k: float
    half_life: float
    CL_F_se: float | None
    Vz_F_se: float | None
    ka_se: float | None
    AUClast: float
    AUCinf: float
    Cmax: float
    Tmax: float
    time_points: list[float]
    observed_conc: list[float]
    fitted_conc: list[float]
    warnings: list[str]
    scope_note: str
    disclaimer: str
