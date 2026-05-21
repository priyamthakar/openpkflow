# openpkflow.be

Bioequivalence analysis: 2x2 crossover TOST, GMR + 90% CI, intra-subject CV.

## Public API

| Symbol | Type | Description |
|--------|------|-------------|
| `BEStudy` | class | Entry point: `__init__(df, parameter, ...)`, `.analyze() -> BEResult`, `.from_nca_results()` |
| `BEResult` | dataclass | Analysis result: `gmr`, `gmr_lower_90ci`, `gmr_upper_90ci`, `bioequivalent`, `cv_intra_pct`, `subjects_df`, `.summary()`, `.report()` |
| `BETOSTResult` | dataclass | Low-level TOST output from `be_tost()` |
| `be_tost(reference, test, ...)` | function | Core TOST computation |

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
