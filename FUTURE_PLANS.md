# Future Plans

This is a living catalog of ideas beyond the [ROADMAP.md](ROADMAP.md) milestones.
ROADMAP keeps the committed schedule; this file captures blue-sky possibilities,
competitive gaps, and longer-term bets that may reshape priorities.

---

## Strategic context

OpenPKFlow targets a transparent **formulation-to-report pipeline** in open-source Python.
The competitive landscape (OpenPKPD, Pharmpy, PKPy, NeoPKPD, OpenDose-PopPK) is converging
on Python pharmacometrics. Differentiation comes from filling genuine gaps, not reimplementing
what others already do well.

---

## v2.6.0 Improvement Sprint (published 2026-07-15)

**PRs:** <https://github.com/priyamthakar/openpkflow/pull/27> (features) and
<https://github.com/priyamthakar/openpkflow/pull/29> (correction/release hardening),
both merged.
**Takeover doc:** [HANDOFF.md](HANDOFF.md)

Shipped in parallel tracks:

- Study pipeline (`openpkflow.pipeline` + `openpkflow study run`)
- SUPAC screening + alcohol dose-dumping f2 assessment
- IVIVC Level B/C MDT/MRT helpers
- Transit oral absorption + analytical SS metrics
- Webapp: BE power calculator, multi-media tab, IVIVC example loader
- IVIVC convolution analytical validation; BE power edge cases
- Positioning docs, pipeline tutorial, Docker/compose polish

## v2.7.0 release (published 2026-07-25)

The post-v2.6.0 sparse NCA, pipeline audit bundle, MAP/SUPAC workflows, formal BE
ANOVA, validated FDA partial-replicate RSABE, hosted deployment, and web polish are
published in v2.7.0 through PR #39.

## v2.7.1 reliability release (published 2026-07-28)

v2.7.1 adds deployment provenance, a fail-closed production convergence check,
the four missing browser regressions, consistent shared result placeholders,
and the FastAPI 0.140 dependency update. It changes no pharmacometric
calculations. PR/CI, GitHub Release, Trusted Publishing, fresh public
installation, and hosted version/commit convergence are verified.

Conda-forge PR #33461 remains a separate external maintainer gate for v2.7.0.

## v2.8.0 Advanced Dissolution Workbench (active release candidate)

Goal: turn OpenPKFlow's already validated dissolution capabilities into one
report-first, auditable workflow without inventing new pharmacometric methods.

Release-ready local checkpoint: the core orchestration/result API, five-model
validated subset, HTML/PDF/DOCX reports, reproducibility ZIP, three FastAPI
endpoints, typed React upload/paste workflow, core/API tests, and Playwright
flows are complete. The full suite, distributions, fresh-wheel smoke, strict
docs, and pre-commit pass. PR/CI, publication, public-install, and hosted
convergence gates remain open until verified.

### Product slice

- vessel-level CSV upload and editable paste input
- reference/test formulation mapping with matched-time validation
- standard f1/f2 comparison
- bootstrap f2 confidence interval and decision summary
- five-model fitting with AICc ranking and parameter/fit diagnostics
- model-dependent comparison
- MSD and maximum-deviation alternatives
- mean and vessel-level profile plots with table views
- HTML/PDF/DOCX report downloads
- reproducibility ZIP containing normalized input, configuration, serialized
  results, report, and SHA-256 manifest

### Architecture

- Reuse `bootstrap_f2()`, `fit_dissolution_models()`,
  `model_dependent_comparison()`, MSD, and maximum-deviation implementations in
  `src/openpkflow/dissolution/`.
- Add orchestration/result structures in the core package only when needed for
  a stable public workflow.
- Follow the established FastAPI schema/service/router/registration pattern.
- Add a typed React page or clearly separated workbench tab; the frontend
  performs no pharmacometric math.
- Reuse pipeline audit-bundle conventions for deterministic manifests and
  normalized artifacts.

### Evidence and release gates

