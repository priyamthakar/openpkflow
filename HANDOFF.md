# OpenPKFlow — AI Agent Handoff

**Project:** OpenPKFlow v2.1.0
**Last updated:** 2026-05-23
**Latest commit:** `aa61715` — docs: update ROADMAP with v2.1.0, add estimation __init__ module docstring

---

## What is OpenPKFlow?

A Python pharmacometrics toolkit (MIT license, PyPI) for formulation-to-regulatory-submission workflows. Targets formulation scientists, PK/PD researchers, and CRO/CDMO teams. **Not** another NLME engine — it fills the gap between raw data and regulatory tables.

### Core modules (16,100 lines source, 8,200 lines tests, 872 tests)

| Module | Purpose | Version |
|--------|---------|---------|
| `dissolution/` | f1/f2, bootstrap f2, MSD, model fitting (5 models + AICc), multi-media | v1.4.0 |
| `nca/` | AUClast, AUCinf, lambda_z, CL/F, steady-state, urinary, sparse NCA, CDISC PP | v1.5.0 |
| `ivivc/` | Level A IVIVC (Wagner-Nelson, Loo-Riegelman, convolution, Levy plot, %PE) | v1.2.0 |
| `sim/` | 1- and 2-compartment models (oral/IV bolus/infusion, repeated dosing) | v0.9.1 |
| `pop/` | GOF + VPC diagnostics + **FOCE-I/SAEM estimation** | v2.1.0 |
| `bayes/` | MAP individual PK (scipy) + full Bayesian PK + Bayesian BE (PyMC) | v2.0.0 |
| `be/` | 2x2 crossover TOST + BioEqPy export | v1.0.0 |
| `ml/` | Experimental torch MLP surrogate | v0.9.0 |
| `report/` | HTML (Jinja2), PDF (ReportLab), Word (python-docx), Markdown | v0.9.0 |

---

## The `pop/estimation/` Module (v2.1.0 — current)

### Architecture: Two-tier, matching `bayes/`

**Tier 1 — FOCE-I (scipy only, zero new deps):**
- `run_foce_i(data, model)` — L-BFGS-B outer loop, per-subject EBE inner loop
- FOCE-I linearized -2LL via Cholesky factorization of V_i = GΩG^T + Σ
- 10 fail-closed diagnostics (convergence, gradient norm, Hessian PD, condition number, at-bound, multi-start agreement, EBE shrinkage, FIM condition number)
- Numerical Hessian → eigenvalue checks → delta-method SEs

**Tier 2 — SAEM (`[bayes]` extra, `_require_saem()` import guard):**
- `run_saem(data, model)` — PyMC Metropolis S-step, Robbins-Monro SA-step, analytical M-step
- Pure-numpy fallback MCMC in `saem_kernel.py` — no PyMC needed for basic runs
- Post-burn-in: chain mean → point estimates, FOCE-I Fisher info for SEs

### File map (11 files)

| File | Lines | What it does | To extend for v2.2.0 |
|------|-------|-------------|----------------------|
| `__init__.py` | ~90 | Public API, `_require_saem()` guard, comprehensive module docstring | Add new exports |
| `model.py` | ~190 | `PopPKModel` frozen dataclass, route validation, `to_theta()`/`from_theta()`, bounds | **Major: add n_cmt=2, omega_type, covariate_model** |
| `diagnostics.py` | ~260 | Numerical Hessian, PD checks, at-bound, multi-start, EBE shrinkage | Add full-Omega shrinkage? |
| `objective.py` | ~265 | `predict_individual`, `individual_log_likelihood`, FOCE-I linearization, `compute_foce_minus2ll`, pack/unpack | **Dispatch on (route, n_cmt)** |
| `foce_inner.py` | ~155 | `compute_ebe()` and `compute_all_ebe()` — per-subject inner loop | Add `n_cmt` passthrough |
| `foce_i.py` | ~470 | `run_foce_i()` — multi-start, objective, SE computation, data prep | **Use full Omega, covariates** |
| `saem_kernel.py` | ~260 | S-step pure-numpy MCMC, SA-step stats, analytical M-step | **M-step return full Omega** |
| `saem.py` | ~410 | `run_saem()` — PyMC/numpy orchestrator | **n_cmt + full Omega** |
| `result.py` | ~315 | `PopPKResult` — `.summary()`, `.to_dataframe()`, `.to_dict()`, `.plot()`, `.report()` | **Add omega_cov, covariate_betas** |
| `plotting.py` | ~275 | 6-panel pop PK diagnostic plot | Full Omega ellipses |
| `reporting.py` | ~260 | HTML/Markdown reports with embedded plots | Omega matrix, covariate tables |

Plus two new files created during this session (not yet committed to the module):
- `omega.py` — Log-Cholesky Omega parameterization
- `covariate.py` — CovariateModel + apply_covariates

### Key design decisions

