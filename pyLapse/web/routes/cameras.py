"""Camera routes — list, preview, grab, edit, add, remove."""
from __future__ import annotations

import asyncio
import base64
import io
import json
import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse

from pyLapse.web.app import templates
from pyLapse.web.collections_store import collections_store
from pyLapse.web.scheduler import capture_scheduler

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_all_timezones() -> list[str]:
    """Return a sorted list of all IANA timezone names."""
    try:
        from zoneinfo import available_timezones
    except ImportError:
        try:
            from backports.zoneinfo import available_timezones  # type: ignore[no-redef]
        except ImportError:
            return []
    return sorted(available_timezones())


def _load_config() -> dict:
    """Read the raw config from disk."""
    path = capture_scheduler.config_path
    if not path:
        return {"cameras": {}}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"cameras": {}}


def _save_config(data: dict) -> None:
    """Write config to disk."""
    path = capture_scheduler.config_path
    if not path:
        raise ValueError("No config path configured")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _reload_scheduler() -> None:
    """Reload config and restart scheduler jobs."""
    capture_scheduler.load_config(capture_scheduler.config_path)
    capture_scheduler.setup_jobs()


def _ensure_collection(cam_id: str, cam: dict) -> None:
    """Create or update a collection for a camera's output directory."""
    output_dir = cam.get("output_dir", "")
    if not output_dir:
        return
    # Check if a collection already exists for this output dir
    for coll_id, coll in collections_store.get_all().items():
        if coll.get("path") == output_dir:
            return  # Already exists
    coll_data: dict = {
        "name": cam.get("name", cam_id),
        "path": output_dir,
        "date_source": "filename",
    }
    ext = cam.get("ext", "jpg")
    if ext:
        coll_data["ext"] = ext
    tz = cam.get("timezone", "")
    if tz:
        coll_data["timezone"] = tz
    collections_store.save(cam_id, coll_data)


def _render_camera_grid(request: Request) -> HTMLResponse:
    """Return all camera view cards for the grid."""
    html_parts = []
    for cam_id, cam in capture_scheduler._camera_config.items():
        html_parts.append(
            templates.get_template("partials/camera_view.html").render(
                request=request, cam_id=cam_id, cam=cam,
            )
        )
    return HTMLResponse("".join(html_parts))


@router.get("/", response_class=HTMLResponse)
async def cameras_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("cameras.html", {
        "request": request,
        "cameras": capture_scheduler.cameras,
        "camera_config": capture_scheduler._camera_config,
    })


def _fetch_preview(url: str) -> bytes:
    """Blocking fetch — run in a thread pool."""
    from pyLapse.img_seq.image import ImageIO
    img = ImageIO.fetch_image_from_url(url, timeout=8)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=70)
    return buf.getvalue()


@router.post("/{cam_id}/preview", response_class=HTMLResponse)
async def camera_preview(cam_id: str) -> HTMLResponse:
    """Fetch a live image from the camera and return an <img> tag."""
    camera = capture_scheduler.cameras.get(cam_id)
    cfg = capture_scheduler._camera_config.get(cam_id, {})
    if not camera:
        url = cfg.get("url", "")
        return HTMLResponse(
            f'<div class="inline-result">'
            f'<button type="button" class="dismiss-btn" onclick="this.parentElement.remove()">&times;</button>'
            f'<p class="error">Could not connect to camera. Check that the URL is valid: <code>{url}</code></p>'
            f'</div>'
        )

    try:
        loop = asyncio.get_event_loop()
        jpeg_bytes = await loop.run_in_executor(None, _fetch_preview, camera.imageurl)
        b64 = base64.b64encode(jpeg_bytes).decode()
        return HTMLResponse(
            f'<div class="inline-result">'
            f'<button type="button" class="dismiss-btn" onclick="this.parentElement.remove()">&times;</button>'
            f'<img src="data:image/jpeg;base64,{b64}" alt="{camera.name}" '
            f'style="max-width:100%; border-radius:4px;">'
            f'</div>'
        )
    except Exception as exc:
        logger.error("Preview failed for %s: %s", cam_id, exc)
        return HTMLResponse(
            f'<div class="inline-result">'
            f'<button type="button" class="dismiss-btn" onclick="this.parentElement.remove()">&times;</button>'
            f'<p class="error">Preview failed: {exc}</p>'
            f'</div>'
        )


def _build_save_kwargs(cfg: dict) -> dict:
    """Build save_image kwargs from camera config."""
    kwargs: dict[str, Any] = {}
    if cfg.get("prefix"):
        kwargs["prefix"] = cfg["prefix"]
    if cfg.get("filename_format"):
        kwargs["filenameformat"] = cfg["filename_format"]
    if cfg.get("ext"):
        kwargs["ext"] = cfg["ext"]
    if cfg.get("quality") is not None:
        kwargs["quality"] = int(cfg["quality"])
    if cfg.get("resize"):
        kwargs["resize"] = True
        w = int(cfg.get("resize_width", 1920))
        h = int(cfg.get("resize_height", 1080))
        kwargs["resolution"] = (w, h)
    return kwargs


