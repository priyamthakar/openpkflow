"""Student-friendly one-liner APIs for dissolution, NCA, and PK model fitting.

Designed for pharmacy students: drop in your data, get answers.
No configuration needed -- sensible defaults for everything.

Usage::

    from openpkflow.student import fit_dissolution, analyze_pk, fit_pk_model

    # Dissolution: fit all 6 release models, rank by AICc
    results = fit_dissolution("my_data.csv")
    print(results.summary())
    results.plot()

    # NCA: AUC, Cmax, Tmax, t1/2, CL/F, Vz/F
    results = analyze_pk("my_pk_data.csv")
    print(results.summary())
    results.plot()

    # PK model fitting: 1- or 2-compartment
    results = fit_pk_model(times, concs, dose=100, route="oral")
    print(results.summary())
"""

from openpkflow.student.dissolution import DissolutionAnalysis, fit_dissolution
from openpkflow.student.nca import NCAAnalysis, analyze_pk
from openpkflow.student.sim import PKModelFit, fit_pk_model

__all__ = [
    "fit_dissolution",
    "DissolutionAnalysis",
    "analyze_pk",
    "NCAAnalysis",
    "fit_pk_model",
    "PKModelFit",
]
