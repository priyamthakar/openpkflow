# Positioning

What OpenPKFlow is, what it is not, and how to place it next to commercial and
regulatory systems.

## What OpenPKFlow is

OpenPKFlow is a transparent, reproducible, open-source Python workflow for:

- Dissolution similarity (f1, f2, bootstrap f2, MSD, model fitting, multi-media)
- Noncompartmental analysis (NCA), including steady-state and urinary parameters
- Analytical PK simulation (1- and 2-compartment models)
- Level A IVIVC (Wagner-Nelson, Loo-Riegelman, convolution, Levy plot, %PE)
- Bioequivalence screening (2x2 TOST convenience layer and power / sample size)
- Pharmacometric reporting (Markdown, HTML, PDF, DOCX)
- Research-grade population PK diagnostics and estimation helpers

The product focus is a **formulation-to-report pipeline**: load study data,
run validated-style calculations, and export shareable reports for formulation,
PK, and regulatory review teams.

Philosophy:

> A transparent, reproducible, open-source Python workflow for dissolution, NCA,
> PK/PD simulation, and pharmacometric reporting.

## What OpenPKFlow is not

OpenPKFlow is **not**:

- FDA-approved software
- A validated system under 21 CFR Part 11 or ICH Q2 by itself
- A replacement for expert regulatory judgement
- A full substitute for commercial platforms used under controlled, locked,
  regulated environments (e.g. Phoenix WinNonlin, NONMEM production pipelines)
- A complete regulator-grade RSABE / replicate-design BE engine

Final regulatory interpretation must always be reviewed by qualified formulation,
pharmacokinetic, and regulatory experts.

## Where formal BE and PopPK live

| Capability | OpenPKFlow role | Formal / companion path |
|---|---|---|
| 2x2 crossover TOST | Convenience layer for screening and teaching | Study SOPs + independent statistical review |
| Power and sample size | Exact TOST power (PowerTOST-aligned) | Confirm with PowerTOST or study statistician |
| RSABE / replicate designs | Partial screening only | Companion **BioEqPy** package (out of scope here) |
| Population PK FOCE-I / SAEM | Research-grade; limited model space | Pharmpy, nlmixr2, NONMEM for primary NLME |

Population PK estimation in OpenPKFlow is frozen for extension beyond bug fixes.
Treat PopPK results as research and method-development tools, not as a primary
regulatory NLME engine.

## Formulation-to-report pipeline

Typical sequential workflow (library APIs or CLI):

1. **Dissolution** -- f1/f2 (and optional bootstrap) on multi-batch profiles
2. **NCA** -- per-subject AUClast, Cmax, half-life, CL/F (or CL for IV)
3. **BE** -- paired TOST on NCA-derived parameters (or pre-computed AUCs)
4. **Report** -- HTML / Markdown / PDF / DOCX with the mandatory disclaimer

IVIVC Level A sits beside this path for extended-release development when
dissolution and IV / oral PK support a correlation.

See [Pipeline tutorial](tutorials/pipeline.md) for CLI and Python walkthroughs,
and `examples/pipeline_walkthrough.py` for a dependency-light script.

## Validation transparency

Cross-checks against public and published references are documented in:

- [Validation matrix](validation-matrix.md) (docs summary)
- [`VALIDATION.md`](https://github.com/priyamthakar/openpkflow/blob/main/VALIDATION.md)
  (full test-to-reference map at repo root)

Executable tests under `tests/validation/` lock those claims. Agreement with a
comparator does **not** make OpenPKFlow a Part 11 validated system. Regulated
use still requires local SOPs, version control, locked environments, and
independent review.

## Claims to avoid

Do **not** describe OpenPKFlow as:

- "FDA-approved"
- "replaces Certara" / "replaces Phoenix"
- "Part 11 validated out of the box"
- "regulator-grade RSABE"
- "AI discovers the perfect formulation"

Use transparent, reproducible, open-source language instead.
