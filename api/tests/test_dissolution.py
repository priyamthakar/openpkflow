"""Dissolution endpoint tests."""

from __future__ import annotations

from pathlib import Path

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
