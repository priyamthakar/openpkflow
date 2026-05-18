# OpenPKFlow — Session Context Handout

Read this at the start of every new session. It contains the full current state of the project, design decisions made, known gotchas, and what comes next. Cross-reference with `CLAUDE.md` for code conventions and pharmacometric rules.

---

## Identity

- **Package:** `openpkflow`
- **Author:** Priyam Thakar, priyamthakar1@gmail.com
- **GitHub:** https://github.com/priyamthakar/openpkflow (username: `priyamthakar`, not `priyamthakar1`)
- **PyPI:** https://pypi.org/project/openpkflow/ — live and installable
- **Working directory:** `D:\openpkflow`
- **Python floor:** 3.10+
- **Build:** hatchling, `src/` layout

---

## Current version: 0.3.0

Published to PyPI. GitHub Actions Trusted Publishing handles every release automatically on `v*.*.*` tags.

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

---

## What is actually built (v0.3.0)

### Public API — entry points users should use

```python
from openpkflow.dissolution import (
    f1, f2, DissolutionStudy, bootstrap_f2, BootstrapF2Result,
    ModelFit, DissolutionFitResults, fit_dissolution_models,
)
from openpkflow.datasets import example_dissolution_path, example_similar_path, example_not_similar_path
```

### `f1(reference, test)` / `f2(reference, test, *, method="all_points")`

Scalar functions. Take `Sequence[float]` (plain Python lists), return float.

`f2` accepts `method="all_points"` (default) or `method="regulatory"` which trims timepoints per the FDA 85% rule.

### `DissolutionStudy`

High-level study object. Always use this when working with CSV data.

```python
study = DissolutionStudy.from_csv("data.csv")
study.formulations()                          # -> list[str]
result = study.compare("reference", "test")   # -> ComparisonResult
boot   = study.bootstrap_compare("reference", "test", n_replicates=5000, seed=42)  # -> BootstrapF2Result
fits   = study.fit_models("reference")        # -> DissolutionFitResults
```

### `ComparisonResult`

Dataclass with: `f1_value`, `f2_value`, `n_timepoints`, `reference_mean`, `test_mean`, `time_points`.

```python
result.summary()                                  # -> str
result.report("out.html")                         # HTML (default)
result.report("out.md", format="markdown")        # Markdown
result.report("out.pdf", format="pdf")            # PDF via ReportLab (requires [reports])
result.report("out.docx", format="docx")          # Word via python-docx (requires [reports])
result.plot(output_path="plot.png", show=False)
result.to_dict()
```

### `DissolutionFitResults`

```python
fits.best             # -> ModelFit with lowest AICc
fits.summary()        # -> str, ASCII, ranked table
fits.plot()           # matplotlib overlay
fits.report("fit.html")                      # HTML report
fits.report("fit.pdf", format="pdf")         # PDF (requires [reports])
fits.report("fit.docx", format="docx")       # Word (requires [reports])
fits.to_dict()
```

`ModelFit` frozen dataclass: `model_name`, `params`, `r_squared`, `aic`, `aicc`, `bic`, `n_points`, `n_params`, `converged`. Has `predict(t_array)` and `to_dict()`.

Five standard models: `zero_order`, `first_order`, `higuchi`, `korsmeyer_peppas`, `weibull`.
Korsmeyer-Peppas fires `UserWarning` when >1 timepoint exceeds 60% release.
Weibull noted as empirical-only in report (FDA/EMA guidance context).

### `fit_dissolution_models(time_points, observed_mean, formulation_label, models=None)`

Low-level public API — fits without a loaded CSV. Returns `DissolutionFitResults`.

### `bootstrap_f2` / `BootstrapF2Result` (low-level)

`bootstrap_f2()` takes 2D numpy arrays. Users should call `study.bootstrap_compare()` instead.

### Datasets

```python
from openpkflow.datasets import example_dissolution_path, example_similar_path, example_not_similar_path
```

CSV format: `formulation,batch,time,percent_released`.

---

## Architecture: file map

```
src/openpkflow/
  __init__.py                    # version only
  cli.py                         # Typer CLI: version, similarity, dissolution compare
  py.typed                       # PEP 561 marker

  dissolution/
    __init__.py                  # exports all public symbols
    similarity.py                # f1(), f2()
    loader.py                    # load_dissolution_csv(), DissolutionCSVConfig
    study.py                     # DissolutionStudy, ComparisonResult
    bootstrap.py                 # bootstrap_f2(), BootstrapF2Result
    models.py                    # ModelFit, DissolutionFitResults, fit_dissolution_models()
                                 #   five model callables, _REGISTRY, AICc ranking
    plotting.py                  # dissolution_profile_plot_b64(), dissolution_fit_plot_b64()
    reporting.py                 # render_markdown_report(), report_dissolution()
                                 #   dispatcher for html/markdown/pdf/docx

  report/
    __init__.py
    html.py                      # render_html_report(), render_model_fit_html_report()
    pdf.py                       # render_comparison_pdf_report(), render_model_fit_pdf_report()
                                 #   lazy reportlab imports, [reports] extra guard
    docx.py                      # render_comparison_docx_report(), render_model_fit_docx_report()
                                 #   lazy docx imports, [reports] extra guard
    templates/
      dissolution_report.html    # Navy header comparison report
      fit_report.html            # Navy header model fit report

  datasets/
    __init__.py                  # example_*_path() functions
    example_dissolution.csv
    example_similar.csv
    example_not_similar.csv

  nca/, sim/, pop/, bayes/, ml/, validation/  # stubs only, not yet implemented
```

