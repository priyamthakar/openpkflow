# OpenPKFlow — Session Context Handout

Read this at the start of every new session. It contains the full current state of the project, design decisions made, known gotchas, and what comes next. Cross-reference with `CLAUDE.md` for code conventions and pharmacometric rules.

---

## Identity

- **Package:** `openpkflow`
- **Author:** Priyam Thakar, priyamthakar1@gmail.com
- **GitHub:** https://github.com/priyamthakar/openpkflow (username: `priyamthakar`, not `priyamthakar1`)
- **PyPI:** https://pypi.org/project/openpkflow/ — live and installable (v0.3.0 on PyPI; v0.4.0 built locally, not yet tagged/released)
- **Working directory:** `D:\openpkflow`
- **Python floor:** 3.10+
- **Build:** hatchling, `src/` layout

---

## Current version: 0.4.0 (local, not yet on PyPI)

### Version history

| Version | What shipped |
|---|---|
| 0.1.0 | f1, f2, CSV loader, DissolutionStudy, CLI, Markdown/HTML reports, 50 tests |
| 0.1.1 | bootstrap_f2, profile plot in HTML, CI workflow, example datasets, py.typed |
| 0.1.2 | PyPI Trusted Publishing workflow (no code changes) |
| 0.1.3 | f2(method="regulatory"), CV% warning in compare(), README polish |
| 0.1.4 | DissolutionStudy.bootstrap_compare(), ComparisonResult.plot(), demo.ipynb rewritten |
| 0.2.0 | Dissolution model fitting: 5 models, ModelFit, DissolutionFitResults, AICc ranking, HTML fit report |
| 0.3.0 | PDF (ReportLab) + Word (python-docx) reports for comparison and model fit |
| 0.4.0 | NCA engine: AUClast, AUCinf, Cmax, Tmax, lambda_z (BAR²), CL/F, Vz/F; HTML+Markdown reports; Theoph reference dataset; 93 NCA tests |

---

## What is actually built (v0.4.0)

### Dissolution public API

```python
from openpkflow.dissolution import (
    f1, f2, DissolutionStudy, bootstrap_f2, BootstrapF2Result,
    ModelFit, DissolutionFitResults, fit_dissolution_models,
)
from openpkflow.datasets import example_dissolution_path, example_similar_path, example_not_similar_path
```

Key objects:
- `DissolutionStudy.from_csv(path)` → compare, bootstrap_compare, fit_models
- `ComparisonResult` — f1_value, f2_value, report(format="html"|"markdown"|"pdf"|"docx")
- `DissolutionFitResults` — best model, AICc ranking, report(format=...)
- `ModelFit` frozen dataclass — model_name, params, r_squared, aic, aicc, bic, predict()

### NCA public API

```python
from openpkflow.nca import NCAStudy, NCAResult, NCASummaryResults
from openpkflow.datasets import example_theoph_path
```

```python
study = NCAStudy.from_csv(
    "pk_data.csv",
    auc_method="linear_up_log_down",  # required; "linear" | "log" | "linear_up_log_down"
    blq_method="none",                 # required; "none" | "drop" | "zero" | "half_lloq" | "lloq"
)
summary = study.analyze()             # -> NCASummaryResults

# Per-subject
result = summary.results[0]
result.AUClast                        # float
result.AUCinf_obs                     # float | None
result.AUC_percent_extrapolated       # float | None
result.Cmax, result.Tmax
result.lambda_z, result.half_life     # float | None each
result.CL_F, result.Vz_F             # float | None — oral apparent
result.CL, result.Vz                  # float | None — IV absolute
result.warnings                       # list[str]
result.summary()                      # ASCII str
result.to_dict()                      # flat dict
result.report("sub.html")             # HTML or Markdown

summary.summary()                     # ASCII tabular
summary.to_dataframe()                # pd.DataFrame, one row per subject
summary.report("summary.html")
```

NCA CSV format: `subject,time,conc,dose,route`  
- dose in the same unit as conc*time (e.g. mg when conc is mg/L, time is h)  
- route: `"oral"` → CL_F/Vz_F; `"iv_bolus"` / `"iv_infusion"` → CL/Vz  

