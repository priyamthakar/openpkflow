# OpenPKFlow — AI Agent Handoff

**Project:** OpenPKFlow v2.2.0  
**Last updated:** 2026-05-23  
**Latest commits:**
- `35097fd` — feat: 2-compartment, full Omega matrix, and covariate support (v2.2.0)
- `e56390c` — chore: add HANDOFF.md, v2.2.0 foundation files (omega.py, covariate.py), update README and ROADMAP for v2.1.0
- `b830fab` — feat: FOCE-I and SAEM population PK estimation (v2.1.0)

---

## What is OpenPKFlow?

A Python pharmacometrics toolkit (MIT license, PyPI, Python >=3.10) for formulation-to-regulatory-submission workflows. Targets formulation scientists, PK/PD researchers, and CRO/CDMO teams. **Not** another NLME engine — it fills the gap between raw data and regulatory tables.

### Core modules (~960 files, 117 pop tests)

| Module | Purpose | Version |
|--------|---------|---------|
| `dissolution/` | f1/f2, bootstrap f2, MSD, model fitting (5 models + AICc), multi-media | v1.4.0 |
| `nca/` | AUClast, AUCinf, lambda_z, CL/F, steady-state, urinary, sparse NCA, CDISC PP | v1.5.0 |
| `ivivc/` | Level A IVIVC (Wagner-Nelson, Loo-Riegelman, convolution, Levy plot, %PE) | v1.2.0 |
| `sim/` | 1- and 2-compartment models (oral/IV bolus/infusion, repeated dosing) | v0.9.1 |
| `pop/` | GOF + VPC diagnostics + **FOCE-I/SAEM estimation (v2.2.0)** | v2.2.0 |
| `bayes/` | MAP individual PK (scipy) + full Bayesian PK + Bayesian BE (PyMC) | v2.0.0 |
| `be/` | 2x2 crossover TOST + BioEqPy export | v1.0.0 |
| `ml/` | Experimental torch MLP surrogate | v0.9.0 |
| `report/` | HTML (Jinja2), PDF (ReportLab), Word (python-docx), Markdown | v0.9.0 |

---

## The `pop/estimation/` Module (v2.2.0 — current state)

### Architecture: Two-tier, matching `bayes/`

**Tier 1 — FOCE-I (scipy only, zero new deps):**
- `run_foce_i(data, model)` — L-BFGS-B outer loop, per-subject EBE inner loop
- FOCE-I linearized -2LL via Cholesky factorization of V_i = GΩG^T + Σ
- 10 fail-closed diagnostics
- Numerical Hessian → eigenvalue checks → delta-method SEs
- **Supports:** 1- and 2-cmt models, diagonal and full Omega

**Tier 2 — SAEM (`[bayes]` extra, `_require_saem()` import guard):**
- `run_saem(data, model)` — PyMC Metropolis S-step, Robbins-Monro SA-step, analytical M-step
- Pure-numpy fallback MCMC in `saem_kernel.py`
- Post-burn-in: chain mean → point estimates
- **Supports:** 1- and 2-cmt models, diagonal and full Omega

### File map (13 files in `pop/estimation/`)

