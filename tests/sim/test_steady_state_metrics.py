"""Tests for analytical 1-cmt oral steady-state metrics.

References
----------
Gibaldi, M., & Perrier, D. (1982). Pharmacokinetics (2nd ed.). Marcel Dekker.
Rowland, M., & Tozer, T. N. Clinical Pharmacokinetics and Pharmacodynamics
concepts for Css_avg and fluctuation at steady state.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from openpkflow.sim.methods import (
    c_1cmt_oral,
    steady_state_metrics_1cmt_oral,
    superpose,
)


class TestSteadyStateMetrics1CmtOral:
    """Tests for steady_state_metrics_1cmt_oral."""

    def test_css_avg_equals_dose_over_cl_tau(self) -> None:
        """Degenerate/sanity: Css_avg = Dose / (CL * tau), AUCtau = Dose/CL.

        Reference: Gibaldi & Perrier (1982); for linear kinetics
        AUCtau,ss = F*Dose/CL and Css_avg = AUCtau/tau.
        """
        dose, tau, CL, Vz, ka = 100.0, 12.0, 5.0, 50.0, 1.0
        m = steady_state_metrics_1cmt_oral(dose, tau, CL, Vz, ka)
        assert math.isclose(m["AUCtau"], dose / CL, rel_tol=1e-12)
        assert math.isclose(m["Css_avg"], dose / (CL * tau), rel_tol=1e-12)
        assert m["Css_max"] > m["Css_min"]
        assert m["Css_max"] > m["Css_avg"] > m["Css_min"]
        assert math.isclose(
            m["fluctuation"],
            (m["Css_max"] - m["Css_min"]) / m["Css_avg"],
            rel_tol=1e-12,
        )

    def test_matches_superposition_numerical_ss(self) -> None:
        """Closed-form Css_max/min match multi-dose superposition at SS.

        Reference
        ---------
        Gibaldi & Perrier (1982), Chapter 3: steady-state multi-dose
        concentration for one-compartment first-order absorption is the
        infinite geometric series of single-dose Bateman contributions,
        equivalent to the closed form used here.
        """
        dose, tau, CL, Vz, ka = 100.0, 8.0, 4.0, 40.0, 1.5
        m = steady_state_metrics_1cmt_oral(dose, tau, CL, Vz, ka)

        # Superpose many doses; evaluate last interval densely
        n_doses = 40
        dose_times = [i * tau for i in range(n_doses)]
        amounts = [dose] * n_doses
        t0 = (n_doses - 1) * tau
        t_grid = np.linspace(t0, t0 + tau, 401)

        def unit_fn(t_rel: np.ndarray, amount: float) -> np.ndarray:
            return c_1cmt_oral(t_rel, dose=amount, CL_F=CL, Vz_F=Vz, ka=ka)

        c_ss = superpose(t_grid, dose_times, amounts, unit_fn)
        num_max = float(np.max(c_ss))
        num_min = float(c_ss[-1])  # trough at end of interval
        assert math.isclose(m["Css_max"], num_max, rel_tol=0.02)
        assert math.isclose(m["Css_min"], num_min, rel_tol=0.02)

    def test_hand_check_auctau(self) -> None:
        """Hand-check AUCtau and Css_avg with simple integers.

        dose=120, CL=10, tau=6 -> AUCtau=12, Css_avg=2.

        Reference: Rowland & Tozer / Gibaldi & Perrier: Css_avg = (F*Dose/CL)/tau.
        """
        m = steady_state_metrics_1cmt_oral(dose=120.0, tau=6.0, CL=10.0, Vz=50.0, ka=2.0)
        assert math.isclose(m["AUCtau"], 12.0, rel_tol=1e-12)
        assert math.isclose(m["Css_avg"], 2.0, rel_tol=1e-12)

    def test_flip_flop_raises(self) -> None:
        with pytest.raises(ValueError, match="numerically equal"):
            steady_state_metrics_1cmt_oral(
                dose=100.0,
                tau=12.0,
                CL=5.0,
                Vz=50.0,
                ka=0.1,  # k = 0.1
            )

    def test_invalid_tau_raises(self) -> None:
        with pytest.raises(ValueError, match="tau"):
            steady_state_metrics_1cmt_oral(dose=100.0, tau=0.0, CL=5.0, Vz=50.0, ka=1.0)
