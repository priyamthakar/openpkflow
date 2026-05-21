"""Bayesian PK module -- no public API in v1.0.0, planned for v1.1.0.

Bayesian NLME estimation (PyMC, CmdStanPy) is deferred. The optional
dependency extras are wired so ``pip install openpkflow[bayes]`` installs
PyMC >= 5.0 and CmdStanPy >= 1.2 when available, but no estimation functions
are exported yet.

To check if the bayes extras are installed:
    from openpkflow.bayes import _require_pymc; _require_pymc()
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
