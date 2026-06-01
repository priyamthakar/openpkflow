"""Simulation endpoints."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Body
from fastapi.responses import FileResponse

from app.schemas.sim import SimRequest, SimResponse
from app.services.sim_service import run_sim

router = APIRouter(prefix="/api/sim", tags=["sim"])

_MIME: dict[str, str] = {
    "html": "text/html",
    "markdown": "text/markdown",
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
_EXT: dict[str, str] = {"html": ".html", "markdown": ".md", "pdf": ".pdf", "docx": ".docx"}


@router.post("/simulate", response_model=SimResponse)
def simulate_endpoint(req: SimRequest = Body(...)) -> SimResponse:
    """Run a PK simulation and return the full concentration-time profile."""
    data = run_sim(req)
    return SimResponse(**data)


@router.post("/report")
def report(
    req: SimRequest = Body(...),
    format: Literal["html", "markdown", "pdf", "docx"] = "html",
) -> FileResponse:
    """Run simulation and stream the rendered report for download."""
    import numpy as np

    from app.services.sim_service import _build_model
    from openpkflow.sim.dosing import DoseRegimen
    from openpkflow.sim.simulate import simulate as _sim

    model = _build_model(req)
    regimen = DoseRegimen.from_repeated(
        amount=req.regimen.amount,
        route=req.route,
        tau=req.regimen.tau,
        n_doses=req.regimen.n_doses,
        t_start=req.regimen.t_start,
        t_inf=req.regimen.t_inf,
    )
    times = np.linspace(req.times.start, req.times.stop, req.times.n)
    result = _sim(model, regimen, times)

    from starlette.background import BackgroundTask

    ext = _EXT.get(format, ".html")
    tmp_out = Path(tempfile.mktemp(suffix=ext))
    result.report(tmp_out, format=format)
    return FileResponse(
        path=str(tmp_out),
        media_type=_MIME.get(format, "text/html"),
        filename=f"sim_report{ext}",
        background=BackgroundTask(tmp_out.unlink, missing_ok=True),
    )
