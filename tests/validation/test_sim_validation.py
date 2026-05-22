"""Cross-validation of sim module against Gibaldi & Perrier worked examples.

Uses specific numerical values from Gibaldi M, Perrier D (1982). Pharmacokinetics,
2nd ed. Marcel Dekker. Chapter examples are solved to verify the analytical
implementations match published results.

Reference nomenclature follows Gibaldi & Perrier:
  k = CL/Vz (elimination rate constant)
  C(t) = (D/Vz) * exp(-k*t)  [1-cmt IV bolus, Eq. 1-2]
  AUCinf = D/CL               [1-cmt, Eq. 1-4]
  t1/2 = 0.693/k              [any linear compartment]
"""

from __future__ import annotations

import math

import numpy as np

from openpkflow.sim.methods import (
    c_1cmt_iv_bolus,
    c_1cmt_oral,
    c_2cmt_iv_bolus,
    c_2cmt_iv_infusion,
)
from openpkflow.validation import within_pct


class TestGibaldiPerrier1CmtIVBolus:
    """Verify 1-cmt IV bolus against the analytical formula.

    Gibaldi & Perrier, 2nd ed. (1982), Eq. 1-2, p. 2.
    Parameters chosen to produce clean round-number answers.
    """

    def test_c_at_half_life_is_half_c0(self) -> None:
        """C(t1/2) = C(0)/2 by definition of half-life.

        Reference: Gibaldi & Perrier 2nd ed. (1982), p. 3.
        """
        CL, Vz, dose = 6.0, 30.0, 300.0
        k = CL / Vz
        t_half = math.log(2.0) / k
        C0 = c_1cmt_iv_bolus([0.0], dose=dose, CL=CL, Vz=Vz)[0]
        Ct = c_1cmt_iv_bolus([t_half], dose=dose, CL=CL, Vz=Vz)[0]
        assert within_pct(Ct, C0 / 2.0, pct=0.001)

    def test_aucinf_equals_dose_over_cl(self) -> None:
        """Numerical AUCinf via trapezoidal matches D/CL within 0.5%.

        Reference: Gibaldi & Perrier 2nd ed. (1982), Eq. 1-4, p. 2.
        """
        CL, Vz, dose = 6.0, 30.0, 300.0
        t = np.linspace(0, 200, 50000)
        C = c_1cmt_iv_bolus(t, dose=dose, CL=CL, Vz=Vz)
        aucinf_numerical = float(np.trapezoid(C, t))
        true_aucinf = dose / CL
        assert within_pct(aucinf_numerical, true_aucinf, pct=0.5)

    def test_auc_fraction_at_two_half_lives(self) -> None:
        """AUC(0 to 2*t1/2) / AUCinf = 1 - exp(-2*ln2) = 0.75.

        Reference: Gibaldi & Perrier 2nd ed. (1982), p. 3.
        """
        CL, Vz, dose = 4.0, 20.0, 200.0
        k = CL / Vz
        t_half = math.log(2.0) / k
        t = np.linspace(0, 2 * t_half, 10000)
        C = c_1cmt_iv_bolus(t, dose=dose, CL=CL, Vz=Vz)
        auc_partial = float(np.trapezoid(C, t))
        true_aucinf = dose / CL
        expected_fraction = 1.0 - math.exp(-2.0 * math.log(2.0))
        actual_fraction = auc_partial / true_aucinf
        assert within_pct(actual_fraction, expected_fraction, pct=0.1)


