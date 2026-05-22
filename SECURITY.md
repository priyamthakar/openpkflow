# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 1.0.x   | Yes       |
| < 1.0   | No        |

## Reporting a vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

Email: priyamthakar1@gmail.com

Include:
- A description of the vulnerability
- Steps to reproduce
- Potential impact

You will receive a response within 7 days. If the issue is confirmed, a patch release will be prepared and you will be credited in the changelog unless you prefer otherwise.

## Scope

OpenPKFlow is a local computation library with no network calls, no authentication, and no server components. The most likely security-relevant issues are:

- Path traversal in file-loading functions (`load_dissolution_csv`, `load_nca_csv`)
- Malicious Jinja2 template injection via user-supplied report paths
- Arbitrary code execution via serialized model files (not currently used)
