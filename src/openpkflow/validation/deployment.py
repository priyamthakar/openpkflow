"""Verify that a deployed OpenPKFlow API matches the expected release."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import urlopen

from openpkflow import __version__


def _load_json(url: str, timeout: float) -> dict[str, Any]:
    """Load a JSON object from a production endpoint."""
    try:
        with urlopen(url, timeout=timeout) as response:  # noqa: S310
            payload = json.load(response)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Could not read {url}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"Expected a JSON object from {url}")
    return payload


def verify_deployment(
    base_url: str,
    expected_version: str,
    expected_git_sha: str | None = None,
    timeout: float = 30.0,
) -> dict[str, str]:
    """Verify health and OpenAPI release provenance for a deployed API.

    Parameters
    ----------
    base_url : str
        Base URL of the deployed API.
    expected_version : str
        Package version required from health and OpenAPI metadata.
    expected_git_sha : str or None
        Optional required prefix of the deployed Git commit.
    timeout : float
        Per-request timeout in seconds.

    Returns
    -------
    dict[str, str]
        Observed version and deployment provenance.

    Raises
    ------
    RuntimeError
        If an endpoint is unavailable or its metadata does not match.
    """
    normalized_url = base_url.rstrip("/") + "/"
    health = _load_json(urljoin(normalized_url, "health"), timeout)
    openapi = _load_json(urljoin(normalized_url, "openapi.json"), timeout)

    actual = {
        "health_version": str(health.get("engine_version", "")),
        "openapi_version": str(openapi.get("info", {}).get("version", "")),
        "git_sha": str(health.get("git_sha", "")),
        "git_branch": str(health.get("git_branch", "")),
        "service_id": str(health.get("service_id", "")),
    }
    failures: list[str] = []
    if health.get("status") != "ok":
        failures.append(f"health status is {health.get('status')!r}, expected 'ok'")
    if actual["health_version"] != expected_version:
        failures.append(
            f"health engine_version is {actual['health_version']!r}, expected {expected_version!r}"
        )
    if actual["openapi_version"] != expected_version:
        failures.append(
            f"OpenAPI version is {actual['openapi_version']!r}, expected {expected_version!r}"
        )
    if expected_git_sha and not actual["git_sha"].startswith(expected_git_sha):
        failures.append(
            f"health git_sha is {actual['git_sha']!r}, expected prefix {expected_git_sha!r}"
        )
    if failures:
        raise RuntimeError("; ".join(failures))
    return actual


def main() -> int:
    """Run the production convergence check from the command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--expected-version", default=__version__)
    parser.add_argument("--expected-git-sha")
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args()

    try:
        actual = verify_deployment(
            args.base_url,
            args.expected_version,
            expected_git_sha=args.expected_git_sha,
            timeout=args.timeout,
        )
    except RuntimeError as exc:
        print(f"Production convergence check failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(actual, indent=2, sort_keys=True))
    return 0
