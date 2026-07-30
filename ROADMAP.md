# OpenPKFlow Roadmap (post-1.0.0)

## North star

OpenPKFlow owns the **formulation-to-regulatory-submission pipeline** in open-source Python:
dissolution -> IVIVC -> NCA -> BE -> reports. Not another NLME engine — those exist.
The gap we fill is the CRO/CDMO bench scientist who needs clean, auditable, shareable outputs
without WinNonlin or a SAS programmer.

OpenPKFlow owns paired TOST convenience analysis, formal complete balanced TR/RT
2x2 crossover ANOVA, and FDA partial-replicate RSABE (validated against Patterson &
Jones 2012). EMA ABEL, full-replicate RSABE, and unvalidated formal designs remain
out of scope.

---

## Greenfield differentiators (near-zero open-source Python competition)

| Capability | Status in open-source Python |
|---|---|
| IVIVC (Level A: deconvolution + convolution prediction) | OpenPKFlow ✅ |
| Mahalanobis Statistical Distance (MSD) / f2 alternatives | OpenPKFlow ✅ |
| Multi-media dissolution (ICH M13A/B, alcohol dose-dumping) | OpenPKFlow ✅ |
| Steady-state NCA + urinary excretion | OpenPKFlow ✅ |
| Formal complete balanced 2x2 ANOVA | OpenPKFlow: implemented with independent R cross-check ✅ |
| FDA partial-replicate RSABE | OpenPKFlow: implemented, validated against Patterson & Jones (2012) Table II ✅ |
| CDISC PP / ADPPK-compliant PK parameter output | OpenPKFlow ✅ |
| Sparse oral PK (model-informed fit from 3+ samples) | OpenPKFlow ✅ screening |

---

## Milestones

### v1.1.0 -- Dissolution regulatory toolkit (target: ~2 weeks)

Scope: expand `dissolution/` with FDA/EMA-accepted f2 alternatives. No new module.

- `msd()` -- Mahalanobis Statistical Distance (FDA PSA guidance 1999) ✅
- `model_dependent_comparison()` -- compare fitted dissolution model parameters via 90% CI ✅
- `maximum_deviation()` -- another FDA-accepted alternative metric ✅
- ICH M13B RSD constraint check: RSD > 8% at early time points -> `UserWarning` ✅
- New tests: degenerate + published-reference citations for each metric (~20 tests)
- Report: `MSDResult` object, `report()` dispatch added to `dissolution/reporting.py`

Definition of done: all new functions have NumPy docstrings, ASCII-only CLI output,
degenerate + reference test, disclaimer in generated reports, mypy strict clean.

---

### v1.2.0 -- IVIVC Level A (target: ~6 weeks) ✅ DONE

Scope: new `ivivc/` module. Level A only. Predictability assessment included.
Level B/C and adaptive IVIVC deferred.

- `wagner_nelson()` -- deconvolution of in vivo absorption fraction from plasma data ✅
- `loo_riegelman()` -- two-compartment deconvolution ✅
- `convolution_predict()` -- predict in vivo profile from in vitro dissolution + unit impulse response ✅
- `levy_plot()` -- IVIVC correlation plot with regression overlay ✅
- `ivivc_predictability()` -- %PE for Cmax and AUCinf (<15% FDA acceptance criterion) ✅
- `IVIVCResult` dataclass with `summary()`, `plot()`, `report()` methods ✅
- HTML/Markdown/PDF/DOCX reports following existing template style ✅
- New `openpkflow ivivc` CLI command ✅
- Tests: 45 new tests, Wagner-Nelson hand-checked against Gibaldi & Perrier reference ✅

---

### v1.3.0 -- NCA expansion: steady-state + urinary excretion ✅ DONE

Scope: expand `nca/` module. Sparse NCA moved to future milestone.

