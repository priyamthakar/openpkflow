# Tutorial: Dissolution Similarity

!!! info "Theory"
    See the [Theory Guide](../theory.md#dissolution-similarity) for the f1, f2 formula
    derivations, dissolution model equations, and FDA threshold rationale.


This tutorial walks through dissolution f1/f2 analysis, bootstrap confidence intervals,
and dissolution model fitting using OpenPKFlow.

---

## 1. Quick f1 and f2

```python
from openpkflow.dissolution import f1, f2

reference = [20.0, 40.0, 60.0, 80.0, 90.0]
test      = [21.0, 39.0, 61.0, 79.0, 88.0]

print(f"f1 = {f1(reference, test):.2f}")   # 1.33
print(f"f2 = {f2(reference, test):.2f}")   # 72.80
# f2 >= 50 → profiles are similar (FDA 1997 guidance)
```

**FDA threshold:** f2 >= 50 indicates similarity. f1 < 15 is sometimes cited as a complementary criterion.

---

## 2. From a CSV file

Create a CSV file with columns: `formulation`, `batch`, `time`, `percent_released`.

```csv
formulation,batch,time,percent_released
reference,R1,15,22.1
reference,R1,30,45.3
reference,R1,45,64.7
reference,R1,60,79.5
reference,R2,15,21.8
reference,R2,30,44.9
reference,R2,45,65.1
reference,R2,60,80.2
test,T1,15,21.5
test,T1,30,43.8
test,T1,45,62.9
test,T1,60,78.1
```

```python
from openpkflow.dissolution import DissolutionStudy

study = DissolutionStudy.from_csv("dissolution_data.csv")
result = study.compare(reference="reference", test="test")

result.summary()   # prints f1, f2, time points, means
result.report("dissolution_report.html")   # generates HTML report
```

---

## 3. Bootstrap f2

Bootstrap f2 gives a confidence interval that accounts for between-batch variability.

```python
result = study.bootstrap_compare(
    reference="reference",
    test="test",
    n_bootstrap=1000,
    seed=42,
)

print(f"Bootstrap f2: {result.f2_mean:.1f} [{result.f2_lower:.1f}, {result.f2_upper:.1f}]")
```

---

## 4. Dissolution model fitting

Fit five standard release kinetics models and rank by AICc:

```python
from openpkflow.dissolution import fit_dissolution_models

time_points = [15, 30, 45, 60, 90]
observed    = [21.5, 43.8, 62.9, 78.1, 91.4]

results = fit_dissolution_models(time_points, observed, "test_formulation")

print(f"Best model: {results.best.name} (AICc={results.best.AICc:.1f})")
results.report("model_fit_report.html")
```

Models fitted: Weibull, Korsmeyer-Peppas (power law), Higuchi, first-order, zero-order.

---

## 5. PDF and Word export

```python
result.report("dissolution_report.pdf")    # requires pip install openpkflow[reports]
result.report("dissolution_report.docx")
```

---

## Regulatory notes

- f2 requires a minimum of 3 matched time points.
- At most one time point where both profiles exceed 85% may be included (FDA 1997 guidance).
  Use `f2(method="regulatory")` to automatically apply this rule.
- The Korsmeyer-Peppas model is only mechanistically valid when release < 60%.