BLQ handling: "none" | "drop" | "zero" | "half_lloq" (needs lloq=) | "lloq" (needs lloq=)  
Aliases: "m1" → "drop", "m2" → "zero"  
String BLQ: `<0.5` in conc column is parsed and treated as BLQ.

---

## Architecture: file map

```
src/openpkflow/
  __init__.py                      version only
  cli.py                           Typer CLI: version, similarity, dissolution compare
  py.typed                         PEP 561 marker

  dissolution/
    __init__.py                    exports all public symbols
    similarity.py                  f1(), f2()
    loader.py                      load_dissolution_csv(), DissolutionCSVConfig
    study.py                       DissolutionStudy, ComparisonResult
    bootstrap.py                   bootstrap_f2(), BootstrapF2Result
    models.py                      ModelFit, DissolutionFitResults, fit_dissolution_models()
    plotting.py                    dissolution_profile_plot_b64(), dissolution_fit_plot_b64()
    reporting.py                   render_markdown_report(), report_dissolution()

  nca/
    __init__.py                    exports all public NCA symbols
    methods.py                     pure math: AUC (3 methods), cmax, tmax, lambda_z (BAR²),
                                   auc_inf_obs, auc_percent_extrapolated,
                                   clearance_volume_parameters; AUCResult, LambdaZResult
    loader.py                      load_nca_csv() with BLQ handling
    results.py                     NCAResult, NCASummaryResults dataclasses
    study.py                       NCAStudy: from_csv(), analyze()
    reporting.py                   report_nca_single(), report_nca_summary()

  report/
    __init__.py
    html.py                        dissolution HTML renderers (Jinja2)
    pdf.py                         dissolution PDF renderers (ReportLab, lazy import)
    docx.py                        dissolution Word renderers (python-docx, lazy import)
    templates/
      dissolution_report.html      comparison report template
      fit_report.html              model fit report template
      nca_single_report.html       NCA per-subject report
      nca_summary_report.html      NCA multi-subject summary

  datasets/
    __init__.py                    example_dissolution_path(), example_similar_path(),
                                   example_not_similar_path(), example_theoph_path()
    example_dissolution.csv
    example_similar.csv
    example_not_similar.csv
    theoph.csv                     R nlme::Theoph — 12 subjects, oral theophylline

  sim/, pop/, bayes/, ml/, validation/   stubs only
```

---

## Data flows

### Dissolution

```
CSV -> load_dissolution_csv() -> DissolutionStudy
     -> study.compare(ref, test) -> ComparisonResult -> result.report("out.html|pdf|docx|md")
     -> study.fit_models("ref")  -> DissolutionFitResults -> fits.report("fit.html|pdf|docx")
```

### NCA

```
CSV -> load_nca_csv() (BLQ handled) -> NCAStudy
     -> study.analyze() -> NCASummaryResults
     -> summary.to_dataframe()
     -> summary.report("summary.html|md")
     -> result.report("sub.html|md")
```

---

## Report format support matrix

| Format | Dissolution comparison | Dissolution model fit | NCA single | NCA summary |
|--------|----------------------|-----------------------|------------|-------------|
| html   | yes | yes | yes | yes |
| markdown | yes | no | yes | yes |
| pdf    | yes (requires [reports]) | yes (requires [reports]) | v0.4.1 | v0.4.1 |
| docx   | yes (requires [reports]) | yes (requires [reports]) | v0.4.1 | v0.4.1 |

---

## Test suite (223 tests as of v0.4.0)

```
tests/
  dissolution/
    test_similarity.py         f1/f2 validation, regulatory method
    test_study.py              loader, compare, bootstrap, reports
    test_bootstrap.py          BootstrapF2Result
    test_models.py             5 models, AICc ranking, fit API, reports
  nca/
    test_methods.py            all math functions, hand-checked expected values
    test_loader.py             BLQ handling, string-BLQ, edge cases
    test_study.py              NCAStudy integration, NCAResult field coverage
    test_theoph_reference.py   regression against R nlme Theoph dataset
  report/
    test_pdf.py                magic bytes, file write, import guard
    test_docx.py               magic bytes, disclaimer round-trip, import guard
  test_cli.py                  CLI commands
```

---

## CI / Release pipeline

