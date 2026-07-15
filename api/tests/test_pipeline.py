"""Study-pipeline endpoint tests."""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

from fastapi.testclient import TestClient


def _options() -> str:
    return json.dumps(
        {
            "title": "API pipeline test",
            "dissolution_reference": "reference",
            "dissolution_test": "test",
        }
    )


def test_analyze_dissolution_pipeline(client: TestClient, dissolution_csv: Path) -> None:
    with dissolution_csv.open("rb") as file:
        response = client.post(
            "/api/pipeline/analyze",
            data={"options": _options()},
            files={"dissolution_file": ("dissolution.csv", file, "text/csv")},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["metadata"]["stages_completed"] == ["dissolution"]
    assert body["metadata"]["config"]["dissolution_csv"] == "dissolution.csv"
    assert body["dissolution"]["f2_value"] >= 50
    assert "regulatory experts" in body["disclaimer"]


def test_pipeline_report(client: TestClient, dissolution_csv: Path) -> None:
    with dissolution_csv.open("rb") as file:
        response = client.post(
            "/api/pipeline/report",
            data={"options": _options(), "format": "html"},
            files={"dissolution_file": ("dissolution.csv", file, "text/csv")},
        )

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert b"API pipeline test" in response.content


def test_pipeline_audit_bundle(client: TestClient, dissolution_csv: Path) -> None:
    with dissolution_csv.open("rb") as file:
        response = client.post(
            "/api/pipeline/audit-bundle",
            data={"options": _options()},
            files={"dissolution_file": ("dissolution.csv", file, "text/csv")},
        )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        assert "manifest.json" in archive.namelist()
        assert "inputs/dissolution.csv" in archive.namelist()
