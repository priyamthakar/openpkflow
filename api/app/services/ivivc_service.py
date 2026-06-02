"""IVIVC adapter: HTTP payload -> IVIVCStudy -> serializable dict."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from app.schemas.ivivc import IvIvcRequest
from openpkflow.ivivc.study import IVIVCStudy

_DISCLAIMER = (
    "This report was generated using OpenPKFlow (open-source). Final regulatory "
    "interpretation should be reviewed by qualified formulation, pharmacokinetic, "
    "and regulatory experts."
)


def _safe(v: Any) -> Any:
    if isinstance(v, float) and not math.isfinite(v):
        return None
    return v


def run_ivivc(req: IvIvcRequest) -> dict[str, Any]:
    study = IVIVCStudy(
        in_vivo_times=req.in_vivo_times,
        in_vivo_concs=req.in_vivo_concs,
        dissolution_times=req.dissolution_times,
        dissolution_pct=req.dissolution_pct,
        iv_uir_times=req.iv_uir_times,
        iv_uir_concs=req.iv_uir_concs,
        method=req.method,
        kel=req.kel,
        k12=req.k12,
        k21=req.k21,
        dose_diss=req.dose_diss,
        dose_iv=req.dose_iv,
        study_label=req.study_label,
    )
    result = study.analyze()

    lp = result.levy_plot
    pp = result.predictability

    return {
        "method": result.method,
        "study_label": result.study_label,
        "times": result.times.tolist(),
        "concentrations": result.concentrations.tolist(),
        "fa": result.fa.tolist(),
        "levy_slope": _safe(lp.get("slope")),
        "levy_intercept": _safe(lp.get("intercept")),
        "levy_r_squared": _safe(lp.get("r_squared")),
        "ivt_times": result.ivt_times.tolist(),
        "ivt_fraction": result.ivt_fraction.tolist(),
        "predicted_times": result.predicted_times.tolist(),
        "predicted_concs": result.predicted_concs.tolist(),
        "pe_cmax": _safe(pp.get("%PE_Cmax")),
        "pe_auc": _safe(pp.get("%PE_AUC")),
        "mean_abs_pe": _safe(pp.get("mean_abs_%PE")),
        "overall_pass": bool(pp.get("overall_pass", False)),
        "disclaimer": _DISCLAIMER,
    }


def write_ivivc_report(req: IvIvcRequest, out_path: Path, fmt: str) -> None:
    study = IVIVCStudy(
        in_vivo_times=req.in_vivo_times,
        in_vivo_concs=req.in_vivo_concs,
        dissolution_times=req.dissolution_times,
        dissolution_pct=req.dissolution_pct,
        iv_uir_times=req.iv_uir_times,
        iv_uir_concs=req.iv_uir_concs,
        method=req.method,
        kel=req.kel,
        k12=req.k12,
        k21=req.k21,
        dose_diss=req.dose_diss,
        dose_iv=req.dose_iv,
        study_label=req.study_label,
    )
    result = study.analyze()
    result.report(out_path, format=fmt)
