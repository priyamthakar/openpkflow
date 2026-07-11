"""IVIVC request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel


class IvIvcRequest(BaseModel):
    in_vivo_times: list[float]
    in_vivo_concs: list[float]
    dissolution_times: list[float]
    dissolution_pct: list[float]
    iv_uir_times: list[float]
    iv_uir_concs: list[float]
    method: str = "wagner_nelson"
    kel: float | None = None
    k12: float | None = None
    k21: float | None = None
    dose_diss: float | None = None
    dose_iv: float | None = None
    study_label: str = ""
    # Web UI dissolution grid is labeled minutes; library converts to hours.
    dissolution_time_unit: str = "minutes"


class IvIvcResponse(BaseModel):
    method: str
    study_label: str
    times: list[float]
    concentrations: list[float]
    fa: list[float]
    levy_slope: float | None
    levy_intercept: float | None
    levy_r_squared: float | None
    ivt_times: list[float]
    ivt_fraction: list[float]
    predicted_times: list[float]
    predicted_concs: list[float]
    pe_cmax: float | None
    pe_auc: float | None
    mean_abs_pe: float | None
    overall_pass: bool | None
    predictability_note: str | None = None
    disclaimer: str
