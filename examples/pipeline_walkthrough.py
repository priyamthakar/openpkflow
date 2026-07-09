"""Sequential formulation-to-report walkthrough (dissolution + NCA).

Runs dissolution similarity on the bundled example dataset, then NCA on the
Theoph reference dataset, and prints ASCII summaries.  Dependency-light:
core openpkflow only (numpy/pandas/scipy as already required by the package).

Run from the repo root after installing the package::

    pip install -e .
    python examples/pipeline_walkthrough.py

Or without installing (editable source on sys.path)::

    python examples/pipeline_walkthrough.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_repo_root = Path(__file__).resolve().parent.parent
_src = _repo_root / "src"
if _src.exists() and str(_src) not in sys.path:
    sys.path.insert(0, str(_src))


def _banner(title: str) -> None:
    line = "=" * 62
    print(line)
    print(f"  {title}")
    print(line)
    print()


def run_dissolution() -> None:
    """Dissolution f1/f2 on bundled multi-batch example CSV."""
    from openpkflow.datasets import example_dissolution_path
    from openpkflow.dissolution import DissolutionStudy

    path = example_dissolution_path()
    print(f"Dataset: {path}")
    study = DissolutionStudy.from_csv(path)
    result = study.compare(reference="reference", test="test")
    print(result.summary())
    print()
    print("Note: f2 >= 50 suggests similarity (FDA 1997 IR dissolution guidance).")
    print()


def run_nca() -> None:
    """NCA on R nlme::Theoph oral theophylline (12 subjects)."""
    from openpkflow.datasets import example_theoph_path
    from openpkflow.nca import NCAStudy

    path = example_theoph_path()
    print(f"Dataset: {path}")
    study = NCAStudy.from_csv(
        path,
        auc_method="linear_up_log_down",
        blq_method="none",
    )
    summary = study.analyze()
    df = summary.to_dataframe()
    cols = [
        c for c in ("subject", "Cmax", "Tmax", "AUClast", "half_life", "CL_F") if c in df.columns
    ]
    print(df[cols].to_string(index=False))
    print()
    if "AUClast" in df.columns:
        print(f"Mean AUClast : {df['AUClast'].mean():.3f}")
    if "Cmax" in df.columns:
        print(f"Mean Cmax    : {df['Cmax'].mean():.3f}")
    if "half_life" in df.columns:
        print(f"Mean t1/2    : {df['half_life'].mean():.3f}")
    print()
    print("AUClast method: linear_up_log_down; BLQ: none (explicit).")
    print()


def main() -> None:
    _banner("OpenPKFlow -- Pipeline walkthrough (dissolution -> NCA)")
    print("Sequential demo. Unified `openpkflow pipeline` CLI may arrive later.")
    print("See docs/tutorials/pipeline.md and docs/positioning.md.")
    print()

    _banner("Step 1: Dissolution similarity")
    run_dissolution()

    _banner("Step 2: NCA (Theoph reference)")
    run_nca()

    _banner("Done")
    print("Next steps (optional, not run here):")
    print("  - openpkflow be compare be_params.csv --report out/be.html")
    print("  - result.report(...) / summary.report(...) for HTML/PDF/DOCX")
    print("  - IVIVC Level A: see docs/tutorials/ivivc.md")
    print()
    print("Disclaimer: OpenPKFlow is open-source research software. Final")
    print("regulatory interpretation requires qualified expert review.")
    print()


if __name__ == "__main__":
    main()
