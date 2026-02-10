"""API routes — SSE progress streams, JSON endpoints, filesystem browser."""
from __future__ import annotations

import asyncio
import io
import json
import os
import sys

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from sse_starlette.sse import EventSourceResponse

from pyLapse.web.scheduler import capture_scheduler
from pyLapse.web.tasks import task_manager
from pyLapse.web.app import templates, shutdown_event

router = APIRouter()


@router.get("/tasks")
async def api_tasks() -> JSONResponse:
    return JSONResponse([t.to_dict() for t in task_manager.get_all_tasks()])


@router.get("/tasks/active")
async def api_tasks_active() -> JSONResponse:
    """Return only running/pending tasks for the global task tray."""
    active = [t.to_dict() for t in task_manager.get_all_tasks() if t.status in ("running", "pending")]
    return JSONResponse(active)


@router.post("/tasks/{task_id}/cancel")
async def api_task_cancel(task_id: str) -> JSONResponse:
    """Cancel a running task."""
    ok = task_manager.cancel_task(task_id)
    if ok:
        return JSONResponse({"status": "cancelled", "task_id": task_id})
    task = task_manager.get_task(task_id)
    if not task:
        return JSONResponse({"error": "Task not found"}, status_code=404)
    return JSONResponse({"error": f"Cannot cancel task in state: {task.status}"}, status_code=400)


@router.get("/tasks/{task_id}/progress")
async def api_task_progress(task_id: str) -> EventSourceResponse:
    """SSE stream: yields task progress every 500ms until done."""

    async def event_generator():
        while not shutdown_event.is_set():
            task = task_manager.get_task(task_id)
            if task is None:
                yield {"event": "error", "data": json.dumps({"error": "Task not found"})}
                return

            data = json.dumps(task.to_dict())
            yield {"event": "progress", "data": data}

            if task.status in ("completed", "failed", "cancelled"):
                return

            # Wait up to 0.5s but break early if shutdown is signalled
            try:
                await asyncio.wait_for(shutdown_event.wait(), timeout=0.5)
                return  # shutdown signalled
            except asyncio.TimeoutError:
                pass  # normal — keep polling

    return EventSourceResponse(event_generator())


@router.get("/cameras/{cam_id}/thumbnail")
async def api_camera_thumbnail(cam_id: str) -> Response:
    """Serve the most recent capture image as a JPEG thumbnail."""
    fpath = capture_scheduler.last_capture_path.get(cam_id)
    if not fpath or not os.path.isfile(fpath):
        # Return a 1x1 transparent pixel as fallback
        return Response(content=b"", status_code=204)

    try:
        from PIL import Image
        loop = asyncio.get_event_loop()

        def _make_thumb() -> bytes:
            with Image.open(fpath) as img:
                img.thumbnail((480, 270))
                buf = io.BytesIO()
                img.save(buf, "JPEG", quality=60)
            return buf.getvalue()

        data = await loop.run_in_executor(None, _make_thumb)
        return Response(content=data, media_type="image/jpeg",
                        headers={"Cache-Control": "no-cache"})
    except Exception:
        return Response(content=b"", status_code=204)


# ---------------------------------------------------------------------------
# Dashboard section endpoints (granular htmx polling)
# ---------------------------------------------------------------------------


@router.get("/dash/stats", response_class=HTMLResponse)
async def api_dash_stats(request: Request) -> HTMLResponse:
    from pyLapse.web.routes.dashboard import _ctx_stats
    ctx = _ctx_stats()
    ctx["request"] = request
    return templates.TemplateResponse("partials/dash_stats.html", ctx)


@router.get("/dash/cameras", response_class=HTMLResponse)
async def api_dash_cameras(request: Request) -> HTMLResponse:
    from pyLapse.web.routes.dashboard import _ctx_cameras
    ctx = _ctx_cameras()
    ctx["request"] = request
    return templates.TemplateResponse("partials/dash_cameras.html", ctx)


