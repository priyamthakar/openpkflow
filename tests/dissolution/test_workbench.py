"""Advanced dissolution workbench orchestration and audit tests.

References:
    FDA Guidance for Industry: Dissolution Testing of Immediate Release Solid
    Oral Dosage Forms (1997).
    Costa P, Lobo JMS (2001). DOI: 10.1016/S0928-0987(01)00095-1.
    Shah VP et al. (1998). Pharm Res 15(6):889-896.
"""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from openpkflow.dissolution.workbench import (
    VALIDATED_WORKBENCH_MODELS,
    DissolutionWorkbenchConfig,
    run_dissolution_workbench,
)

_TIMES = [5.0, 10.0, 15.0, 20.0, 30.0, 45.0, 60.0]
_REFERENCE = [8.0, 19.0, 34.0, 50.0, 70.0, 88.0, 96.0]
_TEST = [7.0, 18.0, 33.0, 49.0, 69.0, 87.0, 95.0]


def _workbench_dataframe() -> pd.DataFrame:
    rows: list[dict[str, str | float]] = []
    offsets = (-1.0, 0.0, 1.0)
    for formulation, values, prefix in (
        ("Reference", _REFERENCE, "R"),
        ("Test", _TEST, "T"),
    ):
        for vessel_index, offset in enumerate(offsets, 1):
            for time, value in zip(_TIMES, values, strict=True):
                rows.append(
                    {
                        "formulation": formulation,
                        "batch": f"{prefix}{vessel_index}",
                        "time": time,
                        "percent_released": min(100.0, max(0.0, value + offset)),
                    }
                )
    return pd.DataFrame(rows)


def _config() -> DissolutionWorkbenchConfig:
    return DissolutionWorkbenchConfig(
        reference_label="Reference",
        test_label="Test",
        bootstrap_replicates=250,
        seed=42,
    )


def test_workbench_exposes_validated_complete_result() -> None:
    """The orchestrator delegates every claim to the validated FDA/Costa methods."""
    result = run_dissolution_workbench(_workbench_dataframe(), _config())
    payload = result.to_dict()

    assert result.comparison.f2_value >= 50.0
    assert result.bootstrap.n_reference_vessels == 3
    assert result.bootstrap.n_test_vessels == 3
    assert len(result.reference_vessels) == 3
    assert len(result.test_vessels) == 3
    assert {fit.model_name for fit in result.reference_models.fits} == set(
        VALIDATED_WORKBENCH_MODELS
    )
    assert len(payload["normalized_rows"]) == 42  # type: ignore[arg-type]
    assert payload["disclaimer"]


def test_workbench_seed_reproduces_bootstrap_interval() -> None:
    """Shah et al. (1998) bootstrap configuration is reproducible with a fixed seed."""
    first = run_dissolution_workbench(_workbench_dataframe(), _config())
    second = run_dissolution_workbench(_workbench_dataframe(), _config())
    assert second.bootstrap.ci_lower == pytest.approx(first.bootstrap.ci_lower)
    assert second.bootstrap.ci_upper == pytest.approx(first.bootstrap.ci_upper)


def test_workbench_rejects_unmatched_vessel_timepoints() -> None:
    """FDA f2 inputs must remain aligned; no interpolation or reindexing is allowed."""
    data = _workbench_dataframe()
    data = data[~((data["batch"] == "T3") & (data["time"] == 60.0))]
    with pytest.raises(ValueError, match="does not share the same time points"):
        run_dissolution_workbench(data, _config())


def test_workbench_rejects_unmatched_formulation_timepoints() -> None:
    """FDA 1997 requires matched reference/test time points."""
    data = _workbench_dataframe()
    data = data[~((data["formulation"] == "Test") & (data["time"] == 60.0))]
    with pytest.raises(ValueError, match="do not share identical time points"):
        run_dissolution_workbench(data, _config())


@pytest.mark.parametrize(
    ("column", "value"),
    [("time", np.inf), ("percent_released", np.nan)],
)
def test_workbench_rejects_nonfinite_values(column: str, value: float) -> None:
    """Non-finite vessel data fail closed before any calculation."""
    data = _workbench_dataframe()
    data.loc[0, column] = value
    with pytest.raises(ValueError, match="NaN|non-finite"):
        run_dissolution_workbench(data, _config())


def test_workbench_rejects_duplicate_vessel_time() -> None:
    """A vessel may have only one observation at each matched time point."""
    data = pd.concat([_workbench_dataframe(), _workbench_dataframe().iloc[[0]]])
    with pytest.raises(ValueError, match="duplicate vessel/time"):
        run_dissolution_workbench(data, _config())


def test_workbench_rejects_empty_vessel_identifier() -> None:
    """Every vessel-level row must retain a traceable vessel identifier."""
    data = _workbench_dataframe()
    data.loc[0, "batch"] = ""
    with pytest.raises(ValueError, match="empty vessel identifier"):
        run_dissolution_workbench(data, _config())