1. Map every exposed output to its existing validation fixture and reference.
2. Add degenerate and published-reference tests for any new orchestration
   formula or decision field.
3. Fail closed on unmatched time points, invalid vessel data, non-finite values,
   or unsupported comparison conditions.
4. Add API contract/report/audit tests and Playwright upload/paste/download
   flows.
5. Run the complete package/API/web/docs/build gate before publication.
6. Publish through a normal PR, tag, Trusted Publishing, fresh install, and
   hosted convergence check.

### Explicit non-goals for v2.8.0

- no new dissolution algorithm without independent validation
- no interpolation to repair unmatched time points
- no pharmacometric calculations in FastAPI or React
- no extension of frozen `pop/estimation/`
- no claim of regulatory approval or replacement of expert review

## Historical v2.4.0 Credibility Sprint

Goal: make the next release about trust, usability, and release discipline rather
than broad new scientific scope. All changes should be additive, with no breaking
API changes before v3.0.0.

### Bioequivalence hardening

- Add external reference fixtures from PowerTOST/SAS/R for GMR, CVwR, conventional
  ABE CI, and scaled-limit calculations.
- Add `tests/validation/test_be_replicate_reference.py`.
- Keep FDA/EMA RSABE labels explicitly caveated until full upper-bound and
  mixed-model parity are validated against jurisdiction-specific workflows.

### Replicate BE workflow

- Add CLI: `openpkflow be replicate input.csv --parameter Cmax --report out.html --json out.json`.
- Add HTML/Markdown report support for `ReplicateBEResult`.
- Add a small example CSV for `TRR/RTR/RRT` partial replicate data.

### Validation infrastructure

- Mark computationally heavy FOCE reference validation as `slow`.
- Add a nightly or manually triggered CI job for slow validation tests.
- Remove or relocate stale "latest local verification" text from static docs so
  validation pages do not drift.

### Release discipline

- Add a documented `RELEASE.md` workflow for v2.x releases.
- Keep GitHub release notes generated from `docs/changelog.md`.
- Add a short "what OpenPKFlow is / is not" page to reduce overclaiming around
  regulatory use.

---

## Greenfield differentiators — high-impact gaps no one does well

### IVIVC

Level A and the bounded Level B/C MDT/MRT helpers are implemented:

- Level A: deconvolution (Wagner-Nelson, Loo-Riegelman), convolution prediction, Levy plot, predictability assessment (%PE < 15 % for Cmax/AUC)  **✅ DONE**
- Level B/C: mean dissolution time vs. mean residence time helpers **✅ DONE (v2.6.0)**
- FDA guidance compliance: IVIVC summary tables matching the FDA ER guidance format

### Multimedia dissolution (ICH M13A/B)

FDA and EMA increasingly require dissolution in 3+ media:

- Simultaneous f2 across pH 1.2, 4.5, 6.8 with summary table **✅ DONE**
- Alcohol dose-dumping f2 against control **✅ DONE (screening)**
- SUPAC-IR change-level classification **✅ DONE (screening)**
- Dissolution safe-space contour plots (dissolution parameters vs. bioequivalence)

### Sparse oral PK screening ✅ DONE (v1.5.0)

- ~~Model-informed AUC from 2-5 samples per subject~~ — **DONE**: `fit_sparse_1cmt_oral()`, `SparseNCAResult`
- ~~Rich-vs-sparse sampling comparison diagnostics~~ — **DONE**: `sparse_nca_bias_analysis()`
- Bayesian priors for population-prior-informed NCA — still open

---

## Module expansions — building out committed scope

### Dissolution

- ~~Mahalanobis distance (MSD)~~ — **DONE** (v1.1.0): FDA's preferred f2 alternative with chi-squared significance test
- ~~Model-dependent comparison~~ — **DONE** (v1.1.0): fit regression models, compare parameters via 90% CI
- ~~Maximum deviation method~~ — **DONE** (v1.1.0): another FDA-accepted alternative
- ~~f2 with RSD constraints~~ — **DONE** (v1.1.0): ICH M13B RSD ≤ 8% at early time points
- Multivariate statistical distance per FDA/EMA guidance

