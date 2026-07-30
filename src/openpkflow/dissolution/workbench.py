"""Auditable orchestration for the validated dissolution toolkit."""

from __future__ import annotations

import json
import math
import warnings
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Literal

import numpy as np
import pandas as pd

from openpkflow import __version__
from openpkflow.dissolution.bootstrap import BootstrapF2Result, bootstrap_f2
from openpkflow.dissolution.loader import (
    DissolutionCSVConfig,
    validate_dissolution_dataframe,
)
from openpkflow.dissolution.models import (
    DissolutionFitResults,
    ModelComparisonResult,
    fit_dissolution_models,
    model_dependent_comparison,
)
from openpkflow.dissolution.similarity import MSDResult, max_deviation, msd
from openpkflow.dissolution.study import ComparisonResult, DissolutionStudy

if TYPE_CHECKING:
    from collections.abc import Sequence

VALIDATED_WORKBENCH_MODELS: tuple[str, ...] = (
    "zero_order",
    "first_order",
    "higuchi",
    "korsmeyer_peppas",
    "weibull",
)

_DISCLAIMER = (
    "This report was generated using OpenPKFlow (open-source). Final regulatory "
    "interpretation should be reviewed by qualified formulation, pharmacokinetic, "
    "and regulatory experts."
)


@dataclass(frozen=True)
class DissolutionWorkbenchConfig:
    """Configuration for a complete dissolution workbench analysis.

    Parameters
    ----------
    reference_label : str
        Reference formulation label.
    test_label : str
        Test formulation label.
    f2_method : {"regulatory", "all_points"}, optional
        Time-point method for the point-estimate f2 calculation.
    bootstrap_replicates : int, optional
        Number of bootstrap resamples.
    confidence_level : float, optional
        Bootstrap confidence level.
    seed : int | None, optional
        Reproducible bootstrap seed.
    model_comparison_model : str, optional
        Validated model used for the parameter comparison.
    model_comparison_param_index : int, optional
        Zero-based fitted parameter index.
    """

    reference_label: str
    test_label: str
    f2_method: Literal["regulatory", "all_points"] = "regulatory"
    bootstrap_replicates: int = 5000
    confidence_level: float = 0.90
    seed: int | None = 2026
    model_comparison_model: str = "weibull"
    model_comparison_param_index: int = 0

    def __post_init__(self) -> None:
        """Validate configuration values."""
        if not self.reference_label.strip() or not self.test_label.strip():
            raise ValueError("reference_label and test_label must not be empty.")
        if self.reference_label == self.test_label:
            raise ValueError("reference_label and test_label must be different.")
        if self.f2_method not in {"regulatory", "all_points"}:
            raise ValueError("f2_method must be 'regulatory' or 'all_points'.")
        if self.bootstrap_replicates < 100:
            raise ValueError("bootstrap_replicates must be at least 100.")
        if not 0.0 < self.confidence_level < 1.0:
            raise ValueError("confidence_level must be between 0 and 1.")
        if self.model_comparison_model not in VALIDATED_WORKBENCH_MODELS:
            raise ValueError(
                f"model_comparison_model must be one of {list(VALIDATED_WORKBENCH_MODELS)}."
            )
        if self.model_comparison_param_index < 0:
            raise ValueError("model_comparison_param_index must be non-negative.")

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-safe configuration dictionary.

        Returns
        -------
        dict[str, object]
            Exact analysis configuration.
        """
        return asdict(self)


@dataclass(frozen=True)
class VesselProfile:
    """One vessel-level dissolution profile."""

    formulation: str
    vessel_id: str
    time_points: list[float]
    percent_released: list[float]

    def to_dict(self) -> dict[str, object]:
        """Return a serializable vessel profile.

        Returns
        -------
        dict[str, object]
            Vessel label, formulation, time points, and measurements.
        """
        return asdict(self)


@dataclass
class DissolutionWorkbenchResult:
    """Complete result from the Advanced Dissolution Workbench."""

    config: DissolutionWorkbenchConfig
    normalized_rows: list[dict[str, str | float]]
    reference_vessels: list[VesselProfile]
    test_vessels: list[VesselProfile]
    comparison: ComparisonResult
    bootstrap: BootstrapF2Result
    reference_models: DissolutionFitResults
    test_models: DissolutionFitResults
    model_comparison: ModelComparisonResult
    msd_result: MSDResult
    maximum_deviation: float
    warnings: list[str]
    generated_at_utc: str

    def to_dict(self) -> dict[str, object]:
        """Return the full result as JSON-safe basic types.

        Returns
        -------
        dict[str, object]
            Serialized inputs, configuration, calculations, and evidence labels.
        """
        return {
            "metadata": {
                "openpkflow_version": __version__,
                "generated_at_utc": self.generated_at_utc,
                "workflow": "advanced_dissolution_workbench",
            },
            "config": self.config.to_dict(),
            "normalized_rows": self.normalized_rows,
            "vessel_profiles": {
                "reference": [profile.to_dict() for profile in self.reference_vessels],
                "test": [profile.to_dict() for profile in self.test_vessels],
            },
            "similarity": {
                **self.comparison.to_dict(),
                "f2_method": self.comparison.f2_method,
                "similar": self.comparison.f2_value >= 50.0,
                "warnings": list(self.comparison.warnings),
            },
            "bootstrap_f2": {
                "f2_observed": self.bootstrap.f2_observed,
                "ci_lower": self.bootstrap.ci_lower,
                "ci_upper": self.bootstrap.ci_upper,
                "confidence_level": self.bootstrap.confidence_level,
                "n_replicates": self.bootstrap.n_replicates,
                "n_timepoints": self.bootstrap.n_timepoints,
                "n_reference_vessels": self.bootstrap.n_reference_vessels,
                "n_test_vessels": self.bootstrap.n_test_vessels,
                "is_similar": self.bootstrap.is_similar,
                "method": "all_points",
            },
            "model_fits": {
                "reference": _serialize_model_results(self.reference_models),
                "test": _serialize_model_results(self.test_models),
            },
            "model_comparison": {
                "model_name": self.model_comparison.model_name,
                "param_name": self.model_comparison.param_name,
                "ref_value": self.model_comparison.ref_value,
                "test_value": self.model_comparison.test_value,
                "se_diff": self.model_comparison.se_diff,
                "ratio_pct": self.model_comparison.ratio_pct,
                "ci_lo": self.model_comparison.ci_lo,
                "ci_hi": self.model_comparison.ci_hi,
                "is_similar": self.model_comparison.is_similar,
            },
            "alternatives": {
                "maximum_deviation": self.maximum_deviation,
                "msd": self.msd_result.msd,
                "msd_squared": self.msd_result.msd_squared,
                "chi2_05_critical": self.msd_result.chi2_05_critical,
                "n_timepoints": self.msd_result.n_timepoints,
                "msd_is_similar": self.msd_result.is_similar,
            },
            "warnings": list(self.warnings),
            "disclaimer": _DISCLAIMER,
        }

    def report(
        self,
        output_path: str | Path,
        *,
        format: Literal["html", "pdf", "docx"] = "html",
    ) -> str | bytes:
        """Write a complete workbench report.

        Parameters
        ----------
        output_path : str | Path
            Destination report path.
        format : {"html", "pdf", "docx"}, optional
            Report format.

        Returns
        -------
        str | bytes
            Rendered report content.
        """
        from openpkflow.dissolution.workbench_reporting import report_workbench

        return report_workbench(self, output_path, format=format)

    def audit_bundle(self, output_path: str | Path) -> Path:
        """Write a reproducibility ZIP with a SHA-256 manifest.

        Parameters
        ----------
        output_path : str | Path
            Destination ZIP path.

        Returns
        -------
        Path
            Resolved archive path.
        """
        from openpkflow.dissolution.workbench_reporting import write_workbench_audit_bundle

        return write_workbench_audit_bundle(self, output_path)


def _serialize_model_results(results: DissolutionFitResults) -> dict[str, object]:
    fits: list[dict[str, object]] = []
    for fit in sorted(results.fits, key=lambda item: (not item.converged, _finite(item.aicc))):
        fits.append(
            {
                "model_name": fit.model_name,
                "params": {name: value for name, value in fit.params.items()},
                "r_squared": _finite_or_none(fit.r_squared),
                "aic": _finite_or_none(fit.aic),
                "aicc": _finite_or_none(fit.aicc),
                "bic": _finite_or_none(fit.bic),
                "n_points": fit.n_points,
                "n_params": fit.n_params,
                "converged": fit.converged,
                "fitted_values": list(fit.fitted_values),
                "time_points": list(fit.time_points),
            }
        )
    best = results.best
    return {
        "formulation_label": results.formulation_label,
        "time_points": list(results.time_points),
        "observed_mean": list(results.observed_mean),
        "best_model": best.model_name,
        "fits": fits,
    }


def _finite(value: float) -> float:
    return value if math.isfinite(value) else math.inf


def _finite_or_none(value: float) -> float | None:
    return value if math.isfinite(value) else None


def _vessel_profiles(
    df: pd.DataFrame,
    formulation: str,
) -> tuple[list[VesselProfile], np.ndarray, list[float]]:
    subset = df[df["formulation"] == formulation]
    if subset.empty:
        raise ValueError(f"Formulation '{formulation}' was not found.")
    if subset["batch"].str.strip().eq("").any():
        raise ValueError(f"Formulation '{formulation}' contains an empty vessel identifier.")
    duplicate = subset.duplicated(subset=["batch", "time"], keep=False)
    if duplicate.any():
        pairs = (
            subset.loc[duplicate, ["batch", "time"]]
            .drop_duplicates()
            .astype(str)
            .agg("@".join, axis=1)
            .tolist()
        )
        raise ValueError(f"Formulation '{formulation}' has duplicate vessel/time rows: {pairs}.")

    profiles: list[VesselProfile] = []
    expected_times: list[float] | None = None
    matrix_rows: list[list[float]] = []
    for batch, group in subset.groupby("batch", sort=True):
        ordered = group.sort_values("time")
        times = ordered["time"].astype(float).tolist()
        values = ordered["percent_released"].astype(float).tolist()
        if expected_times is None:
            expected_times = times
        elif times != expected_times:
            raise ValueError(
                f"Formulation '{formulation}' vessel '{batch}' does not share "
                "the same time points as the other vessels."
            )
        profiles.append(
            VesselProfile(
                formulation=formulation,
                vessel_id=str(batch),
                time_points=times,
                percent_released=values,
            )
        )
        matrix_rows.append(values)

    if len(profiles) < 2:
        raise ValueError(
            f"Formulation '{formulation}' requires at least 2 vessels for bootstrap f2."
        )
    if expected_times is None or len(expected_times) < 3:
        raise ValueError(f"Formulation '{formulation}' requires at least 3 matched time points.")
    return profiles, np.asarray(matrix_rows, dtype=float), expected_times


def _normalized_rows(df: pd.DataFrame, labels: Sequence[str]) -> list[dict[str, str | float]]:
    selected = df[df["formulation"].isin(labels)].copy()
    order = {label: index for index, label in enumerate(labels)}
    selected["_form_order"] = selected["formulation"].map(order)
    selected = selected.sort_values(["_form_order", "batch", "time"])
    return [
        {
            "formulation": str(row.formulation),
            "batch": str(row.batch),
            "time": float(row.time),
            "percent_released": float(row.percent_released),
        }
        for row in selected.itertuples(index=False)
    ]


def run_dissolution_workbench(
    data: pd.DataFrame,
    config: DissolutionWorkbenchConfig,
    *,
    columns: DissolutionCSVConfig | None = None,
) -> DissolutionWorkbenchResult:
    """Run the complete validated dissolution workbench.

    Parameters
    ----------
    data : pd.DataFrame
        Vessel-level dissolution rows.
    config : DissolutionWorkbenchConfig
        Exact analysis configuration.
    columns : DissolutionCSVConfig | None, optional
        Input column mapping.

    Returns
    -------
    DissolutionWorkbenchResult
        Complete auditable analysis.

    Raises
    ------
    ValueError
        If vessel data, time alignment, labels, or configuration are invalid.

    References
    ----------
    FDA Guidance for Industry: Dissolution Testing of Immediate Release Solid
    Oral Dosage Forms (1997). Costa P, Lobo JMS (2001), DOI:
    10.1016/S0928-0987(01)00095-1. Shah VP et al. (1998), Pharm Res 15:889-896.
    """
    validated = validate_dissolution_dataframe(
        data,
        columns,
        source_name="dissolution workbench input",
    )
    labels = (config.reference_label, config.test_label)
    reference_vessels, reference_matrix, reference_times = _vessel_profiles(
        validated, config.reference_label
    )
    test_vessels, test_matrix, test_times = _vessel_profiles(validated, config.test_label)
    if reference_times != test_times:
        raise ValueError(
            "Reference and test formulations do not share identical time points; "
            "the workbench does not interpolate or reindex profiles."
        )

    selected = validated[validated["formulation"].isin(labels)].copy()
    study = DissolutionStudy(selected)
    captured: list[str] = []
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        comparison = study.compare(
            config.reference_label,
            config.test_label,
            f2_method=config.f2_method,
        )
        bootstrap = bootstrap_f2(
            reference_matrix,
            test_matrix,
            n_replicates=config.bootstrap_replicates,
            confidence_level=config.confidence_level,
            seed=config.seed,
        )
        reference_models = fit_dissolution_models(
            reference_times,
            reference_matrix.mean(axis=0),
            config.reference_label,
            models=list(VALIDATED_WORKBENCH_MODELS),
        )
        test_models = fit_dissolution_models(
            test_times,
            test_matrix.mean(axis=0),
            config.test_label,
            models=list(VALIDATED_WORKBENCH_MODELS),
        )
        model_comparison = model_dependent_comparison(
            reference_times,
            reference_matrix.mean(axis=0),
            test_times,
            test_matrix.mean(axis=0),
            config.model_comparison_model,
            config.model_comparison_param_index,
        )
        captured.extend(str(item.message) for item in caught)

    reference_mean = reference_matrix.mean(axis=0).tolist()
    test_mean = test_matrix.mean(axis=0).tolist()
    msd_result = msd(reference_mean, test_mean)
    maximum = max_deviation(reference_mean, test_mean)
    all_warnings = list(dict.fromkeys([*comparison.warnings, *captured]))

    return DissolutionWorkbenchResult(
        config=config,
        normalized_rows=_normalized_rows(validated, labels),
        reference_vessels=reference_vessels,
        test_vessels=test_vessels,
        comparison=comparison,
        bootstrap=bootstrap,
        reference_models=reference_models,
        test_models=test_models,
        model_comparison=model_comparison,
        msd_result=msd_result,
        maximum_deviation=maximum,
        warnings=all_warnings,
        generated_at_utc=datetime.now(timezone.utc).isoformat(),
    )


def run_dissolution_workbench_csv(
    path: str | Path,
    config: DissolutionWorkbenchConfig,
    *,
    columns: DissolutionCSVConfig | None = None,
) -> DissolutionWorkbenchResult:
    """Run the workbench from a vessel-level CSV file.

    Parameters
    ----------
    path : str | Path
        Input CSV path.
    config : DissolutionWorkbenchConfig
        Exact analysis configuration.
    columns : DissolutionCSVConfig | None, optional
        Input column mapping.

    Returns
    -------
    DissolutionWorkbenchResult
        Complete auditable analysis.
    """
    csv_path = Path(path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Dissolution CSV not found: {csv_path}")
    return run_dissolution_workbench(
        pd.read_csv(csv_path),
        config,
        columns=columns,
    )


def workbench_result_json(result: DissolutionWorkbenchResult) -> str:
    """Serialize a workbench result as stable formatted JSON.

    Parameters
    ----------
    result : DissolutionWorkbenchResult
        Completed workbench analysis.

    Returns
    -------
    str
        Sorted, indented JSON.
    """
    return json.dumps(result.to_dict(), indent=2, sort_keys=True, allow_nan=False)
