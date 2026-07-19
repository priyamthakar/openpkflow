"""Bayesian endpoints."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Literal

from fastapi import APIRouter
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from app.schemas.bayes import MapPkRequest, MapPkResponse
from app.services.bayes_service import run_map_pk, write_map_pk_report

router = APIRouter(prefix="/api/bayes", tags=["bayes"])

_MIME: dict[str, str] = {"html": "text/html", "markdown": "text/markdown"}
_EXT: dict[str, str] = {"html": ".html", "markdown": ".md"}


@router.post("/map/analyze", response_model=MapPkResponse)
def analyze_map(request: MapPkRequest) -> MapPkResponse:
    """Compute MAP individual PK estimates from sparse concentration data."""
    return MapPkResponse(**run_map_pk(request))


@router.post("/map/report")
def report_map(
    request: MapPkRequest,
    format: Literal["html", "markdown"] = "html",
) -> FileResponse:
    """Compute MAP estimates and stream a screening report."""
    ext = _EXT.get(format, ".html")
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp_out = Path(tmp.name)
    try:
        write_map_pk_report(request, tmp_out, fmt=format)
    except Exception:
        tmp_out.unlink(missing_ok=True)
        raise
    return FileResponse(
        path=str(tmp_out),
        media_type=_MIME.get(format, "text/html"),
        filename=f"map_pk_report{ext}",
        background=BackgroundTask(tmp_out.unlink, missing_ok=True),
    )