---

## Dissolution data flow

```
CSV file
  -> load_dissolution_csv()        pydantic-validated DataFrame
  -> DissolutionStudy.from_csv()   wraps DataFrame
  -> study.compare(ref, test)      get_formulation_means() -> f1/f2
  -> ComparisonResult
  -> result.report("out.html")     report_dissolution() -> render_html_report()
  -> result.report("out.pdf")      report_dissolution() -> render_comparison_pdf_report()
  -> result.report("out.docx")     report_dissolution() -> render_comparison_docx_report()

  -> study.fit_models("ref")       get_formulation_means() -> fit_dissolution_models()
  -> DissolutionFitResults
  -> fits.report("fit.html")       render_model_fit_html_report()
  -> fits.report("fit.pdf")        render_model_fit_pdf_report()
  -> fits.report("fit.docx")       render_model_fit_docx_report()
```

---

## Report format support matrix

| Format | Comparison | Model Fit | Notes |
|--------|-----------|-----------|-------|
| html   | yes       | yes       | Jinja2 templates; always available |
| markdown | yes     | no        | always available |
| pdf    | yes       | yes       | requires `pip install openpkflow[reports]` |
| docx   | yes       | yes       | requires `pip install openpkflow[reports]` |

CLI format inference: `.md`/`.markdown` -> markdown, `.pdf` -> pdf, `.docx` -> docx, else html.

---

## CI / Release pipeline

- **CI:** `.github/workflows/ci.yml` — pytest matrix over Python 3.10/3.11/3.12; installs `.[dev,reports]`
- **Publish:** `.github/workflows/publish.yml` — triggers on `v*.*.*` tags, OIDC Trusted Publishing
- **Tag pattern:** `git tag v0.x.x && git push origin v0.x.x`

---

## Known gotchas (do not repeat these mistakes)

### 1. Windows cp1252 console — ASCII only in CLI output
Em dashes (`—`), right arrows (`->`) etc. cause `UnicodeEncodeError` on Windows cp1252 terminals. All CLI docstrings and `typer.echo()` must use plain ASCII. Document content in PDF/DOCX files is fine (binary format).

### 2. Jinja2 does not expose Python builtins
`zip()` must be manually injected in every `jinja2.Environment`:
```python
env.globals["zip"] = zip
```

### 3. `.gitignore` blocks HTML templates and notebooks
Exceptions declared in `.gitignore`: `!src/**/*.html`, `!demo.ipynb`. Add exceptions for any new templates.

### 4. `datasets/__init__.py` uses functions, not constants
`example_dissolution_path()` — always call as a function, not a constant.

### 5. `bootstrap_f2` is low-level — use `study.bootstrap_compare()` in user-facing code

### 6. `[reports]` extra is required for PDF/DOCX
`reportlab` and `python-docx` are optional. The renderers raise `ImportError` with a helpful message if not installed. CI now installs `.[dev,reports]`.

### 7. `import docx` not `import python_docx`
The python-docx package imports as `import docx` even though it's installed as `python-docx`.

### 8. GitHub username is `priyamthakar` — not `priyamthakar1`

---

## Test suite (130 tests as of v0.3.0)

```
tests/
  dissolution/
    test_similarity.py    f1/f2 validation, regulatory method
    test_study.py         loader, compare, bootstrap, reports
    test_bootstrap.py     BootstrapF2Result
    test_models.py        5 models, AICc ranking, fit API, report
  report/
    test_pdf.py           magic bytes, file write, import guard (reportlab)
    test_docx.py          magic bytes, disclaimer round-trip, import guard (python-docx)
  test_cli.py             CLI commands
```

Run: `pytest` or `pytest --tb=short -q`

---

## Next: v0.4.0 — NCA engine

```python
from openpkflow.nca import NCAStudy
study = NCAStudy.from_csv("pk_data.csv")
result = study.compute("subject_01")
result.summary()   # AUC, Cmax, Tmax, lambda_z, t1/2, CL/F, Vz/F
result.report("nca.html")
```

NCA scope:
- AUClast (linear-log trapezoidal), AUCinf, AUCpct_extrap
- lambda_z (terminal slope via log-linear regression, adjustable fit range)
- t1/2 = ln(2)/lambda_z
- CL/F (oral), Vz/F — always labelled as apparent (slash-F) unless IV
- Cmax, Tmax from observed data
- BLQ handling: explicit method required (none / M1 / M2)

Key correctness rules from CLAUDE.md: AUC method must be explicit; apparent vs absolute parameter names must be distinguished; BLQ handling must be explicit.

After v0.4.0: v0.5.0 PK simulation (1-comp/2-comp, oral/IV/infusion, repeated dosing).

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
- Davit BM et al. (2013) AAPS J 15(4):1150-1157 — bootstrap f2 regulatory context
- Costa P, Lobo JMS (2001) Eur J Pharm Sci 13:123-133 — dissolution model fitting reference
