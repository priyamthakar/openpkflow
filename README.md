# OpenPKFlow

**A transparent, reproducible, open-source Python workflow for dissolution, NCA, PK/PD simulation, and pharmacometric reporting.**

[![CI](https://github.com/priyamthakar/openpkflow/actions/workflows/ci.yml/badge.svg)](https://github.com/priyamthakar/openpkflow/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/openpkflow)](https://pypi.org/project/openpkflow/)
[![Python](https://img.shields.io/pypi/pyversions/openpkflow)](https://pypi.org/project/openpkflow/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## What it does

OpenPKFlow gives formulation scientists, PK/PD researchers, and CRO/CDMO teams a clean Python workflow for:

- **Dissolution similarity:** f1, f2, bootstrap f2, model fitting — Weibull, Higuchi, first-order, zero-order, Korsmeyer-Peppas
- **NCA:** AUClast, AUCinf, Cmax, Tmax, lambda_z, half-life, CL/F, Vz/F — three AUC methods, explicit BLQ handling
- **Report generation:** Markdown, HTML, PDF, Word
- **PK simulation:** 1- and 2-compartment models, oral/IV/infusion — planned v0.5.0

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

result = study.compare(reference="reference", test="test")
result.summary()
result.report("dissolution_report.html")
result.report("dissolution_report.pdf", format="pdf")   # requires [reports]
```

CSV format: `formulation,batch,time,percent_released`

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
Dose units must match concentration × time — mg when conc is mg/L and time is h.
Route values: `"oral"`, `"iv_bolus"`, `"iv_infusion"`.

Oral route yields apparent clearance and volume: `CL_F`, `Vz_F`.
IV routes yield absolute clearance and volume: `CL`, `Vz`.

---

## Current status

| Module | Status |
|---|---|
| Dissolution f1 / f2 | Stable |
| Bootstrap f2 | Stable |
| Dissolution CSV loader | Stable |
| Dissolution model fitting (5 models, AICc) | Stable |
| HTML, Markdown, PDF, Word reports | Stable |
| NCA (AUC, lambda_z, CL/F, reports) | Stable — v0.4.0 |
| PK simulation (1/2-comp, oral/IV) | Planned v0.5.0 |
| Population PK diagnostics | Planned v0.6.0 |
| Bayesian PK (PyMC, CmdStanPy) | Planned v0.8.0 |
| ML / neural ODE | Planned v0.9.0 |

---

## Validation

All formula implementations are validated against published FDA/EMA guidance examples.
Each test case cites its source: paper DOI, FDA guidance ID, or R-package vignette.
NCA results are validated against the R nlme Theoph reference dataset.
See `tests/` for details.

---

## Disclaimer

This software is for research and decision-support workflows.
Final regulatory interpretation should be reviewed by qualified formulation, pharmacokinetic, and regulatory experts.

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

MIT · see [LICENSE](LICENSE)
