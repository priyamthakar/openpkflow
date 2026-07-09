"""Dissolution endpoint tests."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from fastapi.testclient import TestClient

from openpkflow.dissolution.loader import DissolutionCSVConfig
from openpkflow.dissolution.study import DissolutionStudy


def _ref_compare(path: Path, ref: str, test: str) -> tuple[float, float]:
    study = DissolutionStudy.from_csv(path, DissolutionCSVConfig())
    result = study.compare(ref, test)
    return result.f1_value, result.f2_value


def test_formulations(client: TestClient, dissolution_csv: Path) -> None:
    with dissolution_csv.open("rb") as f:
        resp = client.post(
            "/api/dissolution/formulations",
            data={"columns": "{}"},
            files={"file": ("diss.csv", f, "text/csv")},
        )
    assert resp.status_code == 200
    fms = resp.json()["formulations"]
    assert len(fms) >= 2


def test_compare_golden(client: TestClient, dissolution_csv: Path) -> None:
    study = DissolutionStudy.from_csv(dissolution_csv)
    fms = study.formulations()
    ref_label, test_label = fms[0], fms[1]
    f1_ref, f2_ref = _ref_compare(dissolution_csv, ref_label, test_label)

    with dissolution_csv.open("rb") as f:
        resp = client.post(
            "/api/dissolution/compare",
            data={"reference": ref_label, "test": test_label, "columns": "{}"},
            files={"file": ("diss.csv", f, "text/csv")},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert abs(body["f1_value"] - f1_ref) < 1e-4
    assert abs(body["f2_value"] - f2_ref) < 1e-4
    assert body["similar"] == (f2_ref >= 50.0)


def test_compare_bad_formulation(client: TestClient, dissolution_csv: Path) -> None:
    with dissolution_csv.open("rb") as f:
        resp = client.post(
            "/api/dissolution/compare",
            data={"reference": "DOES_NOT_EXIST", "test": "reference", "columns": "{}"},
            files={"file": ("diss.csv", f, "text/csv")},
        )
    assert resp.status_code == 422


def test_compare_disclaimer(client: TestClient, dissolution_csv: Path) -> None:
    study = DissolutionStudy.from_csv(dissolution_csv)
    fms = study.formulations()
    with dissolution_csv.open("rb") as f:
        resp = client.post(
            "/api/dissolution/compare",
            data={"reference": fms[0], "test": fms[1], "columns": "{}"},
            files={"file": ("diss.csv", f, "text/csv")},
        )
    assert "disclaimer" in resp.json()


def test_compare_custom_columns(client: TestClient, dissolution_csv: Path, tmp_path: Path) -> None:
    df = pd.read_csv(dissolution_csv)
    df = df.rename(
        columns={
            "formulation": "FORM",
            "batch": "LOT",
            "time": "MINUTES",
            "percent_released": "PCT_REL",
        }
    )
    custom_csv = tmp_path / "diss_custom.csv"
    df.to_csv(custom_csv, index=False)
    columns = '{"formulation":"FORM","batch":"LOT","time":"MINUTES","percent_released":"PCT_REL"}'

    with custom_csv.open("rb") as f:
        resp = client.post(
            "/api/dissolution/compare",
            data={"reference": "reference", "test": "test", "columns": columns},
            files={"file": ("diss_custom.csv", f, "text/csv")},
        )

    assert resp.status_code == 200
    assert resp.json()["f2_value"] > 0


def _media_rows(ref: list[float], test: list[float], times: list[int] | None = None) -> list[dict]:
    if times is None:
        times = [5, 10, 15, 20, 30, 45, 60]
    rows: list[dict] = []
    for i, t in enumerate(times):
        rows.append(
            {
                "formulation": "reference",
                "batch": "R1",
                "time": t,
                "percent_released": ref[i],
            }
        )
        rows.append(
            {
                "formulation": "test",
                "batch": "T1",
                "time": t,
                "percent_released": test[i],
            }
        )
    return rows


def test_multi_media_analyze_pass(client: TestClient) -> None:
    ref = [5, 15, 30, 45, 60, 80, 95]
    tst = [6, 16, 31, 44, 58, 78, 93]
    payload = {
        "media": [
            {"name": "pH 1.2", "rows": _media_rows(ref, tst)},
            {"name": "pH 6.8", "rows": _media_rows(ref, tst)},
        ],
        "reference_label": "reference",
        "test_label": "test",
    }
    resp = client.post("/api/dissolution/multi-media/analyze", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["overall_pass"] is True
    assert body["media_names"] == ["pH 1.2", "pH 6.8"]
    assert body["f2_summary"]["pH 1.2"] >= 50
    assert len(body["per_media"]) == 2
    assert "disclaimer" in body


def test_multi_media_analyze_fail(client: TestClient) -> None:
    ref = [5, 15, 30, 45, 60, 80, 95]
    far = [5, 60, 90, 95, 98, 99, 100]
    tst = [6, 16, 31, 44, 58, 78, 93]
    payload = {
        "media": [
            {"name": "Good", "rows": _media_rows(ref, tst)},
            {"name": "Bad", "rows": _media_rows(ref, far)},
        ],
        "reference_label": "reference",
        "test_label": "test",
    }
    resp = client.post("/api/dissolution/multi-media/analyze", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["overall_pass"] is False
    assert body["f2_summary"]["Bad"] < 50


def test_multi_media_requires_two_media(client: TestClient) -> None:
    ref = [5, 15, 30, 45, 60, 80, 95]
    payload = {
        "media": [{"name": "Only", "rows": _media_rows(ref, ref)}],
        "reference_label": "reference",
        "test_label": "test",
    }
    resp = client.post("/api/dissolution/multi-media/analyze", json=payload)
    assert resp.status_code == 422