| File | Lines | Purpose | Key API |
|------|-------|---------|---------|
| `model.py` | ~300 | `PopPKModel` frozen dataclass, `(route, n_cmt)` param maps, `to_theta()`/`from_theta()` for full Omega + covariates, bounds | `PopPKModel(route, n_cmt, omega_type, covariate_model)` |
| `omega.py` | ~220 | Log-Cholesky Omega parameterization, PD enforcement | `log_cholesky_to_omega()`, `omega_to_log_cholesky()`, `extract_omega_cov_dict()` |
| `covariate.py` | ~225 | `CovariateDef`, `CovariateModel`, `apply_covariates()`, `pack_betas()`/`unpack_betas()` | `CovariateModel(covariates=[CovariateDef(...)], beta_init={...})` |
| `diagnostics.py` | ~260 | Numerical Hessian, PD checks, at-bound, multi-start, EBE shrinkage | `numerical_hessian()`, `check_hessian()`, `compute_ebd_shrinkage()` |
| `objective.py` | ~300 | 4-way dispatch: `(route, n_cmt)` → c_1cmt_*/c_2cmt_*, FOCE-I linearization | `predict_individual()`, `compute_foce_minus2ll()` |
| `foce_inner.py` | ~175 | Per-subject EBE (L-BFGS-B), `n_cmt` passthrough | `compute_ebe()`, `compute_all_ebe()` |
| `foce_i.py` | ~290 | FOCE-I outer loop, full Omega via `log_cholesky_to_omega()`, extended SEs | `run_foce_i(data, model)` |
| `saem_kernel.py` | ~195 | S-step pure-numpy MCMC, SA-step, M-step returns full Omega matrix | `saem_m_step()`, `saem_sa_step()`, `saem_s_step_single_subject_mcmc()` |
| `saem.py` | ~380 | SAEM orchestrator, full Omega chain storage, `n_cmt` dispatch | `run_saem(data, model)` |
| `result.py` | ~220 | `PopPKResult` — `omega_off_diag`, `omega_off_se`, `covariate_betas`, `.summary()`, `.to_dataframe()`, `.plot()`, `.report()` | `PopPKResult(method, route, ...)` |
| `plotting.py` | ~275 | 6-panel pop PK diagnostic plot | `pop_pk_figure(result)` |
| `reporting.py` | ~260 | HTML/Markdown reports with embedded plots | `report_pop_pk(result, output_path, fmt="html")` |
| `__init__.py` | ~110 | Public API, `_require_saem()` guard, comprehensive module docstring | `from openpkflow.pop.estimation import PopPKModel, run_foce_i, run_saem` |

### Key design decisions

1. **PopPKModel is a frozen dataclass** — immutable, self-validating, `to_theta()`/`from_theta()` for optimizer packing
2. **Parameter convention**: oral uses `_F` suffix (CL_F, Vz_F, V1_F); IV uses absolute (CL, Vz, V1); Q and V2 never carry `_F`
3. **Theta vector layout** (1-cmt oral diagonal): `[log(θ_pop)... | log_cholesky_diag... | (off_diag...) | (betas...) | log(σ_prop), σ_add]`
4. **Full Omega via Log-Cholesky**: L lower-triangular, `L[i,i]=exp(d_i)`, `L[i,j]` (i>j) unconstrained, `Omega = L @ L.T`
5. **SAEM M-step returns full Omega** — eigenvalue clipping enforces positive-definiteness
6. **warn_list pattern**: all diagnostic warnings collected in a `list[str]`, returned in result, surfaced in reports
7. **`_require_saem()` import guard**: called at function entry, not module import — `import openpkflow.pop` always works

### Parameter count reference

| Route | n_cmt | PK params | Omega diagonal | Omega full | Theta total (diagonal) | Theta total (full) |
|-------|-------|-----------|----------------|------------|------------------------|---------------------|
| oral | 1 | 3 (CL_F, Vz_F, ka) | 3 | 6 | 8 | 11 |
| oral | 2 | 5 (CL_F, V1_F, Q, V2, ka) | 5 | 15 | 12 | 22 |
| iv_bolus | 1 | 2 (CL, Vz) | 2 | 3 | 6 | 7 |
| iv_bolus | 2 | 4 (CL, V1, Q, V2) | 4 | 10 | 10 | 16 |

Add `n_cov * n_params` for covariates.

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
- **117 tests in `tests/pop/`**, 872 total

### CLI
- Typer with subcommand groups (`app.add_typer(...)`)
- Error handling: `try/except (FileNotFoundError, ValueError) → typer.echo(err=True) → Exit(1)`
- Entry point: `openpkflow = "openpkflow.cli:app"` in pyproject.toml
- Existing pop commands: `pop foce-i`, `pop saem`

### Package extras
- `[reports]`: openpyxl, reportlab, python-docx
- `[bayes]`: pymc, arviz, cmdstanpy
- `[ml]`: scikit-learn, torch
- `[dev]`: pytest, ruff, mypy, build, twine, mkdocs-material

### Git
- Co-author trailer required on all commits: `Co-authored-by: CommandCodeBot <noreply@commandcode.ai>`
- Commit format: `type: description` (e.g., `feat: ...`, `docs: ...`, `fix: ...`)
- `--no-verify` sometimes needed due to pre-existing lint issues in other files

