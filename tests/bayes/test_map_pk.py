"""Tests for MAP individual PK estimation.

References
----------
Sheiner LB & Beal SL (1982) Bayesian individualization of PK: simple
implementation. J Pharm Sci 71:1344-8. DOI:10.1002/jps.2600710906

Rowland & Tozer, Clinical Pharmacokinetics (2011), Ch. 3 & 5.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from openpkflow.bayes import PKPrior, map_individual_pk
from openpkflow.bayes.map_pk import (
    _log_likelihood,
    _log_prior,
    _make_objective,
    _numerical_hessian,
)
from openpkflow.bayes.priors import _log_normal_logpdf
from openpkflow.sim.methods import c_1cmt_iv_bolus, c_1cmt_oral

# ---------------------------------------------------------------------------
# Synthetic ground truth: oral 1-cmt
# TRUE: CL_F=5, Vz_F=50, ka=1.2, dose=100mg, sigma=0.1
# ---------------------------------------------------------------------------
_TRUE_CL_F = 5.0
_TRUE_VZ_F = 50.0
_TRUE_KA = 1.2
_DOSE = 100.0
_TIMES_ORAL = [0.5, 1.0, 2.0, 4.0, 8.0, 12.0]
_TRUE_ORAL = c_1cmt_oral(np.array(_TIMES_ORAL), _DOSE, _TRUE_CL_F, _TRUE_VZ_F, _TRUE_KA).tolist()

# IV bolus ground truth: CL=3, Vz=30
_TRUE_CL = 3.0
_TRUE_VZ = 30.0
_TIMES_IV = [0.25, 1.0, 3.0, 8.0]
_TRUE_IV = c_1cmt_iv_bolus(np.array(_TIMES_IV), _DOSE, _TRUE_CL, _TRUE_VZ).tolist()


class TestPKPrior:
    def test_default_construction(self):
        p = PKPrior()
        assert p.log_cl_mean == pytest.approx(1.609, abs=0.01)
        assert p.sigma_mean == 0.2

    def test_log_normal_logpdf_at_mean_is_max(self):
        v_at_mean = _log_normal_logpdf(1.0, 1.0, 0.5)
        v_off = _log_normal_logpdf(2.0, 1.0, 0.5)
        assert v_at_mean > v_off

    def test_log_prior_oral_sums_three_normals(self):
        p = PKPrior()
        lp = p.log_prior_oral(p.log_cl_mean, p.log_v_mean, p.log_ka_mean)
        expected = (
            _log_normal_logpdf(p.log_cl_mean, p.log_cl_mean, p.log_cl_sd)
            + _log_normal_logpdf(p.log_v_mean, p.log_v_mean, p.log_v_sd)
            + _log_normal_logpdf(p.log_ka_mean, p.log_ka_mean, p.log_ka_sd)
        )
        assert lp == pytest.approx(expected)

    def test_log_prior_iv_sums_two_normals(self):
        p = PKPrior()
        lp = p.log_prior_iv(p.log_cl_mean, p.log_v_mean)
        expected = _log_normal_logpdf(
            p.log_cl_mean, p.log_cl_mean, p.log_cl_sd
        ) + _log_normal_logpdf(p.log_v_mean, p.log_v_mean, p.log_v_sd)
        assert lp == pytest.approx(expected)


class TestObjectiveSign:
    """Verify the MAP objective direction and sign conventions.

    The objective is -(log_prior + log_likelihood). Log-densities of continuous
    Normal distributions are NOT bounded above by 0 (the PDF can exceed 1 when
    sigma < 1/sqrt(2*pi) ~= 0.4), so the objective is not guaranteed non-negative.
    The invariant that matters is: objective is LOWER at the true MAP than at
    deliberately bad parameter values.

    Per the ADR: both log terms are negative relative to their maximum, so the
    negated objective is globally minimized at the MAP.
    """

    def test_objective_is_negated_log_posterior(self):
        """Objective equals -(log_prior + log_likelihood) at any point."""
        prior = PKPrior()
        obj = _make_objective(np.array(_TIMES_ORAL), np.array(_TRUE_ORAL), _DOSE, "oral", prior)
        x = np.array([math.log(_TRUE_CL_F), math.log(_TRUE_VZ_F), math.log(_TRUE_KA)])
        lp = _log_prior(x, prior, "oral")
        ll = _log_likelihood(
            x, np.array(_TIMES_ORAL), np.array(_TRUE_ORAL), _DOSE, "oral", prior.sigma_mean
        )
        assert obj(x) == pytest.approx(-(lp + ll), rel=1e-6)

    def test_objective_lower_at_true_than_at_bad_params(self):
        """Objective at true parameters must be lower than at deliberately bad params."""
        prior = PKPrior()
        obj = _make_objective(np.array(_TIMES_ORAL), np.array(_TRUE_ORAL), _DOSE, "oral", prior)
        x_true = np.array([math.log(_TRUE_CL_F), math.log(_TRUE_VZ_F), math.log(_TRUE_KA)])
        x_bad_low = np.array([math.log(0.001), math.log(_TRUE_VZ_F), math.log(_TRUE_KA)])
        x_bad_high = np.array([math.log(1000.0), math.log(_TRUE_VZ_F), math.log(_TRUE_KA)])
        assert obj(x_true) < obj(x_bad_low)
        assert obj(x_true) < obj(x_bad_high)

    def test_log_likelihood_higher_at_true_than_at_bad_params(self):
        """Log-likelihood is higher (less negative) at the true parameters."""
        x_true = np.array([math.log(_TRUE_CL_F), math.log(_TRUE_VZ_F), math.log(_TRUE_KA)])
        x_bad = np.array([math.log(0.001), math.log(_TRUE_VZ_F), math.log(_TRUE_KA)])
        ll_true = _log_likelihood(
            x_true, np.array(_TIMES_ORAL), np.array(_TRUE_ORAL), _DOSE, "oral", 0.2
        )
        ll_bad = _log_likelihood(
            x_bad, np.array(_TIMES_ORAL), np.array(_TRUE_ORAL), _DOSE, "oral", 0.2
        )
        assert ll_true > ll_bad


class TestMapOral:
    def test_recovers_true_params_within_10pct(self):
        """MAP from noiseless oral data recovers CL_F, Vz_F, ka within 10%.

        Reference: Sheiner & Beal (1982), J Pharm Sci 71:1344-8.
        """
        prior = PKPrior(
            log_cl_mean=math.log(_TRUE_CL_F),
            log_v_mean=math.log(_TRUE_VZ_F),
            log_ka_mean=math.log(_TRUE_KA),
        )
        result = map_individual_pk(_TIMES_ORAL, _TRUE_ORAL, _DOSE, "oral", prior)
        assert result.converged
        assert pytest.approx(_TRUE_CL_F, rel=0.10) == result.CL_F
        assert result.Vz_F == pytest.approx(_TRUE_VZ_F, rel=0.10)
        assert result.ka == pytest.approx(_TRUE_KA, rel=0.10)

    def test_route_fields_populated(self):
        result = map_individual_pk(_TIMES_ORAL, _TRUE_ORAL, _DOSE, "oral")
        assert result.CL_F is not None
        assert result.Vz_F is not None
        assert result.ka is not None
        assert result.CL is None
        assert result.Vz is None

    def test_derived_params_finite(self):
        result = map_individual_pk(_TIMES_ORAL, _TRUE_ORAL, _DOSE, "oral")
        assert math.isfinite(result.half_life)
        assert math.isfinite(result.AUCinf)
        assert result.Cmax > 0
        assert result.Tmax >= 0

    def test_predicted_length_matches_times(self):
        result = map_individual_pk(_TIMES_ORAL, _TRUE_ORAL, _DOSE, "oral")
        assert len(result.predicted_conc) == len(_TIMES_ORAL)

    def test_subject_label_preserved(self):
        result = map_individual_pk(_TIMES_ORAL, _TRUE_ORAL, _DOSE, "oral", subject="S01")
        assert result.subject == "S01"

    def test_to_dict_keys(self):
        result = map_individual_pk(_TIMES_ORAL, _TRUE_ORAL, _DOSE, "oral")
        d = result.to_dict()
        for key in ("CL_F", "Vz_F", "ka", "converged", "half_life", "AUCinf"):
            assert key in d

    def test_summary_contains_disclaimer(self):
        result = map_individual_pk(_TIMES_ORAL, _TRUE_ORAL, _DOSE, "oral")
        assert "Disclaimer" in result.summary()

    def test_summary_is_ascii(self):
        result = map_individual_pk(_TIMES_ORAL, _TRUE_ORAL, _DOSE, "oral")
        result.summary().encode("ascii")  # must not raise


class TestMapIV:
    def test_recovers_true_params_within_10pct(self):
        """MAP from noiseless IV data recovers CL, Vz within 10%.

        Reference: Rowland & Tozer, Clinical Pharmacokinetics (2011), Ch. 3.
        """
        prior = PKPrior(
            log_cl_mean=math.log(_TRUE_CL),
            log_v_mean=math.log(_TRUE_VZ),
        )
        result = map_individual_pk(_TIMES_IV, _TRUE_IV, _DOSE, "iv_bolus", prior)
        assert result.converged
        assert pytest.approx(_TRUE_CL, rel=0.10) == result.CL
        assert result.Vz == pytest.approx(_TRUE_VZ, rel=0.10)

    def test_route_fields_populated(self):
        result = map_individual_pk(_TIMES_IV, _TRUE_IV, _DOSE, "iv_bolus")
        assert result.CL is not None
        assert result.Vz is not None
        assert result.CL_F is None
        assert result.Vz_F is None
        assert result.ka is None


class TestDiagnostics:
    def test_converged_flag_true_on_easy_problem(self):
        result = map_individual_pk(_TIMES_ORAL, _TRUE_ORAL, _DOSE, "oral")
        assert result.converged is True

    def test_gradient_norm_stored(self):
        result = map_individual_pk(_TIMES_ORAL, _TRUE_ORAL, _DOSE, "oral")
        assert isinstance(result.gradient_norm, float)
        assert result.gradient_norm >= 0.0

    def test_condition_number_stored(self):
        result = map_individual_pk(_TIMES_ORAL, _TRUE_ORAL, _DOSE, "oral")
        assert isinstance(result.condition_number, float)
        assert result.condition_number >= 1.0

    def test_uncertainty_reliable_on_clean_data(self):
        prior = PKPrior(
            log_cl_mean=math.log(_TRUE_CL_F),
            log_v_mean=math.log(_TRUE_VZ_F),
            log_ka_mean=math.log(_TRUE_KA),
        )
        result = map_individual_pk(_TIMES_ORAL, _TRUE_ORAL, _DOSE, "oral", prior)
        assert result.uncertainty_reliable is True

    def test_se_available_when_reliable(self):
        prior = PKPrior(
            log_cl_mean=math.log(_TRUE_CL_F),
            log_v_mean=math.log(_TRUE_VZ_F),
            log_ka_mean=math.log(_TRUE_KA),
        )
        result = map_individual_pk(_TIMES_ORAL, _TRUE_ORAL, _DOSE, "oral", prior)
        if result.uncertainty_reliable:
            assert result.CL_F_se is not None
            assert result.Vz_F_se is not None
            assert result.ka_se is not None
            assert result.CL_F_se > 0

    def test_warnings_is_list(self):
        result = map_individual_pk(_TIMES_ORAL, _TRUE_ORAL, _DOSE, "oral")
        assert isinstance(result.warnings, list)


class TestValidation:
    def test_too_few_obs_oral_raises(self):
        with pytest.raises(ValueError, match="3 observations"):
            map_individual_pk([1.0, 2.0], [5.0, 3.0], _DOSE, "oral")

    def test_too_few_obs_iv_raises(self):
        with pytest.raises(ValueError, match="2 observations"):
            map_individual_pk([1.0], [5.0], _DOSE, "iv_bolus")

    def test_unsupported_route_raises(self):
        with pytest.raises(ValueError, match="Unsupported route"):
            map_individual_pk(_TIMES_ORAL, _TRUE_ORAL, _DOSE, "subcutaneous")

    def test_negative_dose_raises(self):
        with pytest.raises(ValueError, match="dose must be"):
            map_individual_pk(_TIMES_ORAL, _TRUE_ORAL, -1.0, "oral")

    def test_mismatched_lengths_raises(self):
        with pytest.raises(ValueError, match="same length"):
            map_individual_pk([1.0, 2.0, 3.0], [5.0, 3.0], _DOSE, "oral")

    @pytest.mark.parametrize(
        ("times", "concentrations", "message"),
        [
            (_TIMES_ORAL, [0.0] * len(_TIMES_ORAL), "at least one"),
            (_TIMES_ORAL, [-1.0, *_TRUE_ORAL[1:]], ">= 0"),
            ([0.5, 1.0, 1.0, 4.0, 8.0, 12.0], _TRUE_ORAL, "strictly increasing"),
            ([-0.5, 1.0, 2.0, 4.0, 8.0, 12.0], _TRUE_ORAL, ">= 0"),
        ],
    )
    def test_invalid_profile_raises(self, times, concentrations, message):
        with pytest.raises(ValueError, match=message):
            map_individual_pk(times, concentrations, _DOSE, "oral")


class TestNumericalHessian:
    def test_hessian_is_symmetric(self):
        prior = PKPrior(
            log_cl_mean=math.log(_TRUE_CL_F),
            log_v_mean=math.log(_TRUE_VZ_F),
            log_ka_mean=math.log(_TRUE_KA),
        )
        obj = _make_objective(np.array(_TIMES_ORAL), np.array(_TRUE_ORAL), _DOSE, "oral", prior)
        x = np.array([math.log(_TRUE_CL_F), math.log(_TRUE_VZ_F), math.log(_TRUE_KA)])
        H = _numerical_hessian(obj, x)
        assert H.shape == (3, 3)
        np.testing.assert_allclose(H, H.T, atol=1e-4)

    def test_hessian_positive_definite_at_true_params(self):
        prior = PKPrior(
            log_cl_mean=math.log(_TRUE_CL_F),
            log_v_mean=math.log(_TRUE_VZ_F),
            log_ka_mean=math.log(_TRUE_KA),
        )
        obj = _make_objective(np.array(_TIMES_ORAL), np.array(_TRUE_ORAL), _DOSE, "oral", prior)
        x = np.array([math.log(_TRUE_CL_F), math.log(_TRUE_VZ_F), math.log(_TRUE_KA)])
        H = _numerical_hessian(obj, x)
        eigvals = np.linalg.eigvalsh(H)
        assert np.all(eigvals > 0)


class TestReport:
    def test_html_report_generated(self, tmp_path):
        result = map_individual_pk(_TIMES_ORAL, _TRUE_ORAL, _DOSE, "oral")
        out = tmp_path / "map_report.html"
        content = result.report(out, format="html")
        assert out.exists()
        assert "<html" in content
        assert "Disclaimer" in content

    def test_markdown_report_generated(self, tmp_path):
        result = map_individual_pk(_TIMES_ORAL, _TRUE_ORAL, _DOSE, "oral")
        out = tmp_path / "map_report.md"
        content = result.report(out, format="markdown")
        assert out.exists()
        assert "# MAP" in content

    def test_unknown_format_raises(self, tmp_path):
        result = map_individual_pk(_TIMES_ORAL, _TRUE_ORAL, _DOSE, "oral")
        with pytest.raises(ValueError, match="Unknown format"):
            result.report(tmp_path / "out.xyz", format="xyz")

    def test_html_contains_converged_status(self, tmp_path):
        result = map_individual_pk(_TIMES_ORAL, _TRUE_ORAL, _DOSE, "oral")
        content = result.report(tmp_path / "r.html", format="html")
        assert "Converged" in content

    def test_html_report_escapes_subject(self, tmp_path):
        result = map_individual_pk(
            _TIMES_ORAL,
            _TRUE_ORAL,
            _DOSE,
            "oral",
            subject="<script>alert(1)</script>",
        )
        content = result.report(tmp_path / "escaped.html", format="html")
        assert "&lt;script&gt;" in content
        assert "<script>" not in content

    def test_iv_html_report(self, tmp_path):
        result = map_individual_pk(_TIMES_IV, _TRUE_IV, _DOSE, "iv_bolus")
        content = result.report(tmp_path / "iv_report.html", format="html")
        assert "CL (systemic clearance)" in content
