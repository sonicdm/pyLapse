"""Dashboard route — overview of scheduler, cameras, and tasks."""
from __future__ import annotations

import os
import shutil
import time
from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from pyLapse.web.app import templates
from pyLapse.web.history_store import history_store
from pyLapse.web.scheduler import capture_scheduler
from pyLapse.web.tasks import task_manager

router = APIRouter()


def _disk_usage(path: str) -> dict[str, str | float] | None:
    """Return disk usage for *path* if it exists."""
    if not os.path.isdir(path):
        return None
    usage = shutil.disk_usage(path)
    gb = 1 << 30
    return {
        "path": path,
        "total": f"{usage.total / gb:.1f} GB",
        "used": f"{usage.used / gb:.1f} GB",
        "free": f"{usage.free / gb:.1f} GB",
        "percent": round(usage.used / usage.total * 100, 1),
    }


def _format_next_run(iso: str | None) -> str:
    """Convert an ISO timestamp to a human-friendly 'in X min' string."""
    if not iso:
        return "\u2014"
    try:
        dt = datetime.fromisoformat(iso)
        delta = dt - datetime.now(dt.tzinfo)
        secs = int(delta.total_seconds())
        if secs < 0:
            return "overdue"
        if secs < 60:
            return f"in {secs}s"
        if secs < 3600:
            return f"in {secs // 60}m"
        return f"in {secs // 3600}h {(secs % 3600) // 60}m"
    except (ValueError, TypeError):
        return str(iso)


def _format_capture_time(iso: str) -> str:
    """Format a capture timestamp for display."""
    try:
        dt = datetime.fromisoformat(iso)
        return dt.strftime("%I:%M:%S %p")
    except (ValueError, TypeError):
        return str(iso)


# ---------------------------------------------------------------------------
# Context builders for each dashboard section
# ---------------------------------------------------------------------------


def _ctx_stats() -> dict:
    exports = history_store.get_exports()
    videos = history_store.get_videos()
    return {
        "scheduler_running": capture_scheduler.running,
        "camera_count": len(capture_scheduler.cameras),
        "job_count": len(capture_scheduler.get_jobs()),
        "export_count": len(exports),
        "video_count": len(videos),
    }


def _ctx_cameras() -> dict:
    camera_status: dict[str, dict] = {}
    for cam_id, cfg in capture_scheduler._camera_config.items():
        last_capture = None
        for h in capture_scheduler.capture_history:
            if h.get("camera_id") == cam_id:
                last_capture = h
                if "time_short" not in last_capture:
                    last_capture["time_short"] = _format_capture_time(last_capture.get("time", ""))
                break

        has_thumbnail = cam_id in capture_scheduler.last_capture_path
        camera_status[cam_id] = {
            "name": cfg.get("name", cam_id),
            "enabled": cfg.get("enabled", True),
            "url": cfg.get("url", ""),
            "output_dir": cfg.get("output_dir", ""),
            "last_capture": last_capture,
            "schedule_count": len(cfg.get("schedules", [])),
            "has_thumbnail": has_thumbnail,
        }

    return {
        "camera_status": camera_status,
        "now_ts": int(time.time()),
    }


def _ctx_tasks() -> dict:
    return {"tasks": [t.to_dict() for t in task_manager.get_all_tasks()]}


def _ctx_upcoming() -> dict:
    jobs = capture_scheduler.get_jobs()
    for job in jobs:
        job["next_run_human"] = _format_next_run(job.get("next_run"))
    return {"jobs": jobs}


def _ctx_history(limit: int = 10) -> dict:
    history = list(capture_scheduler.capture_history[:limit])
    for h in history:
        h["time_short"] = _format_capture_time(h.get("time", ""))
    total = len(capture_scheduler.capture_history)
    return {"history": history, "history_limit": limit, "history_total": total}


def _ctx_disk() -> dict:
    disk_info: list[dict] = []
    seen: set[str] = set()
    for cam_id, cfg in capture_scheduler._camera_config.items():
        d = cfg.get("output_dir", "")
        if d and d not in seen:
            seen.add(d)
            info = _disk_usage(d)
            if info:
                info["camera"] = cfg.get("name", cam_id)
                disk_info.append(info)
    return {"disk_info": disk_info}


def _build_dashboard_context() -> dict:
    """Build the full context for initial page render."""
    ctx: dict = {}
    ctx.update(_ctx_stats())
    ctx.update(_ctx_cameras())
    ctx.update(_ctx_tasks())
    ctx.update(_ctx_upcoming())
    ctx.update(_ctx_history())
    ctx.update(_ctx_disk())
    return ctx


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request) -> HTMLResponse:
    ctx = _build_dashboard_context()
    ctx["request"] = request
    return templates.TemplateResponse("dashboard.html", ctx)
