# Future Plans

This is a living catalog of ideas beyond the [ROADMAP.md](ROADMAP.md) milestones.
ROADMAP keeps the committed schedule; this file captures blue-sky possibilities,
competitive gaps, and longer-term bets that may reshape priorities.

---

## Strategic context

OpenPKFlow owns the **formulation-to-regulatory-submission pipeline** in open-source Python.
The competitive landscape (OpenPKPD, Pharmpy, PKPy, NeoPKPD, OpenDose-PopPK) is converging
on Python pharmacometrics. Differentiation comes from filling genuine gaps, not reimplementing
what others already do well.

---

## Greenfield differentiators — high-impact gaps no one does well

### IVIVC (full toolkit — Level A/B/C)

Level A is now implemented (v1.2.0). Level B/C remain open-source gaps:

- Level A: deconvolution (Wagner-Nelson, Loo-Riegelman), convolution prediction, Levy plot, predictability assessment (%PE < 15 % for Cmax/AUC)  **✅ DONE**
- Level B/C: mean dissolution time vs. mean residence time, disintegration time correlations
- FDA guidance compliance: IVIVC summary tables matching the FDA ER guidance format

### Multimedia dissolution (ICH M13A/B)

FDA and EMA increasingly require dissolution in 3+ media:

- Simultaneous f2 across pH 1.2, 4.5, 6.8 with summary table
- Alcohol dose-dumping: f2 at 0%, 5%, 20%, 40% ethanol vs. control
- SUPAC/MR change level auto-classification (Level 1/2/3)
- Dissolution safe-space contour plots (dissolution parameters vs. bioequivalence)

### Sparse-sampling NCA

Competitors (OpenPKPD, WinNonlin) are moving here:

- Model-informed AUC from 2–5 samples per subject
- Bayesian priors for population-prior-informed NCA
- Rich-vs-sparse sampling comparison diagnostics

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

- Replicate designs (RTR, RTRT, TRTR): RSABE for HVDs/HVDPs per FDA Progesterone guidance
- Adaptive BE designs: two-stage Potvin/Maurer methods
- Group-sequential BE with futility stopping
- Multiple-endpoint BE: simultaneous Cmax + AUCinf with multiplicity adjustment
- NTI auto-detection per FDA lists

### PK simulation

- 3-compartment models
- Transit-compartment absorption (Erlang distribution)
- Michaelis-Menten / nonlinear elimination
- Enterohepatic recirculation
- Metabolite kinetics (parent + metabolite simultaneous simulation)
- Analytical steady-state metrics (no simulation to SS required)

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

### Bayesian PK

- MAP individual PK estimation from sparse TDM samples (CmdStanPy, 1-cmt oral/IV)
- Bayesian BE: posterior probability of BE > 0.95 for 2×2 crossover
- Prior-posterior comparison plots with shrinkage visualization

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

- **Documentation site**: fix GitHub Pages 404 — ship full MkDocs site with `mkdocstrings` API reference
- **Tutorial gallery**: Jupyter notebooks for each module
- **Theory guide**: math derivations for each formula module (regulatory review support)
- **Migration guide**: "Coming from WinNonlin / NONMEM / R" cheat sheets
- **VALIDATION.md**: cross-reference table mapping every test to FDA/EMA guidance + DOI
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
| Sparse NCA | ✅ | ✅ | — | — | ✅ |
| CDISC output | ✅ | partial | — | — | ✅ |
| BE (2x2 crossover TOST) | ✅ | ✅ | — | — | ✅ |
| RSABE / replicate BE | planned | — | — | — | ✅ |
| PopPK estimation | deferred | ✅ | ✅ | ✅ | — |
| PK simulation (1-2 cmt) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Bayesian | planned | partial | ✅ (via NONMEM) | — | — |
| HTML/PDF/DOCX reports | ✅ | ✅ | ✅ | ✅ | ✅ |
| GUI | deferred | ✅ | — | — | ✅ |
| ML surrogate | ✅ (exp.) | — | — | — | — |

---

## Explicitly out of scope

- WeasyPrint for PDF — GTK dependency pain on Windows; ReportLab only
- Full FOCE-I/SAEM from scratch — deferred until feasibility post-v1.5.0
- GUI (Streamlit/Gradio) — deferred until core science modules stabilize
- CDISC Define.xml — revisit after CDISC PP output ships
- eCTD table formatting — manual formatting required; automation deferred