- Steady-state NCA: `AUCtau`, `Cmax_ss`, `Cmin_ss`, `Cavg_ss`, fluctuation, swing, accumulation ratio ✅
- Urinary excretion PK: `Ae`, `Ae_pct`, `CLr` -- urine volume/concentration column support ✅
- `%AUCextrap` flag: warn if >20% (FDA criterion), add to `NCAResult` and reports ✅
- Lambda_z quality metrics: adjusted R2, n points used ✅
- CDISC PP-format output: `NCASummaryResults.to_cdisc_pp()` -> DataFrame with CDISC PP variable names ✅
- Dose-normalised parameter tables: DN-AUC, DN-Cmax in summary reports ✅
- Tests: 26 new tests ✅

---

### v1.4.0 -- Multi-media dissolution ✅ DONE

Scope: expand `dissolution/` module.

- `MultiMediaStudy` — accepts `{media_name: csv_path}` dict, wraps `DissolutionStudy` instances ✅
- `MultiMediaResult` — per-medium f2 grid, overall PASS/FAIL verdict, `.summary()`, `.report()`, `.plot()` ✅
- `multi_media_report.html` — summary grid + per-medium detail sections + multi-panel plot ✅
- HTML/PDF/DOCX reports following existing template style ✅
- Tests: 26 new tests ✅

---

### v1.5.0 -- Sparse NCA ✅ DONE

Scope: model-informed AUC from limited sampling (2-5 samples).

- `fit_sparse_1cmt_oral()` — fits 1-cmt oral model via scipy curve_fit ✅
- `SparseNCAResult` — CL_F, Vz_F, ka, AUCinf, Cmax, Tmax, half-life, standard errors ✅
- `sparse_nca_bias_analysis()` — pct bias vs rich-sampling reference ✅
- Handles 3-data-point minimal sampling, non-convergence gracefully ✅
- Tests: 16 new tests ✅

---

### v2.0.0 -- Bayesian PK ✅ DONE

Scope: `bayes/` module. Architecture Decision Record: `V2_ARCHITECTURE_DECISION.md`.

**Phase 1 -- MAP (scipy, zero new dependencies):**
- `PKPrior` frozen dataclass: log-normal priors for CL, Vz, ka, sigma with bounds ✅
- `map_individual_pk()`: L-BFGS-B in log-space, proportional error model, 3-start multi-start ✅
- 10 fail-closed diagnostics: convergence, gradient norm, Hessian PD, condition number,
  at-bound, multi-start agreement, prior-dominance ✅
- `MapPKResult`: MAP estimates + delta-method SEs (inverse Hessian), derived PK parameters ✅
- HTML report template: 4 diagnostic cards, parameter table, concentration-time profile ✅
- 35 tests ✅

**Phase 2 -- Full posterior + Bayesian BE (`[bayes]` extra, PyMC >= 5.0):**
- `bayes_individual_pk()`: PyMC Metropolis sampler; numpy PK model wrapped as pytensor `as_op`;
  shrinkage estimation; ESS check via arviz ✅
- `bayes_be()`: PyMC NUTS on log-scale linear mixed model (2x2 crossover); fixed effects for
  sequence/period/treatment; non-centered random subject effect; P(0.80 <= GMR <= 1.25);
  frequentist 90% CI side-by-side; R-hat + ESS convergence diagnostics ✅
- HTML report templates: GMR posterior histogram, Bayesian vs frequentist comparison table ✅
- 26 tests (non-PyMC validation tests run without `[bayes]` extra) ✅

**Also shipped:**
- `DissolutionStudy.from_excel()` + `load_dissolution_excel()` (openpyxl, `[reports]` extra) ✅
- Codecov integration with project/patch coverage thresholds ✅
- GitHub Pages docs site activated ✅

**Not in v2.0.0:** full FOCE-I/SAEM population estimation (reserved for v2.1.0).

---

### v2.1.0 -- FOCE-I & SAEM Population PK ✅ DONE (2026-05-23)

