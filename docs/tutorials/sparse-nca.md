# Tutorial: Sparse oral PK fitting

OpenPKFlow can fit a one-compartment oral model to three or more
time-concentration observations. This is a **model-informed screening workflow**,
not standard noncompartmental analysis and not a primary regulatory analysis.

## Fit a published example

The example below uses five observations from subject 1 of the published R
`nlme::Theoph` dataset.

```python
from openpkflow.nca import fit_sparse_1cmt_oral

result = fit_sparse_1cmt_oral(
    times=[0.25, 1.12, 3.82, 9.05, 24.37],
    concentrations=[2.84, 10.50, 8.58, 6.89, 3.28],
    dose=320.0,
    p0=(3.0, 30.0, 2.0),
)

if not result.converged:
    raise RuntimeError("Sparse oral fit did not converge")

print(result.summary())
result.report("sparse_nca.html")
result.report("sparse_nca.md", format="markdown")
```

The fitted parameters are apparent oral clearance (`CL_F`), apparent volume
(`Vz_F`), and absorption rate constant (`ka`). Derived quantities such as AUCinf,
Cmax, Tmax, and half-life come from the fitted model rather than direct NCA of a
rich profile.

## Inputs and failure behavior

- Supply at least three matched time-concentration pairs.
- Times must be finite, non-negative, and strictly increasing.
- Concentrations must be finite and non-negative, with at least one positive value.
- Dose must be positive and use units consistent with the concentration data.
- Always inspect `converged`, standard errors, residuals, and whether estimates sit
  near the fitting bounds.

Three observations identify three fitted parameters mathematically, but provide
almost no redundancy for diagnostics. Prefer more samples spanning absorption,
peak, and elimination when the study permits it.

## Web workflow

Run the FastAPI backend and React app, then open `/nca/sparse`. The page includes
the same published example, an editable grid, fit diagnostics, an observed-versus-
fitted plot, and HTML/Markdown report downloads.

API clients can use:

- `POST /api/nca/sparse/analyze`
- `POST /api/nca/sparse/report`

## Validation evidence

`tests/validation/test_sparse_nca_theoph_reference.py` checks the Python result
against an independent bounded nonlinear least-squares fit from R 4.6.0
`stats::nls`. Recreate the reference with `scripts/sparse_nca_theoph_crossval.R`.

Agreement on this published example is a reproducible cross-check, not general
validation for every drug, sampling design, or structural model.
