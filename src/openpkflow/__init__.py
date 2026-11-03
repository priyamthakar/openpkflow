"""OpenPKFlow -- Python-first pharmacometrics and dissolution toolkit."""

from __future__ import annotations

import importlib
from types import ModuleType
from typing import TYPE_CHECKING

__version__ = "2.9.0"
__author__ = "Priyam Thakar"
__email__ = "priyamthakar1@gmail.com"
__license__ = "MIT"

# Subpackages load on first attribute access so `import openpkflow` stays cheap.
_SUBMODULES = frozenset(
    {
        "bayes",
        "be",
        "datasets",
        "dissolution",
        "ivivc",
        "ml",
        "nca",
        "pipeline",
        "pop",
        "report",
        "sim",
        "student",
        "validation",
    }
)

__all__ = [
    "__version__",
    "bayes",
    "be",
    "datasets",
    "dissolution",
    "ivivc",
    "ml",
    "nca",
    "pipeline",
    "pop",
    "report",
    "sim",
    "student",
    "validation",
]

if TYPE_CHECKING:
    from openpkflow import (
        bayes,
        be,
        datasets,
        dissolution,
        ivivc,
        ml,
        nca,
        pipeline,
        pop,
        report,
        sim,
        student,
        validation,
    )


def __getattr__(name: str) -> ModuleType:
    """Import a subpackage the first time it is accessed as an attribute.

    Parameters
    ----------
    name : str
        Attribute name, for example ``"nca"``.

    Returns
    -------
    ModuleType
        The imported subpackage.

    Raises
    ------
    AttributeError
        If *name* is not an OpenPKFlow subpackage.
    """
    if name in _SUBMODULES:
        module = importlib.import_module(f"{__name__}.{name}")
        globals()[name] = module
        return module
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    """List public attributes, including subpackages not yet imported."""
    return sorted(set(globals()) | _SUBMODULES)