Scope: new `pop/estimation/` sub-package. Two-tier architecture matching `bayes/` pattern.
1-cmt models (oral + IV bolus), diagonal Ω, combined error.

**Architecture:** `pop/estimation/` sub-package (11 files, ~4,500 lines).

- `PopPKModel` frozen dataclass: structural + statistical model, `to_theta()`/`from_theta()` pack/unpack ✅
- `run_foce_i()`: scipy tier (zero new deps), L-BFGS-B outer loop, per-subject EBE inner loop,
  FOCE-I linearized -2LL, 10 fail-closed diagnostics from `bayes/map_pk.py` ported ✅
- `run_saem()`: PyMC tier (`[bayes]` extra), Metropolis S-step, Robbins-Monro SA-step with γ=1/k^α,
  analytical M-step, numpy MCMC fallback, `_require_saem()` import guard ✅
- `PopPKResult` dataclass: `.summary()`, `.to_dataframe()`, `.to_dict()`, `.plot()`, `.report()` ✅
- 6-panel pop PK diagnostic plot: OBS vs PRED/IPRED, CWRES vs TIME/PRED, EBE histograms + pairs ✅
- HTML/Markdown reports with embedded plots, parameter tables, warnings, disclaimer ✅
- CLI: `openpkflow pop foce-i` and `openpkflow pop saem` (Typer subcommands) ✅
- Tests: 47 new tests (model, diagnostics, objective, FOCE-I integration, SAEM integration) ✅

**Deferred to v2.2.0:** 2-cmt models, full Omega block matrix, PDF/DOCX reports.
Covariate skeleton APIs briefly shipped in v2.2.0 but were removed in v2.3.0 because
they did not affect estimation.

---

## v2.5.0 -- Reactive Web Application (2026-05-31)

Scope: new `api/` (FastAPI) and `webapp/` (React + Vite + Tailwind) at repo root.
The library is **not modified** -- the web layer calls existing validated public APIs.

- FastAPI backend: `/api/nca/*`, `/api/dissolution/*`, `/api/sim/*`, `/health` ✅
- React frontend: dark enterprise theme (Linear/Sentry aesthetic), side-nav layout ✅
- NCA page: CSV upload, column mapping, AUC/Cmax/Tmax/t1/2 metric cards, per-subject
  concentration-time chart, linear/semi-log toggle, report download ✅
- Dissolution page: formulation dropdowns, f1/f2 comparison, overlaid profile chart
  with 85% threshold line, regulatory warning surface, report download ✅
- Sim page: interactive sliders for all PK params (1-/2-cmt, oral/IV/infusion),
  debounced live chart, Cmax/Tmax/Cmin/Clast metric cards, report download ✅
- 16 backend golden + error tests; production build clean ✅
- CLAUDE.md updated with scope ratification note ✅

**Anti-drift guarantee:** all pharmacometric numbers originate from `src/openpkflow/`
via the FastAPI adapters. The frontend never computes pharmacometric values.

---

## v2.6.0 -- Study pipeline + science helpers + web polish (2026-07-09)

Scope: multi-track improvement sprint. Library code merged via PR #27, followed by
the correction and release-hardening work merged via PR #29. v2.6.0 was tagged and
published to PyPI on 2026-07-15.

### Library

- `pipeline/` -- `StudyPipeline`, `PipelineConfig`, multi-section HTML/Markdown reports ✅
- CLI: `openpkflow study run config.json --report out.html` ✅
- `dissolution/supac.py` -- SUPAC-IR level screening + alcohol dose-dumping f2 assessment ✅
- `ivivc/level_bc.py` -- MDT, MRT, Level B/C linear correlation ✅
- `sim`: `c_1cmt_oral_transit`, `steady_state_metrics_1cmt_oral` ✅
- Validation: IVIVC convolution analytical reference; BE power edge cases ✅

### Web layer

- BE power / sample-size API + calculator tab ✅
- Multi-media dissolution API + Dissolution page tab ✅
- IVIVC load-example + dose_diss / dose_iv UI ✅
- Playwright smoke coverage expanded ✅

