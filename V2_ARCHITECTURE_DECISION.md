# v2.0.0 Architecture Decision: Bayesian PK

**Date:** 2026-05-22  
**Author:** Priyam T.  
**Status:** DECIDED

---

## The Question

Should v2.0.0 expand the roadmap scope to include population FOCE-I/SAEM estimation
(Option B), or stay roadmap-exact with MAP individual estimation + Bayesian BE only
(Option A)?

**Decision: Option A -- roadmap-exact.**

Rationale: The Pharmpy bridge (v0.7.0) was already skipped once. BioEqPy was kept
as a separate package. The pattern is consistent: stay narrow, ship complete, avoid
R/binary dependencies. FOCE-I/SAEM from scratch is a multi-quarter effort with high
implementation risk for a solo maintainer. Option B is explicitly deferred to v2.1.0.

---

## v2.0.0 Scope (Option A, locked)

**In scope:**
- MAP individual PK estimation from sparse TDM samples (1-cmt oral/IV, 3-5 samples)
- Bayesian BE: posterior probability of BE > 0.95 for 2x2 crossover (research tool)
- Prior-posterior comparison plots with shrinkage visualization
- HTML/PDF/DOCX reports following existing template style

**Explicitly out of scope:**
- Full FOCE-I/SAEM population estimation (deferred to v2.1.0)
- nlmixr2/rpy2 bridge (R dependency; deferred)
- Hierarchical/population Bayesian model (deferred to v2.1.0)
- Any feature that crosses into medical device territory (FDA 510(k))

---

## Library Decision: Two-Tier

### Tier 1 -- MAP point estimate (primary, zero new dependencies)

Use `scipy.optimize.minimize` (L-BFGS-B) for MAP estimation.

- scipy is already a hard dependency (used in `nca/sparse.fit_sparse_1cmt_oral()`)
- Returns MAP point estimate + approximate uncertainty from inverse Hessian
- Installs everywhere, no C++ toolchain, no new maintenance surface
- Scientifically defensible: FDA sparse sampling guidance does not require full
  posterior, only a defensible parameter estimate
- Pattern already established in the codebase; v2.0.0 extends it with a prior term

### Tier 2 -- Full posterior + Bayesian BE (optional, `[bayes]` extra)

Use **PyMC >= 5.0** as the single MCMC backend.

PyMC wins over CmdStanPy on every constraint that matters for this project:

| Constraint | PyMC | CmdStanPy |
|---|---|---|
| Windows install | Pure-Python wheel, no C++ toolchain | Needs MSVC or MinGW (~4 GB, 15-60 min) |
| MAP speed (1-cmt, 5 obs) | find_MAP() ~0.1-2s, no compile | optimize() fast after ~60s first compile |
| Python API | Inline model definition | Separate .stan file + Python dict |
| Solo maintenance | Stable since v5.0, pure-Python | Binary artifact, version mismatch risk |
| Already in extras | Yes (PyMC >= 5.0, listed first) | Yes (CmdStanPy >= 1.2, listed second) |

CmdStanPy has stronger pharmacometric community precedent (Torsten, TDM literature),
but for a 3-parameter 1-cmt model the speed difference is irrelevant and the Windows
install friction is a real barrier for the target users (bench scientists, CRO teams).
CmdStanPy stays in the `[bayes]` extra for future use but is not the v2.0.0 backend.

**Note on Bayesian BE:** P(BE) > 0.95 is investigational -- no FDA or EMA guidance
accepts it as a primary criterion. ICH M13A (2024) and EMA BE guideline still require
frequentist 90% CI. Implement with a prominent research-only disclaimer. The existing
CLAUDE.md disclaimer requirement covers this.

---

## Regulatory Profile Summary

| Feature | Regulatory status | Position in openpkflow |
|---|---|---|
| MAP individual PK (pop-PK post-hoc EBE) | Well-established; required in NDA/ANDA pop-PK | Core v2.0.0 feature |
| MAP for TDM dose individualization | Standard clinical practice (InsightRx, DoseMe) | Research tool; disclaimer required |
| Bayesian BE (P(BE) > 0.95) | Investigational; not a primary regulatory criterion | Research/simulation only |
| FOCE-I/SAEM | Standard (NONMEM, Monolix); no Python precedent in pivotal submissions | v2.1.0 |

FDA does not certify software. NONMEM and Monolix dominate pivotal submissions.
nlmixr2 is growing. Stan/PyMC have no documented precedent in pivotal NDAs as of
August 2025. openpkflow v2.0.0 is positioned as a research and exploratory analysis
tool, not a submission-ready engine. The existing disclaimer in CLAUDE.md is correct.

---

## Implementation Plan (high-level)

### Phase 1: MAP individual PK (scipy tier, no new deps)

