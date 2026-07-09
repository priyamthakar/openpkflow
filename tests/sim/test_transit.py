"""Tests for transit-compartment oral absorption (c_1cmt_oral_transit).

References
----------
Savic, R. M., Jonker, D. M., van Houten, P., & Karlsson, M. O. (2007).
Implementation of a transit compartment model for describing drug absorption
in pharmacokinetic studies. J Pharmacokinet Pharmacodyn, 34(5), 711-726.
DOI: 10.1007/s10928-007-9066-0

Gibaldi, M., & Perrier, D. (1982). Pharmacokinetics (2nd ed.). Marcel Dekker.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from openpkflow.sim.methods import c_1cmt_oral, c_1cmt_oral_transit


class TestC1CmtOralTransit:
    """Tests for c_1cmt_oral_transit."""

    def test_n1_matches_classical_oral(self) -> None:
        """Degenerate: n_transit=1 reduces to Bateman 1-cmt oral.

        Reference: Gibaldi & Perrier (1982), Eq. 1-13 (first-order oral);
        with a single absorption depot the transit chain is classical oral.
        """
        t = np.linspace(0.0, 24.0, 49)
        kwargs = dict(dose=100.0, CL=5.0, Vz=50.0, ka=1.2)
        c_tr = c_1cmt_oral_transit(t, n_transit=1, mtt=1.0, **kwargs)
        c_or = c_1cmt_oral(t, dose=100.0, CL_F=5.0, Vz_F=50.0, ka=1.2)
        np.testing.assert_allclose(c_tr, c_or, rtol=1e-12, atol=1e-12)

    def test_concentrations_nonnegative(self) -> None:
        """All concentrations are non-negative (mass conservation sanity)."""
        t = np.linspace(0.0, 48.0, 97)
        c = c_1cmt_oral_transit(t, dose=100.0, CL=4.0, Vz=40.0, ka=0.8, n_transit=5, mtt=2.0)
        assert np.all(c >= -1e-14)
        assert c[0] == pytest.approx(0.0, abs=1e-12)

    def test_higher_n_delays_tmax(self) -> None:
        """Increasing n_transit delays Tmax (Savic transit delay property).

        Reference
        ---------
        Savic et al. (2007), DOI: 10.1007/s10928-007-9066-0: additional
        transit compartments delay and smooth the absorption input, shifting
        Tmax later for fixed MTT.
        """
        t = np.linspace(0.0, 24.0, 241)
        common = dict(dose=100.0, CL=5.0, Vz=50.0, ka=1.5, mtt=2.0)
        c3 = c_1cmt_oral_transit(t, n_transit=3, **common)
        c8 = c_1cmt_oral_transit(t, n_transit=8, **common)
        tmax3 = float(t[int(np.argmax(c3))])
        tmax8 = float(t[int(np.argmax(c8))])
        assert tmax8 > tmax3

    def test_auc_approaches_dose_over_cl(self) -> None:
        """Trapezoidal AUC to late time approaches Dose/CL (bioavailability=1).

        Reference: Gibaldi & Perrier (1982), AUC_inf = F*Dose/CL with F=1.
        """
        dose, CL, Vz, ka = 100.0, 5.0, 50.0, 1.0
        t = np.linspace(0.0, 72.0, 721)
        c = c_1cmt_oral_transit(t, dose=dose, CL=CL, Vz=Vz, ka=ka, n_transit=4, mtt=1.5)
        auc = float(np.trapezoid(c, t) if hasattr(np, "trapezoid") else np.trapz(c, t))
        assert math.isclose(auc, dose / CL, rel_tol=0.02)

    def test_invalid_n_transit_raises(self) -> None:
        with pytest.raises(ValueError, match="n_transit"):
            c_1cmt_oral_transit(
                [0.0, 1.0], dose=10.0, CL=1.0, Vz=10.0, ka=1.0, n_transit=0, mtt=1.0
            )

    def test_invalid_mtt_raises(self) -> None:
        with pytest.raises(ValueError, match="mtt"):
            c_1cmt_oral_transit(
                [0.0, 1.0], dose=10.0, CL=1.0, Vz=10.0, ka=1.0, n_transit=3, mtt=0.0
            )
