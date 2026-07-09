"""SUPAC-IR change-level screening and alcohol dose-dumping helpers.

Transparent screening utilities based on FDA SUPAC-IR (1995) style thresholds.
These helpers do NOT replace a full SUPAC guidance interpretation, regulatory
filing strategy, or qualified CMC judgement.

References
----------
FDA Guidance for Industry: Immediate Release Solid Oral Dosage Forms:
Scale-Up and Postapproval Changes (SUPAC-IR, 1995). CDER.

FDA Guidance for Industry: Dissolution Testing of Immediate Release Solid
Oral Dosage Forms (1997). CDER.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

from openpkflow.dissolution.similarity import f2

# Component categories used by the simplified screening table.
# non_critical: fillers/diluents and similar bulk excipients (SUPAC-IR Level 1
#   filler band is +/-5% of total formulation weight).
# critical: release-affecting or high-risk functional excipients with tighter
#   bands (binder / disintegrant / lubricant style thresholds collapsed).
ComponentCategory = Literal["non_critical", "critical"]

SupacLevel = Literal[1, 2, 3]

# Thresholds are percent change of the total target dosage-form weight
# (absolute magnitude). Documented screening assumptions, not a full SUPAC
# multi-row table for every functional class.
#
# non_critical (filler-like): L1 <= 5%, L2 <= 10%, else L3
# critical (binder/disintegrant/lubricant-like collapse): L1 <= 1%, L2 <= 2.5%, else L3
_THRESHOLDS: dict[ComponentCategory, tuple[float, float]] = {
    "non_critical": (5.0, 10.0),
    "critical": (1.0, 2.5),
}

_LEVEL_TESTS: dict[SupacLevel, list[str]] = {
    1: [
        "Application/compendial release and identity testing",
        "Stability: one batch on long-term conditions (commitment)",
    ],
    2: [
        "Multi-point dissolution profile comparison (f2) vs approved product",
        "Stability: one batch, 3 months accelerated + long-term commitment",
    ],
    3: [
        "Multi-point dissolution profile comparison (f2) vs approved product",
        "In vivo bioequivalence study (when dissolution alone is insufficient)",
        "Stability: three batches, 3 months accelerated + long-term commitment",
    ],
}


@dataclass(frozen=True)
class SupacClassification:
    """SUPAC-IR style screening classification for a component change.

    Parameters
    ----------
    level : {1, 2, 3}
        Screened change level (1 = small, 2 = moderate, 3 = large).
    change_pct : float
        Absolute percent change supplied by the caller.
    component_category : {"non_critical", "critical"}
        Excipient risk category used for threshold selection.
    rationale : str
        Human-readable explanation of the level assignment.
    recommended_tests : list[str]
        Screening-level recommended tests for the assigned level.
    """

    level: SupacLevel
    change_pct: float
    component_category: ComponentCategory
    rationale: str
    recommended_tests: list[str]


@dataclass(frozen=True)
class AlcoholDoseDumpingResult:
    """f2-based alcohol dose-dumping screening result.

    Parameters
    ----------
    control_label : str
        Label for the aqueous control medium.
    f2_by_ethanol_pct : dict[float, float]
        f2 of each ethanol medium vs the control profile, keyed by ethanol %.
    f2_threshold : float
        Similarity threshold applied (default 50).
    overall_pass : bool
        True if every ethanol medium has f2 >= f2_threshold.
    """

    control_label: str
    f2_by_ethanol_pct: dict[float, float]
    f2_threshold: float
    overall_pass: bool


def classify_supac_ir_level(
    change_pct: float,
    component_category: ComponentCategory,
) -> SupacClassification:
    """Classify a SUPAC-IR style composition change level (screening only).

    This is a simplified, transparent helper. It does not implement the full
    multi-row SUPAC-IR component table, site/scale/equipment changes, or
    biowaiver eligibility logic. Final regulatory classification requires
    review of the complete SUPAC-IR guidance by qualified CMC experts.

    Screening thresholds (absolute % of total formulation weight)
    -------------------------------------------------------------
    non_critical (filler-like)::

        Level 1: change_pct <= 5
        Level 2: 5 < change_pct <= 10
        Level 3: change_pct > 10

    critical (release-affecting / functional, tighter band)::

        Level 1: change_pct <= 1
        Level 2: 1 < change_pct <= 2.5
        Level 3: change_pct > 2.5

    Parameters
    ----------
    change_pct : float
        Absolute magnitude of the component change as percent of the total
        target dosage-form weight. Must be >= 0.
    component_category : {"non_critical", "critical"}
        Excipient category. Use ``"non_critical"`` for bulk fillers/diluents;
        use ``"critical"`` for binders, disintegrants, lubricants, and other
        release-affecting functional excipients (collapsed tighter band).

    Returns
    -------
    SupacClassification
        Frozen result with level, rationale, and recommended tests.

    Raises
    ------
    ValueError
        If change_pct is negative or non-finite, or component_category is
        not a supported value.

    Notes
    -----
    Caveats: (1) screening only -- not a substitute for full SUPAC-IR
    interpretation; (2) per-function SUPAC rows (e.g. starch vs other
    disintegrant, Mg stearate vs other lubricant) are collapsed into two
    categories; (3) cumulative multi-component changes and process changes
    are out of scope.

    References
    ----------
    FDA Guidance for Industry: Immediate Release Solid Oral Dosage Forms:
    Scale-Up and Postapproval Changes (SUPAC-IR, 1995). CDER.
    """
    if component_category not in _THRESHOLDS:
        raise ValueError(
            f"component_category must be one of {sorted(_THRESHOLDS)!r} "
            f"(got {component_category!r})."
        )
    pct = float(change_pct)
    if pct != pct or pct == float("inf") or pct == float("-inf"):  # NaN/inf
        raise ValueError(f"change_pct must be finite (got {change_pct!r}).")
    if pct < 0.0:
        raise ValueError(f"change_pct must be >= 0 (got {pct}).")

    l1_max, l2_max = _THRESHOLDS[component_category]
    if pct <= l1_max:
        level: SupacLevel = 1
        band = f"<= {l1_max:g}%"
    elif pct <= l2_max:
        level = 2
        band = f"{l1_max:g}% < change <= {l2_max:g}%"
    else:
        level = 3
        band = f"> {l2_max:g}%"

    rationale = (
        f"Screening Level {level} for component_category={component_category!r} "
        f"with |change|={pct:g}% (band: {band}). "
        f"Thresholds: L1 <= {l1_max:g}%, L2 <= {l2_max:g}%, else L3. "
        "Screening only; see FDA SUPAC-IR 1995 for full classification."
    )
    return SupacClassification(
        level=level,
        change_pct=pct,
        component_category=component_category,
        rationale=rationale,
        recommended_tests=list(_LEVEL_TESTS[level]),
    )


def alcohol_dose_dumping_assessment(
    control_means: Sequence[float],
    eth_means_by_pct: Mapping[float, Sequence[float]],
    time_points: Sequence[float] | None = None,
    f2_threshold: float = 50.0,
    *,
    control_label: str = "control",
) -> AlcoholDoseDumpingResult:
    """Screen alcohol dose-dumping risk via f2 vs aqueous control.

    For each ethanol medium (keyed by ethanol percent), computes the f2
    similarity factor against the control medium mean profile. Profiles that
    remain similar (f2 >= threshold) are less consistent with alcohol-driven
    dose dumping; failure indicates a need for further evaluation.

    Parameters
    ----------
    control_means : Sequence[float]
        Mean percent dissolved in the aqueous control medium at each time
        point (aligned arrays).
    eth_means_by_pct : Mapping[float, Sequence[float]]
        Map of ethanol percent (e.g. 5, 20, 40) to mean percent-dissolved
        profiles aligned to the same time points as ``control_means``.
    time_points : Sequence[float] or None, optional
        Optional time grid (minutes). Not used in the f2 calculation but
        accepted for API completeness / caller documentation. Must match
        profile length if provided.
    f2_threshold : float, optional
        Similarity threshold, by default 50.0 (FDA 1997 f2 criterion).
    control_label : str, optional
        Label for the control medium, by default ``"control"``.

    Returns
    -------
    AlcoholDoseDumpingResult
        Per-ethanol f2 values and overall pass/fail.

    Raises
    ------
    ValueError
        If eth_means_by_pct is empty, f2_threshold is not positive, time
        points length mismatches, or f2 validation fails for any profile.

    Notes
    -----
    This is a dissolution-similarity screen, not a full dose-dumping clinical
    assessment. Regulatory context for alcohol media is typically modified-
    release products; applying the same f2 screen to IR data is a transparent
    descriptive comparison only.

    References
    ----------
    FDA Guidance for Industry: Dissolution Testing of Immediate Release
    Solid Oral Dosage Forms (1997). CDER. (f2 criterion)

    FDA Guidance for Industry: Immediate Release Solid Oral Dosage Forms:
    Scale-Up and Postapproval Changes (SUPAC-IR, 1995). CDER.
    """
    if not eth_means_by_pct:
        raise ValueError("eth_means_by_pct must contain at least one ethanol medium.")
    thr = float(f2_threshold)
    if thr <= 0.0:
        raise ValueError(f"f2_threshold must be > 0 (got {thr}).")

    n = len(control_means)
    if time_points is not None and len(time_points) != n:
        raise ValueError(
            f"time_points length ({len(time_points)}) must match control_means length ({n})."
        )

    f2_by: dict[float, float] = {}
    for eth_pct, means in eth_means_by_pct.items():
        key = float(eth_pct)
        if len(means) != n:
            raise ValueError(
                f"Ethanol {key:g}% profile length ({len(means)}) must match "
                f"control_means length ({n})."
            )
        f2_by[key] = f2(control_means, means)

    overall = all(v >= thr for v in f2_by.values())
    return AlcoholDoseDumpingResult(
        control_label=control_label,
        f2_by_ethanol_pct=f2_by,
        f2_threshold=thr,
        overall_pass=overall,
    )
