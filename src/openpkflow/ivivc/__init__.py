"""IVIVC -- In Vitro-In Vivo Correlation (Level A) for openpkflow.

Provides Wagner-Nelson and Loo-Riegelman deconvolution, convolution prediction,
Levy plots, and FDA predictability assessment per the FDA Extended Release
guidance (1997).

References
----------
FDA Guidance for Industry: Extended Release Oral Dosage Forms: Development,
Evaluation, and Application of In Vitro/In Vivo Correlations (1997). CDER.
"""

from __future__ import annotations

from .level_bc import (
    LinearCorrelationResult,
    level_b_correlation,
    level_c_correlation,
    mean_dissolution_time,
    mean_residence_time,
)
from .methods import (
    convolution_predict,
    ivivc_predictability,
    ivivc_predictability_aggregate,
    levy_plot_data,
    loo_riegelman,
    wagner_nelson,
)
from .results import IVIVCResult
from .study import IVIVCStudy

__all__ = [
    "IVIVCResult",
    "IVIVCStudy",
    "convolution_predict",
    "ivivc_predictability",
    "ivivc_predictability_aggregate",
    "levy_plot_data",
    "loo_riegelman",
    "wagner_nelson",
    "LinearCorrelationResult",
    "mean_dissolution_time",
    "mean_residence_time",
    "level_b_correlation",
    "level_c_correlation",
]
