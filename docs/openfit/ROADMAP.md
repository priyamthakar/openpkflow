# ROADMAP.md -- openfit

Reproducible, open-source nonlinear curve fitting with publication-quality reports.

---

## Guiding Principles

1. **Validation before features.** No model ships without NIST StRD or published-reference tests.
2. **Reproducibility is the moat.** Every fit emits a FitSpec. Anyone with the spec and the data gets the identical result.
3. **Domain-agnostic engine.** openfit knows math, not biology. Domain interpretation lives in downstream packages (openassayflow, openpkflow).
4. **Report-first.** The deliverable is a shareable document, not a number in a terminal.
5. **Explicit over implicit.** Weights, initial guesses, and CI methods are never silently defaulted.

---

## Release Ladder

### Phase 1 -- Foundation (v0.1.x)

```
v0.1.0  Core engine + essential models + reports
        -----------------------------------------------
        - Fit() engine wrapping scipy.optimize.least_squares (LM + TRF)
        - Models: Hill3P, Hill4P (4PL), Hill5P (5PL), MonoExp, BiExp,
          MichaelisMenten, Logistic4P, Poly1-Poly3
        - Smart initial_guess(x, y) for every model (data-driven heuristics)
        - Weighting: uniform, 1/Y, 1/Y^2, 1/SD^2
        - FitResult: params, asymptotic SE, R^2, AICc, BIC, residuals
        - FitSpec: reproducibility manifest (.to_json() / .from_json())
        - HTML report with fit overlay + residual panel (Jinja2 + matplotlib)
        - Markdown report
        - CLI: openfit fit, openfit version
        - Input validation: NaN/Inf rejection, monotonicity checks where required
        - Tests: degenerate cases + hand-checkable examples for every model
        Definition of done: pip install -e . works, pytest green, wheel builds clean.

v0.1.1  NIST StRD validation suite
        -----------------------------------------------
        - All 27 NIST nonlinear regression datasets parsed and loaded
        - Parametrized pytest: every dataset recovers certified values to >= 6 sig digits
        - Certified values for: parameters, standard errors, residual sum of squares
        - CI: validation badge or matrix in README showing pass/fail per dataset
        Definition of done: all 27 NIST datasets pass. This is the credibility anchor.

v0.1.2  PyPI publish + packaging
        -----------------------------------------------
        - PyPI Trusted Publishing (GitHub Actions on version tags)
        - README with quickstart, validation badge, comparison table
        - py.typed marker for downstream type checking
```

### Phase 2 -- Statistical Depth (v0.2.x - v0.3.x)

```
v0.2.0  Model comparison + GOF diagnostics
        -----------------------------------------------
        - compare_models(): AICc, BIC, evidence ratio, Akaike weights
        - F-test (extra sum-of-squares) for nested model pairs
        - Nestedness detection: auto-check if model A is a special case of model B
        - Residual analysis: runs test (Wald-Wolfowitz), replicates test, Shapiro-Wilk
        - QQ plot, residuals-vs-predicted plot
        - Comparison HTML report: side-by-side fit overlays + criteria table
        Definition of done: F-test matches published examples (Motulsky & Christopoulos,
        "Fitting Models to Biological Data Using Linear and Nonlinear Regression", 2003).

v0.3.0  Profile-likelihood CI + bootstrap CI
        -----------------------------------------------
        - profile_likelihood_ci(): walk each parameter, find likelihood ratio boundary
        - Detect non-unimodal profiles, warn user
        - bootstrap_ci(): residual resampling + case resampling, BCa correction
        - Fixed random seed in FitSpec for bootstrap reproducibility
        - Comparison: asymptotic vs profile vs bootstrap in report
        - Validation: compare profile CI to Prism published examples where available
        Definition of done: profile CI on Hill4P recovers known asymmetric intervals
        from Motulsky & Christopoulos Table 22.1.
```

### Phase 3 -- The Moat Features (v0.4.x - v0.5.x)

```
v0.4.0  Global/shared-parameter fitting
        -----------------------------------------------
        - GlobalFit(datasets, model, shared=[...], local=[...])
        - Joint optimization: shared params constrained equal across datasets
        - Per-dataset local params fitted independently within the joint objective
        - F-test: is sharing justified? Compare joint vs. independent RSS
        - Global fit report: overlay all datasets with shared curve + local curves
        - Validation: textbook shared-fitting examples (Motulsky & Christopoulos Ch. 25)
        Definition of done: this is THE feature Prism has and no OSS tool matches.
        Must work on >= 5 datasets simultaneously with mixed shared/local params.

v0.5.0  ROUT outlier detection
        -----------------------------------------------
        - rout_outliers(): implementation of Motulsky & Brown (BMC Bioinformatics 2006)
        - Adaptive: robust fit -> FDR-controlled outlier identification
        - Q parameter (false discovery rate) user-configurable, default 1%
        - Report: flagged points highlighted on fit plot
        - Validation: reproduce Figure 2 / Table 1 from the original paper
        Definition of done: results match the published ROUT examples within tolerance.
```

### Phase 4 -- Model Library Expansion (v0.6.x)