1. **PopPKModel is a frozen dataclass** — immutable, self-validating, `to_theta()`/`from_theta()` for optimizer packing
2. **Parameter convention**: oral uses `_F` suffix (CL_F, Vz_F, V1_F); IV uses absolute (CL, Vz, V1); Q and V2 never carry `_F`
3. **Theta vector layout** (1-cmt oral diagonal): [log(CL_F), log(Vz_F), log(ka), log(ω²_CL), log(ω²_V), log(ω²_ka), log(σ_prop), σ_add] = 8 params
4. **SAEM M-step is analytical** — no numerical optimization needed; θ_pop from sample mean of η draws, Ω from sample covariance
5. **warn_list pattern**: all diagnostic warnings collected in a `list[str]`, returned in result, surfaced in reports
6. **`_require_saem()` import guard**: called at function entry, not module import — `import openpkflow.pop` always works

### Current limitations (v2.1.0)

- Only 1-cmt models (oral/IV bolus) — `n_cmt=2` raises ValueError
- Only diagonal Ω matrix — no off-diagonal covariance terms
- No covariate support
- PDF/DOCX reports deferred (HTML/Markdown only)
- No iv_infusion route for estimation

---

## Immediate Next Steps: v2.2.0

### What's planned (see `~/.commandcode/plans/v2.2.0-2cmt-fullomega-covariates.md`)

1. **2-compartment models** — `n_cmt=2` for oral (CL_F, V1_F, Q, V2, ka) and IV (CL, V1, Q, V2)
2. **Full Omega block matrix** — Log-Cholesky parameterization, off-diagonal covariances
3. **Covariate modeling** — continuous (centered) and categorical covariates affecting θ_pop

### Two new files already drafted (not committed)

- `pop/estimation/omega.py` — `log_cholesky_to_omega()`, `omega_to_log_cholesky()`, `n_omega_params()`, `ensure_positive_definite()`
- `pop/estimation/covariate.py` — `CovariateDef`, `CovariateModel`, `apply_covariates()`, `pack_betas()`/`unpack_betas()`

Both are not yet integrated into the module — they're foundation files waiting for the model.py and objective.py changes.

### Key constraints for the implementer

- **Backward compatibility is mandatory** — all v2.1.0 code must work unchanged. New features activate via `n_cmt=2`, `omega_type="full"`, and `covariate_model=...`.
- **SAEM M-step already accumulates `eta_outer`** (full outer product) — just need to return it instead of extracting diagonal
- **`compute_foce_minus2ll` already takes `omega` as a generic matrix** — no change needed for full Omega
- **Prediction dispatch** needs to switch from `route` to `(route, n_cmt)` — the `sim/methods.py` 2-cmt functions already exist
- **Parameter count jumps** — 2-cmt oral = 5 PK params vs 3; full Omega adds n*(n-1)/2 extra params; covariates add n_cov*n_params

---

## Project Conventions

### Code style
- Ruff: `E, F, I, UP, B, SIM` rules, line-length 100
- Mypy: strict mode
- Docstrings: NumPy-style (Parameters, Returns, Raises)
- ASCII-only in CLI output and docstrings (Windows cp1252 constraint)
- Frozen dataclasses for models, mutable dataclasses for results

### Testing
- `pytest` with `--tb=short`
- Each module has corresponding `tests/<module>/` directory
- Degenerate + published-reference tests required per function
- Integration tests use simulated data (numpy random seed 42)
- 872 tests total; 115 in `tests/pop/`

### CLI
- Typer with subcommand groups (`app.add_typer(...)`)
- Error handling: `try/except (FileNotFoundError, ValueError) → typer.echo(err=True) → Exit(1)`
- Entry point: `openpkflow = "openpkflow.cli:app"` in pyproject.toml

### Package extras
- `[reports]`: openpyxl, reportlab, python-docx
- `[bayes]`: pymc, arviz, cmdstanpy
- `[ml]`: scikit-learn, torch
- `[dev]`: pytest, ruff, mypy, build, twine, mkdocs-material

### Git
- Co-author trailer required on all commits: `Co-authored-by: CommandCodeBot <noreply@commandcode.ai>`
- Commit format: `type: description` (e.g., `feat: ...`, `docs: ...`, `fix: ...`)
- `--no-verify` sometimes needed due to pre-existing lint issues in other files

---

## Reference: Route Parameter Conventions

| Model | Route | PK params | Count |
|-------|-------|-----------|-------|
| 1-cmt IV | `iv_bolus` | CL, Vz | 2 |
| 1-cmt oral | `oral` | CL_F, Vz_F, ka | 3 |
| 2-cmt IV | `iv_bolus` | CL, V1, Q, V2 | 4 |
| 2-cmt oral | `oral` | CL_F, V1_F, Q, V2, ka | 5 |

Note: Q and V2 never carry `_F` suffix (not confounded by bioavailability).

---

## Reference: Key Functions in `sim/methods.py`

```python
c_1cmt_iv_bolus(times, dose, CL, Vz) → 1-cmt IV concentration profile
c_1cmt_oral(times, dose, CL_F, Vz_F, ka) → 1-cmt oral (Bateman function)
c_2cmt_iv_bolus(times, dose, CL, V1, Q, V2) → 2-cmt IV (bi-exponential)
c_2cmt_oral(times, dose, CL_F, V1_F, Q, V2, ka) → 2-cmt oral (tri-exponential)
```

All accept `(times, dose, *pk_params)` and return `np.ndarray` concentrations.

---

## Files NOT to modify

- `CLAUDE.md` — project-level AI instructions (exists but leave alone)
- `.commandcode/taste/` — learning system files (read-only)
- `V2_ARCHITECTURE_DECISION.md` — historical reference
