# CLAUDE.md -- openassayflow

This file provides guidance to Claude Code (claude.ai/code) when working with code in the openassayflow repository.

## Scope and boundary (read this first)

**In scope -- build, extend, polish:**
- `curve/` -- StandardCurve: 4PL/5PL fitting (via openfit), calibration curve construction
- `backcalc/` -- inverse prediction of unknown concentrations + Fieller CI
- `acceptance/` -- %recovery, %RE, %CV, accuracy/precision per FDA 2018 BMV guidance
- `lloq/` -- LLOQ/ULOQ determination from curve + acceptance criteria
- `parallelism/` -- relative potency, parallel-line and parallel-curve analysis (USP <1032/1034>)
- `ada/` -- anti-drug-antibody screening/confirmatory cut point calculation (FDA/EMA)
- `plate/` -- 96/384-well plate layout parsing, blank subtraction, replicate collapse
- `report/` -- bioanalytical run report (regulatory-style HTML, PDF, Markdown)
- `validation/` -- cross-checks against published ELISA/bioassay reference data

**Out of scope -- do not build:**
- Curve fitting engine internals -- that is openfit's job. openassayflow imports openfit.
- Plate reader hardware drivers or instrument communication.
- LIMS integration, sample tracking, or barcode scanning.
- LC-MS/MS bioanalytical methods (chromatographic, not immunoassay).
- Electronic signatures, 21 CFR Part 11 compliance, audit trails.
- GUI / web dashboard -- library-first, CLI-second.
- PK/PD calculations, NCA, simulation -- that is openpkflow's domain.

**Rules for AI agents:**
1. Before adding any feature, verify it is on the in-scope list. If not, ask the user.
2. Validation work outranks new features. Do not add ADA cut points before standard curves are fully validated.
3. openassayflow is an IMMUNOASSAY/BIOASSAY domain package. It depends on openfit for fitting but adds domain-specific logic, acceptance criteria, and regulatory reporting.
4. When ROADMAP.md and CLAUDE.md disagree, CLAUDE.md wins. Flag the conflict to the user.
5. Never use `--no-verify` to bypass pre-commit hooks. Fix the underlying issue instead.

---

## Identity

**Package:** `openassayflow`
**Author:** Priyam Thakar <priyamthakar1@gmail.com>
**GitHub:** https://github.com/priyamthakar/openassayflow
**PyPI target:** `pip install openassayflow`
**License:** MIT
**Dependency:** openfit (for curve fitting engine)
**Philosophy:** Transparent, validated, open-source bioanalytical workflow. SoftMax Pro / MasterPlex costs thousands per seat; this is the reproducible alternative with regulatory-grade reporting.

---

## Commands

```bash
# Install in editable mode with dev tools
pip install -e ".[dev]"

# Run all tests
pytest

# Run validation suite only
pytest tests/validation/ -v

# Lint and auto-fix
ruff check src/ tests/ --fix
ruff format src/ tests/

# Type-check
mypy src/openassayflow

# CLI
openassayflow version
openassayflow fit-curve plate_data.csv --model 4pl --weights 1/y2 --report run_report.html
openassayflow backcalc plate_data.csv --curve standards.json --report results.html
```

---

## Architecture

- **Layout:** `src/` layout (PEP 517/518)
- **Build:** hatchling (`pyproject.toml`)
- **Python floor:** 3.10+
- **Core deps:** openfit, numpy, pandas, pydantic
- **Optional deps:** `[reports]` (jinja2, reportlab, python-docx), `[dev]` (pytest, ruff, mypy)

### Module map

```
openassayflow/
  curve/
    __init__.py         -- StandardCurve, CalibrationResult
    standard_curve.py   -- StandardCurve: wraps openfit 4PL/5PL with domain defaults
                           default weighting: 1/Y^2 (correct for ELISA heteroscedasticity)
                           calibrator levels, anchor points, range validation
    dilution.py         -- minimum required dilution (MRD) handling
  backcalc/
    __init__.py         -- back_calculate(), BackCalcResult
    inverse.py          -- inverse prediction from fitted curve + Fieller CI
                           asymmetric confidence intervals (correct for log-logistic)
    sample.py           -- Sample dataclass: replicates, mean, CV, dilution factor
  acceptance/
    __init__.py         -- run_acceptance(), AcceptanceResult
    criteria.py         -- FDA 2018 BMV acceptance criteria engine
                           accuracy: mean %RE within +/- 15% (20% at LLOQ)
                           precision: %CV <= 15% (20% at LLOQ)
                           >= 75% of QCs within limits, >= 50% per level
    lloq.py             -- LLOQ/ULOQ determination
                           lowest standard meeting accuracy + precision
                           signal-to-noise ratio optional
  parallelism/
    __init__.py         -- test_parallelism(), ParallelismResult
    analysis.py         -- parallel-line analysis (USP <1032>)
                           parallel-curve analysis (USP <1034>)
                           F-test for parallelism, equivalence approach
    potency.py          -- relative potency calculation + Fieller CI
  ada/
    __init__.py         -- screen_cut_point(), confirm_cut_point(), ADAResult
    cut_points.py       -- screening cut point: mean + 1.645 * SD (95th percentile)
                           confirmatory cut point: % inhibition threshold
                           parametric + non-parametric (Shankar et al. 2008)
                           outlier removal before cut point calculation
  plate/
    __init__.py         -- PlateLayout, read_plate()
    layout.py           -- 96/384-well plate layout definition
                           well mapping: standards, QCs, unknowns, blanks
    reader.py           -- plate reader CSV/Excel import (OD/RFU/RLU)
                           blank subtraction, replicate grouping
  report/
    __init__.py         -- report_run(), report_validation()
    templates/          -- Jinja2 HTML templates
    html.py             -- bioanalytical run report (regulatory style)
    pdf.py              -- ReportLab PDF
  cli.py               -- Typer CLI entry point
```

