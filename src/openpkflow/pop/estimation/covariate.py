"""Covariate modeling for population PK estimation.

Covariates modify individual parameters via:
    theta_i_k = theta_pop_k * exp( sum_j beta_{j,k} * cov_{i,j} + eta_i_k )

Supports continuous covariates (centered on population median) and
categorical covariates (0/1 indicator).
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field

import numpy as np

warnings.warn(
    "The covariate API (CovariateModel, CovariateDef, apply_covariates) is a "
    "non-functional skeleton in v2.2.0. Covariates are not applied during "
    "run_foce_i() or run_saem() estimation. This API will be removed or "
    "fully wired in v2.3.0. Do not use in production.",
    DeprecationWarning,
    stacklevel=2,
)


@dataclass(frozen=True)
class CovariateDef:
    """Definition of a single covariate.

    Parameters
    ----------
    name : str
        Short name (e.g. ``"WT"``, ``"SEX"``).
    column : str
        Column name in the dataset CSV.
    type : str
        ``"continuous"`` or ``"categorical"``.
    center : float
        Centering value. For continuous covariates, the population median
        is subtracted from raw values before applying the beta.
    categories : tuple of str or None
        For categorical covariates, the ordered categories. The first
        category is the reference (beta = 0).
    """

    name: str
    column: str
    type: str = "continuous"
    center: float = 0.0
    categories: tuple[str, ...] | None = None

    def __post_init__(self) -> None:
        if self.type not in ("continuous", "categorical"):
            raise ValueError(
                f"covariate type must be 'continuous' or 'categorical'; got '{self.type}'"
            )
        if self.type == "categorical" and self.categories is None:
            raise ValueError("categorical covariate requires 'categories'")


@dataclass(frozen=True)
class CovariateModel:
    """Model for covariate effects on PK parameters.

    Parameters
    ----------
    covariates : list of CovariateDef
        Covariate definitions.
    beta_init : dict of (str, str) → float
        Initial beta coefficients, keyed by ``(param_name, cov_name)``.
        E.g. ``{("CL", "WT"): 0.75}``.
    """

    covariates: list[CovariateDef] = field(default_factory=list)
    beta_init: dict[tuple[str, str], float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        cov_names = {c.name for c in self.covariates}
        for (param, cov), _val in self.beta_init.items():
            if cov not in cov_names:
                raise ValueError(
                    f"beta_init key ({param}, {cov}) references unknown covariate '{cov}'"
                )

    @property
    def n_betas(self) -> int:
        """Number of beta parameters."""
        return len(self.beta_init)


def n_beta_params(cov_model: CovariateModel | None) -> int:
    """Number of beta parameters in a covariate model.

    Parameters
    ----------
    cov_model : CovariateModel or None

    Returns
    -------
    int
    """
    if cov_model is None:
        return 0
    return cov_model.n_betas


def pack_betas(
    cov_model: CovariateModel | None,
    param_names: list[str],
) -> np.ndarray:
    """Pack beta coefficients into a flat array in canonical order.

    Order: iterate param_names, then covariate names.

    Parameters
    ----------
    cov_model : CovariateModel or None
    param_names : list[str]
        PK parameter names.

    Returns
    -------
    np.ndarray
        Flat beta vector.
    """
    if cov_model is None or cov_model.n_betas == 0:
        return np.array([], dtype=float)

    cov_names = [c.name for c in cov_model.covariates]
    betas = np.zeros(len(param_names) * len(cov_names), dtype=float)
    idx = 0
    for pname in param_names:
        for cname in cov_names:
            key = (pname, cname)
            betas[idx] = cov_model.beta_init.get(key, 0.0)
            idx += 1
    return betas


def unpack_betas(
    beta_vec: np.ndarray,
    cov_model: CovariateModel | None,
    param_names: list[str],
) -> dict[tuple[str, str], float]:
    """Unpack a flat beta vector.

    Parameters
    ----------
    beta_vec : np.ndarray
        Flat beta vector.
    cov_model : CovariateModel or None
    param_names : list[str]
        PK parameter names.

    Returns
    -------
    dict
        ``{(param_name, cov_name): value}``
    """
    if cov_model is None or len(beta_vec) == 0:
        return {}

    cov_names = [c.name for c in cov_model.covariates]
    result: dict[tuple[str, str], float] = {}
    idx = 0
    for pname in param_names:
        for cname in cov_names:
            result[(pname, cname)] = float(beta_vec[idx])
            idx += 1
    return result


def apply_covariates(
    theta_pop: np.ndarray,
    cov_model: CovariateModel | None,
    subject_covariates: dict[str, float] | None,
) -> np.ndarray:
    """Apply covariate effects to population parameters for one subject.

    theta_i_k = theta_pop_k * exp( sum_j beta_{j,k} * cov_{i,j} )

    Parameters
    ----------
    theta_pop : np.ndarray
        Population typical values on natural scale (n_params,).
    cov_model : CovariateModel or None
    subject_covariates : dict or None
        Covariate values for this subject, keyed by covariate name.

    Returns
    -------
    np.ndarray
        Individual parameters adjusted for covariates (n_params,).
    """
    if cov_model is None or not cov_model.covariates or subject_covariates is None:
        return theta_pop.copy()

    pk_names = sorted(set(k[0] for k in cov_model.beta_init))

    # Build the adjustment vector
    adjustment = np.zeros(len(theta_pop), dtype=float)
    pk_name_to_idx = {n: i for i, n in enumerate(pk_names)}

    for (pk_param, cov_name), beta in cov_model.beta_init.items():
        cov_val = subject_covariates.get(cov_name, 0.0)
        adjustment[pk_name_to_idx[pk_param]] += beta * cov_val

    return theta_pop * np.exp(adjustment)


def validate_covariate_data(
    data_by_subject: dict[str, tuple],
    cov_model: CovariateModel | None,
    id_col: str,
) -> dict[str, dict[str, float]]:
    """Extract and validate covariate values per subject.

    Parameters
    ----------
    data_by_subject : dict
        Subject data dict.
    cov_model : CovariateModel or None
    id_col : str
        Subject ID column name.

    Returns
    -------
    dict
        ``{subject_id: {cov_name: value}}`` for each subject.
    """
    if cov_model is None or not cov_model.covariates:
        return {subj: {} for subj in data_by_subject}

    return {subj: {} for subj in data_by_subject}
