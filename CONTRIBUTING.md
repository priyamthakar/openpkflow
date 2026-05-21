# Contributing to OpenPKFlow

Thanks for your interest. Contributions that improve pharmacometric correctness, test coverage, documentation, or usability are welcome.

## Before you open a PR

1. Open an issue first for any non-trivial change (new module, API change, algorithm choice). This avoids wasted work if the approach doesn't fit the project.
2. All formula implementations must include at least two test cases — a degenerate/sanity case and a published reference example with citation. See `CLAUDE.md` for the validation discipline rules.

## Setup

```bash
git clone https://github.com/priyamthakar/openpkflow
cd openpkflow
pip install -e ".[dev,reports]"
```

## Workflow

```bash
# Run tests
pytest

# Lint and format
ruff check src/ tests/ --fix
ruff format src/ tests/

# Type-check
mypy src/openpkflow
```

All three must pass cleanly before opening a PR. CI enforces this.

## Code conventions

- Type hints required on all public API functions.
- Docstrings required on all public functions (NumPy style).
- Line length: 100 characters.
- Comments only where the WHY is non-obvious.
- ASCII-only in CLI output and docstrings (Windows cp1252 constraint).

See `CLAUDE.md` for the full pharmacometric correctness rules.

## Pharmacometric correctness

- f1/f2 require matched time points. Never silently reindex or interpolate.
- AUC method must always be explicit — no silent defaults.
- Apparent vs absolute clearance must be distinguished (`CL_F` vs `CL`).
- BLQ handling must be explicit.
- All generated reports must include the disclaimer.

## Commit style

```
feat(dissolution): add zero-order model fitting
fix(nca): correct lambda_z when only two terminal points exist
test(sim): add 2-cmt IV infusion AUCinf validation
docs: update NCA tutorial with BLQ example
```

Format: `<type>(<scope>): <short description>`, imperative mood, under 72 characters.

## Licensing

By contributing you agree that your changes are licensed under the MIT License.
