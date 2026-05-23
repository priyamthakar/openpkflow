"""Population PK model definition — structural + statistical model."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

_ROUTE_REQUIRED_KEYS: dict[str, list[str]] = {
    "oral": ["CL_F", "Vz_F", "ka"],
    "iv_bolus": ["CL", "Vz"],
}

_ROUTE_N_PARAMS: dict[str, int] = {
    "oral": 3,
    "iv_bolus": 2,
}


@dataclass(frozen=True)
class PopPKModel:
    """Structural + statistical model for population PK estimation.

    Parameters
    ----------
    route : str
        ``"oral"`` or ``"iv_bolus"``.
    fixed_effects : dict[str, float]
        Initial population typical values on natural scale, e.g.
        ``{"CL_F": 5.0, "Vz_F": 50.0, "ka": 1.0}`` for oral.
    omega_diag : dict[str, float]
        Initial diagonal Omega values (variance on log scale), e.g.
        ``{"CL_F": 0.1, "Vz_F": 0.1, "ka": 0.1}``.
    sigma_prop : float
        Proportional residual error (CV fraction).
    sigma_add : float
        Additive residual error (same units as concentration).
    error_model : str
        ``"combined"``, ``"proportional"``, or ``"additive"``.

    Raises
    ------
    ValueError
        If route is unsupported, fixed_effects keys don't match route
        expectations, or sigma values are negative.
    """

    route: str
    fixed_effects: dict[str, float]
    omega_diag: dict[str, float]
    sigma_prop: float = 0.15
    sigma_add: float = 0.0
    error_model: str = "combined"
    n_cmt: int = 1

    def __post_init__(self) -> None:
        if self.route not in _ROUTE_REQUIRED_KEYS:
            raise ValueError(
                f"Unsupported route '{self.route}'. Expected one of: {sorted(_ROUTE_REQUIRED_KEYS)}"
            )
        if self.n_cmt != 1:
            raise ValueError(f"v2.1.0 supports n_cmt=1 only; got {self.n_cmt}")
        if self.error_model not in ("combined", "proportional", "additive"):
            raise ValueError(
                f"Unsupported error_model '{self.error_model}'. "
                f"Expected 'combined', 'proportional', or 'additive'"
            )

        required = _ROUTE_REQUIRED_KEYS[self.route]
        actual = set(self.fixed_effects.keys())
        expected = set(required)
        if actual != expected:
            raise ValueError(
                f"fixed_effects keys must be {sorted(expected)} for route '{self.route}'; "
                f"got {sorted(actual)}"
            )
        for k in required:
            if self.fixed_effects[k] <= 0:
                raise ValueError(f"fixed_effects['{k}'] must be > 0")

        if set(self.omega_diag.keys()) != expected:
            raise ValueError(
                f"omega_diag keys must be {sorted(expected)} for route '{self.route}'; "
                f"got {sorted(self.omega_diag.keys())}"
            )
        for k in required:
            if self.omega_diag[k] <= 0:
                raise ValueError(f"omega_diag['{k}'] must be > 0")

        if self.sigma_prop < 0:
            raise ValueError("sigma_prop must be >= 0")
        if self.sigma_add < 0:
            raise ValueError("sigma_add must be >= 0")

    @property
    def param_names(self) -> list[str]:
        """Ordered list of parameter names for this model."""
        return list(_ROUTE_REQUIRED_KEYS[self.route])

    @property
    def n_params(self) -> int:
        """Number of fixed-effect parameters."""
        return _ROUTE_N_PARAMS[self.route]

    @property
    def n_omega(self) -> int:
        """Number of diagonal Omega elements (same as n_params)."""
        return self.n_params

    def to_theta(self) -> np.ndarray:
        """Pack the full parameter vector for optimization.

        Order: [log(theta_pop)... , log(omega_diag)..., log(sigma_prop), sigma_add]

        Returns
        -------
        np.ndarray
            Flat parameter vector of length ``n_params + n_omega + 2``.
        """
        names = self.param_names
        theta_pop_log = np.array([np.log(self.fixed_effects[k]) for k in names])
        omega_log = np.array([np.log(self.omega_diag[k]) for k in names])
        theta = np.concatenate(
            [
                theta_pop_log,
                omega_log,
                [np.log(self.sigma_prop)],
                [self.sigma_add],
            ]
        )
        return theta

    @classmethod
    def from_theta(
        cls,
        theta: np.ndarray,
        route: str,
        *,
        n_cmt: int = 1,
        error_model: str = "combined",
    ) -> PopPKModel:
        """Unpack a flat theta vector back to a ``PopPKModel``.

        Parameters
        ----------
        theta : np.ndarray
            Flat parameter vector from :meth:`to_theta`.
        route : str
            ``"oral"`` or ``"iv_bolus"``.
        n_cmt : int
            Number of compartments (v2.1.0: 1 only).
        error_model : str
            Error model type.

        Returns
        -------
        PopPKModel
        """
        names = _ROUTE_REQUIRED_KEYS[route]
        n = len(names)
        theta_pop_log = theta[:n]
        omega_log = theta[n : 2 * n]
        sigma_prop = float(np.exp(theta[-2]))
        sigma_add = float(theta[-1])
        return cls(
            route=route,
            fixed_effects={k: float(np.exp(v)) for k, v in zip(names, theta_pop_log, strict=False)},
            omega_diag={k: float(np.exp(v)) for k, v in zip(names, omega_log, strict=False)},
            sigma_prop=sigma_prop,
            sigma_add=sigma_add,
            error_model=error_model,
            n_cmt=n_cmt,
        )

    def get_bounds(self) -> list[tuple[float, float | None]]:
        """Return L-BFGS-B bounds for the theta vector.

        Log-scale parameters get wide physiological bounds;
        sigma_add is bounded [0, inf).

        Returns
        -------
        list of tuple
            ``[(lo, hi), ...]`` pairs. hi may be None for unbounded.
        """
        n = self.n_params
        bounds: list[tuple[float, float | None]] = []
        # log theta_pop
        bounds.extend([(-6.0, 6.0)] * n)
        # log omega_diag
        bounds.extend([(-10.0, 2.0)] * n)
        # log sigma_prop
        bounds.append((-5.0, 1.0))
        # sigma_add
        bounds.append((0.0, None))
        return bounds

    def get_initial_theta(self) -> np.ndarray:
        """Return the theta vector from current model values."""
        return self.to_theta()
