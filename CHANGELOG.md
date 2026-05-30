# Changelog

All notable changes to OpenPKFlow will be documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [2.4.0] — 2026-05-30

### Added

- Research-grade replicate bioequivalence screening via `replicate_be()`:
  long-format full/partial replicate data parsing, GMR + conventional 90% CI,
  CVwR estimation, EMA-style scaled-limit summaries, and FDA-style RSABE point
  criterion screening. These outputs are explicitly documented as exploratory
  and not a replacement for jurisdiction-specific validated SAS/R workflows.
- Replicate BE CLI/report workflow: `openpkflow be replicate`, HTML/Markdown
  reports, JSON export, example partial-replicate CSV, and scalar reference
  validation fixtures for the screening calculations.
- Release-readiness documentation and slow-validation workflow for heavyweight
  reference checks, plus a read-only `scripts/release_readiness.py` checker.

---

## [2.3.0] — 2026-05-24

### Breaking Changes

- **`pop/estimation/covariate.py` removed** — `CovariateModel`, `CovariateDef`, `apply_covariates`,
  `pack_betas`, `unpack_betas` are deleted. These symbols were a non-functional skeleton in v2.2.0
  that silently did nothing during `run_foce_i()` or `run_saem()` estimation. Users who imported
  any of these symbols must remove those imports. No estimation results are affected.
- **`PopPKModel.covariate_model` field removed** — `PopPKModel` no longer accepts a
  `covariate_model` keyword argument. Existing `PopPKModel` definitions should drop that argument.
- **`PopPKResult.covariate_betas` field removed** — `PopPKResult.to_dict()` no longer includes
  the `covariate_betas` key.

### Added

- Pop PK cross-validation on the 12-subject Theophylline dataset:
  `tests/validation/test_pop_foce_reference.py`. `run_foce_i()` typical values match
  the `nlme` reference values from Pinheiro & Bates (2000), Table 8.1, within 20%
  relative tolerance. A waiting nlmixr2 5.0.0 script is included at
  `scripts/nlmixr2_popk_crossval.R` for rerun once Rtools/C compiler support is available.

### Changed

- `PopPKModel.n_betas` always returns 0 (property retained for API compatibility with existing
  code that reads it; will be removed in v3.0.0).

## [2.2.0] — 2026-05-23

### Added

**Population PK -- 2-compartment models, full Omega matrix, covariate support**
- `pop/estimation/model.py` -- `PopPKModel` extended: `n_cmt` field (1 or 2), `omega_type` field ("diagonal" or "full"), `covariate_model` field; `to_theta()`/`from_theta()` handle full log-Cholesky Omega parameterization and covariate beta packing
- `pop/estimation/omega.py` -- `log_cholesky_to_omega()`, `omega_to_log_cholesky()`, `extract_omega_cov_dict()`: log-Cholesky Omega parameterization enforcing positive-definiteness; off-diagonal SEs via delta method
- `pop/estimation/covariate.py` -- `CovariateDef`, `CovariateModel`, `apply_covariates()`, `pack_betas()`/`unpack_betas()`: exponential covariate model on population PK parameters; continuous and categorical covariates
- `pop/estimation/objective.py` -- extended 4-way dispatch `(route, n_cmt)` supporting 2-cmt oral and IV bolus; `predict_individual()` passes `n_cmt` through to `sim/` analytical solutions
- `pop/estimation/foce_inner.py` -- `compute_ebe()` and `compute_all_ebe()` pass `n_cmt` to objective; full Omega propagated via Cholesky
- `pop/estimation/foce_i.py` -- outer loop constructs full Omega via `log_cholesky_to_omega()`; extended SEs include off-diagonal Omega elements and covariate betas
- `pop/estimation/saem_kernel.py` -- S-step and M-step return full Omega matrix; eigenvalue clipping enforces PD in SA accumulation step
- `pop/estimation/saem.py` -- SAEM orchestrator stores full Omega chain; covariate-aware M-step; `n_cmt` dispatch
- `pop/estimation/result.py` -- `PopPKResult` extended: `omega_off_diag`, `omega_off_se`, `covariate_betas` fields; `.summary()` and `.to_dataframe()` render covariate and full Omega tables
- `pop/estimation/reporting.py` -- HTML/Markdown report templates updated for covariate coefficient table and off-diagonal Omega correlation matrix

## [2.1.0] — 2026-05-23

### Added

