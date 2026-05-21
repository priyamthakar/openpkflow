# Tutorial: PK Simulation

This tutorial covers 1- and 2-compartment PK simulation for IV and oral routes,
including repeated dosing and multi-format reports.

---

## 1. Single IV bolus dose

```python
import numpy as np
from openpkflow.sim import OneCompartmentModel, DoseRegimen, Dose, simulate

model   = OneCompartmentModel(route="iv_bolus", CL=5.0, Vz=20.0)
regimen = DoseRegimen((Dose(100.0, time=0.0, route="iv_bolus"),))
times   = np.linspace(0, 24, 200)

result = simulate(model, regimen, times)
print(result.summary())
# Cmax=5.0 mg/L at Tmax=0.0 h, t1/2=2.77 h
```

---

## 2. Oral repeated dosing (steady state)

```python
from openpkflow.sim import OneCompartmentModel, DoseRegimen, simulate
import numpy as np

model   = OneCompartmentModel(route="oral", CL_F=4.0, Vz_F=30.0, ka=0.8)
regimen = DoseRegimen.from_repeated(amount=200.0, route="oral", tau=12.0, n_doses=10)
times   = np.linspace(0, 120, 1000)

result = simulate(model, regimen, times)
result.report("oral_md_report.html")
```

---

## 3. IV infusion

```python
from openpkflow.sim import OneCompartmentModel, DoseRegimen, Dose, simulate
import numpy as np

model   = OneCompartmentModel(route="iv_infusion", CL=5.0, Vz=20.0)
dose    = Dose(100.0, time=0.0, route="iv_infusion", t_inf=2.0)  # 2 h infusion
regimen = DoseRegimen((dose,))
times   = np.linspace(0, 12, 200)

result = simulate(model, regimen, times)
result.plot()  # returns base64 PNG
```

---

## 4. Two-compartment IV bolus

```python
from openpkflow.sim import TwoCompartmentModel, DoseRegimen, Dose, simulate
import numpy as np

model = TwoCompartmentModel(
    route="iv_bolus",
    CL=3.0, V1=10.0,
    Q=5.0,  V2=40.0,
)
regimen = DoseRegimen((Dose(500.0, 0.0, "iv_bolus"),))
result  = simulate(model, regimen, np.linspace(0, 48, 500))
result.report("2cmt_iv_report.pdf")   # requires openpkflow[reports]
```

---

## 5. Two-compartment IV infusion

```python
from openpkflow.sim import TwoCompartmentModel, DoseRegimen, Dose, simulate
import numpy as np

model = TwoCompartmentModel(
    route="iv_infusion",
    CL=3.0, V1=10.0,
    Q=5.0,  V2=40.0,
)
dose    = Dose(500.0, time=0.0, route="iv_infusion", t_inf=1.0)  # 1 h infusion
regimen = DoseRegimen((dose,))
result  = simulate(model, regimen, np.linspace(0, 48, 500))
```

---

## Parameter conventions

| Route | Required parameters |
|-------|-------------------|
| `iv_bolus` | `CL`, `Vz` (1-cmt) or `CL`, `V1`, `Q`, `V2` (2-cmt) |
| `iv_infusion` | Same as iv\_bolus, plus `t_inf` on each `Dose` |
| `oral` | `CL_F`, `Vz_F`, `ka` (1-cmt) or `CL_F`, `V1_F`, `Q`, `V2`, `ka` (2-cmt) |

Simulation uses analytical closed-form solutions (not numerical ODE integration).
Superposition is applied for multiple doses — valid only for **linear PK**.
