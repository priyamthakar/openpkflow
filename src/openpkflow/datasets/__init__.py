"""Example datasets for OpenPKFlow."""

from __future__ import annotations

from importlib.resources import files


def _dataset_path(name: str) -> str:
    return str(files("openpkflow.datasets").joinpath(name))


def example_dissolution_path() -> str:
    """Path to the borderline-similar example dataset (f2 approx 57)."""
    return _dataset_path("example_dissolution.csv")


def example_similar_path() -> str:
    """Path to the clearly-similar example dataset (f2 approx 80)."""
    return _dataset_path("example_similar.csv")


def example_not_similar_path() -> str:
    """Path to the not-similar example dataset (f2 approx 38)."""
    return _dataset_path("example_not_similar.csv")


def example_theoph_path() -> str:
    """Path to the R nlme Theoph reference dataset (12 subjects, oral theophylline)."""
    return _dataset_path("theoph.csv")


def example_ss_crossval_path() -> str:
    """Path to the 3-subject synthetic steady-state dataset (1-cmt oral, tau=8 h)."""
    return _dataset_path("ss_crossval.csv")


__all__ = [
    "example_dissolution_path",
    "example_similar_path",
    "example_not_similar_path",
    "example_theoph_path",
    "example_ss_crossval_path",
]