- **CI:** `.github/workflows/ci.yml` — pytest matrix over Python 3.10/3.11/3.12; installs `.[dev,reports]`
- **Publish:** `.github/workflows/publish.yml` — triggers on `v*.*.*` tags, OIDC Trusted Publishing
- **Tag pattern:** `git tag v0.4.0 && git push origin v0.4.0`

---

## Known gotchas (do not repeat these mistakes)

### 1. Windows cp1252 console — ASCII only in CLI output
Em dashes (`—`), right arrows (`->`) etc. cause `UnicodeEncodeError` on Windows cp1252 terminals. All CLI docstrings, `typer.echo()`, and `summary()` methods must use plain ASCII. Document content in HTML/PDF/DOCX files is fine.

### 2. Jinja2 does not expose Python builtins
`zip()` must be manually injected in every `jinja2.Environment`:
```python
env.globals["zip"] = zip
```
NCA templates in `nca/reporting.py` handle this via `_make_jinja_env()`.

### 3. `.gitignore` blocks HTML templates and notebooks
Exceptions declared in `.gitignore`: `!src/**/*.html`, `!demo.ipynb`. Add exceptions for any new templates.

### 4. `datasets/__init__.py` uses functions, not constants
`example_theoph_path()` — always call as a function, not a constant.

### 5. AUC method dispatch asymmetry
`auc_linear` returns `float`; `auc_log` and `auc_linear_up_log_down` return `AUCResult`. Always use the dispatch snippet in NCAStudy.analyze():
```python
if auc_method == "linear":
    auclast, auc_warnings = auc_linear(t, c), []
else:
    fn = auc_log if auc_method == "log" else auc_linear_up_log_down
    res = fn(t, c)
    auclast, auc_warnings = res.value, res.warnings
```

### 6. BLQ handling contract
The loader (`load_nca_csv`) applies BLQ handling before returning. The NCA math functions (`auc_linear`, etc.) do NOT handle NaN — they will raise or produce wrong results if passed NaN concentrations.

### 7. NCA lambda_z requires at least 3 post-Cmax positive points
If fewer are available, `lambda_z()` raises `ValueError`. `NCAStudy.analyze()` catches this and stores `lambda_z=None` with a warning in `NCAResult.warnings`.

### 8. Theoph regression values (linear_up_log_down, no BLQ)
Mean AUClast ~100.1, mean Cmax ~8.89 mg/L, mean half_life ~7.89 h, mean AUCinf ~119.4 h*mg/L.
These are self-consistent regression values from our implementation, NOT PKNCA vignette values (which differ due to configuration differences).

### 9. `[reports]` extra required for PDF/DOCX
`reportlab` and `python-docx` are optional. Renderers raise `ImportError` with a helpful message if not installed.

### 10. GitHub username is `priyamthakar` — not `priyamthakar1`

---

## Next: v0.5.0 — PK simulation

```python
from openpkflow.sim import PKModel

model = PKModel(n_compartments=1, route="oral")
result = model.simulate(dose=320, times=[0,1,2,4,8,12,24], params={"ka": 1.2, "CL": 3.2, "V": 30})
result.plot()
result.report("sim.html")
```

Scope: 1-compartment oral/IV bolus/IV infusion, repeated dosing, single-subject and population overlay.

---

## Positioning (memorize this)

**Use:**
> A transparent, reproducible, open-source Python workflow for dissolution, NCA, PK/PD simulation, and pharmacometric reporting.

**Never say:**
> "FDA-approved", "replaces Certara", "AI discovers the perfect formulation."

---

## Key references for pharmacometric correctness

- FDA 1997 Guidance: Dissolution Testing of Immediate Release Solid Oral Dosage Forms — f1/f2 definition and 85% rule
- Shah VP et al. (1998) Pharm Res 15(6):889-896 — bootstrap f2 methodology
- Costa P, Lobo JMS (2001) Eur J Pharm Sci 13:123-133 — dissolution model fitting
- Pinheiro JC, Bates DM (2000). Mixed-effects models in S and S-PLUS. Springer — Theoph dataset source
- Bacon S et al. (2023). PKNCA: Non-Compartmental Analysis for Pharmacokinetics. CRAN — BAR² algorithm reference
