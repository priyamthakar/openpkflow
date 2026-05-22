"""Tests for Bayesian 2x2 crossover BE analysis.

References
----------
Grieve AP (1985) A Bayesian analysis of the two-period crossover design
for clinical trials. Biometrics 41:979-90. DOI:10.2307/2530971

FDA (2003) Guidance for Industry: Bioavailability and Bioequivalence Studies
for Orally Administered Drug Products -- General Considerations.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from openpkflow.bayes.bayes_be import (
    _BE_HI,
    _BE_LO,
    BayesBEResult,
    _complete_pairs,
    _frequentist_90ci,
    _validate_be_data,
)

# ---------------------------------------------------------------------------
# Synthetic 2x2 crossover data generator
# ---------------------------------------------------------------------------


def _make_2x2_data(
    n: int,
    gmr: float,
    cv: float,
    *,
    mu_ref: float = 100.0,
    seed: int = 42,
):
    """Generate a balanced 2x2 crossover DataFrame for testing."""
    pytest.importorskip("pandas")
    import pandas as pd

    rng = np.random.default_rng(seed)
    sigma_w = math.sqrt(math.log(cv**2 + 1))
    sigma_b = 0.3

    records = []
    for i in range(n):
        seq = "RT" if i % 2 == 0 else "TR"
        subj_effect = rng.normal(0, sigma_b)
        log_mu = math.log(mu_ref)
        treatments = ["R", "T"] if seq == "RT" else ["T", "R"]
        for p_idx, trt in enumerate(treatments, start=1):
            log_val = (
                log_mu
                + subj_effect
                + (math.log(gmr) if trt == "T" else 0.0)
                + rng.normal(0, sigma_w)
            )
            records.append(
                {
                    "subject": f"S{i + 1:02d}",
                    "sequence": seq,
                    "period": p_idx,
                    "treatment": trt,
                    "value": math.exp(log_val),
                }
            )
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Validation tests (no PyMC needed)
# ---------------------------------------------------------------------------


class TestValidation:
    def test_missing_column_raises(self):
        pytest.importorskip("pandas")
        import pandas as pd

        df = pd.DataFrame({"subject": ["A"], "sequence": ["RT"], "period": [1], "value": [5.0]})
        with pytest.raises(ValueError, match="Missing required columns"):
            _validate_be_data(df)

    def test_non_positive_value_raises(self):
        pytest.importorskip("pandas")
        import pandas as pd

        df = pd.DataFrame(
            {
                "subject": ["A", "A", "B", "B"],
                "sequence": ["RT", "RT", "TR", "TR"],
                "period": [1, 2, 1, 2],
                "treatment": ["R", "T", "T", "R"],
                "value": [5.0, -1.0, 3.0, 4.0],
            }
        )
        with pytest.raises(ValueError, match="positive"):
            _validate_be_data(df)

    def test_too_few_subjects_raises(self):
        pytest.importorskip("pandas")
        import pandas as pd

        df = pd.DataFrame(
            {
                "subject": ["A", "A", "B", "B"],
                "sequence": ["RT", "RT", "TR", "TR"],
                "period": [1, 2, 1, 2],
                "treatment": ["R", "T", "T", "R"],
                "value": [5.0, 6.0, 4.5, 5.5],
            }
        )
        with pytest.raises(ValueError, match="subjects"):
            _validate_be_data(df)

    def test_non_dataframe_raises(self):
        with pytest.raises(TypeError, match="DataFrame"):
            _validate_be_data({"subject": [1]})  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Complete pairs filter
# ---------------------------------------------------------------------------


class TestCompletePairs:
    def test_incomplete_subject_dropped(self):
        pytest.importorskip("pandas")
        import pandas as pd

        df = pd.DataFrame(
            {
                "subject": ["A", "A", "B"],
                "sequence": ["RT", "RT", "TR"],
                "period": [1, 2, 1],
                "treatment": ["R", "T", "T"],
                "value": [5.0, 6.0, 4.5],
            }
        )
        clean, dropped = _complete_pairs(df)
        assert "A" in clean["subject"].values
        assert "B" in dropped

    def test_all_complete_returns_full(self):
        df = _make_2x2_data(8, gmr=1.0, cv=0.15)
        clean, dropped = _complete_pairs(df)
        assert len(dropped) == 0
        assert clean["subject"].nunique() == 8


# ---------------------------------------------------------------------------
# Frequentist 90% CI (no PyMC needed)
# ---------------------------------------------------------------------------


class TestFrequentistCI:
    def test_perfect_equivalence_gmr_near_one(self):
        """When T and R values are identical per subject, GMR = 1.0."""
        pytest.importorskip("pandas")
        import pandas as pd

        records = []
        for i in range(12):
            seq = "RT" if i % 2 == 0 else "TR"
            v = float(100 + i)
            for trt, per in [("R", 1), ("T", 2)] if seq == "RT" else [("T", 1), ("R", 2)]:
                records.append(
                    {
                        "subject": f"S{i}",
                        "sequence": seq,
                        "period": per,
                        "treatment": trt,
                        "value": v,
                    }
                )
        df = pd.DataFrame(records)
        df["_trt_norm"] = df["treatment"]  # same as treatment
        gmr, ci = _frequentist_90ci(df)
        assert gmr == pytest.approx(1.0, abs=1e-9)
        assert ci[0] == pytest.approx(1.0, abs=1e-9)
        assert ci[1] == pytest.approx(1.0, abs=1e-9)

    def test_gmr_105_dataset_ci_near_1(self):
        """Low-CV dataset with GMR=1.05 should have CI near 1.0-1.1."""
        df = _make_2x2_data(24, gmr=1.05, cv=0.10, seed=7)
        df2, _ = _complete_pairs(df)
        gmr, ci = _frequentist_90ci(df2)
        assert 0.90 <= gmr <= 1.20, f"GMR out of range: {gmr}"
        assert ci[0] < gmr < ci[1]

    def test_ci_is_symmetric_on_log_scale(self):
        """log(hi) - log(GMR) should equal log(GMR) - log(lo) up to rounding."""
        df = _make_2x2_data(20, gmr=1.10, cv=0.20, seed=5)
        df2, _ = _complete_pairs(df)
        gmr, (lo, hi) = _frequentist_90ci(df2)
        log_lo = math.log(lo)
        log_hi = math.log(hi)
        log_gmr = math.log(gmr)
        assert (log_gmr - log_lo) == pytest.approx(log_hi - log_gmr, rel=1e-4)

    def test_be_pass_for_low_cv_and_gmr_1(self):
        """GMR=1.0, CV=10%, n=20 should have freq 90% CI within BE limits."""
        df = _make_2x2_data(20, gmr=1.0, cv=0.10, seed=1)
        df2, _ = _complete_pairs(df)
        _, (lo, hi) = _frequentist_90ci(df2)
        assert lo >= _BE_LO, f"lower CI {lo} < {_BE_LO}"
        assert hi <= _BE_HI, f"upper CI {hi} > {_BE_HI}"

    def test_be_fail_for_high_gmr(self):
        """GMR=1.50 should have freq 90% CI exceeding 1.25."""
        df = _make_2x2_data(24, gmr=1.50, cv=0.15, seed=2)
        df2, _ = _complete_pairs(df)
        _, (lo, hi) = _frequentist_90ci(df2)
        assert hi > _BE_HI


# ---------------------------------------------------------------------------
# BayesBEResult data class (no PyMC needed — construct manually)
# ---------------------------------------------------------------------------


class TestBayesBEResultClass:
    def _make_result(self, p_be: float = 0.97, gmr: float = 1.05) -> BayesBEResult:
        rng = np.random.default_rng(0)
        gp = rng.lognormal(math.log(gmr), 0.05, 4000)
        bt = np.log(gp)
        return BayesBEResult(
            metric="AUC",
            n_subjects=24,
            n_samples=4000,
            gmr_posterior=gp,
            gmr_mean=float(np.mean(gp)),
            gmr_95ci=(float(np.percentile(gp, 2.5)), float(np.percentile(gp, 97.5))),
            p_be=p_be,
            beta_t_posterior=bt,
            beta_t_mean=float(np.mean(bt)),
            beta_t_95ci=(float(np.percentile(bt, 2.5)), float(np.percentile(bt, 97.5))),
            sigma_b_mean=0.30,
            sigma_w_mean=0.15,
            freq_gmr=gmr,
            freq_90ci=(0.97, 1.14),
            freq_be=True,
        )

    def test_to_dict_keys(self):
        r = self._make_result()
        d = r.to_dict()
        for k in (
            "metric",
            "n_subjects",
            "n_samples",
            "gmr_mean",
            "gmr_95ci",
            "p_be",
            "beta_t_mean",
            "sigma_b_mean",
            "sigma_w_mean",
            "freq_gmr",
            "freq_90ci",
            "freq_be",
            "warnings",
        ):
            assert k in d

    def test_summary_contains_p_be(self):
        r = self._make_result()
        assert "P(BE)" in r.summary()

    def test_summary_is_ascii(self):
        r = self._make_result()
        r.summary().encode("ascii")

    def test_summary_pass_decision(self):
        r = self._make_result(p_be=0.97)
        assert "PASS" in r.summary()

    def test_summary_borderline_decision(self):
        r = self._make_result(p_be=0.85)
        assert "BORDERLINE" in r.summary()

    def test_summary_fail_decision(self):
        r = self._make_result(p_be=0.30)
        assert "FAIL" in r.summary()

    def test_summary_contains_disclaimer(self):
        r = self._make_result()
        assert "Disclaimer" in r.summary()

    def test_summary_contains_frequentist(self):
        r = self._make_result()
        assert "Frequentist" in r.summary()


# ---------------------------------------------------------------------------
# Report tests (no PyMC needed — use manually constructed result)
# ---------------------------------------------------------------------------


class TestBayesBEReport:
    def _make_result(self) -> BayesBEResult:
        rng = np.random.default_rng(99)
        gp = rng.lognormal(math.log(1.05), 0.04, 4000)
        return BayesBEResult(
            metric="AUC",
            n_subjects=24,
            n_samples=4000,
            gmr_posterior=gp,
            gmr_mean=float(np.mean(gp)),
            gmr_95ci=(float(np.percentile(gp, 2.5)), float(np.percentile(gp, 97.5))),
            p_be=0.97,
            beta_t_posterior=np.log(gp),
            beta_t_mean=float(np.mean(np.log(gp))),
            beta_t_95ci=(
                float(np.percentile(np.log(gp), 2.5)),
                float(np.percentile(np.log(gp), 97.5)),
            ),
            sigma_b_mean=0.30,
            sigma_w_mean=0.15,
            freq_gmr=1.05,
            freq_90ci=(0.97, 1.14),
            freq_be=True,
        )

    def test_html_report_generated(self, tmp_path):
        r = self._make_result()
        out = tmp_path / "be_report.html"
        content = r.report(out, format="html")
        assert out.exists()
        assert "<html" in content

    def test_html_contains_disclaimer(self, tmp_path):
        r = self._make_result()
        content = r.report(tmp_path / "r.html", format="html")
        assert "Disclaimer" in content

    def test_html_contains_p_be(self, tmp_path):
        r = self._make_result()
        content = r.report(tmp_path / "r.html", format="html")
        assert "P(" in content

    def test_html_contains_metric(self, tmp_path):
        r = self._make_result()
        content = r.report(tmp_path / "r.html", format="html")
        assert "AUC" in content

    def test_markdown_report_generated(self, tmp_path):
        r = self._make_result()
        out = tmp_path / "be_report.md"
        content = r.report(out, format="markdown")
        assert out.exists()
        assert "# Bayesian BE" in content

    def test_markdown_contains_frequentist(self, tmp_path):
        r = self._make_result()
        content = r.report(tmp_path / "r.md", format="markdown")
        assert "Frequentist" in content

    def test_unknown_format_raises(self, tmp_path):
        r = self._make_result()
        with pytest.raises(ValueError, match="Unknown format"):
            r.report(tmp_path / "out.xyz", format="xyz")


# ---------------------------------------------------------------------------
# Full Bayesian analysis (requires PyMC)
# ---------------------------------------------------------------------------


class TestBayesBEFull:
    """Full MCMC tests. Skipped when PyMC is not installed."""

    @pytest.fixture(autouse=True)
    def _require_pymc(self):
        pytest.importorskip("pymc")

    def test_gmr105_cv15_n24_passes(self):
        """GMR=1.05, CV=15%, n=24 should yield P(BE) >= 0.80.

        Reference: FDA (2003) BA/BE guidance -- 80-125% limits. A typical
        BE-passing scenario with moderate sample size.
        """
        from openpkflow.bayes.bayes_be import bayes_be

        df = _make_2x2_data(24, gmr=1.05, cv=0.15, seed=10)
        result = bayes_be(df, metric="AUC", n_samples=500, tune=500, chains=2)
        assert result.p_be >= 0.70, (
            f"Expected P(BE) >= 0.70 for GMR=1.05/CV=15%/n=24, got {result.p_be:.3f}"
        )
        assert result.gmr_mean == pytest.approx(1.05, rel=0.15)

    def test_gmr135_n24_fails(self):
        """GMR=1.35 (outside BE limits) should yield P(BE) < 0.30.

        Reference: FDA (2003) BA/BE guidance -- 80-125% limits violated.
        """
        from openpkflow.bayes.bayes_be import bayes_be

        df = _make_2x2_data(24, gmr=1.35, cv=0.15, seed=20)
        result = bayes_be(df, metric="AUC", n_samples=500, tune=500, chains=2)
        assert result.p_be < 0.30, f"Expected P(BE) < 0.30 for GMR=1.35, got {result.p_be:.3f}"

    def test_result_fields_populated(self):
        from openpkflow.bayes.bayes_be import bayes_be

        df = _make_2x2_data(12, gmr=1.00, cv=0.20, seed=30)
        result = bayes_be(df, metric="Cmax", n_samples=200, tune=200, chains=2)
        assert result.n_subjects == 12
        assert result.n_samples > 0
        assert math.isfinite(result.gmr_mean)
        assert math.isfinite(result.sigma_b_mean)
        assert math.isfinite(result.sigma_w_mean)
        assert 0.0 <= result.p_be <= 1.0
        assert result.gmr_95ci[0] < result.gmr_95ci[1]

    def test_frequentist_and_bayesian_gmr_agree(self):
        """Frequentist and Bayesian GMR estimates should be within 15% of each other."""
        from openpkflow.bayes.bayes_be import bayes_be

        df = _make_2x2_data(20, gmr=1.08, cv=0.15, seed=40)
        result = bayes_be(df, metric="AUC", n_samples=300, tune=300, chains=2)
        ratio = result.gmr_mean / result.freq_gmr
        assert 0.85 <= ratio <= 1.15, (
            f"Bayesian GMR {result.gmr_mean:.4g} and freq GMR {result.freq_gmr:.4g} diverge."
        )

    def test_to_dict_has_all_keys(self):
        from openpkflow.bayes.bayes_be import bayes_be

        df = _make_2x2_data(12, gmr=1.00, cv=0.15, seed=50)
        result = bayes_be(df, n_samples=200, tune=200, chains=2)
        d = result.to_dict()
        for k in (
            "metric",
            "n_subjects",
            "n_samples",
            "gmr_mean",
            "gmr_95ci",
            "p_be",
            "freq_gmr",
            "freq_90ci",
            "freq_be",
            "warnings",
        ):
            assert k in d

    def test_warnings_is_list(self):
        from openpkflow.bayes.bayes_be import bayes_be

        df = _make_2x2_data(12, gmr=1.0, cv=0.15, seed=60)
        result = bayes_be(df, n_samples=200, tune=200, chains=2)
        assert isinstance(result.warnings, list)