```
v0.6.0  Full model library (~30 equations)
        -----------------------------------------------
        New models (beyond v0.1.0 set):
        - Sigmoidal: Boltzmann, asymmetric (5P) Gompertz-sigmoid
        - Exponential: ExpPlateau, ExpDecay (one/two-phase), association
        - Growth: Gompertz, Richards (5P generalized logistic)
        - Gaussian: single + bi-Gaussian + Lorentzian
        - Enzyme: substrate inhibition, allosteric (Hill-kinetics)
        - Binding: one-site specific, two-site, competitive
        - Polynomial: Poly4-Poly6
        - Each model: equation, smart initial_guess, analytic Jacobian where tractable
        - NIST StRD tests for any matching datasets
        Definition of done: every model has >= 2 tests (degenerate + published reference).
```

### Phase 5 -- Reports + Migration (v0.7.x)

```
v0.7.0  PDF + Word reports + Prism import
        -----------------------------------------------
        - ReportLab PDF report: publication-quality, embeddable in papers
        - python-docx Word report: for collaborators who need .docx
        - Prism .pzfx XML import (read-only): parse data tables and model selections
          so users can migrate existing Prism analyses to openfit
        - Plot export: SVG, PNG, PDF (individual plots, not just in reports)
        Definition of done: a user can import a Prism file, rerun the fit, and get a
        reproducible spec + report that matches the Prism results.
```

### Phase 6 -- Advanced Features (v0.8.x+)

```
v0.8.0  Constraint fitting + parameter expressions
        -----------------------------------------------
        - Parameter bounds (already in scipy, surface it cleanly)
        - Parameter expressions: "Top = 100" (fixed), "EC50_B = 2 * EC50_A" (linked)
        - Penalty functions for soft constraints

v0.9.0  Batch fitting
        -----------------------------------------------
        - Fit the same model to 100+ datasets (e.g., plate reader rows)
        - Summary table: parameter estimates across all fits
        - Batch report: heatmap of R^2, flagged poor fits

v1.0.0  Stable public release
        -----------------------------------------------
        - All NIST StRD datasets passing
        - Full model library (30+)
        - Global fitting, profile CI, bootstrap CI, ROUT
        - HTML + PDF + Markdown + DOCX reports
        - Prism import
        - FitSpec reproducibility for every fit
        - Comprehensive docs (mkdocs)
        - conda-forge recipe
```

---

## Validation Matrix

Every release must maintain the following:

| Validation tier | Source | What it proves |
|----------------|--------|----------------|
| NIST StRD (27 datasets) | NIST public domain | Parameter recovery to 6+ sig digits |
| Motulsky & Christopoulos textbook | Published tables | F-test, AICc, profile CI correctness |
| Motulsky & Brown 2006 | BMC Bioinformatics | ROUT outlier detection correctness |
| R `drc` cross-validation | Ritz et al. 2015, PLOS ONE | 4PL/5PL parameter agreement on shared data |
| Degenerate cases | Mathematical identity | Edge case robustness (zero variance, flat data, single point) |

No release ships if any NIST test regresses.

---

## Downstream Packages (planned)

openfit is the engine. Domain packages add interpretation:

```
openfit                     -- domain-agnostic curve fitting engine
  |
  +-- openassayflow         -- ELISA 4PL/5PL, standard curves, back-calculation,
  |                            LLOQ/ULOQ, parallelism, relative potency,
  |                            ADA cut points, FDA BMV compliance
  |
  +-- openpkflow            -- may adopt openfit for dissolution model fitting
  |                            (Weibull, Korsmeyer-Peppas, etc.)
  |
  +-- (future)              -- environmental dose-response, agricultural assays, etc.
```

Each downstream package:
- Imports openfit for the fitting engine
- Adds domain-specific interpretation, acceptance criteria, and reports
- Has its own validation suite against domain-specific published references
- Has its own CLAUDE.md with domain-specific correctness rules

---

## Non-Goals (things we will never do)

- Replace scipy as a general optimization library
- Build a GUI (Prism's GUI is their moat; our moat is reproducibility + transparency)
- Bayesian inference in core (optional extension only)
- Real-time / streaming fitting
- GPU acceleration (our datasets are small; scipy on CPU is fast enough)

---

## Key References

- Motulsky, H. & Christopoulos, A. (2003). *Fitting Models to Biological Data Using Linear and Nonlinear Regression.* GraphPad Software. -- The textbook behind Prism's methods.
- Motulsky, H.J. & Brown, R.E. (2006). Detecting outliers when fitting data with nonlinear regression: a new method based on robust nonlinear regression and the false discovery rate. *BMC Bioinformatics*, 7, 123. -- The ROUT paper.
- NIST StRD: https://www.itl.nist.gov/div898/strd/nls/nls_main.shtml -- Certified reference datasets.
- Ritz, C. et al. (2015). Dose-Response Analysis Using R. *PLOS ONE*, 10(12), e0146021. -- The R `drc` package paper.
- DeLean, A., Munson, P.J. & Rodbard, D. (1978). Simultaneous analysis of families of sigmoidal curves. *Am. J. Physiol.*, 235(2), E97-E102. -- The original 4PL/ALLFIT paper.
