"""NCA endpoint tests - golden values match the validated openpkflow library output."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from openpkflow.nca import fit_sparse_1cmt_oral
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


def _sparse_payload(path: Path) -> dict[str, object]:
    data = load_nca_csv(path, blq_method="none")
    profile = data[(data["subject"] == "1") & data["time"].isin([0.25, 1.12, 3.82, 9.05, 24.37])]
    return {
        "subject": "1",
        "times": profile["time"].tolist(),
        "concentrations": profile["conc"].tolist(),
        "dose": 320.0,
    }


def test_sparse_analyze_matches_core(client: TestClient, theoph_csv: Path) -> None:
    payload = _sparse_payload(theoph_csv)
    reference = fit_sparse_1cmt_oral(
        payload["times"],  # type: ignore[arg-type]
        payload["concentrations"],  # type: ignore[arg-type]
        320.0,
    )

    response = client.post("/api/nca/sparse/analyze", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["converged"] is True
    assert body["CL_F"] == pytest.approx(reference.CL_F)
    assert body["Vz_F"] == pytest.approx(reference.Vz_F)
    assert body["scope_note"].startswith("Model-informed")
    assert "regulatory experts" in body["disclaimer"]


def test_sparse_analyze_rejects_invalid_profile(client: TestClient) -> None:
    response = client.post(
        "/api/nca/sparse/analyze",
        json={"times": [1, 1, 3], "concentrations": [4, 3, 1], "dose": 100},
    )

    assert response.status_code == 422
    assert "strictly increasing" in response.json()["detail"]


def test_sparse_three_sample_fit_serializes_unavailable_uncertainty(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/nca/sparse/analyze",
        json={
            "times": [0.25, 1.12, 9.05],
            "concentrations": [2.84, 10.5, 6.89],
            "dose": 320,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["CL_F_se"] is None
    assert body["Vz_F_se"] is None
    assert body["ka_se"] is None
    assert any("standard errors" in warning for warning in body["warnings"])
    assert any("Fewer than five" in warning for warning in body["warnings"])


def test_sparse_report_html(client: TestClient, theoph_csv: Path) -> None:
    response = client.post("/api/nca/sparse/report?format=html", json=_sparse_payload(theoph_csv))

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert b"Sparse NCA Screening Report" in response.content
    assert b"Final regulatory interpretation" in response.content