@router.get("/dash/tasks", response_class=HTMLResponse)
async def api_dash_tasks(request: Request) -> HTMLResponse:
    from pyLapse.web.routes.dashboard import _ctx_tasks
    ctx = _ctx_tasks()
    ctx["request"] = request
    return templates.TemplateResponse("partials/dash_tasks.html", ctx)


@router.get("/dash/upcoming", response_class=HTMLResponse)
async def api_dash_upcoming(request: Request) -> HTMLResponse:
    from pyLapse.web.routes.dashboard import _ctx_upcoming
    ctx = _ctx_upcoming()
    ctx["request"] = request
    return templates.TemplateResponse("partials/dash_upcoming.html", ctx)


@router.get("/dash/history", response_class=HTMLResponse)
async def api_dash_history(request: Request, limit: int = Query(10, ge=1, le=500)) -> HTMLResponse:
    from pyLapse.web.routes.dashboard import _ctx_history
    ctx = _ctx_history(limit=limit)
    ctx["request"] = request
    return templates.TemplateResponse("partials/dash_history.html", ctx)


@router.get("/dash/disk", response_class=HTMLResponse)
async def api_dash_disk(request: Request) -> HTMLResponse:
    from pyLapse.web.routes.dashboard import _ctx_disk
    ctx = _ctx_disk()
    ctx["request"] = request
    return templates.TemplateResponse("partials/dash_disk.html", ctx)


@router.get("/export-history", response_class=HTMLResponse)
async def api_export_history(request: Request, limit: int = Query(10, ge=1, le=500)) -> HTMLResponse:
    from pyLapse.web.history_store import history_store
    all_exports = history_store.get_exports()
    return templates.TemplateResponse("partials/export_history.html", {
        "request": request,
        "export_history": all_exports[:limit],
        "history_limit": limit,
        "history_total": len(all_exports),
    })


@router.get("/video-history", response_class=HTMLResponse)
async def api_video_history(request: Request, limit: int = Query(10, ge=1, le=500)) -> HTMLResponse:
    from pyLapse.web.history_store import history_store
    all_videos = history_store.get_videos()
    return templates.TemplateResponse("partials/video_history.html", {
        "request": request,
        "video_history": all_videos[:limit],
        "history_limit": limit,
        "history_total": len(all_videos),
    })


@router.get("/scheduler/status")
async def api_scheduler_status() -> JSONResponse:
    return JSONResponse({
        "running": capture_scheduler.running,
        "cameras": len(capture_scheduler.cameras),
        "jobs": capture_scheduler.get_jobs(),
        "history": capture_scheduler.capture_history[:20],
    })


# ---------------------------------------------------------------------------
# Filesystem browser
# ---------------------------------------------------------------------------


def _get_drives() -> list[dict[str, str]]:
    """Return available drive letters on Windows."""
    if sys.platform != "win32":
        return [{"name": "/", "path": "/"}]
    drives = []
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        p = f"{letter}:\\"
        if os.path.isdir(p):
            drives.append({"name": f"{letter}:", "path": p})
    return drives


@router.get("/browse-dir")
async def browse_dir(
    path: str = Query("", description="Directory to list"),
    target: str = Query("", description="ID of the input element to populate"),
) -> JSONResponse:
    """Return subdirectories of *path* for the folder picker.

    If *path* is empty, returns drive roots (Windows) or ``/`` (Unix).
    """
    if not path:
        return JSONResponse({"dirs": _get_drives(), "parent": "", "current": "", "target": target})

    path = os.path.abspath(path)
    if not os.path.isdir(path):
        return JSONResponse({"error": f"Not a directory: {path}", "dirs": [], "parent": "", "current": path, "target": target})

    dirs: list[dict[str, str]] = []
    try:
        with os.scandir(path) as it:
            for entry in it:
                if entry.is_dir(follow_symlinks=False):
                    dirs.append({"name": entry.name, "path": os.path.join(path, entry.name)})
    except PermissionError:
        pass

    dirs.sort(key=lambda d: d["name"].lower())
    parent = os.path.dirname(path)
    if parent == path:
        parent = ""  # at root

    return JSONResponse({"dirs": dirs, "parent": parent, "current": path, "target": target})
