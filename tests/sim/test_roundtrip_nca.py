"""Round-trip NCA test: simulate a clean PK profile, then recover parameters via NCAStudy.

This cross-validates the sim and nca modules together. If both are correct, the
recovered NCA parameters should match the simulation model parameters within
rounding tolerance.

Validates against Rowland & Tozer, Clinical Pharmacokinetics 4th ed. (2011),
Chapter 3 (NCA) and Chapter 2 (compartmental models).
"""

from __future__ import annotations

import math

import numpy as np

from openpkflow.nca.study import NCAStudy
from openpkflow.sim.dosing import Dose, DoseRegimen
from openpkflow.sim.models import OneCompartmentModel
from openpkflow.sim.simulate import simulate


def _simulate_to_nca_df(model: OneCompartmentModel, dose: float, route: str) -> object:
    """Simulate a clean single-dose profile and return as NCA-compatible DataFrame."""
    import pandas as pd

    regimen = DoseRegimen((Dose(dose, 0.0, route),))  # type: ignore[arg-type]
    t = np.linspace(0.0, 72.0, 500)
    result = simulate(model, regimen, t)

    # NCA loader expects: subject, time, conc, dose, route
    df = pd.DataFrame(
        {
            "subject": "S1",
            "time": result.times,
            "conc": result.concs,
            "dose": dose,
            "route": route,
        }
    )
    return df


class TestRoundTripNCA:
    """Round-trip: simulate -> NCA -> compare recovered vs model parameters."""

    def test_1cmt_iv_bolus_cl_vz_roundtrip(self) -> None:
        """1-cmt IV bolus: recovered CL and Vz match model parameters within 2%.

        Reference: Rowland & Tozer, Clinical Pharmacokinetics 4th ed. (2011), pp. 42-48.
        """
        CL, Vz, dose = 5.0, 30.0, 300.0
        model = OneCompartmentModel(route="iv_bolus", CL=CL, Vz=Vz)
        df = _simulate_to_nca_df(model, dose, "iv_bolus")

        study = NCAStudy(df, auc_method="linear_up_log_down", blq_method="set_zero")
        summary = study.analyze()
        r = summary.results[0]

        # CL = dose / AUCinf
        assert r.AUCinf_obs is not None
        recovered_CL = dose / r.AUCinf_obs
        assert math.isclose(recovered_CL, CL, rel_tol=0.02), (
            f"Recovered CL={recovered_CL:.4g}, expected {CL}"
        )

        # Vz = dose / (AUCinf * lambda_z)
        assert r.lambda_z is not None and r.AUCinf_obs is not None
        recovered_Vz = dose / (r.AUCinf_obs * r.lambda_z)
        assert math.isclose(recovered_Vz, Vz, rel_tol=0.02), (
            f"Recovered Vz={recovered_Vz:.4g}, expected {Vz}"
        )

    def test_1cmt_oral_clfz_vzfz_roundtrip(self) -> None:
        """1-cmt oral: recovered CL_F and Vz_F match model parameters within 2%.

        Reference: Rowland & Tozer, Clinical Pharmacokinetics 4th ed. (2011), pp. 55-62.
        """
        CL_F, Vz_F, ka, dose = 8.0, 40.0, 1.2, 400.0
        model = OneCompartmentModel(route="oral", CL_F=CL_F, Vz_F=Vz_F, ka=ka)
        df = _simulate_to_nca_df(model, dose, "oral")

        study = NCAStudy(df, auc_method="linear_up_log_down", blq_method="set_zero")
        summary = study.analyze()
        r = summary.results[0]

        assert r.AUCinf_obs is not None
        assert r.CL_F is not None
        assert r.Vz_F is not None

        assert math.isclose(r.CL_F, CL_F, rel_tol=0.02), (
            f"Recovered CL_F={r.CL_F:.4g}, expected {CL_F}"
        )
        assert math.isclose(r.Vz_F, Vz_F, rel_tol=0.02), (
            f"Recovered Vz_F={r.Vz_F:.4g}, expected {Vz_F}"
        )

    def test_1cmt_iv_bolus_half_life_roundtrip(self) -> None:
        """Recovered half-life matches model half-life within 1%.

        Reference: Rowland & Tozer, Clinical Pharmacokinetics 4th ed. (2011), p. 43.
        """
        CL, Vz, dose = 3.0, 25.0, 250.0
        model = OneCompartmentModel(route="iv_bolus", CL=CL, Vz=Vz)
        df = _simulate_to_nca_df(model, dose, "iv_bolus")

        study = NCAStudy(df, auc_method="linear_up_log_down", blq_method="set_zero")
        summary = study.analyze()
        r = summary.results[0]

        assert r.half_life is not None
        assert math.isclose(r.half_life, model.half_life, rel_tol=0.01), (
            f"Recovered t1/2={r.half_life:.4g}, expected {model.half_life:.4g}"
        )
