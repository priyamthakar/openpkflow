"""MAP individual PK endpoint tests."""

from fastapi.testclient import TestClient

_ORAL_PAYLOAD = {
    "subject": "Theoph subject 1",
    "dose": 320.0,
    "route": "oral",
    "times": [0.25, 1.12, 3.82, 9.05, 24.37],
    "concentrations": [2.84, 10.5, 8.58, 6.89, 3.28],
}

_IV_PAYLOAD = {
    "subject": "IV subject",
    "dose": 100.0,
    "route": "iv_bolus",
    "times": [0.5, 1.0, 2.0, 4.0, 8.0],
    "concentrations": [55.0, 38.0, 18.0, 4.2, 0.6],
}


def test_map_analyze_oral(client: TestClient) -> None:
    resp = client.post("/api/bayes/map/analyze", json=_ORAL_PAYLOAD)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["route"] == "oral"
    assert body["converged"] is True
    assert body["fit_usable"] is True
    assert body["CL_F"] is not None and body["CL_F"] > 0
    assert body["Vz_F"] is not None and body["Vz_F"] > 0
    assert body["ka"] is not None and body["ka"] > 0
    assert body["CL"] is None and body["Vz"] is None
    assert "disclaimer" in body and "scope_note" in body


def test_map_analyze_iv_bolus(client: TestClient) -> None:
    resp = client.post("/api/bayes/map/analyze", json=_IV_PAYLOAD)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["route"] == "iv_bolus"
    assert body["CL"] is not None and body["CL"] > 0
    assert body["Vz"] is not None and body["Vz"] > 0
    assert body["CL_F"] is None and body["ka"] is None


def test_map_analyze_rejects_too_few_oral_samples(client: TestClient) -> None:
    payload = dict(_ORAL_PAYLOAD)
    payload["times"] = payload["times"][:2]
    payload["concentrations"] = payload["concentrations"][:2]
    resp = client.post("/api/bayes/map/analyze", json=payload)
    assert resp.status_code == 422, resp.text


def test_map_analyze_rejects_invalid_profile(client: TestClient) -> None:
    payload = dict(_ORAL_PAYLOAD)
    payload["concentrations"] = [2.84, -1.0, 8.58, 6.89, 3.28]
    assert client.post("/api/bayes/map/analyze", json=payload).status_code == 422

    payload["concentrations"] = [0.0, 0.0, 0.0, 0.0, 0.0]
    assert client.post("/api/bayes/map/analyze", json=payload).status_code == 422

    payload["concentrations"] = _ORAL_PAYLOAD["concentrations"]
    payload["times"] = [0.25, 1.12, 1.12, 9.05, 24.37]
    assert client.post("/api/bayes/map/analyze", json=payload).status_code == 422


def test_map_report_html(client: TestClient) -> None:
    resp = client.post("/api/bayes/map/report?format=html", json=_ORAL_PAYLOAD)
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"].startswith("text/html")
    assert b"MAP" in resp.content


def test_map_report_escapes_subject_html(client: TestClient) -> None:
    payload = {**_ORAL_PAYLOAD, "subject": "<script>alert(1)</script>"}
    resp = client.post("/api/bayes/map/report?format=html", json=payload)
    assert resp.status_code == 200, resp.text
    assert b"&lt;script&gt;" in resp.content
    assert b"<script>" not in resp.content
