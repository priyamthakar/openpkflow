"""Dose and DoseRegimen dataclasses for PK simulation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Dose:
    """A single dose administration event.

    Parameters
    ----------
    amount : float
        Dose amount (>= 0).
    time : float
        Time of administration (>= 0).
    route : str
        Route: "iv_bolus", "iv_infusion", or "oral".
    t_inf : float or None
        Infusion duration for iv_infusion; must be > 0. None for other routes.
    """

    amount: float
    time: float
    route: Literal["iv_bolus", "iv_infusion", "oral"]
    t_inf: float | None = None

    def __post_init__(self) -> None:
        if self.amount < 0.0:
            raise ValueError(f"amount must be >= 0 (got {self.amount}).")
        if self.time < 0.0:
            raise ValueError(f"time must be >= 0 (got {self.time}).")
        if self.route == "iv_infusion":
            if self.t_inf is None or self.t_inf <= 0.0:
                raise ValueError("iv_infusion requires t_inf > 0.")
        elif self.t_inf is not None:
            raise ValueError(f"t_inf is only valid for iv_infusion (got route={self.route!r}).")
        if self.route not in ("iv_bolus", "iv_infusion", "oral"):
            raise ValueError(
                f"route must be 'iv_bolus', 'iv_infusion', or 'oral' (got {self.route!r})."
            )


@dataclass(frozen=True)
class DoseRegimen:
    """An ordered sequence of dose events.

    Parameters
    ----------
    doses : tuple[Dose, ...]
        One or more dose events; all must share the same route.
    """

    doses: tuple[Dose, ...]

    def __post_init__(self) -> None:
        if len(self.doses) == 0:
            raise ValueError("DoseRegimen must contain at least one dose.")
        routes = {d.route for d in self.doses}
        if len(routes) > 1:
            raise ValueError(f"All doses must share the same route (got {sorted(routes)}).")

    @property
    def route(self) -> str:
        """Route of administration shared by all doses."""
        return self.doses[0].route

    @property
    def dose_times(self) -> list[float]:
        """List of dose administration times."""
        return [d.time for d in self.doses]

    @property
    def dose_amounts(self) -> list[float]:
        """List of dose amounts."""
        return [d.amount for d in self.doses]

    @classmethod
    def from_repeated(
        cls,
        amount: float,
        route: Literal["iv_bolus", "iv_infusion", "oral"],
        tau: float,
        n_doses: int,
        t_start: float = 0.0,
        t_inf: float | None = None,
    ) -> DoseRegimen:
        """Create a regular repeat-dosing regimen.

        Parameters
        ----------
        amount : float
            Dose amount per administration.
        route : str
            Route of administration.
        tau : float
            Dosing interval (same time units as simulation). Must be > 0.
        n_doses : int
            Total number of doses. Must be >= 1.
        t_start : float, optional
            Time of the first dose, by default 0.0.
        t_inf : float or None, optional
            Infusion duration for iv_infusion doses, by default None.

        Returns
        -------
        DoseRegimen
            Regimen with n_doses equally spaced doses starting at t_start.

        Raises
        ------
        ValueError
            If tau <= 0 or n_doses < 1.
        """
        if tau <= 0.0:
            raise ValueError(f"tau must be > 0 (got {tau}).")
        if n_doses < 1:
            raise ValueError(f"n_doses must be >= 1 (got {n_doses}).")
        doses = tuple(
            Dose(amount=amount, time=t_start + i * tau, route=route, t_inf=t_inf)
            for i in range(n_doses)
        )
        return cls(doses=doses)