### Ruff per-file-ignores (pyproject.toml)
```toml
"src/openpkflow/cli.py" = ["B008", "B904"]
"src/openpkflow/pop/estimation/reporting.py" = ["E501"]
"src/openpkflow/pop/estimation/result.py" = ["E501"]
"src/openpkflow/pop/estimation/foce_i.py" = ["E501"]
```

---

## Current Limitations & Next Steps

### What's done (v2.2.0)
- 1-cmt and 2-cmt models (oral, IV bolus)
- Diagonal and full Omega block matrix (Log-Cholesky parameterization)
- Covariate model dataclass + functions (`CovariateDef`, `CovariateModel`, `apply_covariates`)
- Off-diagonal covariances displayed in `summary()` and `to_dataframe()`
- Backward compatibility: all v2.1.0 code works unchanged

### What's NOT done (deferred to v2.3.0+)
- 3-compartment models
- iv_infusion route for estimation
- **Covariates are NOT wired into the estimation loop** — `CovariateModel` exists and validates, but `run_foce_i()` and `run_saem()` don't extract covariates from data or apply them to `theta_pop`. The theta vector layout supports betas (pack/unpack work), but the objective function doesn't use them.
- Covariate selection (stepwise, backward elimination)
- Inter-occasion variability
- PDF/DOCX pop PK reports
- CLI flags for `--n-cmt`, `--omega-type`, `--v1`, `--q`, `--v2` not yet added to `cli.py`
- Full mypy strict pass on estimation files (some `# type: ignore` annotations remain)

### What to do next
1. **Wire covariates into estimation** — in `_foce_objective` and SAEM loop, extract covariate data per subject, compute `theta_i = apply_covariates(...) * exp(eta)`, pass through to likelihood
2. **Add CLI flags** for `--n-cmt 2`, `--v1`, `--q`, `--v2`, `--omega-type full`
3. **Clean mypy strict** on all estimation files
4. **RSABE / replicate-design BE** (from roadmap)
5. **Validate against published Theophylline dataset** for 1-cmt estimates

---

## Reference: Route Parameter Conventions

| Model | Route | PK params | Count |
|-------|-------|-----------|-------|
| 1-cmt IV | `iv_bolus` | CL, Vz | 2 |
| 1-cmt oral | `oral` | CL_F, Vz_F, ka | 3 |
| 2-cmt IV | `iv_bolus` | CL, V1, Q, V2 | 4 |
| 2-cmt oral | `oral` | CL_F, V1_F, Q, V2, ka | 5 |

Note: Q and V2 never carry `_F` suffix (not confounded by bioavailability).

## Reference: Key Functions in `sim/methods.py`

```python
c_1cmt_iv_bolus(times, dose, CL, Vz) → 1-cmt IV concentration profile
c_1cmt_oral(times, dose, CL_F, Vz_F, ka) → 1-cmt oral (Bateman function)
c_2cmt_iv_bolus(times, dose, CL, V1, Q, V2) → 2-cmt IV (bi-exponential)
c_2cmt_oral(times, dose, CL_F, V1_F, Q, V2, ka) → 2-cmt oral (tri-exponential)
```

## Reference: Omega operations (`omega.py`)

```python
log_cholesky_to_omega(L_diag, L_off) → (n_params, n_params) PD Omega matrix
omega_to_log_cholesky(Omega) → (L_diag, L_off)
extract_omega_cov_dict(Omega, param_names) → {"CL_Vz": val, ...}
ensure_positive_definite(Omega) → (adjusted_Omega, was_modified)
```

## Reference: Covariate operations (`covariate.py`)

```python
CovariateDef(name, column, type, center, categories)
CovariateModel(covariates, beta_init)
apply_covariates(theta_pop, cov_model, subject_covariates) → theta_i
pack_betas(cov_model, param_names) → flat array
n_beta_params(cov_model) → int
```

## Files NOT to modify

- `CLAUDE.md` — project-level AI instructions (leave alone)
- `.commandcode/taste/` — learning system files (read-only)
- `V2_ARCHITECTURE_DECISION.md` — historical reference (v2.0.0 decision)
