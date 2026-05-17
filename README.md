# OpenPKFlow

**A transparent, reproducible, open-source Python workflow for dissolution, NCA, PK/PD simulation, and pharmacometric reporting.**

[![CI](https://github.com/priyamthakar/openpkflow/actions/workflows/ci.yml/badge.svg)](https://github.com/priyamthakar/openpkflow/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/openpkflow)](https://pypi.org/project/openpkflow/)
[![Python](https://img.shields.io/pypi/pyversions/openpkflow)](https://pypi.org/project/openpkflow/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## What it does

OpenPKFlow gives formulation scientists, PK/PD researchers, and CRO/CDMO teams a clean Python workflow for:

- **Dissolution similarity:** f1, f2, bootstrap f2, model fitting
- **NCA:** AUC, Cmax, Tmax, half-life, CL/F, Vz/F · planned v0.4.0
- **PK simulation:** 1- and 2-compartment models, oral/IV/infusion · planned v0.5.0
- **Report generation:** Markdown, HTML, PDF, Word · planned v0.3.0

It does not replace expert regulatory judgement or validated commercial platforms.
It makes routine analysis faster, cleaner, and more reproducible.

---

## Install

```bash
pip install openpkflow
```

For report generation:

```bash
pip install openpkflow[reports]
```

---

## Quick start

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
```

### CSV format

```csv
formulation,batch,time,percent_released
reference,R1,5,18.2
reference,R1,10,31.4
reference,R1,15,47.9
test,T1,5,17.5
test,T1,10,30.1
test,T1,15,46.2
```

### CLI

```bash
openpkflow version
openpkflow similarity --reference "20,40,60,80" --test "21,39,61,79"
```

---

## Current status

| Module | Status |
|---|---|
| `dissolution.f1` / `dissolution.f2` | Stable |
| Bootstrap f2 | Stable |
| Dissolution CSV loader | Stable |
| HTML report with profile plot | Stable |
| CLI | Stable |
| Dissolution model fitting | Planned v0.2.0 |
| Full PDF/Word reports | Planned v0.3.0 |
| NCA | Planned v0.4.0 |
| PK simulation | Planned v0.5.0 |
| Population PK | Planned v0.6.0 |
| Bayesian PK | Planned v0.8.0 |
| ML / neural ODE | Planned v0.9.0 |

---

## Validation

All formula implementations are validated against published FDA/EMA guidance examples.
Each test case cites its source: paper DOI, FDA guidance ID, or R-package vignette.
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
