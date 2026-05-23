"""Population PK estimation — FOCE-I and SAEM algorithms.

Two-tier architecture matching the ``bayes/`` module pattern:

**Tier 1 — FOCE-I (scipy, zero new dependencies):**
    - L-BFGS-B outer loop over population parameters (theta_pop, Omega, Sigma)
    - Per-subject EBE inner loop (L-BFGS-B on individual log-posterior)
    - FOCE-I linearized -2LL with Cholesky factorization of V_i = G*Omega*G^T + Sigma
    - Multi-start (3 points), 10 fail-closed diagnostics ported from ``bayes/map_pk.py``
    - Numerical Hessian -> eigenvalue checks -> delta-method SEs
    - Entry point: :func:`run_foce_i`

**Tier 2 — SAEM (``[bayes]`` extra, ``_require_saem()`` import guard):**
    - S-step: Metropolis MCMC sampling of eta_i (PyMC ``@as_op`` blackbox or numpy fallback)
    - SA-step: Robbins-Monro stochastic approximation of sufficient statistics (gamma_k = 1/k^alpha)
    - M-step: analytical updates for theta_pop, Omega, sigma_prop, sigma_add
    - Post-burn-in: chain mean -> point estimates, FOCE-I Fisher info for SEs
    - Entry point: :func:`run_saem`

**Model definition:**
    - :class:`PopPKModel` — frozen dataclass, ``to_theta()``/``from_theta()`` pack/unpack
    - Supports 1-cmt oral and IV bolus (2-cmt deferred to v2.2.0)
    - Diagonal Omega matrix, combined (proportional + additive) error model
    - 8-parameter theta vector for oral: [log(CL_F), log(Vz_F), log(ka),
      log(omega^2_CL), log(omega^2_V), log(omega^2_ka), log(sigma_prop), sigma_add]

**Result:**
    - :class:`PopPKResult` — parameter tables, SEs, RSE%, shrinkage, -2LL/AIC/BIC
    - Methods: ``.summary()``, ``.to_dataframe()``, ``.to_dict()``, ``.plot()``, ``.report()``
    - 6-panel diagnostic plot: OBS vs PRED/IPRED, CWRES vs TIME/PRED, EBE histograms + pairs

**CLI:**
    - ``openpkflow pop foce-i data.csv --route oral --cl 5.0 --v 50.0 --ka 1.0 --report report.html``
    - ``openpkflow pop saem data.csv --route iv_bolus --cl 3.0 --v 30.0 --n-iter 500``

**Tests:** 47 tests across 5 test files in ``tests/pop/``.

**Module files:** model.py, diagnostics.py, objective.py, foce_inner.py, foce_i.py,
saem_kernel.py, saem.py, result.py, plotting.py, reporting.py, __init__.py

**Deferred to v2.2.0:** 2-cmt models, full Omega block matrix, covariate modeling,
inter-occasion variability, PDF/DOCX pop PK reports.
"""

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
