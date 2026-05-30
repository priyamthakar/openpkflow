"""Release readiness checks for OpenPKFlow.

This script is intentionally read-only. It validates local metadata and, when
GitHub CLI is available, checks remote release/tag state for the current version.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parents[1]


def _run(args: list[str]) -> tuple[int, str]:
    proc = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, check=False)
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def _ok(message: str) -> None:
    print(f"OK   {message}")


def _fail(message: str, failures: list[str]) -> None:
    print(f"FAIL {message}")
    failures.append(message)


def main() -> int:
    failures: list[str] = []

    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    version = pyproject["project"]["version"]
    tag = f"v{version}"
    _ok(f"pyproject version: {version}")

    init_text = (ROOT / "src" / "openpkflow" / "__init__.py").read_text(encoding="utf-8")
    match = re.search(r'__version__\s*=\s*"([^"]+)"', init_text)
    if not match:
        _fail("src/openpkflow/__init__.py has no __version__", failures)
    elif match.group(1) != version:
        _fail(f"__version__ {match.group(1)} does not match pyproject {version}", failures)
    else:
        _ok("__version__ matches pyproject")

    changelog = (ROOT / "docs" / "changelog.md").read_text(encoding="utf-8")
    if f"## [{version}]" in changelog or "## [Unreleased]" in changelog:
        _ok("changelog has release or unreleased section")
    else:
        _fail("changelog is missing release/unreleased section", failures)

    code, output = _run(["git", "status", "--short"])
    if code == 0 and not output:
        _ok("git working tree is clean")
    else:
        _fail("git working tree is not clean", failures)

    code, output = _run(["git", "tag", "--list", tag])
    if code == 0 and tag in output.splitlines():
        _ok(f"local tag exists: {tag}")
    else:
        print(f"WARN local tag missing: {tag}")

    code, _output = _run(["gh", "release", "view", tag, "--json", "tagName,url"])
    if code == 0:
        _ok(f"GitHub release exists: {tag}")
    else:
        print(f"WARN GitHub release not found for {tag}")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
