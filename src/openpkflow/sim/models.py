"""PK model parameter containers: OneCompartmentModel and TwoCompartmentModel."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class OneCompartmentModel:
    """1-compartment open PK model.

    Parameters
    ----------
    route : str
        Route of administration: "iv_bolus", "iv_infusion", or "oral".
    CL : float or None
        Systemic clearance (IV routes only). Must be > 0.
    Vz : float or None
        Volume of distribution at terminal phase (IV routes only). Must be > 0.
    CL_F : float or None
        Apparent oral clearance (CL/F) for oral route. Must be > 0.
    Vz_F : float or None
        Apparent volume of distribution (Vz/F) for oral route. Must be > 0.
    ka : float or None
        First-order absorption rate constant (oral route only). Must be > 0.

    Notes
    -----
    IV routes use absolute parameters CL and Vz.
    Oral route uses apparent parameters CL_F and Vz_F, consistent with NCA output.
    """

    route: Literal["iv_bolus", "iv_infusion", "oral"]
    CL: float | None = None
    Vz: float | None = None
    CL_F: float | None = None
    Vz_F: float | None = None
    ka: float | None = None

    def __post_init__(self) -> None:
        if self.route in ("iv_bolus", "iv_infusion"):
            if self.CL is None or self.Vz is None:
                raise ValueError(f"route={self.route!r} requires CL and Vz.")
            if self.CL <= 0.0 or self.Vz <= 0.0:
                raise ValueError("CL and Vz must be > 0.")
            if any(v is not None for v in (self.CL_F, self.Vz_F, self.ka)):
                raise ValueError(
                    f"route={self.route!r} does not accept CL_F, Vz_F, or ka."
                )
        elif self.route == "oral":
            if self.CL_F is None or self.Vz_F is None or self.ka is None:
                raise ValueError("route='oral' requires CL_F, Vz_F, and ka.")
            if self.CL_F <= 0.0 or self.Vz_F <= 0.0 or self.ka <= 0.0:
                raise ValueError("CL_F, Vz_F, and ka must be > 0.")
            if any(v is not None for v in (self.CL, self.Vz)):
                raise ValueError("route='oral' does not accept CL or Vz.")
        else:
            raise ValueError(
                f"Unknown route {self.route!r}. Use 'iv_bolus', 'iv_infusion', or 'oral'."
            )

    @property
    def half_life(self) -> float:
        """Terminal half-life (ln2 / k) in the same time units as the model."""
        if self.route in ("iv_bolus", "iv_infusion"):
            assert self.CL is not None and self.Vz is not None
            return math.log(2.0) / (self.CL / self.Vz)
        assert self.CL_F is not None and self.Vz_F is not None
        return math.log(2.0) / (self.CL_F / self.Vz_F)

    def param_dict(self) -> dict[str, float | str]:
        """Return model parameters as a flat dict (for reporting)."""
        d: dict[str, float | str] = {"route": self.route, "half_life": self.half_life}
        if self.route in ("iv_bolus", "iv_infusion"):
            d["CL"] = self.CL  # type: ignore[assignment]
            d["Vz"] = self.Vz  # type: ignore[assignment]
        else:
            d["CL_F"] = self.CL_F  # type: ignore[assignment]
            d["Vz_F"] = self.Vz_F  # type: ignore[assignment]
            d["ka"] = self.ka  # type: ignore[assignment]
        return d


@dataclass(frozen=True)
class TwoCompartmentModel:
    """2-compartment open PK model.

    Parameters
    ----------
    route : str
        Route of administration: "iv_bolus" or "oral".
        IV infusion for 2-cmt is planned for a future release.
    Q : float
        Intercompartmental clearance. Must be > 0.
    V2 : float
        Peripheral compartment volume. Must be > 0.
    CL : float or None
        Systemic clearance from central (IV routes). Must be > 0.
    V1 : float or None
        Central compartment volume (IV routes). Must be > 0.
    CL_F : float or None
        Apparent oral clearance CL/F (oral route). Must be > 0.
    V1_F : float or None
        Apparent central volume V1/F (oral route). Must be > 0.
    ka : float or None
        First-order absorption rate constant (oral route). Must be > 0.

    Notes
    -----
    Q and V2 are not confounded by bioavailability F.
    IV routes use CL and V1; oral uses CL_F and V1_F.
    """

    route: Literal["iv_bolus", "oral"]
    Q: float
    V2: float
    CL: float | None = None
    V1: float | None = None
    CL_F: float | None = None
    V1_F: float | None = None
    ka: float | None = None

    def __post_init__(self) -> None:
        if self.Q <= 0.0:
            raise ValueError(f"Q must be > 0 (got {self.Q}).")
        if self.V2 <= 0.0:
            raise ValueError(f"V2 must be > 0 (got {self.V2}).")
        if self.route == "iv_bolus":
            if self.CL is None or self.V1 is None:
                raise ValueError("route='iv_bolus' requires CL and V1.")
            if self.CL <= 0.0 or self.V1 <= 0.0:
                raise ValueError("CL and V1 must be > 0.")
            if any(v is not None for v in (self.CL_F, self.V1_F, self.ka)):
                raise ValueError("route='iv_bolus' does not accept CL_F, V1_F, or ka.")
        elif self.route == "oral":
            if self.CL_F is None or self.V1_F is None or self.ka is None:
                raise ValueError("route='oral' requires CL_F, V1_F, and ka.")
            if self.CL_F <= 0.0 or self.V1_F <= 0.0 or self.ka <= 0.0:
                raise ValueError("CL_F, V1_F, and ka must be > 0.")
            if any(v is not None for v in (self.CL, self.V1)):
                raise ValueError("route='oral' does not accept CL or V1.")
        else:
            raise ValueError(
                f"Unknown route {self.route!r}. "
                "TwoCompartmentModel supports 'iv_bolus' and 'oral'. "
                "IV infusion for 2-cmt is planned for a future release."
            )

    def param_dict(self) -> dict[str, float | str]:
        """Return model parameters as a flat dict (for reporting)."""
        d: dict[str, float | str] = {"route": self.route, "Q": self.Q, "V2": self.V2}
        if self.route == "iv_bolus":
            d["CL"] = self.CL  # type: ignore[assignment]
            d["V1"] = self.V1  # type: ignore[assignment]
        else:
            d["CL_F"] = self.CL_F  # type: ignore[assignment]
            d["V1_F"] = self.V1_F  # type: ignore[assignment]
            d["ka"] = self.ka  # type: ignore[assignment]
        return d
