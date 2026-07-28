"""Tests for the production deployment convergence check."""

from __future__ import annotations

import pytest

import openpkflow.validation.deployment as production_smoke


def test_verify_deployment_accepts_matching_release(monkeypatch: pytest.MonkeyPatch) -> None:
    responses = {
        "https://example.test/health": {
            "status": "ok",
            "engine_version": "2.7.1",
            "git_sha": "abc123def",
            "git_branch": "main",
            "service_id": "srv-test",
        },
        "https://example.test/openapi.json": {"info": {"version": "2.7.1"}},
    }
    monkeypatch.setattr(production_smoke, "_load_json", lambda url, timeout: responses[url])

    actual = production_smoke.verify_deployment(
        "https://example.test", "2.7.1", expected_git_sha="abc123"
    )

    assert actual["health_version"] == "2.7.1"
    assert actual["openapi_version"] == "2.7.1"
    assert actual["git_sha"] == "abc123def"


@pytest.mark.parametrize(
    ("health", "openapi", "message"),
    [
        (
            {"status": "ok", "engine_version": "2.7.0", "git_sha": "abc"},
            {"info": {"version": "2.7.1"}},
            "health engine_version",
        ),
        (
            {"status": "ok", "engine_version": "2.7.1", "git_sha": "abc"},
            {"info": {"version": "2.7.0"}},
            "OpenAPI version",
        ),
        (
            {"status": "degraded", "engine_version": "2.7.1", "git_sha": "abc"},
            {"info": {"version": "2.7.1"}},
            "health status",
        ),
    ],
)
def test_verify_deployment_rejects_mismatch(
    monkeypatch: pytest.MonkeyPatch,
    health: dict[str, object],
    openapi: dict[str, object],
    message: str,
) -> None:
    responses = {
        "https://example.test/health": health,
        "https://example.test/openapi.json": openapi,
    }
    monkeypatch.setattr(production_smoke, "_load_json", lambda url, timeout: responses[url])

    with pytest.raises(RuntimeError, match=message):
        production_smoke.verify_deployment("https://example.test", "2.7.1")
