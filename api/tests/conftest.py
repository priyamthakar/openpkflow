"""Shared fixtures for the API test suite."""

from __future__ import annotations

from pathlib import Path

import pytest
from app.main import app
from fastapi.testclient import TestClient

DATASETS = Path(__file__).parent.parent.parent / "src" / "openpkflow" / "datasets"


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
def theoph_csv() -> Path:
    return DATASETS / "theoph.csv"


@pytest.fixture()
def dissolution_csv() -> Path:
    return DATASETS / "example_dissolution.csv"
