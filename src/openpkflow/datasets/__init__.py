"""Example datasets for OpenPKFlow.

Access via pathlib.Path:

    from openpkflow.datasets import EXAMPLE_DISSOLUTION_CSV
    df = pd.read_csv(EXAMPLE_DISSOLUTION_CSV)
"""
from __future__ import annotations

from pathlib import Path

DATASETS_DIR = Path(__file__).parent

EXAMPLE_DISSOLUTION_CSV = DATASETS_DIR / "example_dissolution.csv"

__all__ = ["EXAMPLE_DISSOLUTION_CSV", "DATASETS_DIR"]
