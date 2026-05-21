# openpkflow.nca

Non-Compartmental Analysis: AUC, Cmax, Tmax, lambda_z, half-life, CL/F, Vz/F.

## Public API

| Symbol | Type | Description |
|--------|------|-------------|
| `NCAStudy` | class | Entry point: `.from_csv()`, `.analyze() -> NCASummaryResults` |
| `NCAResult` | dataclass | Per-subject result: `AUClast`, `AUCinf_obs`, `Cmax`, `Tmax`, `lambda_z`, `half_life`, `CL`/`CL_F`, `Vz`/`Vz_F`, `warnings` |
| `NCASummaryResults` | dataclass | Multi-subject container: `.to_dataframe()`, `.report()` |
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

## BLQ methods

`"none"`, `"zero"`, `"half_lloq"` (M1), `"lloq"` (M2), `"drop"`

CSV string-BLQ notation (`"<0.5"`) is parsed automatically.
