# openpkflow.sim

Analytical PK simulation: 1- and 2-compartment models, IV bolus/infusion/oral, repeated dosing.

## Public API

| Symbol | Type | Description |
|--------|------|-------------|
| `simulate(model, regimen, times)` | function | Main entry point; returns `SimulationResult` |
| `OneCompartmentModel` | dataclass | 1-cmt model (frozen); routes: `iv_bolus`, `iv_infusion`, `oral` |
| `TwoCompartmentModel` | dataclass | 2-cmt model (frozen); routes: `iv_bolus`, `iv_infusion`, `oral` |
| `DoseRegimen` | dataclass | Tuple of `Dose` objects; `.from_repeated()` factory |
| `Dose` | dataclass | Single dose: `amount`, `time`, `route`, optional `t_inf` |
| `SimulationResult` | dataclass | `.Cmax`, `.Tmax`, `.summary()`, `.plot()`, `.report()`, `.to_dataframe()` |
| `c_1cmt_iv_bolus(...)` | function | 1-cmt IV bolus analytical equation |
| `c_1cmt_iv_infusion(...)` | function | 1-cmt IV infusion analytical equation |
| `c_1cmt_oral(...)` | function | 1-cmt oral (Bateman) analytical equation |
| `c_2cmt_iv_bolus(...)` | function | 2-cmt IV bolus biexponential equation |
| `c_2cmt_iv_infusion(...)` | function | 2-cmt IV infusion biexponential ramp equation |
| `c_2cmt_oral(...)` | function | 2-cmt oral three-exponential equation |
| `superpose(times, dose_times, dose_amounts, unit_fn)` | function | Linear multi-dose superposition |

## Notes

- All equations are analytical closed-form (no numerical ODE integration).
- Superposition is linear-system only. Not valid for nonlinear (Michaelis-Menten) elimination.
- 2-cmt IV infusion was added in v0.9.1. The analytical formula follows Gibaldi & Perrier, 2nd ed. (1982), Eqs. 3-28 to 3-30.

## Parameter conventions

| Route | 1-cmt | 2-cmt |
|-------|-------|-------|
| IV bolus / infusion | `CL`, `Vz` | `CL`, `V1`, `Q`, `V2` |
| oral | `CL_F`, `Vz_F`, `ka` | `CL_F`, `V1_F`, `Q`, `V2`, `ka` |
