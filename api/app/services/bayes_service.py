"""Bayesian MAP PK adapter: HTTP payload -> map_individual_pk -> serializable dict."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from app.schemas.bayes import MapPkRequest
from openpkflow.bayes.map_pk import map_individual_pk
from openpkflow.bayes.priors import PKPrior

_DISCLAIMER = (
    "This report was generated using OpenPKFlow (open-source). Final regulatory "
    "interpretation should be reviewed by qualified formulation, pharmacokinetic, "
    "and regulatory experts."
)

_SCOPE = (
    "MAP (maximum a posteriori) individual PK screening estimate. This is a "
    "model-informed screening tool, not a regulatory primary analysis, and "
    "requires study-specific validation before any decision use. Prior-dominated "
    "or non-converged fits must not be interpreted as definitive."
)


def _fit(request: MapPkRequest) -> tuple[Any, list[str], bool]:
    prior = PKPrior()
    result = map_individual_pk(
        request.times,
        request.concentrations,
        request.dose,
        request.route,
        prior,
        subject=request.subject,
    )

    warnings: list[str] = list(result.warnings)
    if not result.converged:
        warnings.append(
            "The MAP optimizer did not converge; estimates are unreliable. "
            "Do not interpret as a definitive individual PK profile."
        )
    if not result.uncertainty_reliable:
        warnings.append(
            "Standard errors are not available; the fit is weakly identified "
            "or the Hessian is ill-conditioned."
        )
    if result.n_observations < 4 and request.route == "oral":
        warnings.append(
            "Fewer than four observations provide limited support for a three-parameter oral model."
        )

    fit_usable = (
        result.converged
        and result.uncertainty_reliable
        and math.isfinite(result.gradient_norm)
        and result.gradient_norm <= 1e-3
        and math.isfinite(result.condition_number)
        and math.isfinite(result.objective_value)
    )
    if not fit_usable:
        warnings.append(
            "Fit usability failed. Parameter estimates and derived values must not be used."
        )
    return result, warnings, fit_usable


def _safe(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def run_map_pk(request: MapPkRequest) -> dict[str, Any]:
    result, warnings, fit_usable = _fit(request)
    payload = {key: _safe(value) for key, value in result.to_dict().items()}
    payload["warnings"] = warnings
    payload["fit_usable"] = fit_usable
    payload["scope_note"] = _SCOPE
    payload["disclaimer"] = _DISCLAIMER
    return payload


def write_map_pk_report(request: MapPkRequest, out_path: Path, fmt: str) -> None:
    result, warnings, fit_usable = _fit(request)
    result.warnings = [*warnings, _SCOPE]
    if not fit_usable:
        result.warnings.append(
            "This report does not make the unusable estimates suitable for decision use."
        )
    result.report(out_path, format=fmt)
