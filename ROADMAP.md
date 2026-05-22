# OpenPKFlow Roadmap (post-1.0.0)

## North star

OpenPKFlow owns the **formulation-to-regulatory-submission pipeline** in open-source Python:
dissolution -> IVIVC -> NCA -> BE -> reports. Not another NLME engine — those exist.
The gap we fill is the CRO/CDMO bench scientist who needs clean, auditable, shareable outputs
without WinNonlin or a SAS programmer.

Formal bioequivalence statistics live in the companion BioEqPy package. OpenPKFlow
keeps only a convenience paired-TOST layer plus BioEqPy-ready exports.

---

## Greenfield differentiators (near-zero open-source Python competition)

| Capability | Status in open-source Python |
|---|---|
| IVIVC (Level A: deconvolution + convolution prediction) | None |
| Mahalanobis Statistical Distance (MSD) / f2 alternatives | OpenPKFlow ✅ |
| Multi-media dissolution (ICH M13A/B, alcohol dose-dumping) | None |
| Formal RSABE / replicate-design BE | BioEqPy companion |
| CDISC PP / ADPPK-compliant PK parameter output | OpenPKFlow ✅ |
| Sparse NCA (model-informed AUC from 2-5 samples) | Partial (PKNCA R only) |

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

### v1.2.0 -- IVIVC Level A (target: ~6 weeks)

Scope: new `ivivc/` module. Level A only. Predictability assessment included.
Level B/C and adaptive IVIVC deferred to v1.3.0.

- `wagner_nelson()` -- deconvolution of in vivo absorption fraction from plasma data
- `loo_riegelman()` -- two-compartment deconvolution
- `convolution_predict()` -- predict in vivo profile from in vitro dissolution + unit impulse response
- `levy_plot()` -- IVIVC correlation plot with regression overlay
- `ivivc_predictability()` -- %PE for Cmax and AUCinf (<15% FDA acceptance criterion)
- `IVIVCResult` dataclass with `summary()`, `plot()`, `report()` methods
- HTML/Markdown/PDF/DOCX reports following existing template style
- New `openpkflow ivivc` CLI command
- Tests: ~30 new tests, Wagner-Nelson hand-checked against Gibaldi & Perrier reference

---

### v1.3.0 -- NCA expansion: sparse + steady-state (target: ~4 weeks)

Scope: expand `nca/` module. No new module.

- Steady-state NCA: `AUCtau`, `Cmax_ss`, `Cmin_ss`, fluctuation, swing, accumulation ratio
- `%AUCextrap` flag: warn if >20% (FDA criterion), add to `NCAResult` and reports ✅
- Lambda_z quality metrics: adjusted R2, n points used, visual slope-selector helper ✅ (adj R2 + n_points in NCAResult + HTML reports)
- Urinary excretion PK: `Ae`, `Ae_pct`, `CLr` -- requires `urine` route support in loader
- CDISC PP-format output: `NCASummaryResults.to_cdisc_pp()` -> DataFrame with CDISC PP variable names ✅
- Dose-normalised parameter tables: DN-AUC, DN-Cmax in summary reports ✅
- Tests: ~25 new tests

---

### v1.4.0 -- BioEqPy bridge polish (target: ~1 week)

Scope: keep OpenPKFlow BE lightweight and route formal BE work to BioEqPy.

- Example notebook: OpenPKFlow NCA -> BioEqPy formal BE report
- Documentation showing `BEStudy.to_bioeqpy_dataframe()` and BioEqPy bridge helpers
- Optional dependency note: install BioEqPy only when formal BE analysis is needed

---

### v1.5.0 -- Multi-media dissolution (target: ~3 weeks)

Scope: expand `dissolution/` module.

- `MultiMediaStudy` -- simultaneous f2 across pH 1.2, 4.5, 6.8 with summary table
- Alcohol dose-dumping panel: f2 at 0%, 5%, 20%, 40% ethanol vs. control
- SUPAC/MR change level auto-classification: Level 1/2/3 per dissolution differences
- ICH M13A/B multi-media report template
- Tests: ~20 new tests

---

### v2.0.0 -- Bayesian PK (target: multi-quarter; API break possible)

Scope: `bayes/` module, currently extras-wired but empty.

**Decision required before work starts:** implement FOCE-I/SAEM from scratch vs.
wrap nlmixr2 or Pharmpy. Prior analysis: Pharmpy bridge (v0.7.0) was skipped;
a Python-to-R bridge (nlmixr2 via rpy2) is likely the faster path to population
estimation with less implementation risk.

Tentative scope (pending decision):
- MAP individual PK estimation from sparse TDM samples (CmdStanPy, 1-cmt oral/IV)
- Bayesian BE: posterior probability of BE > 0.95 for 2x2 crossover
- Prior-posterior comparison plots with shrinkage visualization
- `[bayes]` extra: PyMC >= 5.0 or CmdStanPy >= 1.2 required

**Not in v2.0.0:** full FOCE-I/SAEM population estimation (reserved for v2.1.0 or
Pharmpy bridge decision).

---

## Cross-cutting workstreams (parallel to milestones)

### Documentation
- Fix dead GitHub Pages link (priyamthakar.github.io/openpkflow -- currently 404)
  **This is the single highest-priority quick-win.**
- MkDocs tutorials for BE, IVIVC modules as they ship
- Theory guide: derivations for each formula module (regulatory review support)
- "Coming from WinNonlin/NONMEM" migration cheatsheet

### Packaging and distribution
- `conda-forge` recipe PR (reaches biostat/bioinformatics community)
- Docker image: Jupyter + openpkflow + all extras for demos
- Consider Pyodide/WebAssembly for in-browser dissolution demo (low priority)

### Validation infrastructure
- `VALIDATION.md`: cross-reference table mapping every test to FDA/EMA guidance section
  and published DOI. Priority: add before PyPI promotion to CRO/CDMO audiences.
- `pytest-benchmark` CI job: performance regression detection for NCA/dissolution math
- `hypothesis` property-based tests for PK calculations (edge-case fuzzing)

### Discoverability
- README "Comparison" section: feature matrix vs. PKNCA (R), WinNonlin, Pharmpy, OpenPKPD
- Awesome-pharmacometrics / awesome-python list submissions

---

## Quick wins (single-PR scope, no milestone dependency)

| Priority | Task | Effort |
|---|---|---|
| High | Fix GitHub Pages 404 (check `docs.yml` workflow + Pages branch setting) | 1 h |
| High | `DissolutionStudy.from_excel()` via openpyxl | 2 h |
| High | Codecov integration (badge + coverage gating) | 1 h |
| Medium | `pytest-benchmark` + perf regression CI job | 2 h |
| Medium | conda-forge recipe | 3 h |
| Medium | README feature-comparison table (vs. PKNCA, WinNonlin) | 2 h |
| Low | pre-commit hooks: ruff + mypy (complements existing CI) | 1 h |

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
