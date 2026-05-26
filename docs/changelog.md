# Changelog

All notable changes to OpenPKFlow will be documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [2.3.0] -- 2026-05-24

### Breaking Changes

- **`pop/estimation/covariate.py` removed** -- `CovariateModel`, `CovariateDef`, `apply_covariates`,
  `pack_betas`, `unpack_betas` are deleted. These symbols were a non-functional skeleton in v2.2.0
  that silently did nothing during `run_foce_i()` or `run_saem()` estimation.
- **`PopPKModel.covariate_model` field removed** -- `PopPKModel` no longer accepts a
  `covariate_model` keyword argument.
- **`PopPKResult.covariate_betas` field removed** -- `PopPKResult.to_dict()` no longer includes
  the `covariate_betas` key.

### Added

- Pop PK cross-validation on the 12-subject Theophylline dataset:
  `tests/validation/test_pop_foce_reference.py`. `run_foce_i()` typical values match
  the `nlme` reference values from Pinheiro & Bates (2000), Table 8.1, within 20%
  relative tolerance.

### Changed

- `PopPKModel.n_betas` always returns 0 (property retained for API compatibility; will be removed in v3.0.0).

## [2.2.0] -- 2026-05-23

### Added

**Population PK -- 2-compartment models, full Omega matrix, covariate support**
- `pop/estimation/model.py` -- `PopPKModel` extended: `n_cmt` field (1 or 2), `omega_type` field ("diagonal" or "full"), `covariate_model` field
- `pop/estimation/omega.py` -- `log_cholesky_to_omega()`, `omega_to_log_cholesky()`, `extract_omega_cov_dict()`
- `pop/estimation/covariate.py` -- `CovariateDef`, `CovariateModel`, `apply_covariates()`, `pack_betas()`/`unpack_betas()`
- `pop/estimation/objective.py` -- extended 4-way dispatch `(route, n_cmt)` supporting 2-cmt oral and IV bolus
- `pop/estimation/foce_inner.py` -- `compute_ebe()` and `compute_all_ebe()` pass `n_cmt` to objective
- `pop/estimation/foce_i.py` -- outer loop constructs full Omega via `log_cholesky_to_omega()`
- `pop/estimation/saem_kernel.py` -- S-step and M-step return full Omega matrix
- `pop/estimation/saem.py` -- SAEM orchestrator stores full Omega chain
- `pop/estimation/result.py` -- `PopPKResult` extended: `omega_off_diag`, `omega_off_se`, `covariate_betas` fields
- `pop/estimation/reporting.py` -- HTML/Markdown report templates updated for covariate coefficient table and off-diagonal Omega correlation matrix

## [2.1.0] -- 2026-05-23

### Added

**Population PK -- FOCE-I and SAEM estimation**
- `pop/estimation/` -- new sub-package (11 files) implementing two-tier population PK estimation
- `pop/estimation/model.py` -- `PopPKModel` frozen dataclass
- `pop/estimation/foce_i.py` -- `run_foce_i()`: L-BFGS-B outer loop, per-subject EBE inner loop, 10 fail-closed diagnostics
- `pop/estimation/saem.py` -- `run_saem()`: Robbins-Monro SA-step, analytical M-step, PyMC Metropolis S-step
- `pop/estimation/result.py` -- `PopPKResult`: `.summary()`, `.to_dataframe()`, `.to_dict()`, `.plot()`, `.report()`
- `pop/estimation/plotting.py` -- 6-panel pop PK diagnostic figure
- `pop/estimation/reporting.py` -- HTML and Markdown reports
- `pop/__init__.py` -- exports `PopPKModel`, `PopPKResult`, `run_foce_i`, `run_saem`
- CLI: `openpkflow pop foce-i` and `openpkflow pop saem` Typer subcommands
- 47 new tests across `tests/pop/`

---

## [2.0.0] -- 2026-05-22

### Added

**Bayesian PK -- Phase 1 (MAP, no extra dependencies)**
- `bayes/priors.py` -- `PKPrior`: frozen dataclass with log-normal priors for CL, Vz, ka, sigma
- `bayes/map_pk.py` -- `map_individual_pk()`: MAP estimation via scipy L-BFGS-B in log-space; 10 fail-closed diagnostics
- `bayes/results.py` -- `MapPKResult`: dataclass with MAP estimates, SEs, derived parameters, diagnostics
- `bayes/reporting.py` -- `report_map_pk()`: HTML (Jinja2) and Markdown renderers
- 35 new tests in `tests/bayes/test_map_pk.py`

**Bayesian PK -- Phase 2 (full posterior, [bayes] extra)**
- `bayes/bayes_pk.py` -- `bayes_individual_pk()`: full posterior via PyMC 5.x + Metropolis sampler
- `bayes/bayes_be.py` -- `bayes_be()`: Bayesian 2x2 crossover BE via PyMC NUTS
- `bayes/results.py` -- `BayesPKResult`: posterior samples, summary stats, 95% CrI
- `bayes/bayes_be.py` -- `BayesBEResult`: P(BE), GMR posterior, variance components, frequentist comparison
- 26 new tests in `tests/bayes/test_bayes_be.py`

