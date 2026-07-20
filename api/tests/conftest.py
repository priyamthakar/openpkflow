"""Shared fixtures for the API test suite."""

from __future__ import annotations

from pathlib import Path

import pytest
from app.main import app
from fastapi.testclient import TestClient

DATASETS = Path(__file__).parent.parent.parent / "src" / "openpkflow" / "datasets"
VALIDATION_DATA = Path(__file__).parent.parent.parent / "tests" / "validation" / "data"


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
def theoph_csv() -> Path:
    return DATASETS / "theoph.csv"


@pytest.fixture()
def dissolution_csv() -> Path:
    return DATASETS / "example_dissolution.csv"


@pytest.fixture()
def rsabe_patterson2012_csv() -> Path:
    return VALIDATION_DATA / "be_rsabe_partial_replicate_patterson2012.csv"
