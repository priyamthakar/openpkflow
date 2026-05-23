"""Tests for pop/vpc.py — VPCResult and binning functionality.

Reference: Bergstrand et al. (2011) AAPS J 13(2) for VPC methodology.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import numpy as np
import pytest

from openpkflow.pop.vpc import VPCResult, simulate_vpc
from openpkflow.sim.dosing import Dose, DoseRegimen
from openpkflow.sim.models import OneCompartmentModel


def _make_vpc_result(**overrides) -> VPCResult:
    """Construct a minimal VPCResult for direct dataclass testing."""
    defaults = dict(
        bin_mids=[1.5, 4.5, 7.5, 10.5],
        obs_lower=[0.1, 2.0, 1.5, 0.5],
        obs_median=[0.5, 4.0, 3.0, 1.0],
        obs_upper=[1.2, 6.0, 5.0, 2.0],
        sim_lower=[0.0, 1.8, 1.2, 0.3],
        sim_median=[0.4, 3.5, 2.8, 0.9],
        sim_upper=[1.0, 5.5, 4.5, 1.8],
        obs_times=[1.0, 2.0, 4.0, 5.0, 8.0, 12.0],
        obs_dv=[0.5, 0.3, 4.0, 3.5, 3.0, 1.0],
    )
    defaults.update(overrides)
    return VPCResult(**defaults)


def _make_model_and_obs():
    """Create a 1-cmt oral model and observed data for simulate_vpc tests."""
    model = OneCompartmentModel(route="oral", CL_F=5.0, Vz_F=50.0, ka=1.2)
    regimen = DoseRegimen((Dose(amount=100.0, time=0.0, route="oral"),))
    import pandas as pd

    times = [0.5, 1.0, 2.0, 4.0, 6.0, 8.0, 12.0, 16.0, 24.0]
    from openpkflow.sim.simulate import simulate

    result = simulate(model, regimen, times)
    rng = np.random.default_rng(7)
    noisy = [max(0.0, c * (1.0 + rng.normal(0, 0.15))) for c in result.concs]
    obs_df = pd.DataFrame({"TIME": times, "DV": noisy})
    return model, regimen, obs_df


# ---------------------------------------------------------------------------
# VPCResult dataclass
# ---------------------------------------------------------------------------


class TestVPCResultDataclass:
    """Direct VPCResult dataclass creation and method tests."""

    def test_creation_with_defaults(self) -> None:
        r = VPCResult(
            bin_mids=[1.0, 2.0],
            obs_lower=[0.1, 0.2],
            obs_median=[0.5, 0.6],
            obs_upper=[1.0, 1.1],
            sim_lower=[0.15, 0.25],
            sim_median=[0.55, 0.65],
            sim_upper=[1.05, 1.15],
            obs_times=[1.0, 1.0, 2.0, 2.0],
            obs_dv=[0.1, 0.5, 0.2, 0.6],
        )
        assert r.pi == (5.0, 50.0, 95.0)
        assert r.n_bins == 8
        assert r.n_replicates == 500
        assert r.study_label == ""
        assert r.warnings == []

    def test_creation_with_overrides(self) -> None:
        r = VPCResult(
            bin_mids=[1.0],
            obs_lower=[0.1],
            obs_median=[0.5],
            obs_upper=[1.0],
            sim_lower=[0.15],
            sim_median=[0.55],
            sim_upper=[1.05],
            obs_times=[1.0, 1.0],
            obs_dv=[0.1, 0.5],
            pi=(10.0, 50.0, 90.0),
            n_bins=4,
            n_replicates=200,
            study_label="Custom VPC",
            warnings=["some warning"],
        )
        assert r.pi == (10.0, 50.0, 90.0)
        assert r.n_bins == 4
        assert r.n_replicates == 200
        assert r.study_label == "Custom VPC"
        assert len(r.warnings) == 1

    def test_summary_is_string(self) -> None:
        r = _make_vpc_result()
        s = r.summary()
        assert isinstance(s, str)

    def test_summary_contains_n_observed(self) -> None:
        r = _make_vpc_result(obs_times=list(range(50)), obs_dv=list(range(50)))
        s = r.summary()
        assert "50" in s

    def test_summary_contains_n_replicates(self) -> None:
        r = _make_vpc_result(n_replicates=123)
        s = r.summary()
        assert "123" in s

    def test_summary_contains_n_bins(self) -> None:
        r = _make_vpc_result(n_bins=10)
        s = r.summary()
        assert "10" in s

    def test_summary_contains_percentiles(self) -> None:
        r = _make_vpc_result(pi=(10.0, 50.0, 90.0))
        s = r.summary()
        assert "10 / 50 / 90" in s

    def test_summary_with_study_label(self) -> None:
        r = _make_vpc_result(study_label="Phase I Healthy")
        s = r.summary()
        assert "Phase I Healthy" in s

    def test_summary_no_study_label(self) -> None:
        r = _make_vpc_result(study_label="")
        s = r.summary()
        lines = s.split("\n")
        assert lines[0] == "Visual Predictive Check (VPC)"

    def test_summary_with_warnings(self) -> None:
        r = _make_vpc_result(warnings=["Warning A", "Warning B"])
        s = r.summary()
        assert "Warnings" in s
        assert "Warning A" in s
        assert "Warning B" in s

    def test_summary_no_warnings(self) -> None:
        r = _make_vpc_result(warnings=[])
        s = r.summary()
        assert "Warnings" not in s

    def test_summary_ascii_safe(self) -> None:
        r = _make_vpc_result()
        r.summary().encode("ascii")


# ---------------------------------------------------------------------------
# VPCResult.to_dict via dataclasses.asdict
# ---------------------------------------------------------------------------


class TestVPCResultAsDict:
    """VPCResult is a dataclass; dataclasses.asdict() provides dict conversion."""

    def test_asdict_has_all_fields(self) -> None:
        r = _make_vpc_result()
        d = dataclasses.asdict(r)
        for field_name in (
            "bin_mids",
            "obs_lower",
            "obs_median",
            "obs_upper",
            "sim_lower",
            "sim_median",
            "sim_upper",
            "obs_times",
            "obs_dv",
            "pi",
            "n_bins",
            "n_replicates",
            "study_label",
            "warnings",
        ):
            assert field_name in d

    def test_asdict_preserves_values(self) -> None:
        r = _make_vpc_result(n_bins=3, n_replicates=77, study_label="Test")
        d = dataclasses.asdict(r)
        assert d["n_bins"] == 3
        assert d["n_replicates"] == 77
        assert d["study_label"] == "Test"

    def test_asdict_pi_is_tuple(self) -> None:
        r = _make_vpc_result()
        d = dataclasses.asdict(r)
        assert isinstance(d["pi"], tuple | list)
        assert len(d["pi"]) == 3


# ---------------------------------------------------------------------------
# VPCResult.plot
# ---------------------------------------------------------------------------


class TestVPCResultPlot:
    """Plot generation tests for VPCResult."""

    def test_plot_no_errors(self) -> None:
        r = _make_vpc_result()
        r.plot()

    def test_plot_to_file(self, tmp_path: Path) -> None:
        r = _make_vpc_result()
        out = tmp_path / "vpc_plot.png"
        r.plot(output_path=out)
        assert out.exists()
        assert out.stat().st_size > 100

    def test_plot_to_file_other_format(self, tmp_path: Path) -> None:
        r = _make_vpc_result()
        out = tmp_path / "vpc_plot.pdf"
        r.plot(output_path=out)
        assert out.exists()
        assert out.stat().st_size > 100

    def test_plot_with_warnings_no_errors(self) -> None:
        r = _make_vpc_result(warnings=["Something unusual"])
        r.plot()


# ---------------------------------------------------------------------------
# simulate_vpc edge cases
# ---------------------------------------------------------------------------


class TestSimulateVPC:
    """Tests for simulate_vpc() with a 1-cmt oral model.

    Reference: Bergstrand et al. (2011) AAPS J 13(2).
    """

    def test_returns_vpcresult(self) -> None:
        model, regimen, obs_df = _make_model_and_obs()
        result = simulate_vpc(model, regimen, obs_df, n_replicates=30, seed=42)
        assert isinstance(result, VPCResult)

    def test_basic_output_shape(self) -> None:
        model, regimen, obs_df = _make_model_and_obs()
        result = simulate_vpc(model, regimen, obs_df, n_replicates=30, n_bins=4, seed=42)
        assert len(result.bin_mids) == 4
        assert len(result.obs_lower) == 4
        assert len(result.obs_median) == 4
        assert len(result.obs_upper) == 4
        assert len(result.sim_lower) == 4
        assert len(result.sim_median) == 4
        assert len(result.sim_upper) == 4

    def test_single_observation_no_crash(self) -> None:
        """Single observation: bin will have <2 points, producing NaN."""
        import pandas as pd

        model, regimen, _ = _make_model_and_obs()
        obs_df = pd.DataFrame({"TIME": [4.0], "DV": [5.0]})
        result = simulate_vpc(model, regimen, obs_df, n_replicates=20, seed=42)
        assert all(np.isnan(v) for v in result.obs_lower)
        assert all(np.isnan(v) for v in result.obs_median)

    def test_empty_dataframe_raises(self) -> None:
        import pandas as pd

        model, regimen, _ = _make_model_and_obs()
        obs_df = pd.DataFrame({"TIME": [], "DV": []})
        with pytest.raises(ValueError):
            simulate_vpc(model, regimen, obs_df)

    def test_study_label_stored(self) -> None:
        model, regimen, obs_df = _make_model_and_obs()
        result = simulate_vpc(
            model, regimen, obs_df, n_replicates=20, seed=42, study_label="Phase I"
        )
        assert result.study_label == "Phase I"

    def test_custom_percentiles_stored(self) -> None:
        model, regimen, obs_df = _make_model_and_obs()
        result = simulate_vpc(
            model, regimen, obs_df, n_replicates=20, seed=42, pi=(2.5, 50.0, 97.5)
        )
        assert result.pi == (2.5, 50.0, 97.5)

    def test_custom_n_bins_stored(self) -> None:
        model, regimen, obs_df = _make_model_and_obs()
        result = simulate_vpc(model, regimen, obs_df, n_replicates=20, seed=42, n_bins=3)
        assert result.n_bins == 3

    def test_obs_counts_preserved(self) -> None:
        model, regimen, obs_df = _make_model_and_obs()
        result = simulate_vpc(model, regimen, obs_df, n_replicates=20, seed=42)
        assert len(result.obs_times) == len(obs_df)
        assert len(result.obs_dv) == len(obs_df)

    def test_reproducible_with_seed(self) -> None:
        model, regimen, obs_df = _make_model_and_obs()
        r1 = simulate_vpc(model, regimen, obs_df, n_replicates=50, seed=77)
        r2 = simulate_vpc(model, regimen, obs_df, n_replicates=50, seed=77)
        np.testing.assert_array_equal(
            np.array(r1.sim_median, dtype=float),
            np.array(r2.sim_median, dtype=float),
        )
