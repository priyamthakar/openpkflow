# Tutorial: Non-Compartmental Analysis (NCA)

This tutorial demonstrates NCA on single- and multi-subject PK datasets.

---

## 1. Load data and run NCA

Create a CSV with columns: `subject`, `time`, `conc`, `dose`, `route`.

```python
from openpkflow.nca import NCAStudy

study = NCAStudy.from_csv(
    "pk_data.csv",
    auc_method="linear_up_log_down",  # required: "linear", "log", or "linear_up_log_down"
    blq_method="none",                # required: "none", "zero", "half_lloq", "lloq", "drop"
)

summary = study.analyze()
print(summary.to_dataframe())
```

---

## 2. Per-subject reports

```python
for result in summary.results:
    result.report(f"nca_{result.subject}.html")
```

---

## 3. Summary report

```python
summary.report("nca_summary.html")
summary.report("nca_summary.pdf")    # requires openpkflow[reports]
summary.report("nca_summary.docx")
```

---

## 4. Using the Theoph reference dataset

The built-in Theoph dataset (R nlme::Theoph, 12 subjects, oral theophylline) is useful
for validating your setup:

```python
from openpkflow.datasets import example_theoph_path
from openpkflow.nca import NCAStudy

study = NCAStudy.from_csv(
    example_theoph_path(),
    auc_method="linear_up_log_down",
    blq_method="none",
)
summary = study.analyze()
df = summary.to_dataframe()
print(df[["subject", "Cmax", "AUClast", "half_life", "CL_F"]].to_string())
```

Expected mean values (self-consistent regression): AUClast ~98.5, Cmax ~8.9, t1/2 ~7.9 h.

---

## 5. AUClast and tlast

AUClast follows the FDA/EMA NCA definition: AUC from time 0 to **tlast** — the last time
point with a quantifiable (positive) concentration. Trailing zero or negative
concentrations are automatically excluded from the trapezoidal sum. This matches PKNCA
0.12.1 behavior and is validated on all 12 theophylline reference subjects within 2%
relative tolerance.

---

## 6. BLQ handling

| Method | What it does |
|--------|-------------|
| `"none"` | Keep BLQ values as-is |
| `"zero"` | Set BLQ to 0 |
| `"half_lloq"` | Set BLQ to LLOQ/2 (M1 method) |
| `"lloq"` | Set BLQ to LLOQ (M2 method) |
| `"drop"` | Remove BLQ records entirely |

The CSV may contain BLQ flags as `"<0.5"` string values; these are parsed automatically.

---

## 7. AUC methods

| Method | Rule |
|--------|------|
| `"linear"` | Trapezoidal throughout |
| `"log"` | Log-linear throughout (requires all C > 0) |
| `"linear_up_log_down"` | Linear for rising segments, log-linear for declining |

`"linear_up_log_down"` is the default in most regulatory-context NCA software (PKNCA, WinNonlin).

---

## Parameter naming

- **Oral route:** `CL_F` (apparent clearance), `Vz_F` (apparent volume)
- **IV route:** `CL` (absolute clearance), `Vz` (absolute volume)

These are never mixed in the same output column.
