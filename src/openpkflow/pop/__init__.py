"""Population PK diagnostics -- GOF plots, VPC, and NONMEM-style dataset helpers."""

from .dataset import PopCSVConfig, create_nonmem_dataset, load_pop_csv
from .gof import GOFResult, compute_iwres, obs_pred_metrics
from .vpc import VPCResult, simulate_vpc

__all__ = [
    # dataset
    "PopCSVConfig",
    "load_pop_csv",
    "create_nonmem_dataset",
    # gof
    "GOFResult",
    "compute_iwres",
    "obs_pred_metrics",
    # vpc
    "VPCResult",
    "simulate_vpc",
]
