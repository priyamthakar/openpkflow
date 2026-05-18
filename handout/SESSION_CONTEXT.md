# OpenPKFlow — Session Context Handout

Read this at the start of every new session. It contains the full current state of the project, design decisions made, known gotchas, and what comes next. Cross-reference with `CLAUDE.md` for code conventions and pharmacometric rules.

---

## Identity

- **Package:** `openpkflow`
- **Author:** Priyam Thakar, priyamthakar1@gmail.com
- **GitHub:** https://github.com/priyamthakar/openpkflow (username: `priyamthakar`, not `priyamthakar1`)
- **PyPI:** https://pypi.org/project/openpkflow/ — v0.4.1 live; v0.9.0 local only (not yet uploaded)
- **Working directory:** `D:\openpkflow`
- **Python floor:** 3.10+
- **Build:** hatchling, `src/` layout

---

## Current version: 0.9.0 (local) / 0.4.1 (on PyPI)

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
| 0.4.0 | NCA engine: AUClast, AUCinf, Cmax, Tmax, lambda_z (BAR2), CL/F, Vz/F; HTML+Markdown reports; Theoph reference dataset; 93 NCA tests |
| 0.4.1 | NCA PDF (ReportLab) and Word (python-docx) reports; logo added; 26 new tests |
| 0.5.0 | PK simulation: 1-cmt/2-cmt oral/IV bolus/IV infusion, repeated dosing, superposition; HTML/MD/PDF/DOCX reports |
| 0.6.0 | Population PK diagnostics: GOF 4-panel plots, simulation-based VPC with percentile bands, NONMEM-style dataset helpers |
| 0.9.0 | ML surrogate: torch MLP (PKSurrogate) trained on analytical 1-cmt oral data; bayes ImportError guards wired; 363 tests total |

v0.7.0 reserved for Pharmpy bridge (deferred). v0.8.0 deferred: PyMC not installed in dev env; [bayes] extras are wired in pyproject.toml with ImportError guards in bayes/__init__.py.

---

## What is actually built (v0.9.0)

### Dissolution public API

```python
from openpkflow.dissolution import (
    f1, f2, DissolutionStudy, bootstrap_f2, BootstrapF2Result,
    ModelFit, DissolutionFitResults, fit_dissolution_models,
)
from openpkflow.datasets import example_dissolution_path, example_similar_path, example_not_similar_path
```

Key objects:
- `DissolutionStudy.from_csv(path)` -> compare, bootstrap_compare, fit_models
- `ComparisonResult` -- f1_value, f2_value, report(format="html"|"markdown"|"pdf"|"docx")
- `DissolutionFitResults` -- best model, AICc ranking, report(format=...)
- `ModelFit` frozen dataclass -- model_name, params, r_squared, aic, aicc, bic, predict()

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
result.CL_F, result.Vz_F             # float | None -- oral apparent
result.CL, result.Vz                  # float | None -- IV absolute
result.warnings                       # list[str]
result.summary()                      # ASCII str
result.to_dict()                      # flat dict
result.report("sub.html")             # HTML, Markdown, PDF, or DOCX

summary.summary()                     # ASCII tabular
summary.to_dataframe()                # pd.DataFrame, one row per subject
summary.report("summary.html")
```

NCA CSV format: `subject,time,conc,dose,route`
- dose in the same unit as conc*time (e.g. mg when conc is mg/L, time is h)
- route: `"oral"` -> CL_F/Vz_F; `"iv_bolus"` / `"iv_infusion"` -> CL/Vz

BLQ handling: "none" | "drop" | "zero" | "half_lloq" (needs lloq=) | "lloq" (needs lloq=)
Aliases: "m1" -> "drop", "m2" -> "zero"
String BLQ: `<0.5` in conc column is parsed and treated as BLQ.

### Sim public API

```python
from openpkflow.sim import simulate
from openpkflow.sim.models import OneCompartmentModel, TwoCompartmentModel
from openpkflow.sim.dosing import DoseRegimen
import numpy as np

model = OneCompartmentModel(route="oral", CL_F=5.0, Vz_F=50.0, ka=1.2)
regimen = DoseRegimen.from_repeated(amount=100.0, route="oral", tau=24.0, n_doses=3)
times = np.linspace(0, 72, 500)