```
bayes/
  __init__.py      -- import guard + _require_pymc() (existing)
  map_pk.py        -- map_individual_pk(times, concs, dose, route, prior) -> MapPKResult
  priors.py        -- PKPrior dataclass (log-normal priors on CL, V, ka)
  results.py       -- MapPKResult: point estimates, SE, shrinkage, .summary(), .report()
  reporting.py     -- HTML/PDF/DOCX following existing template style
```

`map_individual_pk()` minimizes the negative log-posterior via L-BFGS-B:
  `-(log_prior(theta) + log_likelihood(observed | theta, model))`

Sign convention: `log_prior` and `log_likelihood` each return negative values (log
of a probability <= 1), so their sum is <= 0. The objective passed to
`scipy.optimize.minimize` is the negated sum, which is >= 0 and decreasing toward
the MAP. Tests must assert the objective value is strictly lower at the MAP estimate
than at deliberately bad parameter values (e.g., CL = 0.001, CL = 1000).

where `model` is the existing `sim.c_1cmt_oral()` / `sim.c_1cmt_iv_bolus()`.

### Phase 2: Full posterior + Bayesian BE (PyMC tier, `[bayes]` extra)

```
bayes/
  bayes_pk.py      -- bayes_individual_pk() -> BayesPKResult (MCMC samples)
  bayes_be.py      -- bayesian_be() -> BayesBEResult (P(BE), posterior CI)
```

Gated behind `_require_pymc()`. Fail-fast ImportError if extra not installed.

**Bayesian BE statistical model contract (required for safe implementation):**

Model: log(AUC) and log(Cmax) are modelled on the log scale with additive Normal
error. The 2x2 crossover must include fixed effects for sequence, period, and
treatment; subject-within-sequence as a random effect; and a residual variance term.
This mirrors the standard ANOVA model underlying the frequentist TOST in `be/study.py`.

Decision quantity: `P(0.80 <= GMR <= 1.25)` where GMR = exp(treatment effect on
log scale). The 80-125 limits apply to both AUC and Cmax independently (FDA/EMA
standard). Report must show P(BE) alongside the frequentist 90% CI from TOST so the
user can compare both analyses side by side.

Validation tests required:
- A known 2x2 crossover example where both Bayesian P(BE) and frequentist TOST agree
  (e.g., GMR = 1.05, CV = 15%, n = 24 -- well inside BE window)
- An edge case near the 80% lower bound: frequentist 90% CI just passes, P(BE) also
  passes but is < 0.99 (shows the two methods can differ at the margin)
- An edge case outside the window: both methods fail, and the report clearly shows
  failure for both

### Definition of done (mirrors existing milestones)

- Type hints + NumPy docstrings on all public functions
- ASCII-only CLI output (Windows cp1252 constraint)
- Degenerate test: known analytical solution recovers true parameters within 5%
- Published-reference test: cite the prior/likelihood formulation source
- Disclaimer in all generated reports
- `ruff check`, `ruff format`, `mypy --strict` clean

**Additional MAP-specific acceptance criteria (fail any of these = do not ship):**

- Parameters optimized in log-space (log-CL, log-V, log-ka) to enforce positivity
  and improve conditioning; bounds set to physiologically plausible ranges
- Optimizer `success` flag checked; non-convergence raises a named warning and sets
  `MapPKResult.converged = False`; report must surface this prominently
- Gradient norm at solution checked: if `||grad|| > 1e-3` after convergence, flag as
  potentially not at MAP
- Hessian positive-definiteness: compute inverse Hessian via `scipy` `hess_inv`;
  if the Hessian is not positive-definite (negative eigenvalue), set
  `MapPKResult.uncertainty_reliable = False` and suppress SE values in the report
- Condition number check: if `cond(H) > 1e6`, warn "near-singular Hessian; SEs may
  be unreliable" -- common with sparse data and correlated CL/V
- Parameter-at-bound detection: if any optimized parameter is within 1% of its
  bound, warn that the estimate may be constrained by the prior/bound rather than
  the data
- Multi-start stability: run from 3 starting points (prior mean, prior mean +/- 1 SD
  on log scale); if MAP estimates differ by > 20% across starts, warn of
  identifiability concern
- Prior-dominance warning: if the likelihood contribution is < 10% of the total
  log-posterior, warn "prior-dominated fit; data are insufficient to update the prior"
- Route-specific minimum observations: oral route requires >= 3 observations
  (pre-peak, near-peak, post-peak); IV requires >= 2 (distribution and elimination);
  fewer observations must raise `ValueError` before attempting the fit
- Fail-closed report: if `converged = False` or `uncertainty_reliable = False`, the
  report must not display a parameter table as if it were authoritative; show a
  diagnostic summary instead with the warning text

---

## What This Decision Closes

- nlmixr2/rpy2 bridge: not needed for v2.0.0 scope
- CmdStanPy as primary backend: deferred; stays in extras
- FOCE-I/SAEM scope question: deferred to v2.1.0
- "Bayesian or frequentist BE?" question: both coexist -- frequentist TOST is the
  regulatory primary (v1.0.0 BEStudy); Bayesian BE is a v2.0.0 research companion