**Population PK -- FOCE-I and SAEM estimation**
- `pop/estimation/` -- new sub-package (11 files) implementing two-tier population PK estimation
- `pop/estimation/model.py` -- `PopPKModel` frozen dataclass: structural model definition, `to_theta()`/`from_theta()` for optimizer packing/unpacking, parameter bounds
- `pop/estimation/foce_i.py` -- `run_foce_i()`: L-BFGS-B outer loop, per-subject EBE inner loop, FOCE-I linearized -2LL, 10 fail-closed diagnostics (convergence, gradient norm, Hessian PD, condition number, at-bound, multi-start agreement), delta-method SEs via inverse Hessian; zero new dependencies
- `pop/estimation/saem.py` -- `run_saem()`: Robbins-Monro SA-step with gamma=1/k^alpha, analytical M-step, PyMC Metropolis S-step (`[bayes]` extra), pure-numpy MCMC fallback; `_require_saem()` import guard
- `pop/estimation/result.py` -- `PopPKResult`: `.summary()`, `.to_dataframe()`, `.to_dict()`, `.plot()`, `.report()` methods; -2LL, AIC, BIC, RSE%, EBE shrinkage
- `pop/estimation/plotting.py` -- 6-panel pop PK diagnostic figure: OBS vs PRED, OBS vs IPRED, CWRES vs TIME, CWRES vs PRED, EBE histograms, EBE pairs
- `pop/estimation/reporting.py` -- HTML and Markdown reports with embedded diagnostic plots, parameter tables, warnings section, disclaimer
- `pop/__init__.py` -- exports `PopPKModel`, `PopPKResult`, `run_foce_i`, `run_saem`
- CLI: `openpkflow pop foce-i` and `openpkflow pop saem` Typer subcommands
- 47 new tests across `tests/pop/`

---

## [2.0.0] — 2026-05-22

### Added

**Bayesian PK -- Phase 1 (MAP, no extra dependencies)**
- `bayes/priors.py` -- `PKPrior`: frozen dataclass with log-normal priors for CL, Vz, ka, sigma;
  `log_prior_oral()` / `log_prior_iv()` methods; parameter bounds for L-BFGS-B
- `bayes/map_pk.py` -- `map_individual_pk()`: MAP individual PK estimation via scipy L-BFGS-B in
  log-space; proportional error model; 3-start multi-start; 10 fail-closed diagnostics including
  convergence, gradient norm, Hessian PD, condition number, at-bound, multi-start agreement,
  prior-dominance checks
- `bayes/results.py` -- `MapPKResult`: dataclass with all MAP estimates, standard errors
  (delta-method via inverse Hessian), derived parameters (k, t1/2, AUCinf, Cmax, Tmax),
  diagnostics, `summary()`, `to_dict()`, `plot()`, `report()` methods
- `bayes/reporting.py` -- `report_map_pk()`: HTML (Jinja2) and Markdown renderers for MAP PK reports
- `report/templates/map_pk_report.html` -- navy-header template with 4 diagnostic cards,
  parameter table with SEs, concentration-time profile, observed vs predicted table, disclaimer
- 35 new tests in `tests/bayes/test_map_pk.py`

**Bayesian PK -- Phase 2 (full posterior, [bayes] extra)**
- `bayes/bayes_pk.py` -- `bayes_individual_pk()`: full posterior via PyMC 5.x + Metropolis sampler
  (numpy blackbox wrapped as pytensor `as_op`); shrinkage estimation; ESS check via arviz
- `bayes/bayes_be.py` -- `bayes_be()`: Bayesian 2x2 crossover BE via PyMC NUTS; log-scale linear
  mixed model with fixed effects (sequence, period, treatment) and non-centered random subject effect;
  decision quantity P(0.80 <= GMR <= 1.25); frequentist 90% CI computed side-by-side for comparison;
  R-hat and ESS convergence diagnostics
- `bayes/results.py` -- `BayesPKResult`: posterior samples, summary stats, 95% CrI, shrinkage,
  `summary()`, `to_dict()` methods
- `bayes/bayes_be.py` -- `BayesBEResult`: P(BE), GMR posterior, variance components (sigma_b, sigma_w),
  frequentist comparison, `summary()`, `to_dict()`, `report()` methods
- `bayes/reporting.py` -- `report_bayes_be()`: HTML (Jinja2) + Markdown renderers with GMR posterior
  histogram (matplotlib), Bayesian vs frequentist comparison table
- `report/templates/bayes_be_report.html` -- navy-header template with P(BE) decision banner
  (green/amber/red), GMR posterior plot, variance component cards, comparison table, disclaimer
- 26 new tests in `tests/bayes/test_bayes_be.py` (non-PyMC tests run without `[bayes]` extra)
- `V2_ARCHITECTURE_DECISION.md` -- architecture decision record documenting Option A scope,
  library choice, MAP objective sign convention, 10 diagnostics, Bayesian BE model contract

**Dissolution Excel loader**
- `dissolution/loader.py` -- `load_dissolution_excel()`: loads and validates dissolution data from
  `.xlsx`/`.xls` files; accepts optional `sheet_name` (str or int); requires `openpyxl` (`[reports]` extra)
- `dissolution/study.py` -- `DissolutionStudy.from_excel()`: classmethod mirror of `from_csv()`
- 13 new tests in `tests/dissolution/test_excel_loader.py`

### Changed
- `bayes/__init__.py` -- exports `PKPrior`, `MapPKResult`, `BayesPKResult`, `BayesBEResult`,
  `map_individual_pk`, `bayes_individual_pk`, `bayes_be`
- `dissolution/loader.py` -- validation logic extracted into `_validate_dissolution_df()` private
  helper; shared by both `load_dissolution_csv()` and `load_dissolution_excel()` (no behavior change)
