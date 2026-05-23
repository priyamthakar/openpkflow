# openpkflow.nca

Non-Compartmental Analysis: AUC, Cmax, Tmax, lambda_z, half-life, CL/F, Vz/F.

## Public API

| Symbol | Type | Description |
|--------|------|-------------|
| `NCAStudy` | class | Entry point: `.from_csv()`, `.analyze() -> NCASummaryResults` |
| `NCAResult` | dataclass | Per-subject result: `AUClast`, `AUCinf_obs`, `Cmax`, `Tmax`, `lambda_z`, `half_life`, `CL`/`CL_F`, `Vz`/`Vz_F`, `AUC_percent_extrapolated`, `DN_AUClast`, `DN_Cmax`, `lambda_z_adj_r2`, `lambda_z_n_points`, `warnings` |
| `NCASummaryResults` | dataclass | Multi-subject container: `.to_dataframe()`, `.to_cdisc_pp()`, `.report()` |
| `load_nca_csv(path, config)` | function | CSV loader with BLQ handling |
| `auc_linear(times, concs)` | function | Linear trapezoidal AUC |
| `auc_log(times, concs)` | function | Log-linear trapezoidal AUC |
| `auc_linear_up_log_down(times, concs)` | function | Linear-up/log-down AUC |
| `lambda_z(times, concs, ...)` | function | Terminal rate constant (BAR2 auto-selection) |
| `auc_inf_obs(AUClast, Clast, lambda_z)` | function | AUCinf by extrapolation |
| `cmax(concs)` | function | Maximum concentration |
| `tmax(times, concs)` | function | Time of maximum concentration |
| `clearance_volume_parameters(dose, AUCinf, lambda_z, route)` | function | CL/F, Vz/F (oral) or CL, Vz (IV) |
| `AUCResult` | dataclass | AUC result with method tag |
| `LambdaZResult` | dataclass | lambda\_z with adj-R2, selected time points |

## Parameter naming conventions

- **Oral:** `CL_F` (apparent clearance), `Vz_F` (apparent volume) — never mix with IV labels
- **IV bolus / IV infusion:** `CL`, `Vz` (absolute)

## AUC methods

Pass `auc_method` explicitly to `NCAStudy`. Never left to default.

## AUClast and tlast

AUClast follows the FDA/EMA definition: AUC from time 0 to **tlast**, the last time
point with a quantifiable (positive) concentration. Trailing zero or negative
concentrations are excluded from the trapezoidal sum automatically. This is validated
against PKNCA 0.12.1 on the theophylline reference dataset (12 subjects, all within 2%
relative tolerance).

## Input validation

All AUC functions reject non-finite (NaN/Inf) concentrations and times with explicit
`ValueError` messages. Negative concentrations raise `ValueError`. This prevents silent
garbage propagation through downstream PK parameter calculations.

## BLQ methods

`"none"`, `"zero"`, `"half_lloq"` (M1), `"lloq"` (M2), `"drop"`

CSV string-BLQ notation (`"<0.5"`) is parsed automatically.

> **Note on `blq_method="zero"`**: terminal BLQ values zero-filled by the loader are
> automatically trimmed by the tlast logic (they don't inflate AUClast). However,
> interior BLQs (between quantifiable concentrations) become zero-concentration
> intervals that do affect the trapezoidal sum. For NCA, `"drop"` is the safer choice
> unless FDA guidance for the specific analysis permits zero substitution.

## Validation

The NCA module is cross-validated against PKNCA 0.12.1 (Denney et al., 2015) on the
12-subject R nlme::Theoph theophylline dataset. AUClast matches within 2% relative
tolerance for every subject. Cmax matches exactly. See `tests/validation/` and
`scripts/pknca_theoph_crossval.R`.
