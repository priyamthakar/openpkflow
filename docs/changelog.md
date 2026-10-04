# Changelog

All notable changes to OpenPKFlow will be documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [2.9.0] -- 2026-10-04

Correctness and validation release. It fixes two Advanced Dissolution Workbench
decisions that could report "supports similarity" incorrectly, makes BE power
exact, aligns lambda_z selection with PKNCA and WinNonlin, and adds an NCA CLI.

### Migration notes

- Workbench API: `alternatives.chi2_05_critical` is replaced by MSD CI and
  limit fields, and the MSD fields are `null` when MSD is not evaluable (too few
  vessels or a singular covariance). The three bundled 3-vessel examples are
  not evaluable for MSD.
- `lambda_z` can select more points than before on some profiles; use
  `adj_r2_tolerance=0` to reproduce v2.8.0.
- `msd()` on mean profiles warns; use `msd_vessels()` with vessel data.

### Added

- **`openpkflow nca run`**: command-line NCA over a CSV with required
  `--auc-method` and `--blq-method` (no silent defaults), optional `--tau`
  for steady state, and `--report` (HTML/Markdown/PDF/DOCX), `--csv` and
  `--cdisc-pp` outputs.
- **`msd_vessels()`**: vessel-level Mahalanobis distance with pooled
  covariance and the Tsong et al. (1996) 90% Hotelling region against a
  per-timepoint similarity limit. Cross-validated against `disprofas::mimcr()`
  on six cases, including its documented example
  (`scripts/disprofas_msd_crossval.R`).
- **`lambda_z(adj_r2_tolerance=..., include_tmax=...)`**: the PKNCA
  adjusted-R2 tolerance (default 1e-4) and an opt-in Phoenix WinNonlin IV-bolus
  convention that lets the Cmax sample into the terminal window.
- **Workbench MSD settings**: `msd_similarity_limit_pct` (10% default, up to
  15%) in the library, API and UI, plus the vessel count MSD needs.
- **Paste grid controls** on every web page: row-range selection with bulk
  delete, Ctrl/Cmd+D fill down, Clear, and resizable columns.

### Changed

- **lambda_z auto-selection uses PKNCA's adjusted-R2 tolerance**: windows within
  1e-4 of the best adjusted R2 are treated as equal and the one with the most
  points wins (previously only an exact tie). Pass `adj_r2_tolerance=0` for the
  old rule. Pinned against PKNCA `pk.calc.half.life()`; the WinNonlin reference
  test now covers all 12 Theoph and 6 Indometh subjects with no exclusions.
- **BE power is exact**: `be_tost_power()` integrates Owen's Q and matches
  PowerTOST `power.TOST(method="exact")` to 1e-9. The previous non-central t
  approximation returned 0 at low power (small n or high CV). Sample-size
  results can change by one step where the approximation was off.
- **Sparse NCA AUClast** is the analytic integral of the fitted curve from 0 to
  the last sample instead of a trapezoid over the sparse fitted points.
- **Bootstrap f2 note** points to high variability as the reason to use it and
  warns only below the 12 units per product of FDA (1997), instead of warning
  at 12 or more vessels.

### Fixed

- **Workbench MSD always reported "supports similarity"**: the mean-profile
  `msd()` divided the differences by their own variance, so MSD squared was
  identically n - 1 and below the chi-squared critical value for any pair of
  profiles. The workbench now uses the new vessel-level `msd_vessels()`
  (pooled covariance, Tsong et al. 1996 90% Hotelling region vs. a 10%
  per-timepoint similarity limit) on the same timepoints as f2, and reports
  "not evaluable" when there are too few vessels or the covariance is singular.
  `msd()` now emits a `UserWarning`. `msd_vessels()` is cross-validated against
  `disprofas::mimcr()` (six cases including its documented example) via
  `scripts/disprofas_msd_crossval.R`.
- **Workbench bootstrap f2 ignored the FDA 85% rule**: with the default
  `f2_method="regulatory"`, point f2 used the trimmed timepoints but the
  bootstrap resampled all of them, so plateau points could push the CI above 50
  while point f2 failed. `bootstrap_f2()` and
  `DissolutionStudy.bootstrap_compare()` gain `f2_method`.
