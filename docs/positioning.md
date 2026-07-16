# Positioning

What OpenPKFlow is, what it is not, and how to place it next to commercial and
regulatory systems.

## What OpenPKFlow is

OpenPKFlow is a transparent, reproducible, open-source Python workflow for:

- Dissolution similarity (f1, f2, bootstrap f2, MSD, model fitting, multi-media,
  SUPAC-IR screening helpers, alcohol dose-dumping f2 assessment)
- Noncompartmental analysis (NCA), including steady-state and urinary workflows,
  plus model-informed sparse oral screening
- Analytical PK simulation (1- and 2-compartment models, transit absorption, SS metrics)
- IVIVC Level A (Wagner-Nelson, Loo-Riegelman, convolution, Levy plot, %PE) and
  Level B/C helpers (MDT / MRT correlation)
- Multi-stage study pipeline orchestration (`openpkflow.pipeline` / `study run`)
- Bioequivalence screening (2x2 TOST, power / sample size, research-grade replicate)
- Pharmacometric reporting (Markdown, HTML, PDF, DOCX)
- Research-grade population PK diagnostics and estimation helpers (estimation frozen)

The product focus is a **formulation-to-report pipeline**: load study data,
run transparent calculations, and export shareable reports for formulation,
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
  (formal RSABE belongs in companion BioEqPy, not here)
- A drop-in Part 11 validated quality system without site SOPs and controls
- Full SUPAC automation (v2.6 helpers are screening only)
- A primary regulatory sparse-PK method; the one-compartment oral sparse fit is a
  model-informed screening tool and requires study-specific validation

Final regulatory interpretation must always be reviewed by qualified formulation,
pharmacokinetic, and regulatory experts.

## Current release context (for agents)

Version **2.6.0** was published to PyPI and GitHub Releases on 2026-07-15.
Always read **`HANDOFF.md` at the repository root** in the working tree for
branch name, PR number, verification results, and release status.

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