def _grab_image(camera, output_dir: str, save_kwargs: dict) -> str:
    """Blocking grab — run in a thread pool."""
    camera.save_image(output_dir, **save_kwargs)
    return f"Captured {camera.name} at {datetime.now():%H:%M:%S}"


@router.post("/{cam_id}/grab", response_class=HTMLResponse)
async def camera_grab(cam_id: str) -> HTMLResponse:
    """Trigger an immediate capture for a camera."""
    camera = capture_scheduler.cameras.get(cam_id)
    cfg = capture_scheduler._camera_config.get(cam_id, {})
    if not camera:
        url = cfg.get("url", "")
        return HTMLResponse(
            f'<div class="inline-result">'
            f'<button type="button" class="dismiss-btn" onclick="this.parentElement.remove()">&times;</button>'
            f'<p class="error">Could not connect to camera. Check that the URL is valid: <code>{url}</code></p>'
            f'</div>'
        )

    output_dir = cfg.get("output_dir", "")
    save_kwargs = _build_save_kwargs(cfg)

    try:
        loop = asyncio.get_event_loop()
        msg = await loop.run_in_executor(None, _grab_image, camera, output_dir, save_kwargs)
        return HTMLResponse(
            f'<div class="inline-result">'
            f'<button type="button" class="dismiss-btn" onclick="this.parentElement.remove()">&times;</button>'
            f'<p class="success">{msg}</p>'
            f'</div>'
        )
    except Exception as exc:
        logger.error("Grab failed for %s: %s", cam_id, exc)
        return HTMLResponse(
            f'<div class="inline-result">'
            f'<button type="button" class="dismiss-btn" onclick="this.parentElement.remove()">&times;</button>'
            f'<p class="error">Grab failed: {exc}</p>'
            f'</div>'
        )


# ------------------------------------------------------------------
# Camera CRUD
# ------------------------------------------------------------------


@router.get("/add-form", response_class=HTMLResponse)
async def camera_add_form(request: Request) -> HTMLResponse:
    """Return blank camera form for the add modal."""
    return templates.TemplateResponse("partials/camera_edit.html", {
        "request": request,
        "cam_id": "",
        "cam": {"name": "", "url": "", "output_dir": "", "prefix": "", "enabled": True},
        "is_new": True,
        "all_timezones": _get_all_timezones(),
    })


@router.get("/{cam_id}/edit", response_class=HTMLResponse)
async def camera_edit(request: Request, cam_id: str) -> HTMLResponse:
    """Return the edit form for a camera (loaded into modal)."""
    cam = capture_scheduler._camera_config.get(cam_id, {})
    return templates.TemplateResponse("partials/camera_edit.html", {
        "request": request,
        "cam_id": cam_id,
        "cam": cam,
        "is_new": False,
        "all_timezones": _get_all_timezones(),
    })


def _parse_schedules(form) -> list[dict]:
    """Extract schedule list from form data arrays."""
    types = form.getlist("sched_type")
    hours = form.getlist("sched_hour")
    minutes = form.getlist("sched_minute")
    seconds = form.getlist("sched_second")
    start_dates = form.getlist("sched_start_date")
    int_amounts = form.getlist("sched_interval_amount")
    int_units = form.getlist("sched_interval_unit")
    enabled_list = form.getlist("sched_enabled")

    schedules = []
    count = max(len(hours), len(types), 1)
    for i in range(count):
        sched_type = types[i] if i < len(types) else "cron"
        enabled = (enabled_list[i] == "true") if i < len(enabled_list) else True
        sched: dict[str, Any] = {
            "id": f"sched_{i}",
            "type": sched_type,
            "enabled": enabled,
            "hour": hours[i] if i < len(hours) else "*",
            "minute": minutes[i] if i < len(minutes) else "*",
            "second": seconds[i] if i < len(seconds) else "0",
        }
        if sched_type == "interval":
            sched["interval_amount"] = int(int_amounts[i]) if i < len(int_amounts) and int_amounts[i] else 1
            sched["interval_unit"] = int_units[i] if i < len(int_units) else "minutes"
            sched["start_date"] = start_dates[i] if i < len(start_dates) else ""
        schedules.append(sched)
    return schedules