### NCA

- ~~%AUCextrap flag (FDA criterion >20%)~~ — **DONE** (v1.3.0): quality metrics with auto-warning
- ~~Terminal-phase diagnostics~~ — **DONE** (v1.3.0): adjusted R², n points used
- ~~CDISC PP / ADPPK output~~ — **DONE** (v1.3.0): `NCASummaryResults.to_cdisc_pp()`
- ~~Dose-normalised parameter tables (DN-AUC, DN-Cmax)~~ — **DONE** (v1.3.0)
- ~~Steady-state NCA: AUCtau, Cmax_ss, Cmin_ss, fluctuation, swing, accumulation ratio~~ — **DONE** (v1.3.0)
- ~~Urinary excretion: Ae, Ae%, renal clearance~~ — **DONE** (v1.3.0)

### Bioequivalence

- v2.7.0 adds FDA partial-replicate RSABE validated for complete balanced
  TRR/RTR/RRT allocation against Patterson and Jones (2012), Table II.
  Jurisdiction-specific mixed-model parity and unsupported replicate designs
  remain future BioEqPy/SAS/R work.
- Adaptive BE designs: two-stage Potvin/Maurer methods
- Group-sequential BE with futility stopping
- Multiple-endpoint BE: simultaneous Cmax + AUCinf with multiplicity adjustment
- NTI auto-detection per FDA lists

### PK simulation

- 3-compartment models
- ~~Transit-compartment absorption (Erlang distribution)~~ — **DONE (v2.6.0)**
- Michaelis-Menten / nonlinear elimination
- Enterohepatic recirculation
- Metabolite kinetics (parent + metabolite simultaneous simulation)
- ~~Analytical steady-state metrics (no simulation to SS required)~~ — **DONE (v2.6.0)**

### Population PK diagnostics

- nlmixr2 bridge: run R-based estimation from Python, parse results back
- Run-record integration: parse NONMEM `.lst`/`.ext` into GOFResult objects
- Stepwise covariate modeling (SCM): automated forward addition / backward elimination
- Bootstrap resampling for NLME models (case bootstrap, parametric bootstrap)
- NPDE calculation: normalized prediction distribution errors
- Shrinkage diagnostics: eta shrinkage, epsilon shrinkage
- Covariate forest plots with 95 % CI

---

## Harder strategic bets (multi-quarter)

### Bayesian PK ✅ DONE (v2.0.0)

- ~~MAP individual PK estimation from sparse TDM samples~~ — **DONE**: `map_individual_pk()` (scipy, 10 diagnostics)
- ~~Bayesian BE: posterior probability of BE for 2x2 crossover~~ — **DONE**: `bayes_be()` (PyMC NUTS, P(GMR in 80-125))
- ~~Full posterior sampling~~ — **DONE**: `bayes_individual_pk()` (PyMC Metropolis, shrinkage)
- Prior-posterior comparison plots with shrinkage visualization — still open
- Full FOCE-I/SAEM population estimation — deferred to v2.1.0+

### ML surrogate (experimental)

- Physics-Informed Neural Network (PINN): MLP that respects PK ODE constraints
- Neural ODE (`torchdiffeq`): learn PK parameters directly from concentration-time data
- Surrogate for popPK: ML model predicting individual PK parameters from covariates

### Regulatory submission toolkit

- eCTD-ready tables formatted to FDA style guides
- CDISC Define.xml for PK parameters
- ISS/ISE summary (integrated summary of safety/efficacy PK tables)

### GUI

- Streamlit app: `openpkflow app` launches local browser GUI for dissolution + NCA + BE
- Gradio for interactive sensitivity analysis (sliders for CL, V, ka → live concentration-time plots)

---

## Developer experience & project health