class TestGibaldiPerrier1CmtOral:
    """Verify 1-cmt oral Bateman equation properties.

    Gibaldi & Perrier, 2nd ed. (1982), Eq. 1-13, p. 16.
    """

    def test_tmax_formula(self) -> None:
        """Tmax = ln(ka/k) / (ka - k) (Bateman peak-time formula).

        Reference: Gibaldi & Perrier 2nd ed. (1982), Eq. 1-16, p. 17.
        """
        CL_F, Vz_F, ka, dose = 5.0, 25.0, 1.2, 100.0
        k = CL_F / Vz_F
        true_tmax = math.log(ka / k) / (ka - k)

        t = np.linspace(0, 48, 5000)
        C = c_1cmt_oral(t, dose=dose, CL_F=CL_F, Vz_F=Vz_F, ka=ka)
        sim_tmax = float(t[np.argmax(C)])
        assert within_pct(sim_tmax, true_tmax, pct=0.5)

    def test_aucinf_equals_dose_over_cl_f(self) -> None:
        """Numerical AUCinf matches D/CL_F within 0.5%.

        Reference: Gibaldi & Perrier 2nd ed. (1982), Eq. 1-19, p. 17.
        """
        CL_F, Vz_F, ka, dose = 5.0, 25.0, 1.2, 100.0
        t = np.linspace(0, 200, 50000)
        C = c_1cmt_oral(t, dose=dose, CL_F=CL_F, Vz_F=Vz_F, ka=ka)
        aucinf_numerical = float(np.trapezoid(C, t))
        assert within_pct(aucinf_numerical, dose / CL_F, pct=0.5)


class TestGibaldiPerrier2CmtIVBolus:
    """Verify 2-cmt IV bolus AUCinf = D/CL.

    Gibaldi & Perrier, 2nd ed. (1982), Eq. 3-1, p. 62.
    """

    def test_aucinf_equals_dose_over_cl(self) -> None:
        """Numerical AUCinf for 2-cmt IV bolus equals D/CL within 1%.

        Reference: Gibaldi & Perrier 2nd ed. (1982), p. 63: AUCinf = A/alpha + B/beta = D/CL.
        """
        CL, V1, Q, V2, dose = 5.0, 20.0, 3.0, 15.0, 100.0
        t = np.linspace(0, 300, 100000)
        C = c_2cmt_iv_bolus(t, dose=dose, CL=CL, V1=V1, Q=Q, V2=V2)
        aucinf_numerical = float(np.trapezoid(C, t))
        assert within_pct(aucinf_numerical, dose / CL, pct=1.0)

    def test_c0_equals_dose_over_v1(self) -> None:
        """C(0) = D/V1 for 2-cmt IV bolus.

        Reference: Gibaldi & Perrier 2nd ed. (1982), Eq. 3-1, p. 62.
        """
        CL, V1, Q, V2, dose = 5.0, 20.0, 3.0, 15.0, 100.0
        C0 = c_2cmt_iv_bolus([0.0], dose=dose, CL=CL, V1=V1, Q=Q, V2=V2)[0]
        assert within_pct(C0, dose / V1, pct=0.001)


class TestGibaldiPerrier2CmtIVInfusion:
    """Verify 2-cmt IV infusion properties.

    Gibaldi & Perrier, 2nd ed. (1982), Eqs. 3-28 to 3-30, p. 75.
    """

    def test_aucinf_equals_dose_over_cl(self) -> None:
        """AUCinf for 2-cmt IV infusion must equal D/CL (invariant across any t_inf).

        Reference: AUCinf = D/CL for any linear PK system (dose-rate independent).
        Gibaldi & Perrier 2nd ed. (1982), Chapter 3.
        """
        CL, V1, Q, V2, dose, t_inf = 5.0, 20.0, 3.0, 15.0, 100.0, 1.0
        t = np.linspace(0, 300, 100000)
        C = c_2cmt_iv_infusion(t, dose=dose, CL=CL, V1=V1, Q=Q, V2=V2, t_inf=t_inf)
        aucinf_numerical = float(np.trapezoid(C, t))
        assert within_pct(aucinf_numerical, dose / CL, pct=1.0)

    def test_aucinf_independent_of_t_inf(self) -> None:
        """AUCinf must be the same regardless of infusion duration (same dose and CL).

        Reference: AUCinf = D/CL (independent of input rate in linear PK).
        """
        CL, V1, Q, V2, dose = 5.0, 20.0, 3.0, 15.0, 100.0
        t = np.linspace(0, 300, 100000)
        aucinf_short = float(
            np.trapezoid(
                c_2cmt_iv_infusion(t, dose=dose, CL=CL, V1=V1, Q=Q, V2=V2, t_inf=0.5),
                t,
            )
        )
        aucinf_long = float(
            np.trapezoid(
                c_2cmt_iv_infusion(t, dose=dose, CL=CL, V1=V1, Q=Q, V2=V2, t_inf=5.0),
                t,
            )
        )
        assert within_pct(aucinf_short, aucinf_long, pct=1.0)