### Data flow

```
Plate reader CSV (OD values in 96-well layout)
  -> read_plate(csv, layout)           PlateData: standards, QCs, unknowns
  -> StandardCurve.fit(standards)      4PL/5PL fit via openfit (1/Y^2 weighting)
                                       CalibrationResult: curve, LLOQ, ULOQ, R^2
  -> back_calculate(unknowns, curve)   inverse prediction + Fieller CI per sample
  -> run_acceptance(QCs, curve)        FDA BMV criteria check per level
  -> report_run("run_001.html")        regulatory-style run report:
                                         - calibration curve plot
                                         - back-calculated QC table with pass/fail
                                         - acceptance summary
                                         - FitSpec for reproducibility
```

---

## Correctness Rules (load-bearing)

1. **Standard curves default to 1/Y^2 weighting.** ELISA signal variance increases with concentration (heteroscedastic). Unweighted 4PL overweights the high end and underweights the critical low end near LLOQ. Default is 1/Y^2; user must explicitly opt into uniform.

2. **Back-calculated concentrations use Fieller's theorem for CI.** Inverse prediction on a nonlinear curve produces asymmetric confidence intervals. Naive error propagation (delta method) underestimates uncertainty at the curve extremes. Fieller's theorem is required.

3. **LLOQ requires BOTH accuracy AND precision.** A standard point is not LLOQ just because it's the lowest on the curve. It must also meet: mean %RE within +/- 20%, %CV <= 20% (FDA 2018 BMV). Both criteria must be satisfied simultaneously.

4. **Anchor points: included in fit, excluded from acceptance.** Anchor standards (below LLOQ or above ULOQ) can stabilize the curve fit but must NOT be used to evaluate assay acceptance or report sample concentrations outside the validated range.

5. **ADA cut points must account for biological variability.** Do not use a single-run SD. Cut points should be calculated from a matrix of naive (drug-naive) samples across multiple analysts/days per Shankar et al. (2008) and FDA 2019 immunogenicity guidance.

6. **Relative potency requires demonstrated parallelism.** Do not report a potency ratio if the parallelism test fails (F-test or equivalence test). Flag non-parallel curves as "potency not estimable."

7. **Dilution factor must be applied AFTER back-calculation.** Reported concentration = back-calculated concentration * dilution factor. This seems obvious but is a common source of 10x errors.

8. **Disclaimer in all generated reports:**
    > This report was generated using openassayflow (open-source). Final acceptance decisions and regulatory interpretation should be reviewed by qualified bioanalytical scientists.

---

## Validation Discipline

### FDA 2018 Bioanalytical Method Validation Guidance

The primary regulatory reference. openassayflow must implement the acceptance criteria exactly as stated in the guidance. Key sections:
- Section V.A: calibration curve (>= 6 non-zero standards, +/- 15% accuracy, +/- 20% at LLOQ)
- Section V.B: QC samples (>= 75% overall within limits, >= 50% per level)
- Section VIII: ligand binding assays (LBA-specific requirements)

### Published 4PL/5PL reference datasets

**Critical finding:** No NIST-equivalent certified reference dataset exists for 4PL/5PL
immunoassay fitting. DeLean et al. (1978) contains illustrative figures but no
machine-readable certified data. Findlay & Dillard (2007) is methodological guidance with
no worked numerical examples. Gottschalk & Dunn (2005) has simulated comparisons but no
standalone certified values. FDA 2018 BMV specifies acceptance criteria but no reference
data.

**Our approach:**
- openfit provides synthetic 4PL/5PL datasets with KNOWN exact parameters (v0.1.1)
- openassayflow inherits this validation and adds domain-specific acceptance testing
- Cross-validate against R `drda` (JSS 2023, actively maintained) and R `nplr` (updated 2025)
- R `drc` is stale (no updates since 2016) -- use for historical comparison only

### Cross-validation

- R `drc` package (Ritz et al., 2015): 4PL parameters on shared datasets must agree within tolerance
- R `nplr` package (Commo & Bot, 2015): 5PL cross-check
- openfit NIST validation (inherited): the fitting engine is already validated

---

## Release Ladder

```
v0.1.0  StandardCurve (4PL/5PL via openfit) + back-calculation + acceptance criteria + HTML report
v0.1.1  Validation suite: R drc cross-validation + FDA BMV worked example
v0.2.0  96-well plate layout + reader import + blank subtraction
v0.3.0  LLOQ/ULOQ determination + dilution handling
v0.4.0  Parallelism testing + relative potency (USP <1032/1034>)
v0.5.0  ADA cut point calculation (screening + confirmatory)
v0.6.0  384-well plates + batch processing (multiple plates per run)
v0.7.0  PDF + Word reports
v1.0.0  Stable release: full bioanalytical workflow validated against FDA BMV
```

---

## Key References

- FDA (2018). Bioanalytical Method Validation: Guidance for Industry. U.S. Department of Health and Human Services.
- FDA (2019). Immunogenicity Testing of Therapeutic Protein Products: Guidance for Industry.
- DeLean, A., Munson, P.J. & Rodbard, D. (1978). Simultaneous analysis of families of sigmoidal curves. Am. J. Physiol., 235(2), E97-E102.
- Shankar, G. et al. (2008). Recommendations for the validation of immunoassays used for detection of host antibodies against biotechnology products. J. Pharm. Biomed. Anal., 48, 1267-1281.
- USP <1032> Design and Development of Biological Assays.
- USP <1034> Analysis of Biological Assays.
- Findlay, J.W. & Dillard, R.F. (2007). Appropriate calibration curve fitting in ligand binding assays. AAPS J., 9(2), E260-E267.