### Docs / DX

- `docs/positioning.md`, `docs/tutorials/pipeline.md` ✅
- Docker / docker-compose polish; pipeline examples ✅
- HANDOFF.md / AGENTS.md / CLAUDE.md updated for takeover ✅

### Post-v2.6.0 follow-ups

- Formal BE ANOVA ✅ implemented in OpenPKFlow with independent R cross-check
- FDA partial-replicate RSABE ✅ implemented, validated against Patterson & Jones
  (2012) Table II (DOI 10.1002/pst.498), and wired into `api/`/`webapp/`
  (`/api/be/rsabe/*`, `/be/rsabe` page). Requires balanced sequence allocation;
  unbalanced/dropout data fails closed rather than being analyzed.
- Pipeline page in React webapp ✅ merged in PR #30
- Sparse NCA API/page ✅ merged in PR #31 (`74c070b`)
- MAP PK API/page ✅ merged in PR #32 (`486788c`) with SUPAC/alcohol screening UI
- Formal BE ANOVA API/page ✅ merged in PR #32 (`486788c`)
- Frontend design system polish + mobile pass ✅ merged in PR #33 (`bb0d16a`)
- Hosted production services: Cloudflare Workers frontend is current; the Render
  backend is reachable but still reports engine version 2.6.0 and requires a
  manual deployment/configuration check before v2.7.0 convergence; URLs and gate
  are in `HANDOFF.md`
- Extending frozen `pop/estimation/` — out of scope, not a follow-up (see CLAUDE.md)

### v2.7.0 release (published 2026-07-25)

- Pipeline audit ZIP, FastAPI endpoints, and React page: merged in PR #30.
- Sparse NCA validation/API/page: merged in PR #31.
- Formal BE ANOVA, RSABE gate, MAP PK hardening, SUPAC/alcohol hardening: merged in
  PR #32 (`486788c`).
- Frontend design system polish, three PKChart defect fixes, and mobile/Android pass:
  merged in PR #33 (`bb0d16a`).
- FDA partial-replicate RSABE implemented and validated in `be/rsabe.py` against
  Patterson & Jones (2012) Table II, and wired into `api/` (`/api/be/rsabe/analyze`,
  `/api/be/rsabe/report`) and `webapp/` (`/be/rsabe` page); a `/code-review high`
  pass caught and fixed a `delta_hat` bias for unbalanced sequence allocation
  before merge. Merged in PR #35 (`f041b10`).
- Release hardening fixed the subnormal-float property-test boundary, synchronized
  validation and takeover docs, and passed the complete package/API/web/docs/build
  gate. Release PR #39 was squash-merged as `74039b4`.
- Tag `v2.7.0`, GitHub Release, TestPyPI, PyPI, and a clean public-PyPI install
  smoke are complete.
- Conda-forge staged-recipes PR #33461 now targets the verified v2.7.0 sdist;
  refreshed linter, Linux, Windows, and macOS checks pass. Await maintainer review.
- Production frontend and docs are healthy. Render `/health` still reports 2.6.0;
  manually redeploy from `main` and verify 2.7.0 before closing the deployment gate.
- See `HANDOFF.md` for exact published state and bounded next work.

### v2.7.1 reliability release (published 2026-07-28)

Scope is deliberately non-scientific:

- deployment commit/branch/service provenance in `/health`
- scheduled/manual production convergence verification against both health and
  OpenAPI version metadata
- focused Playwright coverage for chart legend restoration, PNG export,
  persisted sidebar collapse, and mobile navigation
- shared `EmptyResults` use across remaining analysis panes
- FastAPI 0.140 deployment dependency

Completed gates: mandatory baseline build/Twine, Ruff, format, mypy, API
(55 passed), full standard suite (1,313 passed, 22 deselected), strict docs,
pre-commit, final v2.7.1 build/Twine, fresh-wheel CLI smoke, frontend
lint/build, and Playwright (19 passed).

