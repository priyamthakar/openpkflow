# openpkflow.dissolution

Dissolution similarity analysis: f1/f2, bootstrap, model fitting, CSV loading, study-level comparison.

## Public API

| Symbol | Type | Description |
|--------|------|-------------|
| `f1(reference, test)` | function | Difference factor |
| `f2(reference, test, method)` | function | Similarity factor; `method="regulatory"` applies FDA 85% rule |
| `max_deviation(reference, test)` | function | Maximum absolute deviation (FDA/SUPAC-IR 1995) |
| `msd(reference, test)` | function | Mahalanobis Statistical Distance (FDA PSA 1999) |
| `MSDResult` | dataclass | MSD result: `.msd`, `.msd_squared`, `.is_similar`, `.summary()` |
| `model_dependent_comparison(ref_t, ref_Q, tst_t, tst_Q, model)` | function | Compare fitted dissolution model parameters via 90% CI |
| `ModelComparisonResult` | dataclass | Model comparison result: `.ratio_pct`, `.ci_lo`, `.ci_hi`, `.is_similar` |
| `bootstrap_f2(reference, test, ...)` | function | Bootstrap CI for f2 |
| `BootstrapF2Result` | dataclass | Bootstrap result container |
| `DissolutionStudy` | class | Multi-batch study; `.compare()`, `.fit_models()`, `.bootstrap_compare()` |
| `ComparisonResult` | dataclass | f1/f2 comparison result; `.summary()`, `.plot()`, `.report()` |
| `fit_dissolution_models(time_points, observed, label)` | function | Low-level model fitting |
| `DissolutionFitResults` | dataclass | Ranked model fits; `.best`, `.summary()`, `.plot()`, `.report()` |
| `ModelFit` | dataclass | Single model fit: params, R2, AIC, AICc, BIC, `.predict()` |
| `load_dissolution_csv(path, config)` | function | CSV loader with validation |
| `DissolutionCSVConfig` | dataclass | CSV column config |
| `get_formulation_means(df, label)` | function | Extract mean profile for a formulation |

## Models available in `fit_dissolution_models`

`zero_order`, `first_order`, `higuchi`, `korsmeyer_peppas`, `weibull`

Ranked by AICc (small-sample-corrected). Pass `models=["weibull", "first_order"]` to fit a subset.

## Report formats

`.report("out.html")` — HTML
`.report("out.md")` — Markdown
`.report("out.pdf")` — PDF (requires `openpkflow[reports]`)
`.report("out.docx")` — Word (requires `openpkflow[reports]`)
