"""NCA adapter: HTTP payload -> NCAStudy -> serializable dict."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from app.schemas.nca import NcaOptions, SparseNcaRequest, SubjectProfile
from openpkflow.nca.loader import load_nca_csv
from openpkflow.nca.sparse import SparseNCAResult, fit_sparse_1cmt_oral
from openpkflow.nca.study import NCAStudy

_DISCLAIMER = (
    "This report was generated using OpenPKFlow (open-source). Final regulatory "
    "interpretation should be reviewed by qualified formulation, pharmacokinetic, "
    "and regulatory experts."
)

_SPARSE_SCOPE = (
    "Model-informed one-compartment oral screening estimate. This is not a regulatory "
    "primary analysis and requires study-specific validation before decision use."
)


def _safe(v: Any) -> Any:
    if isinstance(v, float) and not math.isfinite(v):
        return None
    return v


def run_nca(path: Path, options: NcaOptions) -> dict[str, Any]:
    cols = options.columns
    df = load_nca_csv(
        path,
        subject_col=cols.subject,
        time_col=cols.time,
        conc_col=cols.conc,
        dose_col=cols.dose,
        route_col=cols.route,
        blq_method=options.blq_method,
        lloq=options.lloq,
    )
    study = NCAStudy(
        df,
        auc_method=options.auc_method,
        blq_method=options.blq_method,
        steady_state=options.steady_state,
        tau=options.tau,
    )
    summary = study.analyze()

    frame = summary.to_dataframe()
    records: list[dict[str, Any]] = [
        {k: _safe(v) for k, v in row.items()} for row in frame.to_dict(orient="records")
    ]

    by_subject = {str(r.subject): r for r in summary.results}
    profiles: list[dict[str, Any]] = []
    warnings_all: list[str] = []
    for subject, grp in df.groupby("subject", sort=True):
        g = grp.sort_values("time")
        res = by_subject.get(str(subject))
        profiles.append(
            SubjectProfile(
                subject=str(subject),
                times=g["time"].tolist(),
                concs=g["conc"].tolist(),
                lambda_z_times=list(res.selected_lambda_z_times) if res else [],
                lambda_z_concs=list(res.selected_lambda_z_concs) if res else [],
            ).model_dump()
        )
        if res and res.warnings:
            warnings_all.extend(f"[{subject}] {w}" for w in res.warnings)

    return {
        "columns": list(frame.columns),
        "subjects": records,
        "profiles": profiles,
        "warnings": warnings_all,
        "disclaimer": _DISCLAIMER,
    }


def write_nca_report(path: Path, options: NcaOptions, out_path: Path, fmt: str) -> None:
    cols = options.columns
    df = load_nca_csv(
        path,
        subject_col=cols.subject,
        time_col=cols.time,
        conc_col=cols.conc,
        dose_col=cols.dose,
        route_col=cols.route,
        blq_method=options.blq_method,
        lloq=options.lloq,
    )
    study = NCAStudy(
        df,
        auc_method=options.auc_method,
        blq_method=options.blq_method,
        steady_state=options.steady_state,
        tau=options.tau,
    )
    summary = study.analyze()
    summary.report(out_path, format=fmt)


def run_sparse_nca(request: SparseNcaRequest) -> tuple[SparseNCAResult, dict[str, Any]]:
    result = fit_sparse_1cmt_oral(request.times, request.concentrations, request.dose)
    result.subject = request.subject
    warnings: list[str] = []
    if not result.converged:
        warnings.append("The nonlinear fit did not converge; parameter estimates are unreliable.")
    if any(value is None for value in (result.CL_F_se, result.Vz_F_se, result.ka_se)):
        warnings.append(
            "Parameter standard errors are unavailable; the fit may be weakly identified."
        )
    if result.n_samples < 5:
        warnings.append(
            "Fewer than five samples provide limited support for a three-parameter fit."
        )
    return result, {
        **result.to_dict(),
        "warnings": warnings,
        "scope_note": _SPARSE_SCOPE,
        "disclaimer": _DISCLAIMER,
    }


def write_sparse_nca_report(request: SparseNcaRequest, out_path: Path, fmt: str) -> None:
    result, _payload = run_sparse_nca(request)
    result.report(out_path, format=fmt)
