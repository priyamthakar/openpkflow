"""Bayesian PK module.

Phase 1 (v2.0.0): MAP individual PK estimation via scipy L-BFGS-B.
No additional dependencies required beyond the base install.

Phase 2 (v2.0.0, [bayes] extra): full posterior sampling and Bayesian BE
via PyMC. Requires: pip install openpkflow[bayes]

To check if the bayes extras are installed:
    from openpkflow.bayes import _require_pymc; _require_pymc()
"""

from __future__ import annotations

from .map_pk import map_individual_pk
from .priors import PKPrior
from .results import MapPKResult


def _require_pymc() -> None:
    try:
        import pymc  # noqa: F401
    except ImportError as exc:
        raise ImportError(
            "Bayesian PK requires PyMC. Install with: pip install openpkflow[bayes]"
        ) from exc


def _require_cmdstanpy() -> None:
    try:
        import cmdstanpy  # noqa: F401
    except ImportError as exc:
        raise ImportError(
            "CmdStanPy-based sampling requires cmdstanpy. "
            "Install with: pip install openpkflow[bayes]"
        ) from exc


__all__ = [
    "PKPrior",
    "MapPKResult",
    "map_individual_pk",
]
