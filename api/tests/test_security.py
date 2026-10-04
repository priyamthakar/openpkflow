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


def test_report_output_is_created_privately_and_removed_on_failure() -> None:
    with pytest.raises(RuntimeError), deps.report_output(".html") as path:
        assert path.exists()
        assert path.stat().st_mode & 0o077 == 0
        leaked = path
        raise RuntimeError("report generation failed")

    assert not leaked.exists()
