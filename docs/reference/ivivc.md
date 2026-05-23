# openpkflow.ivivc

In Vitro-In Vivo Correlation (Level A): deconvolution, convolution prediction, Levy plots, and FDA predictability assessment.

## Public API

| Symbol | Type | Description |
|--------|------|-------------|
| `wagner_nelson(times, concentrations, ...)` | function | 1-cmt Wagner-Nelson deconvolution; returns cumulative F_a |
| `loo_riegelman(times, concentrations, ...)` | function | 2-cmt Loo-Riegelman deconvolution; requires kel, k12, k21 |
| `convolution_predict(dissolution_times, dissolution_pct, ...)` | function | Numerical convolution of dissolution input with IV UIR |
| `levy_plot_data(in_vitro_times, in_vitro_fraction, in_vivo_fraction)` | function | Compute Levy plot regression data (slope, R2, residuals) |
| `ivivc_predictability(observed_cmax, predicted_cmax, observed_auc, predicted_auc)` | function | FDA %PE assessment; returns pass/fail per FDA 1997 criteria |
| `IVIVCResult` | dataclass | Comprehensive IVIVC result; `.summary()`, `.plot()`, `.report()`, `.to_dict()` |
| `IVIVCStudy` | class | High-level orchestrator: `.analyze()` returns `IVIVCResult` |

## Deconvolution methods

| Method | Compartment | Required parameters |
|--------|------------|-------------------|
| Wagner-Nelson | 1-cmt | `kel` (or IV UIR data to estimate it) |
| Loo-Riegelman | 2-cmt | `kel` (k10), `k12`, `k21` |

Both methods return a cumulative fraction absorbed array (F_a) as numpy ndarray.

## Predictability criteria (FDA 1997)

| Criterion | Threshold |
|-----------|-----------|
| %PE Cmax | <= 15% per formulation |
| %PE AUCinf | <= 15% per formulation |
| Mean absolute %PE | <= 10% across formulations |

All three must pass for overall IVIVC predictability.

## IVIVCResult fields

| Field | Type | Description |
|-------|------|-------------|
| `method` | `str` | Deconvolution method used |
| `times` | `np.ndarray` | In vivo plasma sampling times |
| `concentrations` | `np.ndarray` | Observed plasma concentrations |
| `fa` | `np.ndarray` | Cumulative fraction absorbed |
| `levy_plot` | `dict` | Slope, intercept, R-squared, residuals |
| `ivt_times` | `np.ndarray` | In vitro dissolution time points |
| `ivt_fraction` | `np.ndarray` | Cumulative fraction dissolved |
| `predicted_times` | `np.ndarray` | Convolution-predicted plasma times |
| `predicted_concs` | `np.ndarray` | Convolution-predicted concentrations |
| `predictability` | `dict` | %PE_Cmax, %PE_AUC, passes flags, overall_pass |

## Report formats

`.report("out.html")` -- HTML with 4-panel figure
`.report("out.md")` -- Markdown
`.report("out.pdf")` -- PDF (requires `openpkflow[reports]`)
`.report("out.docx")` -- Word (requires `openpkflow[reports]`)

## Notes

- Wagner-Nelson is valid for 1-compartment kinetics only. If the drug shows
  distribution-phase behaviour, use Loo-Riegelman with the 2-cmt microconstants.
- The convolution predictor uses numerical trapezoidal convolution with a uniform
  time grid spanning the UIR range. Input rate is computed from the derivative of
  the interpolated dissolution curve.
- Levy plots filter to the 0.05-0.95 fraction range for robust regression,
  per FDA convention.
