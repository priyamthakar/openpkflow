"""BE endpoint tests (TOST analyze + power / sample-size)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from fastapi.testclient import TestClient

from openpkflow.be.methods import be_sample_size, be_tost_power


def _be_csv(tmp_path: Path) -> Path:
    rows = [
        {"subject": "S01", "sequence": "RT", "reference": 100.2, "test": 96.4},
        {"subject": "S02", "sequence": "RT", "reference": 112.5, "test": 108.1},
        {"subject": "S03", "sequence": "TR", "reference": 95.8, "test": 91.3},
        {"subject": "S04", "sequence": "TR", "reference": 108.0, "test": 102.7},
        {"subject": "S05", "sequence": "RT", "reference": 103.4, "test": 99.8},
        {"subject": "S06", "sequence": "TR", "reference": 97.6, "test": 94.1},
    ]
    path = tmp_path / "be.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def test_be_analyze(client: TestClient, tmp_path: Path) -> None:
    csv_path = _be_csv(tmp_path)
    with csv_path.open("rb") as f:
        resp = client.post(
            "/api/be/analyze",
            data={"options": "{}"},
            files={"file": ("be.csv", f, "text/csv")},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["n"] == 6
    assert "gmr" in body
    assert "disclaimer" in body


def test_be_power_matches_library(client: TestClient) -> None:
    payload = {"gmr": 0.95, "cv": 0.20, "n": 24}
    expected = be_tost_power(0.95, 0.20, 24)
    resp = client.post("/api/be/power", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert abs(body["power"] - expected) < 1e-10
    assert body["n"] == 24
    assert "disclaimer" in body


def test_be_sample_size_matches_library(client: TestClient) -> None:
    payload = {"gmr": 0.95, "cv": 0.20, "target_power": 0.80}
    n_ref, p_ref = be_sample_size(0.95, 0.20, 0.80)
    resp = client.post("/api/be/sample-size", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["n"] == n_ref
    assert abs(body["achieved_power"] - p_ref) < 1e-10


def test_be_power_invalid_gmr(client: TestClient) -> None:
    resp = client.post("/api/be/power", json={"gmr": -1.0, "cv": 0.20, "n": 24})
    assert resp.status_code == 422


def test_be_sample_size_unreachable(client: TestClient) -> None:
    resp = client.post(
        "/api/be/sample-size",
        json={"gmr": 0.85, "cv": 0.40, "target_power": 0.99, "max_n": 10},
    )
    assert resp.status_code == 422