- `dissolution/__init__.py` -- exports `load_dissolution_excel`
- `codecov.yml` -- added `coverage.status` block: project threshold 2%, patch threshold 80%
- README -- added Codecov badge, Docs badge, Bayesian PK quick-start section, updated feature
  comparison and status tables

## [1.5.0] — 2026-05-22

### Added
- `nca/sparse.py` — `fit_sparse_1cmt_oral()`: model-informed NCA from 3-5 samples; fits a
  1-compartment oral model via scipy `curve_fit` in log-space; recovers CL_F, Vz_F, ka with
  standard errors from the covariance matrix; handles non-convergence gracefully
- `nca/sparse.py` — `SparseNCAResult`: dataclass with MAP PK estimates, derived parameters
  (AUCinf, AUClast, Cmax, Tmax, half-life, accumulation ratio), standard errors, convergence flag,
  `summary()`, `to_dict()`, `plot()` methods
- `nca/sparse.py` — `sparse_nca_bias_analysis()`: computes percent bias and percent error of
  sparse vs. rich-sampling reference for AUCinf, Cmax, CL_F
- `nca/__init__.py` — exports `fit_sparse_1cmt_oral`, `SparseNCAResult`, `sparse_nca_bias_analysis`
- 16 new tests in `tests/nca/test_sparse_nca.py`

---

## [1.4.0] — 2026-05-22

### Added
- `dissolution/multi_media.py` — `MultiMediaStudy`: accepts `{media_name: csv_path}` or
  `{media_name: DissolutionStudy}` dict; wraps per-medium `DissolutionStudy` instances; computes
  f2 in each medium; enforces shared time points across media
- `dissolution/multi_media.py` — `MultiMediaResult`: per-medium f2 grid, overall PASS/FAIL verdict
  (all media must achieve f2 >= 50), `summary()`, `report()`, `plot()` methods
- `report/templates/multi_media_report.html` — summary pass/fail grid + per-medium detail sections
  + multi-panel dissolution overlay plot; matches existing navy-header template style
- `dissolution/plotting.py` — `multi_media_plot_b64()`: multi-panel matplotlib figure with one
  subplot per medium, 85% threshold lines, reference/test overlay
- HTML, PDF, and DOCX report dispatch for `MultiMediaResult`
- `dissolution/__init__.py` — exports `MultiMediaStudy`, `MultiMediaResult`
- 26 new tests in `tests/dissolution/test_multi_media.py`

---

## [1.3.0] — 2026-05-22

### Added
- `nca/methods.py` — `steady_state_parameters()`: computes Cmax_ss, Cmin_ss, Cavg_ss, AUCtau,
  fluctuation_pct, swing from steady-state dosing interval data
- `nca/methods.py` — `accumulation_ratio()`: AUCTau_ss / AUCTau_sd ratio
- `nca/methods.py` — `cumulative_urinary_excretion()`: computes Ae from urine volume and
  concentration data
- `nca/methods.py` — `renal_clearance()`: CLr = Ae / AUCinf
- `nca/methods.py` — `percent_excreted()`: 100 * Ae / dose
- `nca/methods.py` — `auc_tau()`: AUC over a dosing interval with method dispatch
- `nca/results.py` — steady-state fields: `Cmax_ss`, `Cmin_ss`, `Cavg_ss`, `AUCtau`,
  `fluctuation_pct`, `swing`, `accumulation_ratio`
- `nca/results.py` — urinary excretion fields: `Ae`, `Ae_pct`, `CLr`
- `nca/study.py` — `NCAStudy` accepts `steady_state=True`, `tau`, `urine_volume_col`,
  `urine_conc_col` parameters; auto-computes steady-state and urine parameters per subject
- 26 new tests in `tests/nca/test_steady_state_urine.py`

### Changed
- `nca/__init__.py` — exports all new functions
- `nca/results.py` — `summary()`, `to_dict()` include new fields when populated
- `nca/study.py` — `analyze()` computes steady-state and urine parameters when configured

## [1.2.0] — 2026-05-22

### Added
- `ivivc/` module — In Vitro-In Vivo Correlation Level A (FDA ER Guidance 1997)
- `ivivc/methods.py` — `wagner_nelson()`: one-compartment oral deconvolution (Wagner & Nelson 1963)
- `ivivc/methods.py` — `loo_riegelman()`: two-compartment oral deconvolution (Loo & Riegelman 1968)
- `ivivc/methods.py` — `convolution_predict()`: numerical convolution of dissolution input rate
  with IV unit impulse response
- `ivivc/methods.py` — `levy_plot_data()`: IVIVC correlation with linear regression
- `ivivc/methods.py` — `ivivc_predictability()`: FDA 1997 %PE assessment for Cmax and AUCinf
  (<=15% individual, <=10% mean abs)
- `ivivc/study.py` — `IVIVCStudy`: orchestrates full deconvolution → Levy plot → convolution →
  predictability workflow
- `ivivc/results.py` — `IVIVCResult` dataclass with `summary()`, `plot()`, `report()`, `to_dict()`
- `ivivc/reporting.py` — HTML, Markdown, PDF, DOCX report renderers
- `report/templates/ivivc_report.html` — 4-panel HTML report with Levy plot, predicted vs observed
  overlay, predictability highlight cards, disclaimer
