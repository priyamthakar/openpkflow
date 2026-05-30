# openpkflow.be

Bioequivalence analysis: paired 2x2 TOST, GMR + 90% CI, intra-subject CV,
and research-grade replicate-design screening. For formal ANOVA-based BE,
jurisdiction-specific NTI decisions, validated ABEL/RSABE, and submission
fixtures, cross-check against BioEqPy, PowerTOST, or validated SAS/R workflows.

## Public API

| Symbol | Type | Description |
|--------|------|-------------|
| `BEStudy` | class | Entry point: `__init__(df, parameter, ...)`, `.analyze() -> BEResult`, `.from_nca_results()` |
| `BEResult` | dataclass | Analysis result: `gmr`, `gmr_lower_90ci`, `gmr_upper_90ci`, `bioequivalent`, `cv_intra_pct`, `subjects_df`, `.summary()`, `.report()` |
| `BETOSTResult` | dataclass | Low-level TOST output from `be_tost()` |
| `be_tost(reference, test, ...)` | function | Core TOST computation |
| `replicate_be(data, value_col, ...)` | function | Long-format replicate-design BE screening |
| `ReplicateBEResult` | dataclass | Replicate BE output with GMR, 90% CI, CVwR, scaled limits, and caveat |
| `ema_scaled_limits(swr, ...)` | function | EMA-style scaled limits from reference within-subject SD |
| `BEStudy.to_bioeqpy_dataframe()` | method | Export BioEqPy-ready long-format BE input |
| `BEStudy.to_bioeqpy_csv(path)` | method | Write BioEqPy-ready CSV input |

## BEStudy

```python
BEStudy(
    df,                      # wide-format DataFrame
    parameter="AUCinf",      # label for output
    *,
    reference_col="reference",
    test_col="test",
    subject_col="subject",
    sequence_col="sequence", # or None; silently dropped if default name absent
)
```

Required DataFrame columns: `subject_col`, `reference_col`, `test_col`.

`sequence_col`:
- Default `"sequence"` — silently dropped if absent from the DataFrame.
- Any other name — raises `ValueError` if absent.
- Pass `None` explicitly to indicate no sequence column.

### `.analyze()`

```python
result = study.analyze(
    be_lower=0.80,   # FDA/EMA standard lower limit
    be_upper=1.25,   # FDA/EMA standard upper limit
    alpha=0.05,      # one-sided significance level (90% CI)
)
```

Returns a `BEResult`.

### `.from_nca_results()`

```python
BEStudy.from_nca_results(
    reference_results,   # NCASummaryResults
    test_results,        # NCASummaryResults
    parameter="AUCinf",  # "AUCinf", "AUClast", or "Cmax"
)
```

Matches subjects by ID. Raises `ValueError` if no common subjects are found.

### `.to_bioeqpy_dataframe()`

```python
from bioeqpy import analyze

table = study.to_bioeqpy_dataframe()
results = analyze(table, parameters=["AUCinf"])
```

Exports long-format columns expected by BioEqPy: `subject`, `sequence`, `period`,
`treatment`, and the selected PK parameter. The current export supports standard
`TR`/`RT` 2x2 crossover studies and requires a sequence column.

### `.to_bioeqpy_csv(path)`

Writes the same BioEqPy-ready long-format table to CSV.

## BEResult

| Attribute | Type | Description |
|-----------|------|-------------|
| `parameter` | str | PK parameter label |
| `n` | int | Number of subjects |
| `gmr` | float | Geometric Mean Ratio (test/reference) |
| `gmr_lower_90ci` | float | Lower bound of 90% CI |
| `gmr_upper_90ci` | float | Upper bound of 90% CI |
| `be_lower` | float | Acceptance limit (lower) |
| `be_upper` | float | Acceptance limit (upper) |
| `bioequivalent` | bool | True if 90% CI within limits |
| `cv_intra_pct` | float | Intra-subject CV% |
| `subjects_df` | DataFrame | Per-subject table (subject, reference, test, ratio, log_diff) |

### `.summary()`

Returns an ASCII table with GMR, 90% CI, acceptance limits, CV%, and verdict.

### `.report(path, format=None)`

Writes an HTML or Markdown report. Format inferred from file extension;
override with `format="html"` or `format="markdown"`.

## replicate_be()

```python
from openpkflow.be import replicate_be

result = replicate_be(
    data,                  # long-format DataFrame
    value_col="AUCinf",    # positive PK metric values
    subject_col="subject",
    sequence_col="sequence",
    period_col="period",
    treatment_col="treatment",
)
```

Required long-format columns:

| Column | Meaning |
|---|---|
| `subject` | Subject identifier |
| `sequence` | Randomized sequence, e.g. `TRTR`, `RTRT`, `TRR`, `RTR`, `RRT` |
| `period` | Period number |
| `treatment` | `T` or `R` |
| value column | Positive PK parameter value such as `AUCinf` or `Cmax` |

The result reports:

- conventional GMR and 90% CI,
- conventional 80-125% ABE decision,
- reference within-subject SD (`swr`) and CVwR%,
- EMA-style scaled limits when CVwR exceeds 30%, capped at the CVwR=50% limit,
- FDA-style RSABE point-criterion screening, not the full 95% upper-bound decision.

!!! warning "Research-grade scope"
    `replicate_be()` is a transparent screening utility. It does not implement
    jurisdiction-specific mixed-model degrees of freedom, SAS PROC MIXED parity,
    FDA RSABE 95% upper confidence bound logic, or NTI decision rules. Use it to
    explore and QA data, then cross-check formal decisions against validated
    regulatory workflows.

CLI usage:

```bash
openpkflow be replicate replicate_be_partial.csv --parameter Cmax --report replicate.html --json replicate.json
```

## be_tost()

```python
from openpkflow.be.methods import be_tost

result = be_tost(
    reference,          # list of reference values (positive floats)
    test,               # list of test values (positive floats, same length)
    *,
    be_lower=0.80,
    be_upper=1.25,
    alpha=0.05,
)
```

Raises `ValueError` for mismatched lengths, n < 2, non-positive values,
or invalid acceptance limits.

## Acceptance limits reference

| Product type | be_lower | be_upper |
|---|---|---|
| Standard (FDA/EMA) | 0.80 | 1.25 |
| NTI (FDA) | 0.90 | 1.1111 |

## Statistical method

Log-transformed TOST (Schuirmann 1987). Within-subject log-differences are
used for GMR estimation and CI construction. Intra-subject CV is derived as
`sqrt(exp(s_d^2) - 1) * 100` (Chow & Liu 2008, eq. 3.3.4).

Reference: Schuirmann DJ (1987). *J Pharmacokinet Biopharm* 15(6):657-680.
FDA guidance: Statistical Approaches to Establishing Bioequivalence (2001).
