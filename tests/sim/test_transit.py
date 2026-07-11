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
    """Tests for c_1cmt_oral_transit (Savic transit + depot + central)."""

    def test_mtt_affects_profile_when_n1(self) -> None:
        """n_transit=1 must still use MTT (not ignore it / collapse to Bateman).

        Hand-checkable: smaller MTT (faster ktr) approaches classical oral;
        larger MTT delays the profile relative to classical Bateman.

        Reference: Savic et al. (2007) DOI: 10.1007/s10928-007-9066-0.
        """
        t = np.linspace(0.0, 24.0, 241)
        common = dict(dose=100.0, CL_F=5.0, Vz_F=50.0, ka=1.2, n_transit=1)
        c_fast = c_1cmt_oral_transit(t, mtt=0.05, **common)
        c_slow = c_1cmt_oral_transit(t, mtt=2.0, **common)
        c_oral = c_1cmt_oral(t, dose=100.0, CL_F=5.0, Vz_F=50.0, ka=1.2)
        # Fast transit nearly matches classical oral Cmax
        assert abs(float(np.max(c_fast)) - float(np.max(c_oral))) < abs(
            float(np.max(c_slow)) - float(np.max(c_oral))
        )
        tmax_fast = float(t[int(np.argmax(c_fast))])
        tmax_slow = float(t[int(np.argmax(c_slow))])
        assert tmax_slow > tmax_fast

    def test_concentrations_nonnegative(self) -> None:
        """All concentrations are non-negative (mass conservation sanity)."""
        t = np.linspace(0.0, 48.0, 97)
        c = c_1cmt_oral_transit(t, dose=100.0, CL_F=4.0, Vz_F=40.0, ka=0.8, n_transit=5, mtt=2.0)
        assert np.all(c >= -1e-14)
        assert c[0] == pytest.approx(0.0, abs=1e-12)

    def test_larger_mtt_delays_tmax(self) -> None:
        """Larger MTT delays Tmax (Savic transit delay property).

        Reference
        ---------
        Savic et al. (2007), DOI: 10.1007/s10928-007-9066-0: mean transit
        time controls the absorption delay for a fixed n.
        """
        t = np.linspace(0.0, 24.0, 241)
        common = dict(dose=100.0, CL_F=5.0, Vz_F=50.0, ka=1.5, n_transit=4)
        c_fast = c_1cmt_oral_transit(t, mtt=0.5, **common)
        c_slow = c_1cmt_oral_transit(t, mtt=3.0, **common)
        tmax_fast = float(t[int(np.argmax(c_fast))])
        tmax_slow = float(t[int(np.argmax(c_slow))])
        assert tmax_slow > tmax_fast

    def test_auc_approaches_dose_over_cl_f(self) -> None:
        """Trapezoidal AUC to late time approaches Dose/CL_F (F=1).

        Reference: Gibaldi & Perrier (1982), AUC_inf = F*Dose/CL with F=1.
        """
        dose, CL_F, Vz_F, ka = 100.0, 5.0, 50.0, 1.0
        t = np.linspace(0.0, 72.0, 721)
        c = c_1cmt_oral_transit(t, dose=dose, CL_F=CL_F, Vz_F=Vz_F, ka=ka, n_transit=4, mtt=1.5)
        auc = float(np.trapezoid(c, t) if hasattr(np, "trapezoid") else np.trapz(c, t))
        assert math.isclose(auc, dose / CL_F, rel_tol=0.03)

    def test_invalid_n_transit_raises(self) -> None:
        with pytest.raises(ValueError, match="n_transit"):
            c_1cmt_oral_transit(
                [0.0, 1.0],
                dose=10.0,
                CL_F=1.0,
                Vz_F=10.0,
                ka=1.0,
                n_transit=0,
                mtt=1.0,
            )

    def test_invalid_mtt_raises(self) -> None:
        with pytest.raises(ValueError, match="mtt"):
            c_1cmt_oral_transit(
                [0.0, 1.0],
                dose=10.0,
                CL_F=1.0,
                Vz_F=10.0,
                ka=1.0,
                n_transit=3,
                mtt=0.0,
            )
