"""Population PK estimation — FOCE-I and SAEM algorithms."""

from __future__ import annotations

from .foce_i import run_foce_i
from .model import PopPKModel
from .result import PopPKResult


def _require_saem() -> None:
    """Check that PyMC is importable; raise ImportError with install hint."""
    try:
        import pymc  # noqa: F401
    except ImportError:
        raise ImportError(
            "SAEM estimation requires PyMC. Install: pip install 'openpkflow[bayes]'"
        ) from None


def run_saem(*args, **kwargs) -> PopPKResult:
    """Run SAEM population PK estimation. Requires PyMC (``openpkflow[bayes]``).

    See :func:`openpkflow.pop.estimation.saem.run_saem` for full signature.
    """
    _require_saem()
    from .saem import run_saem as _run_saem

    return _run_saem(*args, **kwargs)


__all__ = [
    "PopPKModel",
    "PopPKResult",
    "run_foce_i",
    "run_saem",
]
