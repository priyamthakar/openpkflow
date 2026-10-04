"""Cross-validation of msd_vessels() against disprofas::mimcr() (Tsong 1996 MIMCR).

Reference values were produced by ``scripts/disprofas_msd_crossval.R`` with
disprofas 0.2.1.9000 (GitHub commit 429d6f1, 2025-03-23) on R 4.5.3, using the
datasets bundled with disprofas (dip1, dip2, dip3, dip4). The time points are
the ones mimcr() selected with its default ``bounds = c(1, 85)`` rule.

The ``dip3_batch_95_doc_example`` case reproduces the worked example ``res1``
printed in the disprofas ``mimcr()`` help page (DM 0.2384023, Sim.Limit
2.248072, Obs.U 1.543820).

Sources:
    Tsong Y, Hammerstrom T, Sathe P, Shah VP (1996). Statistical assessment of
    mean differences between two dissolution data sets. Drug Inf J 30:1105-1112.
    Dahinden P. disprofas: Non-Parametric Dissolution Profile Analysis, R
    package, mimcr() help page.

disprofas reports Obs.L as |DM - sqrt(F/K)| (a point on the confidence-region
boundary along the mean-difference direction). When the region contains the
origin (DM < sqrt(F/K)) the true lower bound of the MSD over the region is 0,
which is what msd_vessels() reports; the similarity decision uses only the
upper bound, which agrees in every case.
"""

from __future__ import annotations

import pytest

from openpkflow.dissolution.similarity import msd_vessels

