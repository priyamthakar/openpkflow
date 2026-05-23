"""Tests for objective functions."""

import numpy as np
import pytest

from openpkflow.pop.estimation.objective import (
    compute_foce_minus2ll,
    compute_linearization,
    individual_log_likelihood,
    individual_prior_logp,
    pack_theta,
    predict_individual,
    unpack_theta,
)


class TestPredictIndividual:
    def test_oral_predict(self) -> None:
        t = np.array([0.5, 1.0, 2.0, 4.0])
        c = predict_individual(t, 100.0, np.array([5.0, 50.0, 1.0]), "oral")
        assert len(c) == 4
        assert np.all(np.isfinite(c))
        assert np.all(c >= 0)
        assert c[0] < 100.0

    def test_iv_bolus_predict(self) -> None:
        t = np.array([0.5, 1.0, 2.0, 4.0])
        c = predict_individual(t, 100.0, np.array([5.0, 50.0]), "iv_bolus")
        assert len(c) == 4
        assert np.all(np.isfinite(c))
        assert np.all(c >= 0)
        assert c[0] >= c[-1]

    def test_bad_route_raises(self) -> None:
        with pytest.raises(ValueError):
            predict_individual(np.array([1.0]), 100.0, np.array([5.0, 50.0]), "bad_route")


class TestIndividualLogLikelihood:
    def test_perfect_fit(self) -> None:
        t = np.array([1.0, 2.0, 4.0])
        dose = 100.0
        theta_i = np.array([5.0, 50.0, 1.0])
        c_pred = predict_individual(t, dose, theta_i, "oral")
        ll = individual_log_likelihood(t, c_pred, dose, theta_i, 0.01, 0.0, "oral")
        assert np.isfinite(ll)

    def test_small_params_still_finite(self) -> None:
        ll = individual_log_likelihood(
            np.array([1.0]), np.array([1.0]), 1.0, np.array([0.01, 0.01, 0.01]), 0.15, 0.0, "oral"
        )
        assert np.isfinite(ll)


class TestIndividualPrior:
    def test_zero_eta(self) -> None:
        omega = np.diag([0.1, 0.1])
        omega_inv = np.linalg.inv(omega)
        lp = individual_prior_logp(np.array([0.0, 0.0]), omega_inv)
        assert np.isfinite(lp)

    def test_nontrivial_eta(self) -> None:
        omega = np.diag([0.1, 0.1])
        omega_inv = np.linalg.inv(omega)
        lp1 = individual_prior_logp(np.array([0.0, 0.0]), omega_inv)
        lp2 = individual_prior_logp(np.array([2.0, 2.0]), omega_inv)
        assert lp1 > lp2


class TestComputeLinearization:
    def test_shape_and_finite(self) -> None:
        t = np.array([0.5, 1.0, 2.0, 4.0])
        theta_pop = np.array([5.0, 50.0, 1.0])
        eta_hat = np.array([0.0, 0.0, 0.0])
        G, f_hat, theta_i_hat = compute_linearization(t, 100.0, theta_pop, eta_hat, "oral")
        assert G.shape == (4, 3)
        assert len(f_hat) == 4
        assert len(theta_i_hat) == 3
        assert np.all(np.isfinite(G))
        assert np.all(np.isfinite(f_hat))


class TestComputeFoceMinus2ll:
    def test_returns_finite_value(self) -> None:
        t = np.array([0.5, 1.0, 2.0, 4.0])
        y_obs = np.array([0.8, 1.5, 1.2, 0.6])
        theta_pop = np.array([5.0, 50.0, 1.0])
        omega = np.diag([0.1, 0.1, 0.1])
        eta_hat = np.array([0.0, 0.0, 0.0])
        m2ll = compute_foce_minus2ll(t, y_obs, 100.0, theta_pop, omega, 0.15, 0.0, eta_hat, "oral")
        assert np.isfinite(m2ll)
        assert m2ll > 0


class TestPackUnpack:
    def test_roundtrip(self) -> None:
        theta_pop = np.array([5.0, 50.0, 1.0])
        omega_diag = np.array([0.1, 0.09, 0.04])
        sp = 0.15
        sa = 0.01
        theta_vec = pack_theta(theta_pop, omega_diag, sp, sa)
        assert len(theta_vec) == 8
        tp, od, sp2, sa2 = unpack_theta(theta_vec, 3)
        np.testing.assert_allclose(tp, theta_pop, rtol=1e-10)
        np.testing.assert_allclose(od, omega_diag, rtol=1e-10)
        assert abs(sp2 - sp) < 1e-10
        assert abs(sa2 - sa) < 1e-10