- `report/pdf.py` — `render_ivivc_pdf_report()`: ReportLab PDF
- `report/docx.py` — `render_ivivc_docx_report()`: python-docx Word document
- CLI: `openpkflow ivivc run` command registered
- 45 new tests in `tests/ivivc/test_ivivc.py` including Wagner-Nelson, Loo-Riegelman,
  convolution, Levy plot, predictability, PDF, DOCX

## [1.1.0] — 2026-05-21

### Added
- `dissolution/similarity.py` — `max_deviation()`: maximum absolute deviation between profiles
  (FDA/SUPAC-IR 1995); accepted alternative when f2 prerequisites cannot be met
- `dissolution/similarity.py` — `msd()`: Mahalanobis Statistical Distance with chi-squared
  significance test (FDA PSA guidance 1999); returns `MSDResult` dataclass
- `dissolution/models.py` — `model_dependent_comparison()`: compare fitted dissolution model
  parameters via 90% CI (FDA 1997 model-dependent approach); `ModelComparisonResult` dataclass
- `dissolution/study.py` — ICH M13B RSD constraint: warns when RSD > 8% at time points with
  mean <= 60% (stricter than legacy FDA CV limits)
- `nca/results.py` — `lambda_z_adj_r2` and `lambda_z_n_points` quality metric fields added to
  `NCAResult`; displayed in HTML single-subject reports
- `nca/results.py` — dose-normalised parameters: `DN_AUClast`, `DN_AUCinf_obs`, `DN_Cmax`
  (dose-normalised by mg); shown in summary(), summary reports, and HTML templates
- `nca/results.py` — `NCASummaryResults.to_cdisc_pp()`: export CDISC PP-format long-format
  DataFrame with PPTESTCD, PPORRES, PPORRESU, PPSPEC columns
- `nca/study.py` — %AUCextrap FDA flag: auto-warns when `AUC_percent_extrapolated > 20%`
  with message suggesting extended sampling schedule
- `be/study.py` — `BEStudy.to_bioeqpy_dataframe()` and `to_bioeqpy_csv()`: export BioEqPy-ready
  long-format crossover data with subject, sequence, period, treatment columns
- `.github/dependabot.yml` — weekly automated dependency updates for pip and GitHub Actions
- `.github/PULL_REQUEST_TEMPLATE.md` — PR template with pharmacometric correctness checklist
- `.pre-commit-config.yaml` — ruff, ruff-format, mypy, and general hooks
- `codecov.yml` — Codecov configuration with per-Python-version flags
- `CODE_OF_CONDUCT.md` — Contributor Covenant v2.0
- `VALIDATION.md` — regulatory test traceability matrix mapping every test to FDA/EMA guidance
  sections and published DOIs
- `FUTURE_PLANS.md` — strategic roadmap with competitive landscape analysis
- `tests/test_benchmark.py` — performance benchmarks for dissolution, NCA, and BE operations

### Changed
- `nca/results.py` — `NCASummaryResults.summary()` now includes %AUCextrap, DN_AUClast, DN_Cmax
- `report/templates/nca_single_report.html` — added lambda_z quality metrics and DN parameter rows
- `report/templates/nca_summary_report.html` — added DN_AUClast and DN_Cmax columns
- `dissolution/__init__.py` — exports `max_deviation`, `msd`, `MSDResult`,
  `model_dependent_comparison`, `ModelComparisonResult`
- README — feature comparison table updated; added MSD/max-deviation/model-dependent rows;
  added %AUCextrap/CDISC PP row; linked VALIDATION.md; updated counts
- ROADMAP — RSABE milestone replaced with BioEqPy bridge polish (v1.4.0)
- docs — BE tutorial/reference updated to position as convenience layer with BioEqPy exports

### Fixed
- `SECURITY.md` — supported version updated from 0.9.x to 1.0.x
- `tests/test_benchmark.py` — fixed non-existent `auc_trapezoid` import (now `auc_linear`);
  fixed `be_tost` parameter names (`theta_lo` -> `be_lower`)

### Removed
- Generated outputs and artifacts from repository root (sample HTML/PDF reports,
  chat image, handout files)

## [1.0.0] — 2026-05-21

### Added
- `be/` — Bioequivalence module: `BEStudy`, `BEResult`, `be_tost()`, HTML/Markdown reports
  - 2x2 crossover TOST (FDA 2003 / EMA guidance): paired log-difference GMR + 90% CI
  - Parameterised acceptance limits (`be_lower`, `be_upper`; default 80-125%); NTI products
    use `be_lower=0.90, be_upper=1.1111`
  - `BEStudy.from_nca_results()` convenience constructor from two `NCASummaryResults` objects
  - `be_report.html` Jinja2 template with colour-coded verdict banner and CI bar visualisation
  - `openpkflow be compare <csv>` CLI command
  - 36 new tests in `tests/be/` covering TOST math, CI width, CV, NTI limits, report output