- **Log trapezoid precision**: `(c1 - c2) / ln(c1/c2)` lost precision to
  cancellation when consecutive concentrations were nearly equal, breaking
  AUC scale-linearity; it now uses a stable `expm1`/`log1p` form there.
- **BE power fixtures**: the stored PowerTOST sample-size scenario 4 power
  (0.8652) was the approximation's value; regenerated fixtures use PowerTOST's
  0.8675705.
- **NCA study aborted on an all-BLQ subject**: a subject with no quantifiable
  concentration (or only the first sample quantifiable) raised and stopped the
  whole study. AUClast is now 0 with a warning.
- **Sparse NCA silently returned an unconverged fit** when the default initial
  guess fell outside the parameter bounds; the guess is now clipped into the
  bounds. `SparseNCAResult.plot()` also closes saved figures.
- **API report endpoints** used race-prone `tempfile.mktemp` and leaked the
  output file when report generation failed; they now use a private `mkstemp`
  path that is removed on failure.

---

## [2.8.0] -- 2026-07-30

This additive release turns the independently validated dissolution methods
into one report-first, auditable workflow. It adds no new dissolution formula.

### Added

- Advanced Dissolution Workbench for vessel-level f1/f2, bootstrap f2,
  five-model AICc ranking, model-dependent comparison, MSD, and maximum
  deviation.
- Complete HTML, PDF, and DOCX reports with plots, normalized inputs, exact
  configuration, warnings, and the required expert-review disclaimer.
- Reproducibility ZIP containing normalized CSV input, configuration,
  serialized results, HTML report, and a SHA-256 manifest.
- Three typed FastAPI endpoints and an editable upload/paste React workbench
  with report and audit downloads.
- Core, API, and Playwright regression coverage for calculations, fail-closed
  inputs, reports, uploads, and bundle integrity.

### Changed

- In-memory dissolution validation rejects non-finite time and release values.
- The API inventory increases from 29 to 32 endpoints.

---

## [2.7.1] -- 2026-07-28

This reliability release adds deployment provenance and closes the remaining
v2.7.0 web regression gaps. It does not change pharmacometric calculations or
public Python APIs.

### Added

- `/health` now reports engine version, deployed Git commit and branch, and the
  Render service identifier.
- A scheduled/manual production convergence workflow verifies both `/health`
  and `/openapi.json`, with optional commit-prefix matching.
- Playwright coverage protects chart legend restoration, PNG export, persisted
  sidebar collapse, and mobile navigation.

### Changed

- The shared `EmptyResults` state is used consistently across the remaining
  analysis result panes.
- The API deployment floor is updated to FastAPI 0.140.

### Documentation

- Synchronized the README, handoff, agent guidance, release workflow, web/API
  progress, dated session summary, roadmap, and future plans to the verified
  published state and the gated v2.8.0 dissolution milestone.
- Recorded production convergence: Cloudflare frontend and documentation are
  current, while Render reports v2.7.1 at release commit `d24263d`; the automated
  health/OpenAPI smoke check passes.
- Synchronized the API endpoint and web-page inventories and corrected the
  validated FDA partial-replicate RSABE scope.

---

## [2.7.0] -- 2026-07-25

This additive release publishes the validated post-v2.6.0 work across the Python
package, REST API, and web application. No existing public API was removed.

### Added

- **Pipeline audit bundle**: core ZIP export containing normalized inputs,
  configuration, serialized results, HTML report, and SHA-256 manifest.
- **Pipeline API**: analyze, report, and audit-bundle FastAPI endpoints with
  schemas, adapter service, registration, and regression tests.
- **Pipeline web workflow**: React page for optional dissolution, NCA, and paired-BE
  stages with unified results, report downloads, and reproducibility audit ZIP export.
- **Sparse NCA validation and reports**: fail-closed one-compartment oral fitting,
  independent R `stats::nls` cross-validation on published `nlme::Theoph` data, and
  HTML/Markdown screening reports.