def test_workbench_html_pdf_docx_reports_include_required_content(tmp_path: Path) -> None:
    """Report-first outputs preserve results, configuration, and the required disclaimer."""
    result = run_dissolution_workbench(_workbench_dataframe(), _config())

    html_path = tmp_path / "workbench.html"
    pdf_path = tmp_path / "workbench.pdf"
    docx_path = tmp_path / "workbench.docx"
    rendered = result.report(html_path, format="html")
    result.report(pdf_path, format="pdf")
    result.report(docx_path, format="docx")

    assert "Advanced Dissolution Workbench" in rendered
    assert "Final regulatory interpretation" in rendered
    assert "normalized" in rendered.lower()
    assert pdf_path.read_bytes().startswith(b"%PDF")
    assert docx_path.read_bytes().startswith(b"PK")


def test_workbench_audit_bundle_manifest_verifies_every_artifact(tmp_path: Path) -> None:
    """The reproducibility bundle verifies normalized input and every derived artifact."""
    result = run_dissolution_workbench(_workbench_dataframe(), _config())
    bundle = result.audit_bundle(tmp_path / "dissolution_audit.zip")

    with zipfile.ZipFile(bundle) as archive:
        names = set(archive.namelist())
        assert names == {
            "config.json",
            "input/normalized_dissolution.csv",
            "manifest.json",
            "report.html",
            "results.json",
        }
        manifest = json.loads(archive.read("manifest.json"))
        for name, metadata in manifest["files"].items():
            content = archive.read(name)
            assert hashlib.sha256(content).hexdigest() == metadata["sha256"]
            assert len(content) == metadata["size_bytes"]


def test_workbench_configuration_rejects_unvalidated_model() -> None:
    """Only the five independently cross-validated Costa et al. models are promoted."""
    with pytest.raises(ValueError, match="model_comparison_model"):
        DissolutionWorkbenchConfig(
            reference_label="Reference",
            test_label="Test",
            model_comparison_model="hixson_crowell",
        )


def _plateau_dataframe(test_profile: list[float]) -> pd.DataFrame:
    times = [5.0, 10.0, 15.0, 20.0, 30.0, 45.0, 60.0, 90.0]
    reference = [30.0, 55.0, 75.0, 88.0, 95.0, 98.0, 99.0, 100.0]
    rng = np.random.default_rng(0)
    rows: list[dict[str, str | float]] = []
    for formulation, values in (("Reference", reference), ("Test", test_profile)):
        for vessel in range(12):
            for time, value in zip(times, values, strict=True):
                rows.append(
                    {
                        "formulation": formulation,
                        "batch": f"{formulation[0]}{vessel}",
                        "time": time,
                        "percent_released": float(np.clip(value + rng.normal(0, 1.5), 0, 100)),
                    }
                )
    return pd.DataFrame(rows)


def test_workbench_bootstrap_uses_regulatory_timepoints() -> None:
    """Bootstrap f2 follows the FDA (1997) 85% rule used by the point estimate.

    With plateau timepoints included, the bootstrap previously reported a CI lower
    bound above 50 while the regulatory point f2 was below 50.
    """
    slower = [18.0, 38.0, 60.0, 86.0, 94.0, 97.0, 99.0, 100.0]
    result = run_dissolution_workbench(_plateau_dataframe(slower), _config())

    assert result.bootstrap.n_timepoints == result.comparison.n_timepoints == 4
    assert result.bootstrap.f2_observed == pytest.approx(result.comparison.f2_value)
    assert result.comparison.f2_value < 50.0
    assert not result.bootstrap.is_similar


def test_workbench_msd_decision_tracks_profile_difference() -> None:
    """Tsong et al. (1996) vessel-level MSD rejects a clearly slower test product."""
    slower = [18.0, 38.0, 60.0, 86.0, 94.0, 97.0, 99.0, 100.0]
    close = [29.0, 54.0, 74.0, 87.0, 95.0, 98.0, 99.0, 100.0]

    dissimilar = run_dissolution_workbench(_plateau_dataframe(slower), _config())
    similar = run_dissolution_workbench(_plateau_dataframe(close), _config())

    assert dissimilar.msd_result is not None and not dissimilar.msd_result.is_similar
    assert similar.msd_result is not None and similar.msd_result.is_similar
    payload = dissimilar.to_dict()["alternatives"]
    assert payload["msd_is_similar"] is False  # type: ignore[index]


def test_workbench_msd_not_evaluable_with_too_few_vessels() -> None:
    """Three vessels per product cannot estimate a 7x7 pooled covariance."""
    result = run_dissolution_workbench(_workbench_dataframe(), _config())

    assert result.msd_result is None
    assert any("MSD not evaluable" in warning for warning in result.warnings)
    assert result.to_dict()["alternatives"]["msd_is_similar"] is None  # type: ignore[index]