- `pyproject.toml` — B008/B904 ruff suppressions for typer CLI patterns
- `pyproject.toml` — classifier promoted from `2 - Pre-Alpha` to `4 - Beta`
- `CONTRIBUTING.md` — contribution guide with pharmacometric correctness rules
- `SECURITY.md` — vulnerability reporting policy
- `.github/ISSUE_TEMPLATE/` — bug report and feature request templates

### Fixed
- Pre-existing `zip()` without `strict=` in `dissolution/similarity.py`,
  `dissolution/reporting.py`, `validation/__init__.py` (B905)
- Unused `n_batches` variable in `dissolution/study.py` (F841)
- Import ordering in `tests/dissolution/test_study.py` and `tests/validation/test_nca_validation.py`

## [0.9.1] — 2026-05-21

### Added
- `sim/methods.py` — `c_2cmt_iv_infusion()`: 2-compartment constant-rate IV infusion
  (biexponential rectangular-pulse formula, Gibaldi & Perrier 2nd ed. Eqs. 3-28 to 3-30);
  wired into `TwoCompartmentModel` (new `iv_infusion` route), `simulate()`, and `sim/__init__.py`
- `validation/__init__.py` — `pct_bias()`, `rmse()`, `within_pct()` cross-validation utilities
- `tests/validation/` — 20 new tests: NCA recovers CL/Vz/t1/2/AUCinf within 2% on synthetic
  IV bolus data; sim verifies Gibaldi & Perrier properties for 1-cmt bolus/oral and 2-cmt
  bolus/infusion
- Full mkdocs-material docs site: `mkdocs.yml`, `docs/index.md`, 4 tutorials (dissolution, NCA,
  sim, pop), 6 reference pages, changelog; `docs.yml` GitHub Actions workflow for auto-deploy
  to GitHub Pages

### Fixed
- `__version__` was `"0.1.0"` in `src/openpkflow/__init__.py` but `"0.9.0"` in `pyproject.toml` — corrected
- CI now installs `.[ml]` extras so torch surrogate tests run in CI (previously skipped)
- `bayes/__init__.py` docstring now explicitly states no public API in v1.0.0 (planned v1.1.0)

## [0.9.0] — 2026-05-18

### Added
- `ml/surrogate.py` (EXPERIMENTAL) — `PKSurrogate`: torch MLP that approximates
  1-compartment oral PK concentration-time profiles; trained from synthetic data
  generated by `sim.c_1cmt_oral()`; features: (time, dose, CL_F, Vz_F, ka);
  z-score normalisation, Adam optimizer, tanh activations
- `PKSurrogate.from_1cmt_oral()` factory: generates N random parameter sets, simulates
  profiles via openpkflow analytical formula, trains MLP in one call
- 9 tests in `tests/ml/test_surrogate.py`: loss decrease, relative reduction, shape,
  non-negativity, analytical correlation (r > 0.90 on hold-out), reproducibility with seed;
  auto-skip when torch is not installed
- All ml features marked EXPERIMENTAL with disclaimer -- not for regulatory use

### Notes
- v0.7.0 (Pharmpy bridge) intentionally skipped -- number reserved
- v0.8.0 (Bayesian PK): optional `[bayes]` extras wired (PyMC >= 5.0, CmdStanPy >= 1.2);
  PyMC is not installed in the dev environment; the bayes module provides ImportError
  guards -- full Bayesian PK deferred until PyMC is available in the target environment

## [0.6.0] — 2026-05-18

### Added
- `pop/dataset.py` — `PopCSVConfig`, `load_pop_csv()` (NONMEM-style CSV loader with EVID/MDV filtering), `create_nonmem_dataset()` (dose + observation records merged into NONMEM-compatible DataFrame)
- `pop/gof.py` — `compute_iwres()` (individual weighted residuals, proportional error model), `obs_pred_metrics()` (MPE/RMSE/rRMSE/R2), `GOFResult` dataclass with `iwres` property, `pred_metrics()`, `ipred_metrics()`, `summary()`, `to_dataframe()`, `plot()`, `report()`
- `pop/vpc.py` — `VPCResult` dataclass; `simulate_vpc()`: simulation-based VPC using `sim.simulate()` + proportional/additive residual noise, time-binned percentile bands (5th/50th/95th) for both observed and simulated data
- `pop/plotting.py` — `gof_plots_b64()`: 4-panel GOF figure (OBS vs PRED, OBS vs IPRED, IWRES vs TIME, IWRES vs IPRED) at 600 dpi; `vpc_plot_b64()`: VPC scatter + band overlay at 600 dpi
- `pop/reporting.py` — `report_gof()` and `report_vpc()` dispatchers (HTML, Markdown, PDF, DOCX)
- `report/templates/pop_gof_report.html` — dark-navy header, 6-metric highlight grid, embedded GOF 4-panel plot, metrics comparison table, data table, disclaimer
- `report/templates/pop_vpc_report.html` — dark-navy header, VPC plot, VPC band data table, disclaimer
- `render_gof_pdf_report()` and `render_vpc_pdf_report()` in `report/pdf.py`
- `render_gof_docx_report()` and `render_vpc_docx_report()` in `report/docx.py`
- 40 new tests in `tests/pop/`: `test_dataset.py` (10 tests), `test_gof.py` (14 tests), `test_vpc.py` (16 tests); degenerate + reference citations for each metric function

