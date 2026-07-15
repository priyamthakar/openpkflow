"""Safe temp-file handling for uploaded CSVs — cleaned up after each request."""

from __future__ import annotations

import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.config import settings


def _check_extension(filename: str | None) -> str:
    suffix = Path((filename or "").lower()).suffix
    if suffix not in settings.allowed_extensions:
        allowed = ", ".join(settings.allowed_extensions)
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type {suffix!r}. Allowed: {allowed}.",
        )
    return suffix


@contextmanager
def saved_upload(upload: UploadFile) -> Iterator[Path]:
    """Save uploaded file to a temp path, yield it, delete on exit."""
    suffix = _check_extension(upload.filename)
    data = upload.file.read(settings.max_upload_bytes + 1)
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="Upload exceeds configured size limit.")
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(data)
        tmp.flush()
        tmp_path = Path(tmp.name)
    try:
        yield tmp_path
    finally:
        tmp_path.unlink(missing_ok=True)
