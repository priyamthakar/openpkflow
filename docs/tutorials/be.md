# Tutorial: Bioequivalence Convenience Layer

!!! info "Theory"
    See the [Theory Guide](../theory.md#bioequivalence-tost) for the TOST mathematics,
    non-central t power formula, and sample size derivation.


This tutorial demonstrates OpenPKFlow's lightweight paired TOST convenience
layer. For formal regulator-facing BE analysis with ANOVA tables, replicate
designs, NTI, ABEL/RSABE, and validation fixtures, export to BioEqPy.

---

## 1. Prepare the DataFrame

Create a wide-format DataFrame with one row per subject:

```python
import pandas as pd
from openpkflow.be import BEStudy

df = pd.DataFrame({
    "subject":   ["S01", "S02", "S03", "S04", "S05", "S06"],
    "sequence":  ["RT",  "RT",  "RT",  "TR",  "TR",  "TR"],
    "reference": [100.2, 98.7, 105.1, 97.3, 102.8, 99.5],
    "test":      [95.1,  94.0,  99.8, 92.9,  97.4, 94.8],
})

study = BEStudy(df, parameter="AUCinf")
result = study.analyze()
print(result.summary())
```

Required columns: `subject`, `reference`, `test`.
The `sequence` column (`"RT"` / `"TR"`) is optional for paired TOST, but required when exporting to BioEqPy.

---

## 2. Generate a report

```python
result.report("be_report.html")      # HTML (default)
result.report("be_report.md")        # Markdown
```

---

## 3. Interpret results

| Output | Meaning |
|--------|---------|
| GMR | Geometric Mean Ratio (test / reference) |
| 90% CI | Confidence interval from TOST |
| Bioequivalent | True if 90% CI falls entirely within acceptance limits |
| Intra-subject CV% | Within-subject variability estimate |

The report includes a CI bar visualization placing the 90% CI against the
acceptance window.

---

## 4. NTI products (narrow acceptance limits)

For narrow therapeutic index drugs, pass tighter limits:

```python
result_nti = study.analyze(be_lower=0.90, be_upper=1.1111)
print(result_nti.summary())
```

---

## 5. From NCA results (convenience constructor)

If you ran NCA separately on each formulation, feed both
`NCASummaryResults` objects directly:

```python
from openpkflow.be import BEStudy
from openpkflow.nca import NCAStudy

ref_nca = NCAStudy.from_csv("ref_pk.csv", auc_method="linear_up_log_down", blq_method="none")
tst_nca = NCAStudy.from_csv("tst_pk.csv", auc_method="linear_up_log_down", blq_method="none")

ref_summary = ref_nca.analyze()
tst_summary = tst_nca.analyze()

study = BEStudy.from_nca_results(ref_summary, tst_summary, parameter="AUCinf")
result = study.analyze()
print(result.summary())
```

Subjects are matched by ID. Only subjects present in both result sets are used.

---

## 6. Export to BioEqPy for formal BE

```python
from bioeqpy import analyze

bioeqpy_table = study.to_bioeqpy_dataframe()
formal_results = analyze(
    bioeqpy_table,
    parameters=["AUCinf"],
    report="bioeqpy_formal_be_report.html",
)
```

`to_bioeqpy_dataframe()` returns the long-format columns BioEqPy expects:
`subject`, `sequence`, `period`, `treatment`, and the selected PK parameter.
The export requires `TR`/`RT` sequence labels.

---

## 7. CLI

```bash
openpkflow be compare be_data.csv --parameter AUCinf
openpkflow be compare be_data.csv --parameter AUCinf --report be_report.html
```

CSV format: `subject, sequence, reference, test`

---

## Statistical note

The TOST procedure tests two one-sided hypotheses:

- H01: GMR <= lower limit (e.g., 0.80)
- H02: GMR >= upper limit (e.g., 1.25)

Both are rejected at alpha=0.05 if and only if the 90% CI lies entirely within
the acceptance window. This is mathematically equivalent to verifying that
both one-sided t-tests pass at alpha=0.05.

Reference: Schuirmann (1987), *J Pharmacokinet Biopharm* 15(6):657-680.
FDA guidance: Statistical Approaches to Establishing Bioequivalence (2001).
