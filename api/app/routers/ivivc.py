"""IVIVC endpoints."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Query
from fastapi.responses import FileResponse

from app.schemas.ivivc import IvIvcRequest, IvIvcResponse
from app.services.ivivc_service import run_ivivc, write_ivivc_report

router = APIRouter(prefix="/api/ivivc", tags=["ivivc"])

_MIME: dict[str, str] = {
    "html": "text/html",
    "markdown": "text/markdown",
}
_EXT: dict[str, str] = {"html": ".html", "markdown": ".md"}


@router.post("/analyze", response_model=IvIvcResponse)
def analyze(req: IvIvcRequest) -> IvIvcResponse:
    """Run IVIVC Level A analysis on numeric arrays and return results."""
    data = run_ivivc(req)
    return IvIvcResponse(**data)


@router.post("/report")
def report(
    req: IvIvcRequest,
    format: Literal["html", "markdown"] = Query(default="html"),
) -> FileResponse:
    """Run IVIVC Level A analysis and stream the rendered report for download."""
    from starlette.background import BackgroundTask

    ext = _EXT.get(format, ".html")
    tmp_out = Path(tempfile.mktemp(suffix=ext))
    write_ivivc_report(req, tmp_out, fmt=format)
    return FileResponse(
        path=str(tmp_out),
        media_type=_MIME.get(format, "text/html"),
        filename=f"ivivc_report{ext}",
        background=BackgroundTask(tmp_out.unlink, missing_ok=True),
    )
