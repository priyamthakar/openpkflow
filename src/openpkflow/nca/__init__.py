"""NCA (Non-Compartmental Analysis) module for openpkflow."""

from openpkflow.nca.loader import load_nca_csv
from openpkflow.nca.methods import (
    AUCResult,
    LambdaZResult,
    accumulation_ratio,
    auc_inf_obs,
    auc_linear,
    auc_linear_up_log_down,
    auc_log,
    auc_percent_extrapolated,
    auc_tau,
    c0_back_extrapolated,
    clearance_volume_parameters,
    cmax,
    cumulative_urinary_excretion,
    lambda_z,
    percent_excreted,
    renal_clearance,
    steady_state_parameters,
    tmax,
)
from openpkflow.nca.results import NCAResult, NCASummaryResults
from openpkflow.nca.sparse import (
    SparseNCAResult,
    fit_sparse_1cmt_oral,
    sparse_nca_bias_analysis,
)
from openpkflow.nca.study import NCAStudy

__all__ = [
    # Math layer
    "AUCResult",
    "LambdaZResult",
    "auc_linear",
    "auc_log",
    "auc_linear_up_log_down",
    "auc_tau",
    "c0_back_extrapolated",
    "cmax",
    "tmax",
    "lambda_z",
    "auc_inf_obs",
    "auc_percent_extrapolated",
    "clearance_volume_parameters",
    "cumulative_urinary_excretion",
    "renal_clearance",
    "percent_excreted",
    "steady_state_parameters",
    "accumulation_ratio",
    # Data layer
    "load_nca_csv",
    # Orchestration
    "NCAStudy",
    "NCAResult",
    "NCASummaryResults",
    # Sparse NCA
    "fit_sparse_1cmt_oral",
    "sparse_nca_bias_analysis",
    "SparseNCAResult",
]
