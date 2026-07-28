"""Simulation endpoint tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

_ORAL_1CMT = {
    "model_type": "1cmt",
    "route": "oral",
    "params": {"CL_F": 5.0, "Vz_F": 50.0, "ka": 1.2},
    "regimen": {"amount": 100.0, "tau": 12.0, "n_doses": 5, "t_start": 0.0},
    "times": {"start": 0.0, "stop": 60.0, "n": 300},
}

_IV_1CMT = {
    "model_type": "1cmt",
    "route": "iv_bolus",
    "params": {"CL": 5.0, "Vz": 50.0},
    "regimen": {"amount": 100.0, "tau": 12.0, "n_doses": 1},
    "times": {"start": 0.0, "stop": 24.0, "n": 200},
}

_2CMT_ORAL = {
    "model_type": "2cmt",
    "route": "oral",
    "params": {"CL_F": 5.0, "V1_F": 20.0, "Q": 2.0, "V2": 30.0, "ka": 1.2},
    "regimen": {"amount": 100.0, "tau": 12.0, "n_doses": 3},
    "times": {"start": 0.0, "stop": 36.0, "n": 200},
}


def test_simulate_oral(client: TestClient) -> None:
    resp = client.post("/api/sim/simulate", json=_ORAL_1CMT)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["times"]) == 300
    assert len(body["concs"]) == 300
    assert body["Cmax"] > 0
    assert 0.0 < body["Tmax"] < 60.0
    assert len(body["dose_times"]) == 5


def test_simulate_iv_bolus(client: TestClient) -> None:
    resp = client.post("/api/sim/simulate", json=_IV_1CMT)
    assert resp.status_code == 200
    body = resp.json()
    # IV bolus: Cmax at or near t=0
    assert body["Tmax"] < 1.0


def test_simulate_2cmt_oral(client: TestClient) -> None:
    resp = client.post("/api/sim/simulate", json=_2CMT_ORAL)
    assert resp.status_code == 200
    assert resp.json()["Cmax"] > 0


def test_simulate_invalid_params(client: TestClient) -> None:
    bad = {**_ORAL_1CMT, "params": {}}  # missing CL_F/Vz_F/ka
    resp = client.post("/api/sim/simulate", json=bad)
    assert resp.status_code == 422


def test_simulate_disclaimer(client: TestClient) -> None:
    resp = client.post("/api/sim/simulate", json=_ORAL_1CMT)
    assert "disclaimer" in resp.json()


def test_simulate_cmax_consistency(client: TestClient) -> None:
    """Cmax from the API must equal max(concs)."""
    resp = client.post("/api/sim/simulate", json=_ORAL_1CMT)
    body = resp.json()
    assert abs(body["Cmax"] - max(body["concs"])) < 1e-9


def test_health(client: TestClient, monkeypatch) -> None:
    monkeypatch.setenv("RENDER_GIT_COMMIT", "abc123")
    monkeypatch.setenv("RENDER_GIT_BRANCH", "main")
    monkeypatch.setenv("RENDER_SERVICE_ID", "srv-openpkflow")
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {
        "status": "ok",
        "engine_version": resp.json()["engine_version"],
        "git_sha": "abc123",
        "git_branch": "main",
        "service_id": "srv-openpkflow",
    }


def test_health_uses_local_provenance_defaults(client: TestClient, monkeypatch) -> None:
    monkeypatch.delenv("RENDER_GIT_COMMIT", raising=False)
    monkeypatch.delenv("RENDER_GIT_BRANCH", raising=False)
    monkeypatch.delenv("RENDER_SERVICE_ID", raising=False)
    monkeypatch.delenv("OPENPKFLOW_GIT_SHA", raising=False)
    monkeypatch.delenv("OPENPKFLOW_GIT_BRANCH", raising=False)

    body = client.get("/health").json()

    assert body["git_sha"] == "unknown"
    assert body["git_branch"] == "unknown"
    assert body["service_id"] == "local"
