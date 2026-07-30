# Tutorial: Advanced Dissolution Workbench

The Advanced Dissolution Workbench combines the existing validated dissolution
methods into one vessel-level, report-first workflow. It adds orchestration and
audit artifacts; it does not introduce a new dissolution formula.

## Input contract

Use one row per vessel and time point:

```csv
formulation,batch,time,percent_released
reference,R1,5,8
reference,R1,10,19
reference,R1,15,34
reference,R2,5,9
reference,R2,10,20
reference,R2,15,35
test,T1,5,7
test,T1,10,18
test,T1,15,33
test,T2,5,8
test,T2,10,19
test,T2,15,34
```

The workbench fails closed unless:

- reference and test labels are different and present;
- each formulation has at least two vessels;
- every vessel has at least three time points;
- all vessels share exactly the same time points;
- every vessel/time pair occurs once;
- times and percent-released values are finite; and
- release values are within 0 to 100.

No interpolation or automatic time-point repair is performed.

## Run the complete analysis

```python
from openpkflow.dissolution import (
    DissolutionWorkbenchConfig,
    run_dissolution_workbench_csv,
)

config = DissolutionWorkbenchConfig(
    reference_label="reference",
    test_label="test",
    f2_method="regulatory",
    bootstrap_replicates=5000,
    confidence_level=0.90,
    seed=2026,
    model_comparison_model="weibull",
    model_comparison_param_index=0,
)

result = run_dissolution_workbench_csv("vessel_profiles.csv", config)
```

The result contains:

- point f1/f2 with an explicit f2 time-point method;
- bootstrap f2 interval and lower-bound decision;
- zero-order, first-order, Higuchi, Korsmeyer-Peppas, and Weibull fits ranked
  by AICc for both formulations;
- a fitted-parameter ratio and 90% confidence interval;
- Mahalanobis statistical distance and maximum deviation;
- normalized vessel profiles and captured prerequisite warnings; and
- the exact configuration and OpenPKFlow version.

The bootstrap output is explicitly labelled `all_points`; the point f2 method
is independently configured and defaults to the regulatory 85% rule.

## Generate shareable reports

```python
result.report("workbench.html", format="html")
result.report("workbench.pdf", format="pdf")
result.report("workbench.docx", format="docx")
```

PDF and DOCX require `pip install openpkflow[reports]`. Every format includes
the expert-review disclaimer, normalized data, exact configuration, warnings,
summary decisions, profile plot, and model ranking.

## Create and verify the audit ZIP

```python
result.audit_bundle("workbench_audit.zip")
```

The archive contains:

```text
config.json
input/normalized_dissolution.csv
manifest.json
report.html
results.json
```

`manifest.json` records the SHA-256 digest and byte size of every other
artifact. A verifier can recompute each digest:

```python
import hashlib
import json
import zipfile

with zipfile.ZipFile("workbench_audit.zip") as archive:
    manifest = json.loads(archive.read("manifest.json"))
    for name, metadata in manifest["files"].items():
        content = archive.read(name)
        assert hashlib.sha256(content).hexdigest() == metadata["sha256"]
        assert len(content) == metadata["size_bytes"]
```

## Web workflow

Open `/dissolution`, choose **Advanced workbench**, then upload a canonical CSV
or edit the paste grid. The web adapter sends typed vessel rows to FastAPI; all
calculations remain in `src/openpkflow/dissolution/`.

!!! warning
    Workbench decisions support transparent analysis and screening. Final
    regulatory interpretation remains the responsibility of qualified
    formulation, pharmacokinetic, and regulatory experts.
