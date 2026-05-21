"""PK simulation orchestration: simulate() entry point."""

from __future__ import annotations

import numpy as np

from openpkflow.sim.dosing import DoseRegimen
from openpkflow.sim.methods import (
    c_1cmt_iv_bolus,
    c_1cmt_iv_infusion,
    c_1cmt_oral,
    c_2cmt_iv_bolus,
    c_2cmt_iv_infusion,
    c_2cmt_oral,
)
from openpkflow.sim.models import OneCompartmentModel, TwoCompartmentModel
from openpkflow.sim.results import SimulationResult


def simulate(
    model: OneCompartmentModel | TwoCompartmentModel,
    regimen: DoseRegimen,
    times: list[float] | np.ndarray,
    *,
    label: str = "",
) -> SimulationResult:
    """Simulate a PK concentration-time profile using analytical equations.

    Parameters
    ----------
    model : OneCompartmentModel or TwoCompartmentModel
        PK model with fixed parameters.
    regimen : DoseRegimen
        Dosing regimen (one or more doses).
    times : array-like
        Absolute simulation time grid (>= 0, strictly increasing).
    label : str, optional
        Descriptive label for the simulation run.

    Returns
    -------
    SimulationResult
        Simulated concentration-time profile with metadata.

    Raises
    ------
    ValueError
        If model.route does not match regimen.route, times are invalid,
        or the model/route combination is not yet implemented.
    TypeError
        If model is not a recognised model type.

    Notes
    -----
    Uses analytical closed-form solutions (not numerical ODE integration).
    Superposition is applied for multiple doses — valid for linear PK only.
    """
    t = np.asarray(times, dtype=float)
    if t.ndim != 1 or len(t) == 0:
        raise ValueError("times must be a non-empty 1-D array.")
    if np.any(t < 0.0):
        raise ValueError("times must all be >= 0.")
    if len(t) > 1 and not np.all(np.diff(t) > 0.0):
        raise ValueError("times must be strictly increasing.")

    if model.route != regimen.route:
        raise ValueError(
            f"model.route={model.route!r} does not match regimen.route={regimen.route!r}."
        )

    warnings: list[str] = []

    if t[0] < regimen.dose_times[0]:
        warnings.append(
            f"Simulation starts at t={t[0]:.4g} before first dose at "
            f"t={regimen.dose_times[0]:.4g}. Pre-dose concentrations are 0."
        )

    C_total = np.zeros_like(t)

    for dose_obj in regimen.doses:
        t_rel = t - dose_obj.time
        mask = t_rel >= 0.0
        if not mask.any():
            continue

        amount = dose_obj.amount
        tr = t_rel[mask]

        if isinstance(model, OneCompartmentModel):
            if model.route == "iv_bolus":
                assert model.CL is not None and model.Vz is not None
                C_total[mask] += c_1cmt_iv_bolus(tr, amount, CL=model.CL, Vz=model.Vz)

            elif model.route == "iv_infusion":
                assert model.CL is not None and model.Vz is not None
                if dose_obj.t_inf is None:
                    raise ValueError(
                        f"Dose at t={dose_obj.time} has no t_inf; "
                        "iv_infusion doses require t_inf."
                    )
                C_total[mask] += c_1cmt_iv_infusion(
                    tr, amount, CL=model.CL, Vz=model.Vz, t_inf=dose_obj.t_inf
                )

            elif model.route == "oral":
                assert model.CL_F is not None and model.Vz_F is not None and model.ka is not None
                C_total[mask] += c_1cmt_oral(
                    tr, amount, CL_F=model.CL_F, Vz_F=model.Vz_F, ka=model.ka
                )

        elif isinstance(model, TwoCompartmentModel):
            if model.route == "iv_bolus":
                assert model.CL is not None and model.V1 is not None
                C_total[mask] += c_2cmt_iv_bolus(
                    tr, amount, CL=model.CL, V1=model.V1, Q=model.Q, V2=model.V2
                )

            elif model.route == "oral":
                assert model.CL_F is not None and model.V1_F is not None and model.ka is not None
                C_total[mask] += c_2cmt_oral(
                    tr, amount,
                    CL_F=model.CL_F, V1_F=model.V1_F,
                    Q=model.Q, V2=model.V2, ka=model.ka,
                )

            elif model.route == "iv_infusion":
                assert model.CL is not None and model.V1 is not None
                if dose_obj.t_inf is None:
                    raise ValueError(
                        f"Dose at t={dose_obj.time} has no t_inf; "
                        "iv_infusion doses require t_inf."
                    )
                C_total[mask] += c_2cmt_iv_infusion(
                    tr, amount,
                    CL=model.CL, V1=model.V1, Q=model.Q, V2=model.V2,
                    t_inf=dose_obj.t_inf,
                )

            else:
                raise ValueError(
                    f"TwoCompartmentModel does not support route={model.route!r}."
                )

        else:
            raise TypeError(
                f"model must be OneCompartmentModel or TwoCompartmentModel "
                f"(got {type(model).__name__})."
            )

    return SimulationResult(
        times=t.tolist(),
        concs=C_total.tolist(),
        model=model,
        regimen=regimen,
        label=label,
        warnings=warnings,
    )
