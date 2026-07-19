"""SUPAC-IR screening and alcohol dose-dumping request/response schemas."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

_MAX_PROFILE_POINTS = 50
_MAX_ETHANOL_MEDIA = 12
_MAX_LABEL_LENGTH = 100

ComponentCategory = Literal[
    "filler",
    "binder",
    "disintegrant_starch",
    "disintegrant_other",
    "lubricant_stearate",
    "lubricant_other",
    "glidant",
    "film_coat",
    "non_critical",
    "critical",
]

SupacLevel = Literal[1, 2, 3]


class SupacClassifyRequest(BaseModel):
    component_category: ComponentCategory
    change_pct: float = Field(ge=0.0)


class SupacClassifyResponse(BaseModel):
    level: SupacLevel
    change_pct: float
    component_category: str
    rationale: str
    recommended_tests: list[str]
    scope_note: str
    disclaimer: str


class EthanolProfile(BaseModel):
    ethanol_pct: float = Field(gt=0.0, le=100.0)
    means: list[float] = Field(min_length=3, max_length=_MAX_PROFILE_POINTS)

    @field_validator("ethanol_pct", "means")
    @classmethod
    def _finite_values(cls, value: float | list[float]) -> float | list[float]:
        values = value if isinstance(value, list) else [value]
        if not all(math.isfinite(item) for item in values):
            raise ValueError("ethanol profile values must be finite.")
        if isinstance(value, list) and any(item < 0.0 or item > 100.0 for item in value):
            raise ValueError("dissolution means must be in [0, 100].")
        return value


class AlcoholDosingRequest(BaseModel):
    time_points: list[float] = Field(min_length=3, max_length=_MAX_PROFILE_POINTS)
    control_means: list[float] = Field(min_length=3, max_length=_MAX_PROFILE_POINTS)
    ethanol_profiles: list[EthanolProfile] = Field(min_length=1, max_length=_MAX_ETHANOL_MEDIA)
    f2_threshold: float = Field(gt=0.0, le=100.0, default=50.0)
    control_label: str = Field(default="control", max_length=_MAX_LABEL_LENGTH)

    @field_validator("time_points", "control_means", "f2_threshold")
    @classmethod
    def _finite_values(cls, value: float | list[float]) -> float | list[float]:
        values = value if isinstance(value, list) else [value]
        if not all(math.isfinite(item) for item in values):
            raise ValueError("alcohol screening values must be finite.")
        if isinstance(value, list) and any(item < 0.0 or item > 100.0 for item in value):
            raise ValueError("dissolution means must be in [0, 100].")
        return value

    @model_validator(mode="after")
    def _matched_profiles(self) -> AlcoholDosingRequest:
        if len(self.time_points) != len(self.control_means):
            raise ValueError("time_points and control_means must have the same length.")
        if any(value < 0.0 for value in self.time_points):
            raise ValueError("time_points must be >= 0.")
        if any(
            right <= left
            for left, right in zip(self.time_points, self.time_points[1:], strict=False)
        ):
            raise ValueError("time_points must be strictly increasing.")
        if any(len(profile.means) != len(self.time_points) for profile in self.ethanol_profiles):
            raise ValueError("each ethanol profile must match the time_points length.")
        if len({profile.ethanol_pct for profile in self.ethanol_profiles}) != len(
            self.ethanol_profiles
        ):
            raise ValueError("ethanol percentages must be unique.")
        return self


class AlcoholDosingResponse(BaseModel):
    control_label: str
    f2_by_ethanol_pct: dict[str, float]
    f2_threshold: float
    f2_method: Literal["regulatory"]
    overall_pass: bool
    scope_note: str
    disclaimer: str