- **Sparse NCA web workflow**: analyze and report API endpoints plus a React page with
  a published example, fit diagnostics, observed/fitted visualization, and explicit
  model-informed screening scope.
- **MAP individual PK**: FastAPI analyze/report endpoints and a React workflow for
  oral and IV-bolus MAP screening with fit diagnostics and downloadable reports.
- **SUPAC and alcohol screening**: API and web workflows for SUPAC-IR classification
  and alcohol dose-dumping f2 assessment.
- **Formal complete balanced 2x2 BE ANOVA**: long-format TR/RT analysis with a full
  ANOVA table, reports, CLI/API/web interfaces, fail-closed design checks, and an
  independent R cross-check.
- **FDA partial-replicate RSABE**: balanced TRR/RTR/RRT analysis validated against
  Patterson and Jones (2012), Table II. The workflow combines the scaled criterion
  upper bound, point-estimate constraint, and conventional ABE fallback.
- **Web application polish**: theme-aware chart colors, chart toolbar and PNG export,
  grouped collapsible navigation, persisted split-pane width, run shortcuts, improved
  empty states, and visible backend health status.
- **Production deployment wiring**: Cloudflare Workers frontend and Render
  backend configuration. The frontend deploys automatically from `main`; as of
  2026-07-26, the reachable Render service still reports engine version 2.6.0
  and requires a manual deployment/configuration check for v2.7.0.

### Fixed

- The AUC scale-invariance property test now excludes unrepresentable subnormal
  scaling and explicitly covers IEEE-754 underflow at the smallest positive float.
- Compatible React Router, PostCSS, Nano ID, and brace-expansion lockfile updates
  address the available dependency advisories.
- Chart legend restoration, PNG export colors and target selection, mobile drawer
  labels, dark-mode form controls, and light-theme primary-button contrast.

---

## [2.6.0] -- 2026-07-15

The released build passed the full standard suite (1275 passed), API tests,
frontend lint/build/browser tests, strict docs build, mypy, wheel/sdist
validation, Trusted Publishing, and a fresh-install CLI smoke check.

### Release hardening

- CI now runs API, frontend, Python 3.13 Linux/Windows smoke, and enforced
  type-check jobs; Codecov uploads are confirmed working.
- API uploads use bounded reads and responses include standard security headers.
- Fixed full-Omega label generation for population PK models.
- Student dissolution comparison results are typed and PK route handling now
  fails closed instead of treating unknown routes as IV bolus.
- Strict mypy is enforced outside the explicitly frozen legacy estimator.

### Fixed

- BE paired-design intra-subject CV variance-halving before CV back-transform.
- NCA/pipeline fail-closed config validation; stricter BLQ and `auc_tau` handling.
- Sim transit model rebuilt on the Savic absorption-chain structure.
- IVIVC unit conversion, dissolution-rescale, and single-formulation verdict fixes.
- Dissolution `f2_method` now defaults explicitly to `regulatory`; ICH M13B
  Step 2 absolute-SD check.
- SUPAC-IR function-specific threshold tables.
- Webapp stale-result guard extended to BE, Dissolution, and Sim pages.
- `publish.yml` now requires a tag's commit to be reachable from `main`.

### Added

- Study pipeline package and CLI (`openpkflow study run`) with multi-section reports.
- SUPAC-IR screening and alcohol dose-dumping f2 assessment helpers.
- IVIVC Level B/C MDT/MRT correlation helpers.
- Transit-compartment oral absorption and 1-cmt oral steady-state metrics.
- Webapp: BE power calculator, multi-media dissolution tab, IVIVC example loader.
- IVIVC convolution analytical validation tests; BE power edge-case tests.
- Positioning page and pipeline tutorial.

---

## [2.4.0] -- 2026-05-30

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
- `nca/sparse.py` -- `fit_sparse_1cmt_oral()`: model-informed oral PK from 3+ samples,
  fitted in concentration space with explicit convergence status
- `nca/sparse.py` -- `SparseNCAResult`: model-informed estimates, diagnostics,
  derived parameters, plots, and HTML/Markdown reports
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
