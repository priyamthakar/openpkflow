"""Bayesian MAP individual PK request/response schemas."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

_MAX_SAMPLES = 100
_MAX_SUBJECT_LENGTH = 200


class MapPkRequest(BaseModel):
    subject: str = Field(default="", max_length=_MAX_SUBJECT_LENGTH)
    times: list[float] = Field(min_length=2, max_length=_MAX_SAMPLES)
    concentrations: list[float] = Field(min_length=2, max_length=_MAX_SAMPLES)
    dose: float = Field(gt=0, le=1e12)
    route: Literal["oral", "iv_bolus"] = "oral"

    @field_validator("dose")
    @classmethod
    def _finite_dose(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("dose must be finite.")
        return value

    @field_validator("times", "concentrations")
    @classmethod
    def _finite_values(cls, values: list[float]) -> list[float]:
        if not all(math.isfinite(value) for value in values):
            raise ValueError("sample values must be finite.")
        return values

    @model_validator(mode="after")
    def _valid_profile(self) -> MapPkRequest:
        if len(self.times) != len(self.concentrations):
            raise ValueError("times and concentrations must have the same length.")
        if any(value < 0 for value in self.times):
            raise ValueError("times must be >= 0.")
        if any(right <= left for left, right in zip(self.times, self.times[1:], strict=False)):
            raise ValueError("times must be strictly increasing.")
        if any(value < 0 for value in self.concentrations):
            raise ValueError("concentrations must be >= 0.")
        if not any(value > 0 for value in self.concentrations):
            raise ValueError("concentrations must contain at least one value > 0.")
        return self


class MapPkResponse(BaseModel):
    subject: str
    route: Literal["oral", "iv_bolus"]
    dose: float
    n_observations: int
    converged: bool
    uncertainty_reliable: bool
    fit_usable: bool
    CL_F: float | None
    Vz_F: float | None
    ka: float | None
    CL: float | None
    Vz: float | None
    CL_F_se: float | None
    Vz_F_se: float | None
    ka_se: float | None
    CL_se: float | None
    Vz_se: float | None
    k: float
    half_life: float
    AUCinf: float
    Cmax: float
    Tmax: float
    gradient_norm: float | None
    condition_number: float | None
    objective_value: float | None
    time_points: list[float]
    observed_conc: list[float]
    predicted_conc: list[float]
    warnings: list[str]
    scope_note: str
    disclaimer: str
