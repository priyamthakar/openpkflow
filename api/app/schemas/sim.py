"""Simulation request/response schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SimParams(BaseModel):
    """Structural PK parameters — which are required depends on model_type + route."""

    CL: float | None = None
    Vz: float | None = None
    CL_F: float | None = None
    Vz_F: float | None = None
    V1: float | None = None
    V1_F: float | None = None
    Q: float | None = None
    V2: float | None = None
    ka: float | None = None


class SimRegimen(BaseModel):
    amount: float = 100.0
    tau: float = 12.0
    n_doses: int = 1
    t_start: float = 0.0
    t_inf: float | None = None


class SimTimeGrid(BaseModel):
    start: float = 0.0
    stop: float = 48.0
    n: int = Field(default=300, ge=2, le=5000)


class SimRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    model_type: Literal["1cmt", "2cmt"] = "1cmt"
    route: Literal["iv_bolus", "iv_infusion", "oral"] = "oral"
    params: SimParams = Field(default_factory=SimParams)
    regimen: SimRegimen = Field(default_factory=SimRegimen)
    times: SimTimeGrid = Field(default_factory=SimTimeGrid)


class SimResponse(BaseModel):
    times: list[float]
    concs: list[float]
    dose_times: list[float]
    Cmax: float
    Tmax: float
    Cmin: float
    Clast: float
    warnings: list[str]
    disclaimer: str
