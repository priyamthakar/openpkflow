"""SUPAC-IR and alcohol dose-dumping adapter: payload -> core helpers -> dict."""

from __future__ import annotations

from typing import Any

from app.schemas.supac import AlcoholDosingRequest, SupacClassifyRequest
from openpkflow.dissolution.supac import (
    alcohol_dose_dumping_assessment,
    classify_supac_ir_level,
)

_DISCLAIMER = (
    "This report was generated using OpenPKFlow (open-source). Final regulatory "
    "interpretation should be reviewed by qualified formulation, pharmacokinetic, "
    "and regulatory experts."
)

_SCOPE = (
    "SUPAC-IR screening only. This does not replace full SUPAC guidance "
    "interpretation, regulatory filing strategy, cumulative multi-component "
    "totals, site/scale/equipment change assessment, or qualified CMC judgement."
)


def run_supac_classify(request: SupacClassifyRequest) -> dict[str, Any]:
    result = classify_supac_ir_level(request.change_pct, request.component_category)
    return {
        "level": result.level,
        "change_pct": result.change_pct,
        "component_category": result.component_category,
        "rationale": result.rationale,
        "recommended_tests": result.recommended_tests,
        "scope_note": _SCOPE,
        "disclaimer": _DISCLAIMER,
    }


def run_alcohol_dosing(request: AlcoholDosingRequest) -> dict[str, Any]:
    eth_means = {p.ethanol_pct: p.means for p in request.ethanol_profiles}
    result = alcohol_dose_dumping_assessment(
        control_means=request.control_means,
        eth_means_by_pct=eth_means,
        time_points=request.time_points,
        f2_threshold=request.f2_threshold,
        control_label=request.control_label,
    )
    return {
        "control_label": result.control_label,
        "f2_by_ethanol_pct": {f"{k:g}": v for k, v in result.f2_by_ethanol_pct.items()},
        "f2_threshold": result.f2_threshold,
        "f2_method": "regulatory",
        "overall_pass": result.overall_pass,
        "scope_note": _SCOPE,
        "disclaimer": _DISCLAIMER,
    }
