"""Log-Cholesky parameterization of the Omega (between-subject variability) matrix.

Ensures positive-definiteness during unconstrained optimization.
For diagonal Omega, this reduces to log-transformed diagonal elements
(matching v2.1.0 behavior).
"""

from __future__ import annotations

import numpy as np


def n_omega_params(n_pk: int, omega_type: str) -> int:
    """Number of omega parameters for a given PK dimension and type.

    Parameters
    ----------
    n_pk : int
        Number of PK parameters (2 for 1-cmt IV, 3 for 1-cmt oral, etc.).
    omega_type : str
        ``"diagonal"`` or ``"full"``.

    Returns
    -------
    int
        Parameter count.
    """
    if omega_type == "diagonal":
        return n_pk
    elif omega_type == "full":
        return n_pk * (n_pk + 1) // 2
    raise ValueError(f"Unknown omega_type: {omega_type}")


def log_cholesky_to_omega(
    L_diag: np.ndarray,
    L_off: np.ndarray | None = None,
) -> np.ndarray:
    """Build a positive-definite Omega matrix from Log-Cholesky parameters.

    Omega = L @ L.T where L is lower-triangular:
      L[i,i] = exp(L_diag[i])
      L[i,j] = L_off[idx] for i > j

    For diagonal Omega (L_off is None), Omega = diag(exp(L_diag)).

    Parameters
    ----------
    L_diag : np.ndarray
        Log-diagonal elements of Cholesky factor L (n_pk,).
    L_off : np.ndarray | None
        Off-diagonal elements of L, in column-major lower-triangular order.
        Shape ``(n_pk*(n_pk-1)//2,)``. If None, returns diagonal Omega.

    Returns
    -------
    np.ndarray
        ``(n_pk, n_pk)`` positive-definite Omega matrix.
    """
    n = len(L_diag)
    if L_off is None:
        return np.diag(np.exp(L_diag))

    L = np.zeros((n, n), dtype=float)
    np.fill_diagonal(L, np.exp(L_diag))
    idx = 0
    for col in range(n):
        for row in range(col + 1, n):
            L[row, col] = L_off[idx]
            idx += 1

    return L @ L.T


def omega_to_log_cholesky(
    Omega: np.ndarray,
) -> tuple[np.ndarray, np.ndarray | None]:
    """Decompose an Omega matrix into Log-Cholesky parameters.

    Parameters
    ----------
    Omega : np.ndarray
        ``(n_pk, n_pk)`` positive-definite matrix.

    Returns
    -------
    tuple
        ``(L_diag, L_off)`` where L_diag has shape ``(n_pk,)`` and L_off
        has shape ``(n_pk*(n_pk-1)//2,)``. L_off is None when Omega is diagonal.

    Raises
    ------
    np.linalg.LinAlgError
        If Omega is not positive-definite.
    """
    L = np.linalg.cholesky(Omega)
    n = L.shape[0]
    L_diag = np.log(np.maximum(np.diag(L), 1e-300))

    off_diag_count = n * (n - 1) // 2
    if off_diag_count == 0:
        return L_diag, None

    L_off = np.zeros(off_diag_count, dtype=float)

    if np.allclose(L, np.diag(np.diag(L))):
        return L_diag, L_off

    idx = 0
    for col in range(n):
        for row in range(col + 1, n):
            L_off[idx] = L[row, col]
            idx += 1

    return L_diag, L_off


def make_param_labels_omega(
    param_names: list[str],
    omega_type: str,
) -> list[str]:
    """Generate parameter labels for omega section of theta vector.

    Parameters
    ----------
    param_names : list[str]
        PK parameter names (e.g. ``["CL_F", "Vz_F", "ka"]``).
    omega_type : str
        ``"diagonal"`` or ``"full"``.

    Returns
    -------
    list[str]
        Parameter labels.
    """
    labels: list[str] = []
    for name in param_names:
        labels.append(f"log_cholesky_{name}")

    if omega_type == "full":
        n_params = len(param_names)
        for col in range(n_params):
            for row in range(col + 1, n_params):
                labels.append(f"cholesky_{param_names[row]}_{param_names[col]}")

    return labels


def get_omega_off_diagonal_names(
    param_names: list[str],
) -> list[str]:
    """Return display names for Omega off-diagonal covariance terms.

    Parameters
    ----------
    param_names : list[str]
        PK parameter names.

    Returns
    -------
    list[str]
        Names like ``["CL_Vz", "CL_ka", "Vz_ka"]``.
    """
    n = len(param_names)
    names: list[str] = []
    for col in range(n):
        for row in range(col + 1, n):
            names.append(f"{param_names[row]}_{param_names[col]}")
    return names


def extract_omega_cov_dict(
    Omega: np.ndarray,
    param_names: list[str],
) -> dict[str, float]:
    """Extract off-diagonal covariance terms as a flat dict.

    Parameters
    ----------
    Omega : np.ndarray
        ``(n_pk, n_pk)`` Omega matrix.
    param_names : list[str]
        PK parameter names.

    Returns
    -------
    dict
        Keys like ``"CL_Vz"`` → covariance value.
    """
    n = len(param_names)
    result: dict[str, float] = {}
    for col in range(n):
        for row in range(col + 1, n):
            key = f"{param_names[row]}_{param_names[col]}"
            result[key] = float(Omega[row, col])
    return result


def ensure_positive_definite(
    Omega: np.ndarray,
    min_eig: float = 1e-9,
) -> tuple[np.ndarray, bool]:
    """Ensure a matrix is positive-definite by clipping eigenvalues.

    Parameters
    ----------
    Omega : np.ndarray
        Square matrix.
    min_eig : float
        Minimum allowed eigenvalue.

    Returns
    -------
    tuple
        ``(adjusted_Omega, was_modified)``.
    """
    eigvals, eigvecs = np.linalg.eigh(Omega)
    if np.all(eigvals >= min_eig):
        return Omega, False

    eigvals_clipped = np.maximum(eigvals, min_eig)
    Omega_adj = eigvecs @ np.diag(eigvals_clipped) @ eigvecs.T
    return Omega_adj, True
