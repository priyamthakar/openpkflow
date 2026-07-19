"""SUPAC-IR and alcohol dose-dumping endpoint tests."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_supac_classify_filler_level1(client: TestClient) -> None:
    resp = client.post(
        "/api/supac/classify",
        json={"component_category": "filler", "change_pct": 4.0},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["level"] == 1
    assert body["component_category"] == "filler"
    assert "recommended_tests" in body and len(body["recommended_tests"]) > 0
    assert "scope_note" in body and "disclaimer" in body


def test_supac_classify_filler_level3(client: TestClient) -> None:
    resp = client.post(
        "/api/supac/classify",
        json={"component_category": "filler", "change_pct": 25.0},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["level"] == 3


def test_supac_classify_rejects_negative(client: TestClient) -> None:
    resp = client.post(
        "/api/supac/classify",
        json={"component_category": "filler", "change_pct": -1.0},
    )
    assert resp.status_code == 422, resp.text


def test_alcohol_dosing_detects_divergence(client: TestClient) -> None:
    resp = client.post(
        "/api/supac/alcohol",
        json={
            "time_points": [5, 10, 15, 20, 30],
            "control_means": [45, 70, 85, 92, 96],
            "ethanol_profiles": [
                {"ethanol_pct": 5, "means": [44, 69, 84, 91, 95]},
                {"ethanol_pct": 20, "means": [82, 97, 99, 100, 100]},
            ],
            "f2_threshold": 50.0,
            "control_label": "aqueous",
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["f2_by_ethanol_pct"]["5"] >= 50.0
    assert body["f2_by_ethanol_pct"]["20"] < 50.0
    assert body["overall_pass"] is False
    assert body["f2_method"] == "regulatory"


def test_alcohol_dosing_rejects_mismatched_length(client: TestClient) -> None:
    resp = client.post(
        "/api/supac/alcohol",
        json={
            "time_points": [5, 10, 15],
            "control_means": [45, 70, 85],
            "ethanol_profiles": [{"ethanol_pct": 5, "means": [44, 69]}],
        },
    )
    assert resp.status_code == 422, resp.text


def test_alcohol_dosing_rejects_unmatched_times_and_duplicates(client: TestClient) -> None:
    payload = {
        "time_points": [5, 5, 15],
        "control_means": [45, 70, 85],
        "ethanol_profiles": [{"ethanol_pct": 5, "means": [44, 69, 84]}],
    }
    resp = client.post("/api/supac/alcohol", json=payload)
    assert resp.status_code == 422, resp.text

    payload["time_points"] = [5, 10, 15]
    payload["ethanol_profiles"] = [
        {"ethanol_pct": 5, "means": [44, 69, 84]},
        {"ethanol_pct": 5, "means": [44, 69, 84]},
    ]
    resp = client.post("/api/supac/alcohol", json=payload)
    assert resp.status_code == 422, resp.text
