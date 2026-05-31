"""NCA endpoint tests — golden values match the validated openpkflow library output."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from openpkflow.nca.loader import load_nca_csv
from openpkflow.nca.study import NCAStudy


def _nca_ref(path: Path) -> dict[str, float]:
    """Run NCA directly against the library to get reference values."""
    df = load_nca_csv(path, blq_method="none")
    study = NCAStudy(df, auc_method="linear", blq_method="none")
    summary = study.analyze()
    frame = summary.to_dataframe()
    s1 = frame[frame["subject"] == "1"].iloc[0]
    return {"AUClast": float(s1["AUClast"]), "Cmax": float(s1["Cmax"])}


def test_analyze_golden(client: TestClient, theoph_csv: Path) -> None:
    ref = _nca_ref(theoph_csv)
    with theoph_csv.open("rb") as f:
        resp = client.post(
            "/api/nca/analyze",
            data={"options": json.dumps({"auc_method": "linear", "blq_method": "none"})},
            files={"file": ("theoph.csv", f, "text/csv")},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert "subjects" in body
    s1 = next(r for r in body["subjects"] if str(r["subject"]) == "1")
    assert abs(s1["AUClast"] - ref["AUClast"]) < 0.01 * ref["AUClast"], "AUClast mismatch"
    assert abs(s1["Cmax"] - ref["Cmax"]) < 1e-6, "Cmax mismatch"


def test_analyze_bad_column(client: TestClient, theoph_csv: Path) -> None:
    with theoph_csv.open("rb") as f:
        resp = client.post(
            "/api/nca/analyze",
            data={"options": json.dumps({"columns": {"subject": "NONEXISTENT"}})},
            files={"file": ("theoph.csv", f, "text/csv")},
        )
    assert resp.status_code == 422


def test_analyze_disclaimer_present(client: TestClient, theoph_csv: Path) -> None:
    with theoph_csv.open("rb") as f:
        resp = client.post(
            "/api/nca/analyze",
            data={"options": "{}"},
            files={"file": ("theoph.csv", f, "text/csv")},
        )
    assert "disclaimer" in resp.json()
    assert len(resp.json()["disclaimer"]) > 20


def test_analyze_profiles_returned(client: TestClient, theoph_csv: Path) -> None:
    with theoph_csv.open("rb") as f:
        resp = client.post(
            "/api/nca/analyze",
            data={"options": "{}"},
            files={"file": ("theoph.csv", f, "text/csv")},
        )
    body = resp.json()
    assert len(body["profiles"]) == 12  # theoph has 12 subjects
    profile = body["profiles"][0]
    assert "times" in profile and "concs" in profile


def test_report_html(client: TestClient, theoph_csv: Path) -> None:
    with theoph_csv.open("rb") as f:
        resp = client.post(
            "/api/nca/report",
            data={"options": "{}", "format": "html"},
            files={"file": ("theoph.csv", f, "text/csv")},
        )
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert b"OpenPKFlow" in resp.content
