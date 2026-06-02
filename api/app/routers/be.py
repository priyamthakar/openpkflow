"""BE endpoints."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Form, UploadFile
from fastapi.responses import FileResponse

from app.deps import saved_upload
from app.schemas.be import BeOptions, BeResponse
from app.services.be_service import run_be, write_be_report

router = APIRouter(prefix="/api/be", tags=["be"])

_MIME: dict[str, str] = {
    "html": "text/html",
    "markdown": "text/markdown",
}
_EXT: dict[str, str] = {"html": ".html", "markdown": ".md"}


@router.post("/analyze", response_model=BeResponse)
def analyze(
    file: UploadFile,
    options: str = Form(default="{}"),
) -> BeResponse:
    """Run bioequivalence TOST on an uploaded CSV and return results."""
    opts = BeOptions.model_validate(json.loads(options))
    with saved_upload(file) as path:
        data = run_be(path, opts)
    return BeResponse(**data)


@router.post("/report")
def report(
    file: UploadFile,
    options: str = Form(default="{}"),
    format: Literal["html", "markdown"] = Form(default="html"),
) -> FileResponse:
    """Run bioequivalence TOST and stream the rendered report for download."""
    from starlette.background import BackgroundTask

    opts = BeOptions.model_validate(json.loads(options))
    ext = _EXT.get(format, ".html")
    tmp_out = Path(tempfile.mktemp(suffix=ext))
    with saved_upload(file) as path:
        write_be_report(path, opts, tmp_out, fmt=format)
    return FileResponse(
        path=str(tmp_out),
        media_type=_MIME.get(format, "text/html"),
        filename=f"be_report{ext}",
        background=BackgroundTask(tmp_out.unlink, missing_ok=True),
    )