**Dissolution Excel loader**
- `dissolution/loader.py` -- `load_dissolution_excel()`: loads dissolution data from `.xlsx`/`.xls`
- `dissolution/study.py` -- `DissolutionStudy.from_excel()`: classmethod mirror of `from_csv()`

### Changed
- `bayes/__init__.py` -- exports `PKPrior`, `MapPKResult`, `BayesPKResult`, `BayesBEResult`, `map_individual_pk`, `bayes_individual_pk`, `bayes_be`
- `codecov.yml` -- added `coverage.status` block

## [1.5.0] -- 2026-05-22

### Added
- `nca/sparse.py` -- `fit_sparse_1cmt_oral()`: model-informed NCA from 3-5 samples
- `nca/sparse.py` -- `SparseNCAResult`: dataclass with MAP PK estimates
- `nca/sparse.py` -- `sparse_nca_bias_analysis()`: percent bias vs rich-sampling reference
- 16 new tests in `tests/nca/test_sparse_nca.py`

## [1.4.0] -- 2026-05-22

### Added
- `dissolution/multi_media.py` -- `MultiMediaStudy` and `MultiMediaResult`
- `dissolution/plotting.py` -- `multi_media_plot_b64()`: multi-panel dissolution overlay plot
- `report/templates/multi_media_report.html` -- multi-media HTML report template
- 26 new tests in `tests/dissolution/test_multi_media.py`

## [1.3.0] -- 2026-05-22

### Added
- `nca/methods.py` -- steady-state parameters, urinary excretion, CDISC PP output
- `nca/results.py` -- steady-state and urinary excretion fields
- 26 new tests in `tests/nca/test_steady_state_urine.py`

## [1.2.0] -- 2026-05-22

### Added
- `ivivc/` module -- In Vitro-In Vivo Correlation Level A (FDA ER Guidance 1997)
- `ivivc/methods.py` -- `wagner_nelson()`, `loo_riegelman()`, `convolution_predict()`, `levy_plot_data()`, `ivivc_predictability()`
- `ivivc/study.py` -- `IVIVCStudy`: full deconvolution -> Levy plot -> convolution -> predictability workflow
- `ivivc/results.py` -- `IVIVCResult` dataclass
- 45 new tests in `tests/ivivc/test_ivivc.py`

## [1.1.0] -- 2026-05-21

### Added
- `dissolution/similarity.py` -- `max_deviation()`, `msd()`, `model_dependent_comparison()`
- `dissolution/study.py` -- ICH M13B RSD constraint check
- `nca/results.py` -- lambda_z quality metrics, dose-normalised parameters, CDISC PP export
- `nca/study.py` -- %AUCextrap FDA flag
- `be/study.py` -- `BEStudy.to_bioeqpy_dataframe()` and `to_bioeqpy_csv()`
- `.pre-commit-config.yaml`, `.github/dependabot.yml`, `codecov.yml`, `VALIDATION.md`
- `tests/test_benchmark.py` -- performance benchmarks

## [1.0.0] -- 2026-05-21

### Added
- `be/` -- Bioequivalence module: `BEStudy`, `BEResult`, `be_tost()`, HTML/Markdown reports, CLI
- `SECURITY.md`, `CONTRIBUTING.md`, issue templates

## [0.9.1] -- 2026-05-21

### Added
- `sim/methods.py` -- `c_2cmt_iv_infusion()`: 2-compartment IV infusion
- `validation/__init__.py` -- cross-validation utilities
- `tests/validation/` -- 20 new tests: NCA truth recovery, sim Gibaldi & Perrier properties
- Full mkdocs-material docs site

## [0.9.0] -- 2026-05-18

### Added
- `ml/surrogate.py` (EXPERIMENTAL) -- `PKSurrogate`: torch MLP for 1-cmt oral PK

## [0.6.0] -- 2026-05-18

### Added
- `pop/` -- GOF plots (4-panel), VPC simulation-based, NONMEM-style dataset helpers

## [0.5.0] -- 2026-05-18

### Added
- `sim/` -- PK simulation engine: 1-cmt, 2-cmt, IV bolus/infusion/oral, repeated dosing

## [0.4.0] -- 2026-05-18

### Added
- `nca/` -- Non-compartmental analysis: AUC, Cmax, Tmax, lambda_z, half-life, CL/F, Vz/F

## [0.3.0] -- 2026-05-18

### Added
- ReportLab PDF and python-docx Word export for dissolution comparison and model fitting

## [0.2.0] -- 2026-05-18

### Added
- Dissolution model fitting: zero-order, first-order, Higuchi, Korsmeyer-Peppas, Weibull

## [0.1.0] -- 2026-05-17

### Added
- `dissolution.f1()` and `dissolution.f2()` -- difference factor and similarity factor
- CSV loader, CLI commands, example dataset, full test suite