def _parse_camera_fields(form) -> dict[str, Any]:
    """Extract common camera fields from form data."""
    cam: dict[str, Any] = {
        "name": form.get("name", ""),
        "description": form.get("description", ""),
        "url": form.get("url", ""),
        "output_dir": form.get("output_dir", ""),
        "prefix": form.get("prefix", ""),
        "enabled": form.get("enabled", "") == "true",
        "schedules": _parse_schedules(form),
    }
    # Filename & image options
    filename_format = (form.get("filename_format") or "").strip()
    if filename_format:
        cam["filename_format"] = filename_format
    ext = form.get("ext", "jpg")
    if ext and ext != "jpg":
        cam["ext"] = ext
    quality = form.get("quality")
    if quality is not None:
        cam["quality"] = int(quality)
    if form.get("resize") == "true":
        cam["resize"] = True
        cam["resize_width"] = int(form.get("resize_width") or 1920)
        cam["resize_height"] = int(form.get("resize_height") or 1080)
    # Timezone — direct text input with datalist search
    tz = (form.get("timezone") or "").strip()
    if tz:
        cam["timezone"] = tz
    return cam


@router.post("/add", response_class=HTMLResponse)
async def camera_add(request: Request) -> HTMLResponse:
    """Add a new camera."""
    form = await request.form()
    cam_id = (form.get("cam_id") or "").strip().replace(" ", "_")

    config = _load_config()
    cameras = config.setdefault("cameras", {})

    if cam_id in cameras:
        return HTMLResponse(f'<p class="error">Camera ID "{cam_id}" already exists.</p>')

    cam_data = _parse_camera_fields(form)
    cameras[cam_id] = cam_data

    _save_config(config)
    _reload_scheduler()

    if form.get("create_collection") == "true":
        _ensure_collection(cam_id, cam_data)

    return _render_camera_grid(request)


@router.post("/{cam_id}/save", response_class=HTMLResponse)
async def camera_save(request: Request, cam_id: str) -> HTMLResponse:
    """Save changes to an existing camera."""
    form = await request.form()

    config = _load_config()
    cameras = config.setdefault("cameras", {})

    cam_data = _parse_camera_fields(form)
    cameras[cam_id] = cam_data

    _save_config(config)
    _reload_scheduler()

    if form.get("create_collection") == "true":
        _ensure_collection(cam_id, cam_data)

    return _render_camera_grid(request)


@router.post("/{cam_id}/toggle", response_class=HTMLResponse)
async def camera_toggle(request: Request, cam_id: str) -> HTMLResponse:
    """Toggle a camera's enabled state."""
    config = _load_config()
    cameras = config.get("cameras", {})
    cam = cameras.get(cam_id)
    if not cam:
        return HTMLResponse(f'<p class="error">Camera "{cam_id}" not found</p>')

    cam["enabled"] = not cam.get("enabled", True)
    _save_config(config)
    _reload_scheduler()

    # Return just the updated card
    return HTMLResponse(
        templates.get_template("partials/camera_view.html").render(
            request=request, cam_id=cam_id, cam=cam,
        )
    )


@router.post("/{cam_id}/schedule/{sched_idx}/toggle", response_class=HTMLResponse)
async def schedule_toggle(request: Request, cam_id: str, sched_idx: int) -> HTMLResponse:
    """Toggle a schedule's enabled state within a camera."""
    config = _load_config()
    cameras = config.get("cameras", {})
    cam = cameras.get(cam_id)
    if not cam:
        return HTMLResponse(f'<p class="error">Camera "{cam_id}" not found</p>')

    schedules = cam.get("schedules", [])
    if sched_idx < 0 or sched_idx >= len(schedules):
        return HTMLResponse(f'<p class="error">Schedule index out of range</p>')

    schedules[sched_idx]["enabled"] = not schedules[sched_idx].get("enabled", True)
    _save_config(config)
    _reload_scheduler()

    # Return the updated camera card
    return HTMLResponse(
        templates.get_template("partials/camera_view.html").render(
            request=request, cam_id=cam_id, cam=cam,
        )
    )


@router.post("/{cam_id}/create-collection", response_class=HTMLResponse)
async def camera_create_collection(request: Request, cam_id: str) -> HTMLResponse:
    """Create a collection for a camera's output directory."""
    cfg = capture_scheduler._camera_config.get(cam_id, {})
    if not cfg:
        return HTMLResponse(f'<p class="error">Camera "{cam_id}" not found</p>')
    output_dir = cfg.get("output_dir", "")
    if not output_dir:
        return HTMLResponse(f'<p class="error">Camera has no output directory set</p>')
    _ensure_collection(cam_id, cfg)
    return HTMLResponse(
        templates.get_template("partials/camera_view.html").render(
            request=request, cam_id=cam_id, cam=cfg,
        )
    )


@router.post("/{cam_id}/remove", response_class=HTMLResponse)
async def camera_remove(request: Request, cam_id: str) -> HTMLResponse:
    """Remove a camera from the config."""
    config = _load_config()
    cameras = config.get("cameras", {})
    cameras.pop(cam_id, None)
    config["cameras"] = cameras

    _save_config(config)
    _reload_scheduler()
    return _render_camera_grid(request)