result = simulate(model, regimen, times)
result.times    # np.ndarray
result.concs    # np.ndarray  <-- NOTE: use .concs not .concentrations
result.Cmax
result.Tmax
result.summary()
result.plot()
result.report("sim.html")   # HTML, Markdown, PDF, DOCX
```

Models: `OneCompartmentModel(route, CL_F, Vz_F, ka)`, `TwoCompartmentModel(route, CL_F, Vc_F, Vp_F, Q_F, ka=None)`
Routes: `"oral"`, `"iv_bolus"`, `"iv_infusion"` (+ `infusion_duration` for infusion)

### Population PK public API

```python
from openpkflow.pop import (
    PopCSVConfig, load_pop_csv, create_nonmem_dataset,
    GOFResult, compute_iwres, obs_pred_metrics,
    VPCResult, simulate_vpc,
)
```

GOF:
```python
gof = GOFResult(
    dv=[5.2, 8.1, 6.4, 3.2],
    pred=[4.9, 7.8, 6.0, 3.0],
    ipred=[5.1, 8.0, 6.3, 3.1],
    time=[1.0, 2.0, 4.0, 8.0],
    id=["S1", "S1", "S1", "S1"],
    sigma=0.15,
    study_label="Phase 1 Study",
)
gof.iwres           # np.ndarray property
gof.pred_metrics()  # dict: n, MPE, RMSE, rRMSE_pct, R2
gof.ipred_metrics()
gof.summary()
gof.plot()          # matplotlib Figure
gof.report("gof.html")   # HTML, Markdown, PDF, DOCX
```

VPC:
```python
observed = pd.DataFrame({"TIME": [1,2,4,8,12], "DV": [5.1,8.2,6.5,3.8,2.1]})
vpc = simulate_vpc(
    model, regimen, observed,
    sigma_proportional=0.15,
    n_replicates=500,
    seed=42,
)
vpc.summary()
vpc.plot()
vpc.report("vpc.html")
```

NONMEM dataset helpers:
```python
config = PopCSVConfig(id_col="ID", time_col="TIME", dv_col="DV")
df = load_pop_csv("pop_data.csv", config, obs_only=True)

ds = create_nonmem_dataset(
    subject_id="S1",
    dose_times=[0.0, 24.0],
    dose_amounts=[100.0, 100.0],
    obs_times=[1.0, 2.0, 4.0],
    obs_dv=[5.1, 8.2, 6.5],
    route="oral",
)
```

### ML public API (EXPERIMENTAL)

```python
from openpkflow.ml import PKSurrogate

surr = PKSurrogate.from_1cmt_oral(
    n_samples=2000,
    n_timepoints=20,
    t_max=24.0,
    hidden_sizes=(64, 64),
    epochs=300,
    lr=1e-3,
    seed=42,
)
surr.summary()
X = np.array([[t, dose, CL_F, Vz_F, ka] for ...])
y_pred = surr.predict(X)   # np.ndarray, clipped >= 0
```

Training data is synthetic: c_1cmt_oral() called on random (time, dose, CL_F, Vz_F, ka) grid.
Activation: Tanh. Optimizer: Adam. Inputs z-score normalized. Output z-score normalized.
This is an experimental surrogate -- not for regulatory use.

### Bayes (stubs only -- PyMC not installed)

```python
from openpkflow.bayes import _require_pymc
# Raises ImportError with: "pip install openpkflow[bayes]"
```

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
    methods.py                     pure math: AUC (3 methods), cmax, tmax, lambda_z (BAR2),
                                   auc_inf_obs, auc_percent_extrapolated,
                                   clearance_volume_parameters; AUCResult, LambdaZResult
    loader.py                      load_nca_csv() with BLQ handling
    results.py                     NCAResult, NCASummaryResults dataclasses
    study.py                       NCAStudy: from_csv(), analyze()
    reporting.py                   report_nca_single(), report_nca_summary()

  sim/
    __init__.py                    exports all public sim symbols
    methods.py                     pure math: c_1cmt_iv_bolus, c_1cmt_iv_infusion, c_1cmt_oral,
                                   c_2cmt_iv_bolus, c_2cmt_oral, superpose
    dosing.py                      Dose, DoseRegimen dataclasses; DoseRegimen.from_repeated()
    models.py                      OneCompartmentModel, TwoCompartmentModel
    simulate.py                    simulate(model, regimen, times) -> SimulationResult
    results.py                     SimulationResult: .times, .concs, .Cmax, .Tmax, .summary(), .plot(), .report()
    plotting.py                    pk_profile_plot_b64() base64 PNG helper
    reporting.py                   report_simulation() dispatcher (HTML, Markdown, PDF, DOCX)

  pop/
    __init__.py                    exports: PopCSVConfig, load_pop_csv, create_nonmem_dataset,
                                   GOFResult, compute_iwres, obs_pred_metrics,
                                   VPCResult, simulate_vpc
    dataset.py                     PopCSVConfig, load_pop_csv(), create_nonmem_dataset()
    gof.py                         compute_iwres(), obs_pred_metrics(), GOFResult
    vpc.py                         VPCResult, simulate_vpc()
    plotting.py                    _gof_figure(), _vpc_figure(), gof_plots_b64(), vpc_plot_b64()
    reporting.py                   report_gof(), report_vpc() (HTML, Markdown, PDF, DOCX)

  bayes/
    __init__.py                    ImportError guard: _require_pymc() -- pymc NOT installed

  ml/
    __init__.py                    exports: PKSurrogate
    surrogate.py                   PKSurrogate dataclass -- MLP surrogate for 1-cmt oral

  report/
    __init__.py
    html.py                        dissolution HTML renderers (Jinja2)
    pdf.py                         dissolution + NCA + sim + GOF + VPC PDF renderers (ReportLab)
    docx.py                        dissolution + NCA + sim + GOF + VPC DOCX renderers (python-docx)
    templates/
      dissolution_report.html      comparison report template
      fit_report.html              model fit report template
      nca_single_report.html       NCA per-subject report
      nca_summary_report.html      NCA multi-subject summary
      sim_report.html              simulation report template
      pop_gof_report.html          GOF 4-panel report template
      pop_vpc_report.html          VPC report template

  datasets/
    __init__.py                    example_dissolution_path(), example_similar_path(),
                                   example_not_similar_path(), example_theoph_path()
    example_dissolution.csv
    example_similar.csv
    example_not_similar.csv
    theoph.csv                     R nlme::Theoph -- 12 subjects, oral theophylline

  validation/                      stubs only
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
     -> summary.report("summary.html|md|pdf|docx")
     -> result.report("sub.html|md|pdf|docx")
```

