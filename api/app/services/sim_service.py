"""Sim adapter: HTTP payload -> simulate() -> serializable dict."""

from __future__ import annotations

from typing import Any

import numpy as np

from app.schemas.sim import SimRequest
from openpkflow.sim.dosing import DoseRegimen
from openpkflow.sim.models import OneCompartmentModel, TwoCompartmentModel
from openpkflow.sim.simulate import simulate

_DISCLAIMER = (
    "This report was generated using OpenPKFlow (open-source). Final regulatory "
    "interpretation should be reviewed by qualified formulation, pharmacokinetic, "
    "and regulatory experts."
)


def _build_model(req: SimRequest) -> OneCompartmentModel | TwoCompartmentModel:
    p = req.params
    route = req.route
    if req.model_type == "1cmt":
        if route in ("iv_bolus", "iv_infusion"):
            return OneCompartmentModel(route=route, CL=p.CL, Vz=p.Vz)
        return OneCompartmentModel(route=route, CL_F=p.CL_F, Vz_F=p.Vz_F, ka=p.ka)
    # 2cmt — Q and V2 always required
    if route in ("iv_bolus", "iv_infusion"):
        return TwoCompartmentModel(route=route, CL=p.CL, V1=p.V1, Q=p.Q, V2=p.V2)
    return TwoCompartmentModel(route=route, CL_F=p.CL_F, V1_F=p.V1_F, ka=p.ka, Q=p.Q, V2=p.V2)


def run_sim(req: SimRequest) -> dict[str, Any]:
    model = _build_model(req)
    regimen = DoseRegimen.from_repeated(
        amount=req.regimen.amount,
        route=req.route,
        tau=req.regimen.tau,
        n_doses=req.regimen.n_doses,
        t_start=req.regimen.t_start,
        t_inf=req.regimen.t_inf,
    )
    times = np.linspace(req.times.start, req.times.stop, req.times.n)
    result = simulate(model, regimen, times)

    return {
        "times": result.times,
        "concs": result.concs,
        "dose_times": regimen.dose_times,
        "Cmax": result.Cmax,
        "Tmax": result.Tmax,
        "Cmin": float(min(result.concs)),
        "Clast": float(result.concs[-1]),
        "warnings": result.warnings,
        "disclaimer": _DISCLAIMER,
    }