# disprofas 0.2.1.9000, R version 4.5.3 (2026-03-11)
_DISPROFAS_REFERENCE: dict[str, dict] = {
    "dip1_type_90": {
        "columns": ["t.5", "t.10", "t.15", "t.20", "t.30", "t.60", "t.90"],
        "reference": [
            [42.06, 59.91, 65.58, 71.81, 77.77, 85.67, 93.14],
            [44.16, 60.18, 67.17, 70.82, 76.11, 83.27, 88.01],
            [45.63, 55.77, 65.56, 70.5, 76.92, 83.91, 86.83],
            [48.52, 60.39, 66.51, 73.06, 78.45, 84.99, 88],
            [50.49, 61.82, 69.06, 72.85, 78.99, 86.86, 89.7],
            [49.77, 62.73, 69.77, 72.88, 80.18, 84.2, 88.88],
        ],
        "test": [
            [19.99, 36.7, 47.77, 55.08, 65.69, 81.37, 92.39],
            [22.08, 39.29, 49.46, 56.79, 67.22, 82.42, 89.93],
            [21.93, 38.54, 47.76, 55.14, 65.25, 83.49, 90.19],
            [22.44, 39.46, 49.72, 58.67, 69.21, 84.93, 94.12],
            [25.67, 42.35, 52.68, 59.71, 71.51, 86.61, 93.8],
            [26.37, 41.34, 51.01, 57.75, 69.44, 85.9, 94.45],
        ],
        "mtad": 10,
        "confidence_level": 0.9,
        "dm": 25.7166742677055,
        "f_crit": 3.97896624379538,
        "sim_limit": 11.3280414769246,
        "obs_lower": 20.898932429236,
        "obs_upper": 30.534416106175,
        "similar": False,
    },
    "dip1_type_90_mtad15": {
        "columns": ["t.5", "t.10", "t.15", "t.20", "t.30", "t.60", "t.90"],
        "reference": [
            [42.06, 59.91, 65.58, 71.81, 77.77, 85.67, 93.14],
            [44.16, 60.18, 67.17, 70.82, 76.11, 83.27, 88.01],
            [45.63, 55.77, 65.56, 70.5, 76.92, 83.91, 86.83],
            [48.52, 60.39, 66.51, 73.06, 78.45, 84.99, 88],
            [50.49, 61.82, 69.06, 72.85, 78.99, 86.86, 89.7],
            [49.77, 62.73, 69.77, 72.88, 80.18, 84.2, 88.88],
        ],
        "test": [
            [19.99, 36.7, 47.77, 55.08, 65.69, 81.37, 92.39],
            [22.08, 39.29, 49.46, 56.79, 67.22, 82.42, 89.93],
            [21.93, 38.54, 47.76, 55.14, 65.25, 83.49, 90.19],
            [22.44, 39.46, 49.72, 58.67, 69.21, 84.93, 94.12],
            [25.67, 42.35, 52.68, 59.71, 71.51, 86.61, 93.8],
            [26.37, 41.34, 51.01, 57.75, 69.44, 85.9, 94.45],
        ],
        "mtad": 15,
        "confidence_level": 0.9,
        "dm": 25.7166742677055,
        "f_crit": 3.97896624379538,
        "sim_limit": 16.9920622153869,
        "obs_lower": 20.898932429236,
        "obs_upper": 30.534416106175,
        "similar": False,
    },
    "dip3_batch_95_doc_example": {
        "columns": ["x.15", "x.20", "x.25"],
        "reference": [
            [31, 79, 94],
            [13, 64, 97],
            [55, 81, 96],
            [50, 72, 86],
            [37, 91, 99],
            [47, 88, 96],
            [39, 87, 97],
            [3, 33, 80],
            [37, 77, 94],
            [34, 74, 92],
            [4, 59, 91],
            [11, 60, 100],
        ],
        "test": [
            [49, 86, 98],
            [15, 59, 96],
            [56, 84, 96],
            [57, 87, 99],
            [6, 58, 90],
            [62, 90, 97],
            [23, 71, 97],
            [11, 64, 92],
            [9, 61, 88],
            [42, 81, 96],
            [57, 86, 98],
            [4, 48, 82],
        ],
        "mtad": 10,
        "confidence_level": 0.95,
        "dm": 0.23840234418662,
        "f_crit": 3.09839121214078,
        "sim_limit": 2.24807191189174,
        "obs_lower": 1.06701527737264,
        "obs_upper": 1.54381996574588,
        "similar": True,
    },
    "dip3_batch_90": {
        "columns": ["x.15", "x.20", "x.25"],
        "reference": [
            [31, 79, 94],
            [13, 64, 97],
            [55, 81, 96],
            [50, 72, 86],
            [37, 91, 99],
            [47, 88, 96],
            [39, 87, 97],
            [3, 33, 80],
            [37, 77, 94],
            [34, 74, 92],
            [4, 59, 91],
            [11, 60, 100],
        ],
        "test": [
            [49, 86, 98],
            [15, 59, 96],
            [56, 84, 96],
            [57, 87, 99],
            [6, 58, 90],
            [62, 90, 97],
            [23, 71, 97],
            [11, 64, 92],
            [9, 61, 88],
            [42, 81, 96],
            [57, 86, 98],
            [4, 48, 82],
        ],
        "mtad": 10,
        "confidence_level": 0.9,
        "dm": 0.23840234418662,
        "f_crit": 2.38008705106961,
        "sim_limit": 2.24807191189174,
        "obs_lower": 0.905733958046766,
        "obs_upper": 1.38253864642,
        "similar": True,
    },
    "dip4_type_90": {
        "columns": ["x.10", "x.20", "x.30"],
        "reference": [
            [30, 76, 97],
            [10, 59, 96],
            [32, 77, 97],
            [50, 90, 98],
            [16, 64, 95],
            [17, 77, 96],
            [47, 87, 98],
            [37, 83, 98],
            [41, 82, 98],
            [42, 78, 98],
            [34, 81, 97],
            [42, 81, 99],
        ],
        "test": [
            [68, 94, 99],
            [55, 76, 97],
            [51, 83, 98],
            [65, 90, 98],
            [18, 65, 96],
            [66, 88, 99],
            [50, 75, 97],
            [39, 70, 97],
            [64, 83, 99],
            [52, 76, 97],
            [51, 80, 97],
            [36, 74, 97],
        ],
        "mtad": 10,
        "confidence_level": 0.9,
        "dm": 2.82397552092731,
        "f_crit": 2.38008705106961,
        "sim_limit": 17.1757805440848,
        "obs_lower": 1.67983921869393,
        "obs_upper": 3.9681118231607,
        "similar": True,
    },
    "dip2_b0_b4_90": {
        "columns": ["t.30", "t.60", "t.90", "t.180"],
        "reference": [
            [36.1, 58.6, 80, 93.3],
            [33, 59.5, 80.8, 95.7],
            [35.7, 62.3, 83, 97.1],
            [32.1, 62.3, 81.3, 92.8],
            [36.1, 53.6, 72.6, 88.8],
            [34.1, 63.2, 83, 97.4],
            [32.4, 61.3, 80, 96.8],
            [39.6, 61.8, 80.4, 98.6],
            [34.5, 58, 76.9, 93.3],
            [38, 59.2, 79.3, 94],
            [32.2, 56.2, 77.2, 96.3],
            [35.2, 58, 76.7, 96.8],
        ],
        "test": [
            [17.1, 58.6, 80, 93.3],
            [16, 59.5, 80.8, 95.7],
            [12.7, 62.3, 83, 97.1],
            [15.1, 62.3, 81.3, 92.8],
            [14.1, 53.6, 72.6, 88.8],
            [12.1, 63.2, 83, 97.4],
            [14.4, 61.3, 80, 96.8],
            [19.6, 61.8, 80.4, 98.6],
            [14.5, 58, 76.9, 93.3],
            [14, 59.2, 79.3, 94],
            [18.2, 56.2, 77.2, 96.3],
            [13.2, 58, 76.7, 96.8],
        ],
        "mtad": 10,
        "confidence_level": 0.9,
        "dm": 8.76929621434745,
        "f_crit": 2.26630256748804,
        "sim_limit": 5.9391139497171,
        "obs_lower": 7.44663732282473,
        "obs_upper": 10.0919551058702,
        "similar": False,
    },
}


@pytest.mark.parametrize("case_id", sorted(_DISPROFAS_REFERENCE))
def test_msd_vessels_matches_disprofas_mimcr(case_id: str) -> None:
    case = _DISPROFAS_REFERENCE[case_id]
    result = msd_vessels(
        case["reference"],
        case["test"],
        similarity_limit_pct=case["mtad"],
        confidence_level=case["confidence_level"],
    )

    assert result.msd == pytest.approx(case["dm"], rel=1e-9)
    assert result.f_critical == pytest.approx(case["f_crit"], rel=1e-9)
    assert result.similarity_limit == pytest.approx(case["sim_limit"], rel=1e-9)
    assert result.ci_upper == pytest.approx(case["obs_upper"], rel=1e-9)
    assert result.is_similar is case["similar"]
    if result.msd >= result.ci_upper - result.msd:
        assert result.ci_lower == pytest.approx(case["obs_lower"], rel=1e-9)
    else:
        assert result.ci_lower == 0.0
