# OpenPKFlow

<p align="center">
  <img src="docs/logo.png" alt="OpenPKFlow" width="640"/>
</p>

**A transparent, reproducible, open-source Python workflow for dissolution, NCA,
PK/PD simulation, and pharmacometric reporting. Core calculations are backed by
executable reference and analytical tests, with report-first outputs for review.**

[![CI](https://github.com/priyamthakar/openpkflow/actions/workflows/ci.yml/badge.svg)](https://github.com/priyamthakar/openpkflow/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/priyamthakar/openpkflow/branch/main/graph/badge.svg)](https://codecov.io/gh/priyamthakar/openpkflow)
[![PyPI version](https://img.shields.io/pypi/v/openpkflow)](https://pypi.org/project/openpkflow/)
[![Python](https://img.shields.io/pypi/pyversions/openpkflow)](https://pypi.org/project/openpkflow/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Docs](https://img.shields.io/badge/docs-live-brightgreen)](https://priyamthakar.github.io/openpkflow/)

---

## What it does

OpenPKFlow gives formulation scientists, PK/PD researchers, and CRO/CDMO teams a clean Python workflow for:

- **Dissolution similarity:** f1, f2, bootstrap f2, maximum deviation, MSD (Mahalanobis Statistical Distance), model fitting (Weibull, Higuchi, first-order, zero-order, Korsmeyer-Peppas), model-dependent comparison via 90% CI
- **NCA:** AUClast, AUCinf, Cmax, Tmax, lambda_z, half-life, CL/F, Vz/F; three AUC methods, explicit BLQ handling, %AUCextrap flag, dose-normalised parameters, CDISC PP output; model-informed one-compartment oral screening from 3+ samples
- **Bayesian PK (v2.0.0):** MAP individual PK estimation (scipy, no extra deps) plus full posterior via PyMC (`[bayes]` extra); Bayesian 2x2 crossover BE with P(GMR in 80-125) decision quantity alongside frequentist 90% CI
- **Bioequivalence:** paired 2x2 TOST, formal complete balanced TR/RT 2x2 crossover
  ANOVA, and validated FDA balanced partial-replicate RSABE; research-grade replicate
  screening remains separate
- **Report generation:** Markdown, HTML, PDF, Word
- **Study pipeline and web app:** optional dissolution, NCA, and paired-BE orchestration;
  unified reports; reproducibility audit ZIP; React pages backed by a thin FastAPI adapter.
  **Try it: [openpkflow.priyamthakar1.workers.dev](https://openpkflow.priyamthakar1.workers.dev)**
- **PK simulation:** 1- and 2-compartment models, oral/IV bolus/IV infusion, repeated dosing
- **Population PK diagnostics:** 4-panel GOF plots (OBS vs PRED, IWRES vs TIME/IPRED), simulation-based VPC with percentile bands, NONMEM-style dataset helpers
- **Population PK estimation (v2.3.0):** FOCE-I (scipy, zero extra deps) and SAEM (PyMC `[bayes]` extra) for 1- and 2-compartment oral/IV models; diagonal or full Omega block matrix; `PopPKResult` with `.summary()`, `.plot()` (6-panel), `.report()` (research-grade; FOCE-I sanity-checked against the `nlme` Theophylline reference)
- **Theory guide:** Full LaTeX formula derivations for every module (NCA, simulation, dissolution, IVIVC, BE, pop PK, Bayesian PK) for regulatory review support and teaching
- **ML surrogate (experimental):** torch MLP that approximates 1-cmt oral profiles

It does not replace expert regulatory judgement or validated commercial platforms.
It makes routine analysis faster, cleaner, and more reproducible.

---

## Install

```bash
pip install openpkflow
```

For PDF and Word reports:

```bash
pip install openpkflow[reports]
```

For full Bayesian PK (PyMC MCMC):

```bash
pip install openpkflow[bayes]
```

---

## Quick start: dissolution similarity

```python
from openpkflow.dissolution import f1, f2

reference = [20.0, 40.0, 60.0, 80.0, 90.0]
test      = [21.0, 39.0, 61.0, 79.0, 88.0]

print(f"f1 = {f1(reference, test):.2f}")
print(f"f2 = {f2(reference, test):.2f}")
```

### From a CSV file

```python
from openpkflow.dissolution import DissolutionStudy

study = DissolutionStudy.from_csv("dissolution.csv")
# or load directly from Excel (requires pip install openpkflow[reports]):
# study = DissolutionStudy.from_excel("dissolution.xlsx", sheet_name="Data")

result = study.compare(reference="reference", test="test")
result.summary()
result.report("dissolution_report.html")
result.report("dissolution_report.pdf", format="pdf")   # requires [reports]
```

CSV format: `formulation,batch,time,percent_released`

### Advanced dissolution workbench

```python
from openpkflow.dissolution import (
    DissolutionWorkbenchConfig,
    run_dissolution_workbench_csv,
)

config = DissolutionWorkbenchConfig(
    reference_label="reference",
    test_label="test",
    bootstrap_replicates=5000,
    seed=2026,
)
workbench = run_dissolution_workbench_csv("vessel_profiles.csv", config)
print(workbench.comparison.summary())
print(workbench.reference_models.summary())
workbench.report("dissolution_workbench.html")
workbench.audit_bundle("dissolution_workbench_audit.zip")
```

The workbench requires at least two vessels per formulation and three identical
time points in every vessel. It never interpolates or silently reindexes f1/f2
inputs. See the
[workbench tutorial](https://priyamthakar.github.io/openpkflow/tutorials/dissolution-workbench/).

### CLI

```bash
openpkflow version
openpkflow similarity --reference "20,40,60,80" --test "21,39,61,79"
```

---

## Quick start: NCA

```python
from openpkflow.nca import NCAStudy

study = NCAStudy.from_csv(
    "pk_data.csv",
    auc_method="linear_up_log_down",   # required: "linear", "log", or "linear_up_log_down"
    blq_method="none",                  # required: "none", "drop", "zero", "half_lloq", "lloq"
)
summary = study.analyze()
print(summary.summary())               # tabular ASCII output

# Per-subject results
result = summary.results[0]
print(f"Subject: {result.subject}")
print(f"AUClast: {result.AUClast:.2f} h*mg/L")
print(f"Cmax:    {result.Cmax:.2f} mg/L")
print(f"Tmax:    {result.Tmax:.2f} h")
print(f"t1/2:    {result.half_life:.2f} h")
print(f"CL/F:    {result.CL_F:.2f} L/h")

# Reports
result.report("nca_subject1.html")
summary.report("nca_summary.html")
```

### NCA CSV format

```csv
subject,time,conc,dose,route
1,0.0,0.0,320.0,oral
1,0.5,4.2,320.0,oral
1,1.0,8.1,320.0,oral
1,2.0,6.8,320.0,oral
1,4.0,3.5,320.0,oral
1,8.0,1.7,320.0,oral
1,12.0,0.9,320.0,oral
1,24.0,0.2,320.0,oral
```

Required columns: `subject`, `time`, `conc`, `dose`, `route`.
Dose units must match concentration x time (mg when conc is mg/L and time is h).
Route values: `"oral"`, `"iv_bolus"`, `"iv_infusion"`.

Oral route yields apparent clearance and volume: `CL_F`, `Vz_F`.
IV routes yield absolute clearance and volume: `CL`, `Vz`.

---

## Quick start: PK simulation

```python
import numpy as np
from openpkflow.sim import simulate
from openpkflow.sim.models import OneCompartmentModel
from openpkflow.sim.dosing import DoseRegimen

model = OneCompartmentModel(route="oral", CL_F=5.0, Vz_F=50.0, ka=1.2)
regimen = DoseRegimen.from_repeated(amount=100.0, route="oral", tau=24.0, n_doses=3)
times = np.linspace(0, 72, 500)

result = simulate(model, regimen, times)
print(result.summary())
result.report("sim_report.html")
result.report("sim_report.pdf", format="pdf")   # requires [reports]
```

---

## Quick start: Bayesian individual PK (MAP)

```python
from openpkflow.bayes import map_individual_pk, PKPrior
import math

# Noiseless 1-cmt oral data (CL_F=5, Vz_F=50, ka=1.2, dose=100)
times = [0.5, 1.0, 2.0, 4.0, 8.0, 12.0]
concs = [1.23, 1.85, 1.97, 1.61, 0.89, 0.49]

result = map_individual_pk(times, concs, dose=100.0, route="oral", subject="S01")
print(result.summary())   # MAP estimates, SEs, diagnostics, disclaimer
result.report("map_pk_report.html")
```

For full posterior sampling (requires `pip install openpkflow[bayes]`):

```python
from openpkflow.bayes.bayes_pk import bayes_individual_pk

result = bayes_individual_pk(times, concs, dose=100.0, route="oral",
                              n_samples=1000, tune=1000, chains=2)
print(f"CL_F = {result.cl_mean:.3g}  [95% CrI: {result.cl_95ci[0]:.3g}, {result.cl_95ci[1]:.3g}]")
print(f"P(shrinkage) = {result.shrinkage_cl:.1%}")
```

## Quick start: Bayesian bioequivalence (requires `[bayes]`)

```python
import pandas as pd
from openpkflow.bayes.bayes_be import bayes_be

# Long-format 2x2 crossover data
data = pd.DataFrame({
    "subject":   ["S01","S01","S02","S02","S03","S03","S04","S04"],
    "sequence":  ["RT", "RT", "TR", "TR", "RT", "RT", "TR", "TR"],
    "period":    [1,    2,    1,    2,    1,    2,    1,    2   ],
    "treatment": ["R",  "T",  "T",  "R",  "R",  "T",  "T",  "R" ],
    "value":     [98.0, 103.0, 95.0, 91.0, 107.0, 112.0, 99.0, 94.0],
})

result = bayes_be(data, metric="AUC", n_samples=2000, tune=1000, chains=2)
print(f"P(BE) = {result.p_be:.3f}")
print(f"GMR = {result.gmr_mean:.4g}  [95% CrI: {result.gmr_95ci[0]:.4g}, {result.gmr_95ci[1]:.4g}]")
print(f"Frequentist 90% CI: [{result.freq_90ci[0]:.4g}, {result.freq_90ci[1]:.4g}]")
result.report("bayes_be_report.html")
```

---

## Quick start: bioequivalence

```python
import pandas as pd
from openpkflow.be import BEStudy

# Wide-format DataFrame: one row per subject, reference and test PK parameter values
be_df = pd.DataFrame({
    "subject":   ["S01", "S02", "S03", "S04", "S05", "S06"],
    "sequence":  ["RT",  "RT",  "RT",  "TR",  "TR",  "TR"],
    "reference": [100.2, 98.7, 105.1, 97.3, 102.8, 99.5],
    "test":      [95.1,  94.0,  99.8, 92.9,  97.4, 94.8],
})

study = BEStudy(be_df, parameter="AUCinf")
result = study.analyze()          # default: 80-125%, alpha=0.05
print(result.summary())
result.report("be_report.html")

# NTI products: pass narrower limits
result_nti = study.analyze(be_lower=0.90, be_upper=1.1111)
```

### From NCAStudy results (convenience)

```python
from openpkflow.be import BEStudy

# Run NCA separately on each formulation's PK data
# reference_nca_summary = NCAStudy.from_csv("ref_pk.csv", ...).analyze()
# test_nca_summary      = NCAStudy.from_csv("test_pk.csv", ...).analyze()

study = BEStudy.from_nca_results(
    reference_nca_summary, test_nca_summary, parameter="AUCinf"
)
result = study.analyze()
```

### Formal complete balanced 2x2 BE ANOVA

OpenPKFlow supports formal complete balanced `TR`/`RT` 2x2 crossover ANOVA with
long-format data, ANOVA source tables, a treatment contrast, GMR, confidence interval,
and residual CV. It rejects incomplete or unbalanced designs rather than changing the
estimand silently.

```python
from openpkflow.be import formal_be_anova

formal_result = formal_be_anova(long_be_df, parameter="AUCinf")
formal_result.report("formal_be_report.html")
```

FDA partial-replicate `TRR`/`RTR`/`RRT` RSABE is implemented and validated against
Patterson & Jones (2012) *Pharmaceutical Statistics* 11(1):1-7, Table II
(DOI 10.1002/pst.498); `NOT_EVALUABLE` is returned only when the reference is not
highly variable (CVwR < 30%), in which case standard average BE applies instead.
Requires balanced sequence allocation (equal subjects per sequence) — unbalanced
data (e.g. from unequal dropout) fails closed rather than being silently biased.
EMA ABEL, full-replicate RSABE, and NTI decisions remain out of scope.

```python
from openpkflow.be import fda_partial_replicate_rsabe

rsabe_result = fda_partial_replicate_rsabe(partial_replicate_df, parameter="AUC")
rsabe_result.report("rsabe_report.html")
```

### CLI

```bash
openpkflow be compare be_data.csv --parameter AUCinf --report be_report.html
openpkflow be anova formal_be_data.csv --parameter AUCinf --report formal_be_report.html
```

CSV format: `subject, sequence, reference, test`

---

## Quick start: population PK diagnostics

```python
import pandas as pd
from openpkflow.pop import GOFResult, simulate_vpc
from openpkflow.sim.models import OneCompartmentModel
from openpkflow.sim.dosing import DoseRegimen

# GOF: supply your own PRED/IPRED from NONMEM or nlmixr2
gof = GOFResult(
    dv=[5.2, 8.1, 6.4, 3.2],
    pred=[4.9, 7.8, 6.0, 3.0],
    ipred=[5.1, 8.0, 6.3, 3.1],
    time=[1.0, 2.0, 4.0, 8.0],
    id=["S1", "S1", "S1", "S1"],
    sigma=0.15,
    study_label="Phase 1 Study",
)
print(gof.summary())
gof.report("gof_report.html")

# Simulation-based VPC
model = OneCompartmentModel(route="oral", CL_F=5.0, Vz_F=50.0, ka=1.2)
regimen = DoseRegimen.from_repeated(amount=100.0, route="oral", tau=24.0, n_doses=1)
observed = pd.DataFrame({"TIME": [1, 2, 4, 8, 12], "DV": [5.1, 8.2, 6.5, 3.8, 2.1]})

vpc = simulate_vpc(model, regimen, observed, n_replicates=500, seed=42)
vpc.report("vpc_report.html")
```

---

## Feature comparison

| Capability | OpenPKFlow | PKNCA (R) | WinNonlin | Pharmpy |
|---|---|---|---|---|
| Dissolution f1 / f2 | :white_check_mark: | :x: | :white_check_mark: | :x: |
| Bootstrap f2 | :white_check_mark: | :x: | :x: | :x: |
| Dissolution model fitting (5 models + AICc) | :white_check_mark: | :x: | :x: | :x: |
| MSD / max deviation / model-dependent comparison | :white_check_mark: | :x: | :white_check_mark: | :x: |
| NCA (AUClast, AUCinf, CL/F, lambda_z), cross-validated vs Phoenix WinNonlin | :white_check_mark: | :white_check_mark: | :white_check_mark: | :x: |
| C0 back-extrapolation for IV bolus (matches WinNonlin within 2%) | :white_check_mark: | :white_check_mark: | :white_check_mark: | :x: |
| %AUCextrap flag, dose-normalised params | :white_check_mark: | :white_check_mark: | :white_check_mark: | :x: |
| CDISC PP output (SDTM, PPTESTCD codes) | :white_check_mark: | :x: | :white_check_mark: | :x: |
| Bioequivalence convenience (paired 2x2 TOST) | :white_check_mark: | :x: | :white_check_mark: | :x: |
| PK simulation (1/2-cmt, oral/IV) | :white_check_mark: | :x: | :white_check_mark: | :white_check_mark: |
| Population PK diagnostics (GOF, VPC) | :white_check_mark: | :x: | :x: | :white_check_mark: |
| Multi-format reports (HTML, PDF, DOCX) | :white_check_mark: | :x: | :white_check_mark: | :x: |
| Open-source and free | :white_check_mark: | :white_check_mark: | :x: | :white_check_mark: |
| Python-native API | :white_check_mark: | :x: | :x: | :white_check_mark: |
| Regulatory reference validation (citations) | :white_check_mark: | :white_check_mark: | :white_check_mark: | :x: |
| IVIVC (Level A) | :white_check_mark: (v1.2.0) | :x: | :white_check_mark: | :x: |
| Multi-media dissolution | :white_check_mark: (v1.4.0) | :x: | :white_check_mark: | :x: |
| Sparse oral PK screening (model-informed) | :white_check_mark: (v1.5.0) | :white_check_mark: | :x: | :x: |
| Steady-state NCA + urinary excretion | :white_check_mark: (v1.3.0) | :white_check_mark: | :white_check_mark: | :x: |
| MAP individual PK (scipy, no extra deps) | :white_check_mark: (v2.0.0) | :x: | :white_check_mark: | :x: |
| Full Bayesian PK + Bayesian BE (PyMC) | :white_check_mark: (v2.0.0) | :x: | :x: | :x: |
| Population PK estimation: FOCE-I + SAEM (1/2-cmt, full Omega) | :white_check_mark: (v2.3.0)\* | :x: | :x: | :x: |
| Replicate BE screening (CVwR/scaled-limit summaries) | :white_check_mark: (v2.4.0)\*\* | :x: | :white_check_mark: | :x: |
| Formal complete balanced 2x2 BE ANOVA | :white_check_mark: | :x: | :white_check_mark: | :x: |
| Study pipeline (dissolution + NCA + BE orchestration) | :white_check_mark: (v2.6.0) | :x: | :x: | :x: |
| SUPAC-IR screening + alcohol dose-dumping f2 | :white_check_mark: (v2.6.0)\*\*\* | :x: | :x: | :x: |
| IVIVC Level B/C helpers (MDT/MRT) | :white_check_mark: (v2.6.0) | :x: | :x: | :x: |
| Transit-compartment oral absorption + SS metrics | :white_check_mark: (v2.6.0) | :x: | :x: | :x: |
| FDA partial-replicate RSABE decision | :white_check_mark: validated (Patterson & Jones 2012) | :x: | :white_check_mark: | :x: |

\* Research-grade; FOCE-I typical values are sanity-checked against `nlme` Theophylline reference values. See [HANDOFF.md](HANDOFF.md).
\*\* Research-grade screening only; not a validated FDA/EMA RSABE submission engine.
\*\*\* Screening helper with documented thresholds; not full SUPAC guidance automation.

## Roadmap

Post-1.0.0: IVIVC Level A, multi-media, SS/urine NCA, sparse NCA, Bayesian PK/BE,
FOCE-I/SAEM (frozen), replicate BE screening (v2.4), web app (v2.5), study pipeline +
SUPAC/alcohol + IVIVC B/C + transit (v2.6), and sparse NCA + formal BE/RSABE +
pipeline/web hardening (v2.7). See [ROADMAP.md](ROADMAP.md),
[HANDOFF.md](HANDOFF.md), and
[SESSION_SUMMARY_2026-07-28.md](SESSION_SUMMARY_2026-07-28.md) for current state.

v2.8.0 is the current published release. It adds the Advanced Dissolution
Workbench across the core package, API, web app, reports, and reproducibility
bundle without adding new pharmacometric formulas. See
[FUTURE_PLANS.md](FUTURE_PLANS.md) for demand-gated follow-up ideas.

---

## Current status

| Module | Status |
|---|---|
| Dissolution f1 / f2 | Stable |
| MSD / max deviation / model-dependent comparison | Stable |
| Bootstrap f2 | Stable |
| Dissolution CSV loader | Stable |
| Dissolution model fitting (AICc ranking) | Stable |
| SUPAC-IR screening + alcohol dose-dumping f2 | Stable screening (v2.6.0) |
| IVIVC Level A | Stable (v1.2.0) |
| IVIVC Level B/C helpers (MDT/MRT) | Stable (v2.6.0) |
| Multi-media dissolution | Stable (v1.4.0) |
| Study pipeline (`openpkflow study run`) | Stable (v2.6.0) |
| HTML, Markdown, PDF, Word reports | Stable |
| NCA (incl. steady-state, urinary, CDISC PP) | Stable |
| Sparse one-compartment oral fit | Model-informed screening; externally cross-checked |
| PK simulation (1/2-comp + transit oral + SS metrics) | Stable (v2.6.0) |
| Population PK diagnostics (GOF, VPC) | Stable |
| FOCE-I / SAEM pop PK estimation\* | Stable research-grade; **frozen** for extension |
| Covariate modeling | Removed (v2.3.0) |
| MAP / Bayesian PK + Bayesian BE | Stable (v2.0.0) |
| Bioequivalence TOST + power/n + replicate screening\*\* | Stable |
| Formal complete balanced 2x2 crossover ANOVA | Stable; independent R cross-check |
| FDA partial-replicate RSABE | Stable; validated against Patterson & Jones (2012) Table II |
| Web app (`api/` + `webapp/`) | Stable through v2.8.0; includes the Advanced Dissolution Workbench and 32 API endpoints. [Live demo](https://openpkflow.priyamthakar1.workers.dev) |
| ML surrogate (torch MLP, EXPERIMENTAL) | Prototype (v0.9.0) |

\* Research-grade; FOCE-I checked against `nlme` Theophylline reference. See [HANDOFF.md](HANDOFF.md).
\*\* Replicate BE is research-grade screening only.

---

## By the numbers

Measured from the `agent/sparse-nca-web` working tree on 2026-07-16:

| Stat | Value |
|---|---|
| Lines of Python source (`src/`) | 20,658 |
| Lines of Python tests (`tests/`) | 14,308 |
| Python files | 164 (80 source + 84 tests) |
| Standard test selection | 1,285 selected, 22 deselected |
| HTML report templates | 13 |
| Bundled example datasets | 5 |

---

## Validation

Validation combines published/public comparator outputs, analytical solutions, and
hand-checkable sanity cases. Each scientific reference test identifies its comparator
or source; the exact scope is documented in [VALIDATION.md](VALIDATION.md).

**NCA: four-way cross-validation against Phoenix WinNonlin:**
NCA results are cross-validated against Phoenix WinNonlin (Certara), PKNCA 0.12.1, and NonCompart 0.8.0
on the standard R `nlme::Theoph` (12-subject oral theophylline) and `nlme::Indometh` (6-subject IV bolus
indomethacin) datasets. Key validated parameters: AUClast, AUCinf, CL/F, Vz/F, lambda_z, half-life.
C0 back-extrapolation for IV bolus data (WinNonlin's approach: OLS regression on the first 2 points,
linear trapezoid area added from t=0 to t_first) is implemented in `c0_back_extrapolated()` and verified
to match WinNonlin reference values within 2% for all 6 Indometh subjects.

The model-informed sparse oral fit is independently cross-checked against R 4.6.0
`stats::nls` on five samples from published `nlme::Theoph` subject 1. This single
structural-model cross-check does not establish general suitability for every drug or
sampling design.

See [VALIDATION.md](VALIDATION.md) for the full regulatory test traceability matrix.

---

## Disclaimer

This software is for research and decision-support workflows.
Final regulatory interpretation should be reviewed by qualified formulation, pharmacokinetic, and regulatory experts.

---

## Documentation

- **[Theory Guide](https://priyamthakar.github.io/openpkflow/theory/)** - Full LaTeX formula derivations for every module: NCA, simulation, dissolution, IVIVC, BE, pop PK, Bayesian PK. Designed for regulatory review support and teaching.
- **[Migration Guide](https://priyamthakar.github.io/openpkflow/migration-cheatsheet/)** - Coming from WinNonlin, NONMEM, or R? Quick-reference mapping for every parameter and function.
- **[Tutorials](https://priyamthakar.github.io/openpkflow/)** - Step-by-step worked examples for the supported analysis workflows.
- **[Validation Matrix](https://priyamthakar.github.io/openpkflow/validation-matrix/)** - External comparators, analytical checks, test locations, and current limits.
- **[API Reference](https://priyamthakar.github.io/openpkflow/reference/)** - Function and class reference across the public analysis modules.

---

## Contributing

Issues and PRs welcome at https://github.com/priyamthakar/openpkflow/issues

---

## Citation

If you use OpenPKFlow in research, please cite:

```
Thakar, P. (2026). OpenPKFlow: Python-first pharmacometrics and dissolution toolkit.
https://github.com/priyamthakar/openpkflow
```

## License

MIT - see [LICENSE](LICENSE)
