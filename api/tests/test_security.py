"""API boundary security tests."""

from __future__ import annotations

import pytest
from app import deps
from app.config import Settings
from fastapi.testclient import TestClient


def test_security_headers(client: TestClient) -> None:
    response = client.get("/health")

    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["permissions-policy"] == "camera=(), microphone=(), geolocation=()"


def test_upload_limit(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(deps, "settings", Settings(max_upload_bytes=4))

    response = client.post(
        "/api/nca/analyze",
        data={"options": "{}"},
        files={"file": ("profile.csv", b"12345", "text/csv")},
    )

    assert response.status_code == 413
    assert response.json() == {"detail": "Upload exceeds configured size limit."}
