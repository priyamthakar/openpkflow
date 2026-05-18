"""Bayesian PK module -- optional dependency on PyMC and CmdStanPy.

Install the optional extra to enable Bayesian PK fitting:

    pip install openpkflow[bayes]

This installs PyMC and its dependencies. Without it, all imports from this
module raise ImportError with a clear message.
"""

from __future__ import annotations


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


__all__: list[str] = []
