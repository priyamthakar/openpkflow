"""Runtime configuration (environment-variable overridable)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _origins() -> list[str]:
    raw = os.environ.get("OPENPKFLOW_ALLOWED_ORIGINS", "")
    if raw:
        return [o.strip() for o in raw.split(",") if o.strip()]
    return ["http://localhost:5173", "http://127.0.0.1:5173"]


@dataclass(frozen=True)
class Settings:
    allowed_origins: list[str] = field(default_factory=_origins)
    max_upload_bytes: int = int(os.environ.get("OPENPKFLOW_MAX_UPLOAD_BYTES", 10 * 1024 * 1024))
    allowed_extensions: tuple[str, ...] = (".csv", ".xlsx", ".xls")


settings = Settings()
