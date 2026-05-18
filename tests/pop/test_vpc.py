"""Tests for pop.vpc module.

Reference: Bergstrand et al. (2011) AAPS J 13(2) for VPC methodology.
Degenerate: when sigma_proportional=0, all simulated values == base profile.
"""

import math

import numpy as np
import pandas as pd
import pytest

from openpkflow.pop.vpc import simulate_vpc
from openpkflow.sim.dosing import Dose, DoseRegimen
from openpkflow.sim.models import OneCompartmentModel


def _make_1cmt_oral() -> tuple[OneCompartmentModel, DoseRegimen, pd.DataFrame]:
    """1-cmt oral model for use in VPC tests."""
    model = OneCompartmentModel(route="oral", CL_F=5.0, Vz_F=50.0, ka=1.2)
    regimen = DoseRegimen((Dose(amount=100.0, time=0.0, route="oral"),))
    times = [0.5, 1.0, 2.0, 4.0, 6.0, 8.0, 12.0, 16.0, 24.0]
    from openpkflow.sim.simulate import simulate

    result = simulate(model, regimen, times)
    concs = result.concs
    rng = np.random.default_rng(7)
    noisy_concs = [max(0.0, c * (1.0 + rng.normal(0, 0.15))) for c in concs]
    obs_df = pd.DataFrame({"TIME": times, "DV": noisy_concs})
    return model, regimen, obs_df


class TestSimulateVPC:
    def test_basic_output_shape(self):
        model, regimen, obs_df = _make_1cmt_oral()
        result = simulate_vpc(model, regimen, obs_df, n_replicates=50, n_bins=4, seed=42)
        assert len(result.bin_mids) == 4
        assert len(result.obs_lower) == 4
        assert len(result.sim_lower) == 4

    def test_obs_counts_preserved(self):
        model, regimen, obs_df = _make_1cmt_oral()
        result = simulate_vpc(model, regimen, obs_df, n_replicates=50, seed=42)
        assert len(result.obs_times) == len(obs_df)

    def test_zero_sigma_seed_independent(self):
        """With sigma=0, different seeds give identical VPC bands (no randomness)."""
        model, regimen, obs_df = _make_1cmt_oral()
        r1 = simulate_vpc(
            model,
            regimen,
            obs_df,
            sigma_proportional=0.0,
            sigma_additive=0.0,
            n_replicates=20,
            seed=0,
            n_bins=4,
        )
        r2 = simulate_vpc(
            model,
            regimen,
            obs_df,
            sigma_proportional=0.0,
            sigma_additive=0.0,
            n_replicates=20,
            seed=999,
            n_bins=4,
        )
        # Deterministic profile: different seeds make no difference
        assert r1.sim_median == r2.sim_median
        assert r1.sim_lower == r2.sim_lower

    def test_missing_column_raises(self):
        model, regimen, _ = _make_1cmt_oral()
        bad_df = pd.DataFrame({"X": [1.0, 2.0], "Y": [3.0, 4.0]})
        with pytest.raises(ValueError, match="TIME"):
            simulate_vpc(model, regimen, bad_df)

    def test_n_replicates_stored(self):
        model, regimen, obs_df = _make_1cmt_oral()
        result = simulate_vpc(model, regimen, obs_df, n_replicates=123, seed=0)
        assert result.n_replicates == 123

    def test_reproducible_with_seed(self):
        model, regimen, obs_df = _make_1cmt_oral()
        r1 = simulate_vpc(model, regimen, obs_df, n_replicates=50, seed=77)
        r2 = simulate_vpc(model, regimen, obs_df, n_replicates=50, seed=77)
        np.testing.assert_array_equal(
            np.array(r1.sim_median, dtype=float),
            np.array(r2.sim_median, dtype=float),
        )

    def test_different_seeds_differ(self):
        model, regimen, obs_df = _make_1cmt_oral()
        r1 = simulate_vpc(model, regimen, obs_df, n_replicates=100, seed=1)
        r2 = simulate_vpc(model, regimen, obs_df, n_replicates=100, seed=2)
        # Very unlikely to be identical
        non_nan_1 = [v for v in r1.sim_median if not math.isnan(v)]
        non_nan_2 = [v for v in r2.sim_median if not math.isnan(v)]
        assert non_nan_1 != non_nan_2


class TestVPCResult:
    def _make_result(self):
        model, regimen, obs_df = _make_1cmt_oral()
        return simulate_vpc(
            model, regimen, obs_df, n_replicates=100, seed=42, study_label="Test VPC"
        )

    def test_summary_contains_study_label(self):
        r = self._make_result()
        assert "Test VPC" in r.summary()

    def test_summary_contains_n_replicates(self):
        r = self._make_result()
        assert "100" in r.summary()

    def test_html_report(self, tmp_path):
        r = self._make_result()
        out = tmp_path / "vpc.html"
        html = r.report(out, format="html")
        assert out.exists()
        assert "VPC" in html
        assert "OpenPKFlow" in html

    def test_markdown_report(self, tmp_path):
        r = self._make_result()
        out = tmp_path / "vpc.md"
        md = r.report(out, format="markdown")
        assert out.exists()
        assert "VPC" in md