### Simulation

```
OneCompartmentModel(route, CL_F, Vz_F, ka)
  + DoseRegimen.from_repeated(amount, route, tau, n_doses)
  + np.linspace(0, T, N)
  -> simulate()               per-dose analytical superposition (linear systems only)
  -> SimulationResult         .times, .concs, .Cmax, .Tmax
  -> result.report("sim.html|md|pdf|docx")
```

### Population PK

```
GOFResult(dv, pred, ipred, time, id, sigma)
  -> gof.iwres                 np.ndarray (IWRES under proportional error)
  -> gof.pred_metrics()        dict: n, MPE, RMSE, rRMSE_pct, R2
  -> gof.report("gof.html")

simulate_vpc(model, regimen, observed_df, sigma_proportional, n_replicates, seed)
  -> VPCResult                 .bin_mids, .obs_lower/median/upper, .sim_lower/median/upper
  -> vpc.report("vpc.html")
```

---

## Report format support matrix

| Format   | Dissolution | Model fit | NCA single | NCA summary | Simulation | GOF | VPC |
|----------|-------------|-----------|------------|-------------|------------|-----|-----|
| html     | yes | yes | yes | yes | yes | yes | yes |
| markdown | yes | no  | yes | yes | yes | yes | yes |
| pdf      | yes* | yes* | yes* | yes* | yes* | yes* | yes* |
| docx     | yes* | yes* | yes* | yes* | yes* | yes* | yes* |

*requires `pip install openpkflow[reports]`

---

## Test suite (363 tests as of v0.9.0)

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
  sim/
    test_methods.py            analytical solutions, hand-checked values
    test_dosing.py             Dose, DoseRegimen, from_repeated()
    test_simulate.py           simulate() API, SimulationResult fields
    test_models.py             OneCompartmentModel, TwoCompartmentModel
    test_reporting.py          HTML/MD/PDF/DOCX report dispatch
  pop/
    test_dataset.py            PopCSVConfig, load_pop_csv, create_nonmem_dataset (10 tests)
    test_gof.py                IWRES formula, metrics, shape mismatch, sigma guard (14 tests)
    test_vpc.py                simulate_vpc shape, reproducibility, sigma=0 (16 tests)
  ml/
    test_surrogate.py          PKSurrogate fit/predict/from_1cmt_oral (9 tests, skipif no torch)
  report/
    test_pdf.py                magic bytes, file write, import guard
    test_docx.py               magic bytes, disclaimer round-trip, import guard
  test_cli.py                  CLI commands
