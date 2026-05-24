"""Population PK model definition -- structural + statistical model.

Supports 1- and 2-compartment models and diagonal and full Omega matrices.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .omega import (
    log_cholesky_to_omega,
    make_param_labels_omega,
    n_omega_params,
    omega_to_log_cholesky,
)

# (route, n_cmt) -> list of PK parameter names
_ROUTE_N_CMT_PARAMS: dict[tuple[str, int], list[str]] = {
    ("oral", 1): ["CL_F", "Vz_F", "ka"],
    ("oral", 2): ["CL_F", "V1_F", "Q", "V2", "ka"],
    ("iv_bolus", 1): ["CL", "Vz"],
    ("iv_bolus", 2): ["CL", "V1", "Q", "V2"],
}


def _get_param_names(route: str, n_cmt: int) -> list[str]:
    key = (route, n_cmt)
    if key not in _ROUTE_N_CMT_PARAMS:
        raise ValueError(
            f"Unsupported (route={route}, n_cmt={n_cmt}). "
            f"Expected one of: {sorted(_ROUTE_N_CMT_PARAMS.keys())}"
        )
    return list(_ROUTE_N_CMT_PARAMS[key])


@dataclass(frozen=True)
class PopPKModel:
    """Structural + statistical model for population PK estimation.

    Parameters
    ----------
    route : str
        ``"oral"`` or ``"iv_bolus"``.
    fixed_effects : dict[str, float]
        Initial population typical values on natural scale, e.g.
        ``{"CL_F": 5.0, "V1_F": 10.0, "Q": 5.0, "V2": 30.0, "ka": 1.0}`` for 2-cmt oral.
    omega_diag : dict[str, float]
        Initial diagonal Omega values (variance on log scale), e.g.
        ``{"CL_F": 0.1, "Vz_F": 0.1, "ka": 0.1}``.
    sigma_prop : float
        Proportional residual error (CV fraction).
    sigma_add : float
        Additive residual error (same units as concentration).
    error_model : str
        ``"combined"``, ``"proportional"``, or ``"additive"``.
    n_cmt : int
        Number of compartments (1 or 2).
    omega_type : str
        ``"diagonal"`` or ``"full"`` for block Omega matrix.

    Raises
    ------
    ValueError
        If route/n_cmt combination is unsupported, fixed_effects keys
        don't match expected params, or sigma values are negative.
    """

    route: str
    fixed_effects: dict[str, float]
    omega_diag: dict[str, float]
    sigma_prop: float = 0.15
    sigma_add: float = 0.0
    error_model: str = "combined"
    n_cmt: int = 1
    omega_type: str = "diagonal"

    def __post_init__(self) -> None:
        if self.route not in ("oral", "iv_bolus"):
            raise ValueError(f"Unsupported route '{self.route}'. Expected 'oral' or 'iv_bolus'.")
        if self.n_cmt not in (1, 2):
            raise ValueError(f"n_cmt must be 1 or 2; got {self.n_cmt}")
        if self.error_model not in ("combined", "proportional", "additive"):
            raise ValueError(
                f"Unsupported error_model '{self.error_model}'. "
                f"Expected 'combined', 'proportional', or 'additive'"
            )
        if self.omega_type not in ("diagonal", "full"):
            raise ValueError(
                f"Unsupported omega_type '{self.omega_type}'. Expected 'diagonal' or 'full'."
            )

        expected = set(_get_param_names(self.route, self.n_cmt))
        actual = set(self.fixed_effects.keys())
        if actual != expected:
            raise ValueError(
                f"fixed_effects keys must be {sorted(expected)} "
                f"for (route={self.route}, n_cmt={self.n_cmt}); got {sorted(actual)}"
            )
        for k in expected:
            if self.fixed_effects[k] <= 0:
                raise ValueError(f"fixed_effects['{k}'] must be > 0")

        if set(self.omega_diag.keys()) != expected:
            raise ValueError(
                f"omega_diag keys must be {sorted(expected)} "
                f"for (route={self.route}, n_cmt={self.n_cmt}); "
                f"got {sorted(self.omega_diag.keys())}"
            )
        for k in expected:
            if self.omega_diag[k] <= 0:
                raise ValueError(f"omega_diag['{k}'] must be > 0")

        if self.sigma_prop < 0:
            raise ValueError("sigma_prop must be >= 0")
        if self.sigma_add < 0:
            raise ValueError("sigma_add must be >= 0")

    @property
    def param_names(self) -> list[str]:
        """Ordered list of parameter names for this model."""
        return _get_param_names(self.route, self.n_cmt)

    @property
    def n_params(self) -> int:
        """Number of fixed-effect PK parameters."""
        return len(self.param_names)

    @property
    def n_omega_total(self) -> int:
        """Total number of omega parameters (diagonal + off-diagonal)."""
        return n_omega_params(self.n_params, self.omega_type)

    @property
    def n_diag_omega(self) -> int:
        """Number of diagonal omega parameters (= n_params)."""
        return self.n_params

    @property
    def n_betas(self) -> int:
        """Number of covariate beta parameters (always 0 in v2.3.0+)."""
        return 0

    @property
    def n_theta(self) -> int:
        """Total length of the flat theta optimization vector."""
        return self.n_params + self.n_omega_total + 2

    @property
    def param_labels(self) -> list[str]:
        """Human-readable labels for every element of the theta vector."""
        labels: list[str] = []
        for n in self.param_names:
            labels.append(f"log_{n}")
        labels.extend(make_param_labels_omega(self.param_names, self.omega_type))
        labels.append("log_sigma_prop")
        labels.append("sigma_add")
        return labels

    def to_theta(self) -> np.ndarray:
        """Pack the full parameter vector for optimization.

        Order: [log(theta_pop)... | log_cholesky_diag... | cholesky_off_diag...
                | log(sigma_prop), sigma_add]

        Returns
        -------
        np.ndarray
            Flat parameter vector of length ``n_theta``.
        """
        names = self.param_names
        theta_pop_log = np.array([np.log(self.fixed_effects[k]) for k in names], dtype=float)

        L_diag = np.array([np.log(self.omega_diag[k]) for k in names], dtype=float)

        omega = np.diag(np.exp(L_diag))
        _, L_off = omega_to_log_cholesky(omega)

        if self.omega_type == "diagonal" or L_off is None:
            omega_vec = L_diag
        else:
            omega_vec = np.concatenate([L_diag, L_off])

        return np.concatenate(
            [
                theta_pop_log,
                omega_vec,
                [np.log(self.sigma_prop)],
                [self.sigma_add],
            ]
        )

    @classmethod
    def from_theta(
        cls,
        theta: np.ndarray,
        route: str,
        *,
        n_cmt: int = 1,
        omega_type: str = "diagonal",
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
            Number of compartments.
        omega_type : str
            ``"diagonal"`` or ``"full"``.
        error_model : str
            Error model type.

        Returns
        -------
        PopPKModel
        """
        names = _get_param_names(route, n_cmt)
        n_pk = len(names)
        n_om = n_omega_params(n_pk, omega_type)

        theta_pop_log = theta[:n_pk]
        omega_vec = theta[n_pk : n_pk + n_om]
        sigma_prop = float(np.exp(theta[-2]))
        sigma_add = float(theta[-1])

        L_diag = omega_vec[:n_pk]
        L_off = omega_vec[n_pk:] if omega_type == "full" and len(omega_vec) > n_pk else None
        Omega = log_cholesky_to_omega(L_diag, L_off)

        fixed_effects = {k: float(np.exp(v)) for k, v in zip(names, theta_pop_log, strict=False)}
        omega_diag = {k: float(Omega[i, i]) for i, k in enumerate(names)}

        return cls(
            route=route,
            fixed_effects=fixed_effects,
            omega_diag=omega_diag,
            sigma_prop=sigma_prop,
            sigma_add=sigma_add,
            error_model=error_model,
            n_cmt=n_cmt,
            omega_type=omega_type,
        )

    def get_bounds(self) -> list[tuple[float, float | None]]:
        """Return L-BFGS-B bounds for the theta vector.

        Log-scale parameters get wide physiological bounds;
        off-diagonal Cholesky elements are unbounded;
        sigma_add is bounded [0, inf).

        Returns
        -------
        list of tuple
            ``[(lo, hi), ...]`` pairs. hi may be None for unbounded.
        """
        n_pk = self.n_params
        n_om = self.n_omega_total

        bounds: list[tuple[float, float | None]] = []
        bounds.extend([(-6.0, 6.0)] * n_pk)
        bounds.extend([(-10.0, 2.0)] * n_pk)
        if n_om > n_pk:
            off_bounds: list[tuple[float, float | None]] = [(float("-inf"), float("inf"))] * (
                n_om - n_pk
            )
            bounds.extend(off_bounds)
        bounds.append((-5.0, 1.0))
        bounds.append((0.0, None))
        return bounds

    def get_initial_theta(self) -> np.ndarray:
        """Return the theta vector from current model values."""
        return self.to_theta()

    def unpack_omega_matrix(self) -> np.ndarray:
        """Build the current Omega matrix from omega_diag + omega_type.

        Returns
        -------
        np.ndarray
            ``(n_params, n_params)`` Omega matrix.
        """
        names = self.param_names
        L_diag = np.array([np.log(self.omega_diag[k]) for k in names], dtype=float)
        if self.omega_type == "full":
            return np.diag(np.exp(L_diag))
        return np.diag(np.exp(L_diag))