## [0.5.0] — 2026-05-18

### Added
- `sim/methods.py` — pure-math analytical PK functions: `c_1cmt_iv_bolus`, `c_1cmt_iv_infusion`, `c_1cmt_oral` (Bateman + L'Hopital flip-flop), `c_2cmt_iv_bolus`, `c_2cmt_oral` (3-exponential Laplace form), `superpose` (linear multi-dose superposition); `_2cmt_macro_constants` helper for alpha/beta eigenvalues
- `sim/dosing.py` — `Dose` and `DoseRegimen` frozen dataclasses; `DoseRegimen.from_repeated()` factory for regular dosing regimens; route consistency validation
- `sim/models.py` — `OneCompartmentModel` and `TwoCompartmentModel` frozen dataclasses; route-aware parameter validation (IV uses CL/Vz, oral uses CL_F/Vz_F); `half_life` property; `param_dict()` for reporting
- `sim/simulate.py` — `simulate(model, regimen, times)` entry point; per-dose analytical superposition; supports 1-cmt IV bolus, 1-cmt IV infusion, 1-cmt oral, 2-cmt IV bolus, 2-cmt oral; pre-dose warning
- `sim/results.py` — `SimulationResult` dataclass with `Cmax`/`Tmax` properties, `summary()`, `to_dataframe()`, `to_dict()`, `plot()`, `report(format=...)` methods
- `sim/plotting.py` — `pk_profile_plot_b64()`: base64-encoded PNG of PK profile with optional dose-time markers (matplotlib Agg backend)
- `sim/reporting.py` — `report_simulation()` dispatcher; HTML and Markdown renderers; PDF and DOCX dispatch to `report/pdf.py` and `report/docx.py`
- `report/templates/sim_report.html` — dark-navy header, 4-metric highlight cards, embedded PK plot, model/regimen side-by-side cards, data table (capped at 200 rows), warnings, disclaimer
- `render_sim_pdf_report()` in `report/pdf.py` — ReportLab PDF for simulation reports
- `render_sim_docx_report()` in `report/docx.py` — python-docx Word document for simulation reports
- 46 new tests across `tests/sim/`: `test_methods.py` (degenerate + textbook-cited reference cases for all 5 analytical functions + superpose), `test_simulate.py` (1-cmt and 2-cmt simulate, SimulationResult helpers, HTML/MD report), `test_roundtrip_nca.py` (simulate -> NCAStudy -> recover CL, Vz, CL_F, Vz_F, t1/2 within 2%)

### Implementation notes
- Analytical equations follow Gibaldi & Perrier, Pharmacokinetics 2nd ed. (1982); round-trip NCA tests cite Rowland & Tozer, Clinical Pharmacokinetics 4th ed. (2011)
- CL/V parameterization throughout (k is derived, not primary); oral uses apparent parameters (CL_F, Vz_F) consistent with NCA module output
- 2-cmt IV infusion deferred to v0.5.1 (not yet implemented in TwoCompartmentModel)
- Population simulation deferred to v0.6.0 per release ladder

## [0.4.1] — 2026-05-18

### Added
- `render_nca_single_pdf_report()` in `report/pdf.py` — ReportLab PDF for per-subject NCA results; study parameters table, PK parameters table, optional warnings section, disclaimer
- `render_nca_summary_pdf_report()` in `report/pdf.py` — ReportLab PDF for multi-subject NCA summary; 9-column subject table fitted to letter-width, optional study parameters block, disclaimer
- `render_nca_single_docx_report()` in `report/docx.py` — python-docx Word document for per-subject NCA; study and PK parameter tables, warnings list, italic disclaimer
- `render_nca_summary_docx_report()` in `report/docx.py` — python-docx Word document for multi-subject NCA summary; study info block, 9-column subject table, italic disclaimer
- `NCAResult.report(format="pdf"|"docx")` and `NCASummaryResults.report(format="pdf"|"docx")` — PDF and Word export from NCA results
- `report_nca_single(format="pdf"|"docx")` and `report_nca_summary(format="pdf"|"docx")` dispatch arms in `nca/reporting.py`
- 26 new tests in `tests/nca/test_nca_pdf_docx.py`: magic-byte assertions, file-write, None lambda_z, warnings section, full dispatch-chain, disclaimer round-trip via zipfile

### Changed
- `report_nca_single()` and `report_nca_summary()` docstrings updated; `NotImplementedError` stubs replaced with live dispatch
- `NCAResult.report()` and `NCASummaryResults.report()` docstrings extended to include pdf/docx options
- `report/docx.py` gains `TYPE_CHECKING` import block for NCA types (avoids circular import at runtime)
- `docs/logo.png` added — official OpenPKFlow logo

### Implementation notes
- Renderers follow the same lazy-import pattern as dissolution PDF/DOCX; module top is stdlib only
- Route-aware parameter labelling: oral subjects show CL_F/Vz_F; IV subjects show CL/Vz
- None fields (lambda_z, AUCinf_obs, half_life) formatted as "N/A" via inline `_fmt()` helper

## [0.4.0] — 2026-05-18

### Added
- `nca/methods.py` — pure-math NCA layer: `auc_linear`, `auc_log`, `auc_linear_up_log_down` (linear-up/log-down), `cmax`, `tmax`, `lambda_z` (BAR² auto-selection and manual mode), `auc_inf_obs`, `auc_percent_extrapolated`, `clearance_volume_parameters`; `AUCResult` and `LambdaZResult` frozen dataclasses
- `nca/loader.py` — `load_nca_csv()`: CSV loader with full BLQ handling (none/drop/zero/half_lloq/lloq, m1/m2 aliases, `<0.5` string-BLQ parsing via regex)
- `nca/results.py` — `NCAResult` (per-subject) and `NCASummaryResults` dataclasses with `summary()`, `to_dict()`, `to_dataframe()`, `report()` methods; route-aware field naming (oral: CL_F/Vz_F, IV: CL/Vz)
- `nca/study.py` — `NCAStudy` with `__init__(df, ...)`, `from_csv(path, ...)`, and `analyze() -> NCASummaryResults`; explicit auc_method required; lambda_z failure handled gracefully (None + warning)
- `nca/reporting.py` — `report_nca_single()` and `report_nca_summary()` in HTML (Jinja2) and Markdown; PDF/DOCX deferred to v0.4.1
- `report/templates/nca_single_report.html` — per-subject NCA HTML report with navy header, PK parameter table, warnings panel, disclaimer
- `report/templates/nca_summary_report.html` — multi-subject summary HTML report with tabular results
- `datasets/theoph.csv` — R nlme::Theoph reference dataset (12 subjects, 11 timepoints, oral theophylline, doses precomputed in mg)
- `datasets/__init__.py` — adds `example_theoph_path()`
- 93 NCA tests: `tests/nca/test_methods.py` (unit tests for all math functions with hand-checked expected values), `test_loader.py` (BLQ handling, edge cases), `test_study.py` (integration), `test_theoph_reference.py` (regression suite against Theoph dataset)

### Changed
- `nca/__init__.py` wired up to export all public NCA symbols
- `datasets/__init__.py` adds `example_theoph_path()` to `__all__`

### Implementation notes
- AUC dispatch asymmetry: `auc_linear` returns `float`; `auc_log` and `auc_linear_up_log_down` return `AUCResult` — handled in NCAStudy.analyze()
- BAR² lambda_z algorithm: enumerates all tail windows anchored at last quantifiable point, post-Cmax positive only, selects by adjusted R² descending then more points then longer span (mirrors PKNCA R package)
- NaN handling contract: loader cleans arrays; AUC math functions assume clean input
- Theoph regression values: AUClast mean ~100.1, Cmax mean ~8.89, half_life mean ~7.89 h — linear_up_log_down, no BLQ handling

## [0.3.0] — 2026-05-18

### Added
- `render_comparison_pdf_report()` in `report/pdf.py` — ReportLab PDF for dissolution comparison; navy-header table, embedded profile plot, disclaimer
- `render_model_fit_pdf_report()` in `report/pdf.py` — ReportLab PDF for model fit; ranked table with gold best-row highlight, fit overlay plot, dual disclaimer
- `render_comparison_docx_report()` in `report/docx.py` — python-docx Word document for dissolution comparison; summary + data tables, embedded plot, italic disclaimer
- `render_model_fit_docx_report()` in `report/docx.py` — python-docx Word document for model fit; ranked table with bold best row, failed-models note, fit overlay plot, dual disclaimer
- `ComparisonResult.report(format="pdf"|"docx")` — PDF and Word export from study comparison
- `DissolutionFitResults.report(format="pdf"|"docx")` — PDF and Word export from model fitting
- `report_dissolution(format="pdf"|"docx")` dispatcher arms in `dissolution/reporting.py`
- CLI format inference: `.pdf` -> `"pdf"`, `.docx` -> `"docx"` (in addition to existing `.md` -> `"markdown"`, else `"html"`)
- 19 new tests in `tests/report/test_pdf.py` and `tests/report/test_docx.py`: magic-byte assertions, file size, `tmp_path` write, round-trip disclaimer check via python-docx, `pytest.importorskip` skip guard

### Changed
- CI matrix now installs `.[dev,reports]` so reportlab and python-docx are available in test runs
- `DissolutionFitResults.report()` return type widened to `str | bytes`
- `ComparisonResult.report()` and `report_dissolution()` return type widened to `str | bytes`

### Implementation notes
- Both renderers use lazy imports inside function bodies; module top is stdlib only
- Import guard raises `ImportError("... pip install openpkflow[reports]")` if extra not installed
- Plot embedding: `base64.b64decode(plot_b64)` -> `io.BytesIO` -> `Image`/`add_picture`
- All docstrings ASCII-only; rendered document content may use unicode

## [0.2.0] — 2026-05-18

### Added
- `DissolutionStudy.fit_models(formulation, models=None)` — fits one or more standard release models to the mean profile of a formulation; returns `DissolutionFitResults`
- `fit_dissolution_models(time_points, observed_mean, formulation_label, models=None)` — low-level public API for fitting without a loaded CSV
- Five dissolution release models: `zero_order`, `first_order`, `higuchi`, `korsmeyer_peppas`, `weibull`
- `ModelFit` frozen dataclass — fit result per model: params, R2, AIC, AICc, BIC, converged flag, `predict()`, `to_dict()`
- `DissolutionFitResults` dataclass — ranked fit container: `.best` (lowest AICc), `.summary()`, `.plot()`, `.report()`, `.to_dict()`
- `DissolutionFitResults.plot()` — overlay plot of observed mean + fitted curves, ranked by AICc
- `DissolutionFitResults.report("fit.html")` — HTML report with fit table, overlay plot, and regulatory disclaimer
- `dissolution_fit_plot_b64()` in `plotting.py` — base64 PNG for HTML report embedding
- `render_model_fit_html_report()` in `report/html.py` — Jinja2 renderer for `fit_report.html`
- `report/templates/fit_report.html` — navy-header HTML template matching existing dissolution report style
- Korsmeyer-Peppas 60% rule: `UserWarning` when >1 timepoint exceeds 60% release
- Weibull empirical-model note added to report and docstring per FDA/EMA guidance
- All five models exported from `openpkflow.dissolution`: `ModelFit`, `DissolutionFitResults`, `fit_dissolution_models`

### Implementation notes
- Models fitted to mean profile; per-vessel fitting is future scope
- Model ranking by AICc, the small-sample-corrected information criterion; AIC and BIC also returned
- R2 reported for familiarity but not used for selection — it is misleading for nonlinear models
- Each model has data-driven initial-guess and bounds helpers to prevent degenerate fits
- Failed fits included in results with `converged=False`; excluded from ranking and plots
- Reference: Costa P, Lobo JMS (2001) Eur J Pharm Sci 13(2):123-133. DOI: 10.1016/S0928-0987(01)00095-1

## [0.1.4] — 2026-05-18

### Added
- `DissolutionStudy.bootstrap_compare(reference, test, ...)` — runs bootstrap f2 directly from loaded CSV data
- `ComparisonResult.plot(output_path, show)` — plots reference vs test profile with f1/f2 in title
- `demo.ipynb` rewritten: only openpkflow imports, clean 7-section workflow

## [0.1.3] — 2026-05-18

### Added
- `f2(method="regulatory")` option — trims timepoints per the FDA 85% rule; at most one timepoint where both profiles exceed 85% may be included; raises ValueError if fewer than 3 points remain
- CV% warning in `DissolutionStudy.compare()` — warns when coefficient of variation exceeds FDA limits: CV > 20% at early timepoints (<=15 min) or CV > 10% at later timepoints

### Changed
- README: removed em dashes and minimised parentheses; updated status table to reflect v0.1.1 deliverables; softened validation claims
- 78 tests passing

## [0.1.2] — 2026-05-18

### Added
- PyPI Trusted Publishing via GitHub Actions (`publish.yml`) — triggers on version tags, publishes to TestPyPI then PyPI using OIDC (no stored tokens)

## [0.1.1] — 2026-05-18

### Added
- `dissolution.bootstrap_f2()` — bootstrap CI for f2 (Shah 1998, Davit 2013); suitable for small-sample (<12 vessel) similarity assessment
- `dissolution.plotting.dissolution_profile_plot_b64()` — embedded matplotlib profile plot in HTML reports
- HTML reports now include a dissolution profile chart (reference vs test, 85% threshold line)
- `datasets.example_similar_path()` — example dataset with f2 ~80 (clearly similar profiles)
- `datasets.example_not_similar_path()` — example dataset with f2 ~38 (clearly dissimilar profiles)
- `py.typed` marker (PEP 561) — enables mypy type checking in downstream projects
- GitHub Actions CI — matrix build across Python 3.10, 3.11, 3.12

### Changed
- `datasets/__init__.py` — constants replaced with `example_dissolution_path()`, `example_similar_path()`, `example_not_similar_path()` functions using `importlib.resources`
- CLAUDE.md — added Commands section, data flow diagram, Windows ASCII constraint note

## [0.1.0] — 2026-05-17

### Added
- `dissolution.f1()` — difference factor (FDA/EMA dissolution guidance)
- `dissolution.f2()` — similarity factor (FDA/EMA dissolution guidance)
- `dissolution.DissolutionProfile` — validated data container for a single dissolution profile
- `dissolution.DissolutionStudy` — high-level study object: load CSV, compare, fit, report
- `dissolution.loader` — CSV ingestion with schema validation
- `dissolution.reporting` — Markdown and HTML report generation
- CLI command `openpkflow similarity` for f1/f2 from terminal
- CLI command `openpkflow version`
- Example dataset `datasets/example_dissolution.csv`
- Example script `examples/dissolution_basic.py`
- Full test suite with reference validation examples

### Notes
- f1/f2 require caller to supply matched, time-aligned percent-release values
- No external GUI or enterprise platform connectivity in this release
- Disclaimer: open-source research workflow; final regulatory interpretation requires expert review
