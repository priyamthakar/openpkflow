"""Cross-validation of NCA against analytically-known reference values.

Strategy: simulate concentration-time profiles from exact PK equations, then run
NCA and verify that recovered parameters match the true inputs within tolerance.
This tests correctness (not just self-consistency) because the ground truth is derived
from first principles rather than from a previous run of the same code.

Reference for PK equations:
  Gibaldi M, Perrier D (1982). Pharmacokinetics, 2nd ed. Marcel Dekker, New York.
  Rowland M, Tozer TN (2011). Clinical Pharmacokinetics and Pharmacodynamics, 4th ed.

Reference for NCA parameter relationships (IV bolus):
  AUCinf = D/CL (exact, by definition of clearance in a linear system).
  AUClast = AUCinf * (1 - exp(-k*t_last)) for 1-cmt IV bolus.
  lambda_z = k = CL/Vz.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from openpkflow.nca.study import NCAStudy
from openpkflow.sim.methods import c_1cmt_iv_bolus, c_1cmt_iv_infusion
from openpkflow.validation import pct_bias, within_pct


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_iv_bolus_df(
    CL: float,
    Vz: float,
    dose: float,
    subject: str = "SIM001",
    route: str = "iv",
) -> "pandas.DataFrame":
    """Generate a synthetic NCA-ready DataFrame from a 1-cmt IV bolus."""
    import pandas as pd

    t = np.array([0.0, 0.5, 1.0, 2.0, 4.0, 6.0, 8.0, 12.0, 16.0, 24.0])
    conc = c_1cmt_iv_bolus(t, dose=dose, CL=CL, Vz=Vz)
    return pd.DataFrame(
        {"subject": subject, "time": t, "conc": conc, "dose": dose, "route": route}
    )




def _trapezoid(y: "np.ndarray", x: "np.ndarray") -> float:
    """Numpy-version-agnostic trapezoid integration."""
    import numpy as _np
    fn = getattr(_np, "trapezoid", None) or getattr(_np, "trapz")
    return float(fn(y, x))


# ---------------------------------------------------------------------------
# IV bolus: recover CL and Vz from NCA
# ---------------------------------------------------------------------------

class TestNCAIVBolus:
    """Verify that NCA on a synthetic IV bolus dataset recovers true CL and Vz.

    True parameter values are inserted via c_1cmt_iv_bolus() (analytically exact).
    Recovery tolerance is <=2% for CL and Vz (tight grid, dense timepoints).
    """

    @pytest.fixture(scope="class")
    def result(self):
        CL, Vz, dose = 5.0, 20.0, 100.0
        df = _make_iv_bolus_df(CL, Vz, dose, route="iv_bolus")
        study = NCAStudy(df, auc_method="linear_up_log_down", blq_method="none")
        summary = study.analyze()
        return summary.results[0], CL, Vz, dose

    def test_cl_recovered_within_2pct(self, result) -> None:
        """NCA CL from IV bolus must match true CL within 2%.

        Reference: AUCinf = D/CL (Gibaldi & Perrier, 2nd ed., p. 2).
        """
        r, CL, Vz, dose = result
        assert r.CL is not None, "CL must not be None for IV route"
        assert within_pct(r.CL, CL, pct=2.0), (
            f"CL={r.CL:.4f} deviates from true CL={CL} by "
            f"{pct_bias(r.CL, CL):.2f}%"
        )

    def test_vz_recovered_within_2pct(self, result) -> None:
        """NCA Vz from IV bolus must match true Vz within 2%.

        Reference: Vz = D / (AUCinf * lambda_z) (Gibaldi & Perrier, 2nd ed., p. 2).
        """
        r, CL, Vz, dose = result
        assert r.Vz is not None, "Vz must not be None for IV route"
        assert within_pct(r.Vz, Vz, pct=2.0), (
            f"Vz={r.Vz:.4f} deviates from true Vz={Vz} by "
            f"{pct_bias(r.Vz, Vz):.2f}%"
        )

    def test_half_life_recovered_within_2pct(self, result) -> None:
        """NCA t1/2 must match true t1/2 = ln(2) * Vz/CL within 2%.

        Reference: t1/2 = ln(2)/k, k = CL/Vz (Gibaldi & Perrier, 2nd ed., p. 2).
        """
        r, CL, Vz, dose = result
        true_t_half = math.log(2) / (CL / Vz)
        assert r.half_life is not None, "half_life must not be None"
        assert within_pct(r.half_life, true_t_half, pct=2.0), (
            f"half_life={r.half_life:.4f} deviates from true {true_t_half:.4f} by "
            f"{pct_bias(r.half_life, true_t_half):.2f}%"
        )

    def test_aucinf_equals_dose_over_cl(self, result) -> None:
        """AUCinf_obs must equal D/CL within 2% for a dense grid.

        Reference: AUCinf = D/CL (exact identity for linear PK, Rowland & Tozer, 4th ed.,
        p. 80, Eq. 3-1).
        """
        r, CL, Vz, dose = result
        true_aucinf = dose / CL
        assert r.AUCinf_obs is not None, "AUCinf_obs must not be None"
        assert within_pct(r.AUCinf_obs, true_aucinf, pct=2.0), (
            f"AUCinf_obs={r.AUCinf_obs:.4f} deviates from D/CL={true_aucinf:.4f} by "
            f"{pct_bias(r.AUCinf_obs, true_aucinf):.2f}%"
        )

    def test_cmax_equals_dose_over_vz(self, result) -> None:
        """Cmax from IV bolus at t=0 equals D/Vz.

        Reference: C(0) = D/Vz (Gibaldi & Perrier, 2nd ed., Eq. 1-2, p. 2).
        The first time point is t=0 so Cmax is observed exactly.
        """
        r, CL, Vz, dose = result
        true_c0 = dose / Vz
        assert within_pct(r.Cmax, true_c0, pct=0.01), (
            f"Cmax={r.Cmax:.4f} deviates from D/Vz={true_c0:.4f}"
        )


# ---------------------------------------------------------------------------
# Oral route: CL_F from AUCinf
# ---------------------------------------------------------------------------

class TestNCAOral:
    """Verify NCA on a synthetic oral dataset recovers CL_F = CL/F.

    Simulated with c_1cmt_oral(). Since we set F=1 in the simulation
    (i.e. CL_F == CL), recovered CL_F must match within 5% on a 24 h grid.
    """

    @pytest.fixture(scope="class")
    def result(self):
        from openpkflow.sim.methods import c_1cmt_oral
        import pandas as pd

        CL_F, Vz_F, ka, dose = 4.0, 24.0, 0.8, 200.0
        t = np.array([0.0, 0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0, 18.0, 24.0])
        conc = c_1cmt_oral(t, dose=dose, CL_F=CL_F, Vz_F=Vz_F, ka=ka)
        df = pd.DataFrame(
            {"subject": "SIM_ORAL", "time": t, "conc": conc, "dose": dose, "route": "oral"}
        )
        study = NCAStudy(df, auc_method="linear_up_log_down", blq_method="none")
        return study.analyze().results[0], CL_F, Vz_F, dose

    def test_clf_recovered_within_5pct(self, result) -> None:
        """NCA CL_F must equal simulation CL_F within 5% (25-h grid, last point > 90% AUCinf).

        Reference: CL_F = D/AUCinf (Gibaldi & Perrier, 2nd ed., p. 16).
        """
        r, CL_F, Vz_F, dose = result
        assert r.CL_F is not None
        assert within_pct(r.CL_F, CL_F, pct=5.0), (
            f"CL_F={r.CL_F:.4f} deviates from true {CL_F} by "
            f"{pct_bias(r.CL_F, CL_F):.2f}%"
        )

    def test_route_is_oral(self, result) -> None:
        r, *_ = result
        assert r.route == "oral"
        assert r.CL is None
        assert r.Vz is None


# ---------------------------------------------------------------------------
# pct_bias and within_pct utility tests
# ---------------------------------------------------------------------------

class TestValidationUtilities:
    def test_pct_bias_exact_match(self) -> None:
        assert pct_bias(100.0, 100.0) == pytest.approx(0.0)

    def test_pct_bias_10pct_high(self) -> None:
        assert pct_bias(110.0, 100.0) == pytest.approx(10.0, rel=1e-6)

    def test_within_pct_true(self) -> None:
        assert within_pct(102.0, 100.0, pct=5.0)

    def test_within_pct_false(self) -> None:
        assert not within_pct(106.0, 100.0, pct=5.0)