```

---

## CI / Release pipeline

- **CI:** `.github/workflows/ci.yml` -- pytest matrix over Python 3.10/3.11/3.12; installs `.[dev,reports]`
- **Publish:** `.github/workflows/publish.yml` -- triggers on `v*.*.*` tags, OIDC Trusted Publishing
- **Tag pattern:** `git tag v0.9.0 && git push origin v0.9.0`
- **PyPI status:** v0.4.1 is the live PyPI version. v0.9.0 tagged locally, wheel clean, not yet uploaded.

---

## Known gotchas (do not repeat these mistakes)

### 1. Windows cp1252 console -- ASCII only in CLI output
Em dashes, unicode arrows etc. cause `UnicodeEncodeError` on Windows cp1252 terminals. All CLI docstrings, `typer.echo()`, and `summary()` methods must use plain ASCII. Document content in HTML/PDF/DOCX files is fine.

### 2. Jinja2 does not expose Python builtins
`zip()` and `range()` must be manually injected in every `jinja2.Environment`:
```python
env.globals["zip"] = zip
env.globals["range"] = range
```
All reporting modules do this via their `_make_jinja_env()` or inline before `env.get_template()`.

### 3. `.gitignore` blocks HTML templates and notebooks
Exceptions declared in `.gitignore`: `!src/**/*.html`, `!demo.ipynb`. Add exceptions for any new templates.

### 4. `datasets/__init__.py` uses functions, not constants
`example_theoph_path()` -- always call as a function, not a constant.

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
The loader (`load_nca_csv`) applies BLQ handling before returning. The NCA math functions do NOT handle NaN -- they will raise or produce wrong results if passed NaN concentrations.

### 7. NCA lambda_z requires at least 3 post-Cmax positive points
If fewer are available, `lambda_z()` raises `ValueError`. `NCAStudy.analyze()` catches this and stores `lambda_z=None` with a warning.

### 8. Theoph regression values (linear_up_log_down, no BLQ)
Mean AUClast ~100.1, mean Cmax ~8.89 mg/L, mean half_life ~7.89 h, mean AUCinf ~119.4 h*mg/L.
These are self-consistent regression values from our implementation, NOT PKNCA vignette values.

### 9. `[reports]` extra required for PDF/DOCX
`reportlab` and `python-docx` are optional. Renderers raise `ImportError` with a helpful message if not installed.

### 10. GitHub username is `priyamthakar` -- not `priyamthakar1`

### 11. SimulationResult uses `.concs` not `.concentrations`
The field is `result.concs` (np.ndarray). Using `.concentrations` raises AttributeError.

### 12. DOCX heading color -- inline pattern, no helper
Existing DOCX renderers use `_NAVY_RGB = RGBColor(0x0D, 0x3B, 0x66)` inline. There is no `_set_heading_color()` helper function -- do not attempt to call one.

### 13. VPC bins can contain NaN
`VPCResult.obs_lower/median/upper` may be NaN when a bin has no observed data. Jinja2 templates handle this with `if obs_lower[i] == obs_lower[i]` (NaN identity check). Use `np.testing.assert_array_equal` with explicit float dtype cast in tests.

### 14. PKSurrogate is experimental -- skip in CI if torch absent
`tests/ml/test_surrogate.py` uses `pytestmark = pytest.mark.skipif(not _HAS_TORCH, ...)`. The `[ml]` extra installs torch but it is not in the CI matrix by default.

### 15. pdf.py has 5 identical pattern blocks -- use surrounding context for Edit
The `if output_path is not None: ... return pdf_bytes` block appears 5 times (one per report type). When editing, always include the preceding `story.append(...)` line as context to uniquely identify the insertion point.

---

## Next: v1.0.0 -- stable public release

Tasks for v1.0.0:
- Final API review and any breaking-change cleanup
- Complete CI matrix (Python 3.10/3.11/3.12/3.13)
- Upload v0.9.0 to PyPI (or go straight to v1.0.0)
- MkDocs documentation site at https://priyamthakar.github.io/openpkflow/
- Bump `Development Status` classifier from `2 - Pre-Alpha` to `4 - Beta` or `5 - Production/Stable`
- CITATION.cff

---

## Positioning (memorize this)

**Use:**
> A transparent, reproducible, open-source Python workflow for dissolution, NCA, PK/PD simulation, and pharmacometric reporting.

**Never say:**
> "FDA-approved", "replaces Certara", "AI discovers the perfect formulation."

---

## Key references for pharmacometric correctness

- FDA 1997 Guidance: Dissolution Testing of Immediate Release Solid Oral Dosage Forms -- f1/f2 definition and 85% rule
- Shah VP et al. (1998) Pharm Res 15(6):889-896 -- bootstrap f2 methodology
- Costa P, Lobo JMS (2001) Eur J Pharm Sci 13:123-133 -- dissolution model fitting
- Pinheiro JC, Bates DM (2000). Mixed-effects models in S and S-PLUS. Springer -- Theoph dataset source
- Bacon S et al. (2023). PKNCA: Non-Compartmental Analysis for Pharmacokinetics. CRAN -- BAR2 algorithm reference