PR #43, the complete CI matrix, tag, GitHub Release, Trusted Publishing, fresh
public installation, and Render version/commit convergence are verified.

### v2.8.0 Advanced Dissolution Workbench (active release candidate)

**Goal:** expose the validated dissolution toolkit as one auditable,
report-first workflow.

Implementation and local release validation are complete on `release/v2.8.0`:
core orchestration, reports, audit bundle, API, React tab, documentation, 1,324
standard tests, 59 API tests, 21 browser tests, strict docs, final distributions,
and fresh-wheel smoke pass. PR/CI, publication, public-install, and hosted
convergence remain release gates.

**Included:**

- vessel-level input, normalized table, and profile visualization
- f1/f2 plus bootstrap f2 confidence interval
- five-model fitting with AICc ranking
- model-dependent comparison
- MSD and maximum-deviation alternatives
- HTML/PDF/DOCX reports and a SHA-256-manifested reproducibility ZIP
- core orchestration/result API, FastAPI schema/service/router adapter, typed
  React workflow, API tests, Playwright tests, and documentation

**Definition of done:**

1. Every claim-bearing output maps to an existing independent validation
   fixture or receives a new published-reference test.
2. Invalid/non-finite vessel data and unmatched time points fail closed; no
   silent interpolation or reindexing is introduced.
3. Pharmacometric calculations remain in `src/openpkflow/dissolution/`.
4. Reports include the required regulatory-review disclaimer and preserve the
   exact analysis configuration.
5. The audit ZIP contains normalized input, configuration, serialized results,
   report, and a verified SHA-256 manifest.
6. Complete package/API/web/docs/build validation passes.
7. PR, CI, tag, Trusted Publishing, fresh-install CLI smoke, and hosted version
   convergence are verified before release completion is claimed.

**Excluded:** new dissolution mathematics without independent validation,
changes to frozen `pop/estimation/`, and any claim of regulatory approval.

---

## Cross-cutting workstreams (parallel to milestones)

### Documentation
- GitHub Pages MkDocs site at <https://priyamthakar.github.io/openpkflow/> ✅
  Verified HTTP 200 on 2026-07-26.
- MkDocs tutorials for BE, IVIVC, Bayesian PK, PopPK modules as they ship ✅ Done (2026-05-30)
- Theory guide: derivations for each formula module (regulatory review support) ✅ Done (2026-05-30)
- "Coming from WinNonlin/NONMEM" migration cheatsheet ✅ Done (2026-05-29)

### Packaging and distribution
- `conda-forge` staged-recipes PR #33461 is fully green and awaiting maintainer
  review.
- Docker image: Jupyter + openpkflow + all extras for demos
- Consider Pyodide/WebAssembly for in-browser dissolution demo (low priority)

### Validation infrastructure
- `VALIDATION.md`: cross-reference table mapping every test to FDA/EMA guidance section
  and published DOI. Updated 2026-05-24 with all new cross-val entries.
- **Four-way NCA cross-validation** (2026-05-29): openpkflow == PKNCA 0.12.1 ==
  NonCompart 0.8.0 == Phoenix WinNonlin on Theoph (12 subjects) and Indometh (6 subjects).
  AUClast/AUCINF/CL/Vz pass for oral. IV bolus C0 back-extrapolation implemented and verified
  (AUClast gap fully closed). Test: `tests/validation/test_nca_winnonlin_reference.py` (23 tests). ✅ Done.
- **Steady-state NCA PKNCA cross-validation** (2026-05-24): AUCtau, Cmax_ss, Cmin_ss,
  Cavg_ss, fluctuation%, swing. Swing convention documented (dimensionless ratio vs
  PKNCA percent). ✅ Done.
- **Dissolution f2 bootf2 cross-validation** (2026-05-24): bootf2 0.4.1 `calcf2(est.f2)`
  vs openpkflow `f2(method="all_points")`. Algebraically identical. ✅ Done.