- **Documentation site**: MkDocs site is live and returned HTTP 200 on 2026-07-26
- **Tutorial gallery**: Jupyter notebooks for each module
- **Theory guide**: math derivations for each formula module (regulatory review support)
- **Migration guide**: "Coming from WinNonlin / NONMEM / R" cheat sheets
- **VALIDATION.md**: cross-reference table mapping every test to FDA/EMA guidance + DOI
- **Release readiness checks**: verify version, changelog, tag/release, PyPI,
  docs, and conda-forge state before publishing
- **Slow validation CI**: run heavyweight reference checks such as FOCE on a
  manual or nightly schedule
- **Validation docs hygiene**: keep static docs free of stale local-verification
  snapshots
- **Positioning page**: document what OpenPKFlow is and is not, especially for
  regulatory use
- **Property-based testing**: `hypothesis` for fuzzing PK calculations
- **conda-forge recipe**: `conda install -c conda-forge openpkflow`
- **Docker image**: Jupyter + openpkflow + all extras
- **Dependabot**: automated dependency updates
- **Conventional commits + auto-changelog**: commitizen or release-please

---

## Community & adoption

- Peer-reviewed publication (JPKPD or CPT:PSP)
- PAGE / ACoP / WCoP conference abstract
- Demo video: 5-minute dissolution → NCA → BE pipeline walkthrough
- CRO/CDMO public case study
- Pharmpy interop: read/write Pharmpy model objects
- Awesome-list PRs: awesome-pharmacometrics, awesome-python, awesome-cheminformatics
- Cross-link with competitors: PR to Pharmpy / OpenPKPD / NeoPKPD READMEs

---

## Competitive landscape (aspirational)

| Capability | OpenPKFlow | OpenPKPD | Pharmpy | PKPy | WinNonlin |
|---|---|---|---|---|---|
| Dissolution f1/f2 | ✅ | — | — | — | ✅ |
| Bootstrap f2 CI | ✅ | — | — | — | ✅ |
| Dissolution model fitting (5 models + AICc) | ✅ | — | — | — | ✅ |
| Mahalanobis / f2 alternatives | ✅ | — | — | — | ✅ |
| Multi-media dissolution | ✅ | — | — | — | ✅ |
| IVIVC (Level A) | ✅ | — | — | — | ✅ |
| NCA | ✅ | ✅ | ✅ | ✅ | ✅ |
| Steady-state NCA + urine | ✅ | — | — | — | ✅ |
| Sparse oral PK screening | ✅ | ✅ | — | — | ✅ |
| CDISC output | ✅ | partial | — | — | ✅ |
| BE (2x2 crossover TOST) | ✅ | ✅ | — | — | ✅ |
| RSABE / replicate BE | balanced FDA partial-replicate validated; general screening remains research-grade | — | — | — | ✅ |
| PopPK estimation | ✅ research-grade FOCE-I/SAEM | ✅ | ✅ | ✅ | — |
| PK simulation (1-2 cmt) | ✅ | ✅ | ✅ | ✅ | ✅ |
| MAP individual PK | ✅ (v2.0.0) | — | — | — | ✅ |
| Full Bayesian PK + BE | ✅ (v2.0.0) | — | partial | — | — |
| HTML/PDF/DOCX reports | ✅ | ✅ | ✅ | ✅ | ✅ |
| Study pipeline (multi-stage + report) | ✅ (v2.6) | — | — | — | ✅ |
| SUPAC screening helpers | ✅ (v2.6 screening) | — | — | — | ✅ |
| IVIVC Level B/C helpers | ✅ (v2.6) | — | — | — | ✅ |
| Transit oral absorption | ✅ (v2.6) | — | — | — | ✅ |
| GUI / web app | ✅ React webapp | ✅ | — | — | ✅ |
| ML surrogate | ✅ (exp.) | — | — | — | — |

---

## Explicitly out of scope

- WeasyPrint for PDF — GTK dependency pain on Windows; ReportLab only
- FOCE-I/SAEM extension beyond the frozen v2.3.0 implementation
- Streamlit/Gradio embedding; the supported GUI is the separate React/FastAPI web layer
- CDISC Define.xml
- eCTD table formatting — manual formatting required; automation deferred
