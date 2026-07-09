# pipeline

Multi-stage study orchestration added in **v2.6.0**.

## Public API

```python
from openpkflow.pipeline import (
    PipelineConfig,
    StudyPipeline,
    StudyPipelineResult,
    load_pipeline_config,
)
```

| Symbol | Role |
|--------|------|
| `PipelineConfig` | Paths and method options for optional stages |
| `load_pipeline_config(path)` | Load JSON (YAML if PyYAML installed); paths relative to config file |
| `StudyPipeline(config).run()` | Run enabled stages; raise on failure |
| `StudyPipelineResult` | Aggregated results + audit `metadata` |
| `.summary()` | ASCII multi-section text + disclaimer |
| `.report(path)` | HTML (default) or Markdown by extension |
| `.to_dict()` | JSON-serializable audit payload |

## Stages

| Stage | Enabled when | Library used |
|-------|--------------|--------------|
| Dissolution | `dissolution_csv` + reference/test labels | `DissolutionStudy` |
| NCA | `nca_csv` | `NCAStudy` (explicit `nca_auc_method`, `nca_blq_method`) |
| BE | `be_csv` | `BEStudy` TOST |

IVIVC is not wired yet (needs multi-array inputs, not a single CSV).

## CLI

```bash
openpkflow study run examples/study_pipeline_example.json --report out.html
openpkflow study run config.json --json out.json
```

## Examples

- `examples/study_pipeline_example.json`
- `examples/study_pipeline_example.yaml` (needs PyYAML)
- `examples/pipeline_walkthrough.py` (sequential API demo without pipeline package)

## Tutorial

See [Formulation-to-report pipeline](../tutorials/pipeline.md).
