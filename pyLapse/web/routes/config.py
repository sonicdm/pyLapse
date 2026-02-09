"""Config routes — app-level settings editor."""
from __future__ import annotations

import json
import logging

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse

from pyLapse.web.app import templates
from pyLapse.web.scheduler import capture_scheduler

logger = logging.getLogger(__name__)
router = APIRouter()


def _load_config_data() -> dict:
    """Read the raw config dict from disk."""
    path = capture_scheduler.config_path
    if not path:
        return {"cameras": {}}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"cameras": {}}


def _save_config_data(data: dict) -> None:
    """Write config dict to disk."""
    path = capture_scheduler.config_path
    if not path:
        raise ValueError("No config path configured")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


@router.get("/", response_class=HTMLResponse)
async def config_page(request: Request) -> HTMLResponse:
    data = _load_config_data()
    jobs = capture_scheduler.get_jobs()
    return templates.TemplateResponse("config.html", {
        "request": request,
        "config_path": capture_scheduler.config_path or "(not set)",
        "ffmpeg_path": data.get("ffmpeg_path", ""),
        "max_retries": data.get("max_retries", 2),
        "retry_delay": data.get("retry_delay", 5),
        "scheduler_running": capture_scheduler.running,
        "camera_count": len(capture_scheduler.cameras),
        "job_count": len(jobs),
        "jobs": jobs,
    })


@router.post("/save", response_class=HTMLResponse)
async def config_save(request: Request) -> HTMLResponse:
    """Save app-level settings, preserving cameras."""
    form = await request.form()
    ffmpeg_path = form.get("ffmpeg_path", "").strip()
    max_retries = form.get("max_retries", "2").strip()
    retry_delay = form.get("retry_delay", "5").strip()

    # Load existing config to preserve cameras
    data = _load_config_data()

    if ffmpeg_path:
        data["ffmpeg_path"] = ffmpeg_path
    else:
        data.pop("ffmpeg_path", None)

    data["max_retries"] = int(max_retries) if max_retries else 2
    data["retry_delay"] = int(retry_delay) if retry_delay else 5

    try:
        _save_config_data(data)
    except Exception as exc:
        return HTMLResponse(
            f'<div class="inline-result">'
            f'<button type="button" class="dismiss-btn" onclick="this.parentElement.remove()">&times;</button>'
            f'<p class="error">Save failed: {exc}</p></div>'
        )

    return HTMLResponse(
        '<div class="inline-result">'
        '<button type="button" class="dismiss-btn" onclick="this.parentElement.remove()">&times;</button>'
        '<p class="success">Settings saved.</p></div>'
    )


@router.post("/reload", response_class=HTMLResponse)
async def config_reload() -> HTMLResponse:
    """Reload the config and restart scheduler jobs."""
    try:
        capture_scheduler.load_config(capture_scheduler.config_path)
        capture_scheduler.setup_jobs()
        return HTMLResponse(
            '<div class="inline-result">'
            '<button type="button" class="dismiss-btn" onclick="this.parentElement.remove()">&times;</button>'
            '<p class="success">Config reloaded, scheduler updated.</p></div>'
        )
    except Exception as exc:
        logger.error("Config reload failed: %s", exc)
        return HTMLResponse(
            f'<div class="inline-result">'
            f'<button type="button" class="dismiss-btn" onclick="this.parentElement.remove()">&times;</button>'
            f'<p class="error">Reload failed: {exc}</p></div>'
        )


@router.post("/add-schedule", response_class=HTMLResponse)
async def config_add_schedule(request: Request, cam_id: str = Form(...)) -> HTMLResponse:
    """Return a new empty schedule row partial (used by camera edit on Cameras page)."""
    import uuid
    idx = uuid.uuid4().hex[:6]
    return templates.TemplateResponse("partials/schedule_row.html", {
        "request": request,
        "cam_id": cam_id,
        "idx": idx,
        "sched": {"id": "", "hour": "*", "minute": "*", "second": "", "enabled": True},
    })