- **IVIVC Level A cross-validation** (2026-05-24): Wagner-Nelson and Loo-Riegelman
  independently implemented in R (no package needed — formula-level algebraic identity).
  13 tests. F_a values match to < 1e-8 relative. ✅ Done.
- **Urinary NCA cross-validation** (2026-05-24): Ae, CLr, %Ae independently implemented
  in R; verified against analytical truth (1-cmt IV bolus renal excretion model, 3
  subjects). 17 tests. ✅ Done.
- **Dissolution model fitting cross-validation** (2026-05-24): All 5 models (zero-order,
  first-order, Higuchi, KP, Weibull) cross-validated against base R lm/optim on
  noise-free data. 24 tests. ✅ Done.
- `pytest-benchmark` CI job: performance regression detection for NCA/dissolution math. ✅ Done.
- `hypothesis` property-based tests for PK calculations (edge-case fuzzing). ✅ Done.
- **C0 back-extrapolation for IV bolus NCA** (2026-05-29): `c0_back_extrapolated()` added to
  `nca/methods.py`. OLS on first 2 points matches WinNonlin C0 to 4 d.p. for all 6 Indometh
  subjects. AUClast within 2% for all 6; AUCinf/CL/Vz within 2% for 5/6 (S4 excluded: lambda_z
  auto-selection diverges). 5 new tests in `TestWinNonLinIndomethC0BackExt`. ✅ Done.

### Discoverability
- README "Comparison" section: feature matrix vs. PKNCA (R), WinNonlin, Pharmpy, OpenPKPD
- Awesome-pharmacometrics / awesome-python list submissions

---

## Quick wins (single-PR scope, no milestone dependency)

| Priority | Task | Effort | Status |
|---|---|---|---|
| High | Fix GitHub Pages 404 | 1 h | ✅ Done |
| High | `DissolutionStudy.from_excel()` via openpyxl | 2 h | ✅ Done |
| High | Codecov integration (badge + coverage gating) | 1 h | ✅ Done |
| Medium | `pytest-benchmark` + perf regression CI job | 2 h | ✅ Done |
| Medium | conda-forge recipe | 3 h | [staged-recipes PR #33461](https://github.com/conda-forge/staged-recipes/pull/33461) targets 2.7.0 and passes linter plus Linux, Windows, and macOS builds; awaiting maintainer review, with no feedstock/package yet |
| Medium | README feature-comparison table (vs. PKNCA, WinNonlin) | 2 h | ✅ Done (v2.2.0 — CDISC PP row split, PKNCA claims corrected, caveat added) |
| Low | pre-commit hooks: ruff + mypy (complements existing CI) | 1 h | ✅ Done |

---

## Explicitly out of scope

- **WeasyPrint** for PDF -- GTK dependency pain on Windows (per CLAUDE.md). ReportLab only.
- **Pharmpy bridge (v0.7.0)** -- slot reserved; un-skip decision documented in v2.0.0 section above.
- **Full FOCE-I/SAEM from scratch** -- deferred until feasibility is assessed post-v1.5.0.
- **GUI (Streamlit/Gradio)** -- useful but out of scope until core science modules stabilize.
- **CDISC Define.xml** -- too niche for early milestones; revisit after CDISC PP output ships.
- **eCTD table formatting** -- manual formatting required; automation deferred.

---

## Definition of done (all milestones)

Every new public function must have:
1. Type hints on all parameters and return values.
2. NumPy-style docstring (one-line description + Parameters/Returns/Raises).
3. ASCII-only text in docstring and CLI output (Windows cp1252 constraint).
4. Degenerate/sanity test with hand-checkable expected value.
5. Published-reference test with DOI or FDA guidance ID in the test docstring.
6. Disclaimer in all generated reports.
7. `ruff check`, `ruff format`, `mypy --strict` clean.
