"""Collection routes — browse, save, manage, and export from collections."""
from __future__ import annotations

import asyncio
import os
from typing import Any, Callable

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse

from apscheduler.triggers.cron import CronTrigger

from pyLapse.web.app import templates
from pyLapse.web.collections_store import collections_store
from pyLapse.web.history_store import history_store
from pyLapse.web.tasks import task_manager
from pyLapse.img_seq.image import imageset_load, ImageIO, prepare_output_dir
from pyLapse.img_seq.lapsetime import cron_image_filter
from pyLapse.img_seq.fonts import list_available_fonts
from pyLapse.img_seq.video import render_sequence_to_video

router = APIRouter()


def _load_collection_stats(
    path: str,
    date_source: str = "filename",
    progress_callback: Callable[[int, int, str], None] | None = None,
) -> dict[str, Any]:
    """Load an image set and compute stats."""
    imageset = imageset_load(path, date_source=date_source, progress_callback=progress_callback)
    day_counts = {
        day: len(files) for day, files in imageset.imageindex.items()
    }
    sorted_days = sorted(day_counts.keys())

    return {
        "total": imageset.imagecount,
        "days": len(sorted_days),
        "first_day": sorted_days[0] if sorted_days else None,
        "last_day": sorted_days[-1] if sorted_days else None,
        "day_counts": dict(sorted(day_counts.items())),
        "avg_per_day": round(imageset.imagecount / max(len(sorted_days), 1), 1),
    }


def _get_all_timezones() -> list[dict[str, str]]:
    """Return sorted list of IANA timezone dicts with friendly labels.

    Each entry is ``{"value": "Pacific/Auckland", "label": "Pacific/Auckland (New Zealand)"}``.
    Common aliases get human-readable labels so that searching "New Zealand"
    or "Eastern" finds the right entry in a ``<datalist>``.
    """
    from zoneinfo import available_timezones

    # Map IANA names → friendly labels for common zones
    _LABELS: dict[str, str] = {
        "Pacific/Auckland": "New Zealand",
        "Pacific/Chatham": "New Zealand — Chatham Islands",
        "NZ": "New Zealand (legacy alias)",
        "NZ-CHAT": "New Zealand Chatham (legacy alias)",
        "US/Eastern": "US Eastern",
        "US/Central": "US Central",
        "US/Mountain": "US Mountain",
        "US/Pacific": "US Pacific",
        "US/Alaska": "US Alaska",
        "US/Hawaii": "US Hawaii",
        "America/New_York": "US Eastern — New York",
        "America/Chicago": "US Central — Chicago",
        "America/Denver": "US Mountain — Denver",
        "America/Los_Angeles": "US Pacific — Los Angeles",
        "America/Anchorage": "US Alaska — Anchorage",
        "Pacific/Honolulu": "US Hawaii — Honolulu",
        "Europe/London": "United Kingdom",
        "Europe/Paris": "France / Central Europe",
        "Europe/Berlin": "Germany / Central Europe",
        "Europe/Moscow": "Russia — Moscow",
        "Asia/Tokyo": "Japan",
        "Asia/Shanghai": "China",
        "Asia/Kolkata": "India",
        "Asia/Dubai": "UAE / Gulf",
        "Australia/Sydney": "Australia — Sydney (Eastern)",
        "Australia/Melbourne": "Australia — Melbourne (Eastern)",
        "Australia/Perth": "Australia — Perth (Western)",
        "Australia/Adelaide": "Australia — Adelaide (Central)",
        "Australia/Brisbane": "Australia — Brisbane (Queensland)",
    }

    tzs = sorted(available_timezones())
    result = []
    for tz in tzs:
        label = _LABELS.get(tz)
        if label:
            result.append({"value": tz, "label": f"{tz} ({label})"})
        else:
            result.append({"value": tz, "label": tz})
    return result


@router.get("/", response_class=HTMLResponse)
async def collections_page(request: Request) -> HTMLResponse:
    saved = collections_store.get_all()
    fonts = list_available_fonts()
    return templates.TemplateResponse("collections.html", {
        "request": request,
        "saved_collections": saved,
        "fonts": fonts,
        "all_timezones": _get_all_timezones(),
    })


@router.post("/browse", response_class=HTMLResponse)
async def collections_browse(
    request: Request,
    path: str = Form(...),
    name: str = Form(""),
    date_source: str = Form("filename"),
) -> HTMLResponse:
    """Start loading a collection as a background task with progress."""
    task = task_manager.create_task(
        f"Loading {name or os.path.basename(path)}",
        _load_collection_stats,
        path=path,
        date_source=date_source,
    )
    task.meta = {"path": path, "name": name, "date_source": date_source}
    return templates.TemplateResponse("partials/task_progress.html", {
        "request": request,
        "task": task.to_dict(),
        "result_url": f"/collections/task-result/{task.id}",
    })


@router.post("/save", response_class=HTMLResponse)
async def collections_save(
    request: Request,
    coll_id: str = Form(""),
    name: str = Form(...),
    path: str = Form(...),
    date_source: str = Form("filename"),
    export_dir: str = Form(""),
    ext: str = Form("jpg"),
    timezone: str = Form(""),
) -> HTMLResponse:
    """Save or update a collection."""
    # Preserve existing exports when updating collection metadata
    existing = collections_store.get(coll_id) if coll_id else None
    data: dict[str, Any] = {
        "name": name,
        "path": path,
        "date_source": date_source,
        "export_dir": export_dir,
        "ext": ext,
    }
    tz = timezone.strip()
    if tz:
        data["timezone"] = tz
    if existing and "exports" in existing:
        data["exports"] = existing["exports"]
    coll_id = collections_store.save(coll_id or None, data)
    # Return updated saved collections list
    saved = collections_store.get_all()
    return templates.TemplateResponse("partials/saved_collections.html", {
        "request": request,
        "saved_collections": saved,
        "message": f'Collection "{name}" saved.',
    })


@router.post("/delete", response_class=HTMLResponse)
async def collections_delete(request: Request, coll_id: str = Form(...)) -> HTMLResponse:
    """Delete a saved collection."""
    collections_store.delete(coll_id)
    saved = collections_store.get_all()
    return templates.TemplateResponse("partials/saved_collections.html", {
        "request": request,
        "saved_collections": saved,
        "message": "Collection deleted.",
    })


@router.post("/load-saved", response_class=HTMLResponse)
async def collections_load_saved(
    request: Request,
    coll_id: str = Form(...),
) -> HTMLResponse:
    """Load a saved collection as a background task with progress."""
    coll = collections_store.get(coll_id)
    if not coll:
        return HTMLResponse('<p class="error">Collection not found.</p>')

    task = task_manager.create_task(
        f"Loading {coll.get('name', coll_id)}",
        _load_collection_stats,
        path=coll["path"],
        date_source=coll.get("date_source", "filename"),
    )
    task.meta = {"coll_id": coll_id}
    return templates.TemplateResponse("partials/task_progress.html", {
        "request": request,
        "task": task.to_dict(),
        "result_url": f"/collections/task-result/{task.id}",
    })


@router.get("/task-result/{task_id}", response_class=HTMLResponse)
async def collections_task_result(request: Request, task_id: str) -> HTMLResponse:
    """Return the collection HTML after a browse/load task completes."""
    task = task_manager.get_task(task_id)
    if not task:
        return HTMLResponse('<p class="error">Task not found.</p>')
    if task.status != "completed":
        return HTMLResponse(f'<p class="error">Task not ready: {task.status}</p>')

    stats = task.result
    if not isinstance(stats, dict):
        return HTMLResponse('<p class="error">No result data.</p>')

    meta = task.meta

    # If this was a saved collection load, render the detail view
    coll_id = meta.get("coll_id")
    if coll_id:
        coll = collections_store.get(coll_id)
        if not coll:
            return HTMLResponse('<p class="error">Collection not found.</p>')
        fonts = list_available_fonts()
        return templates.TemplateResponse("partials/collection_detail.html", {
            "request": request,
            "coll_id": coll_id,
            "coll": coll,
            "stats": stats,
            "fonts": fonts,
        })

    # Otherwise it was a browse — render the table view
    return templates.TemplateResponse("partials/collection_table.html", {
        "request": request,
        "path": meta.get("path", ""),
        "name": meta.get("name", ""),
        "date_source": meta.get("date_source", "filename"),
        "stats": stats,
    })


def _get_ffmpeg_path() -> str | None:
    """Read ffmpeg_path from capture_config.json if set."""
    from pyLapse.web.scheduler import capture_scheduler
    import json as _json
    path = capture_scheduler.config_path
    if not path or not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = _json.load(f)
        ffmpeg = data.get("ffmpeg_path", "")
        return ffmpeg if ffmpeg else None
    except Exception:
        return None


def _run_collection_export(
    input_dir: str,
    output_dir: str,
    date_source: str,
    hour: str,
    minute: str,
    second: str,
    resize: bool,
    keep_aspect: bool,
    resolution_w: int,
    resolution_h: int,
    quality: int,
    optimize: bool,
    drawtimestamp: bool,
    timestampformat: str,
    timestampfont: str | None,
    timestampfontsize: int,
    timestampcolor: tuple[int, int, int],
    timestamppos: tuple[int, int],
    prefix: str,
    zeropadding: int,
    coll_name: str = "",
    create_video: bool = False,
    video_fps: int = 24,
    video_pattern: str = "*.jpg",
    video_codec: str = "libx264",
    video_output: str = "",
    timestamp_source_tz: str = "",
    timestamp_display_tz: str = "",
    progress_callback: Callable[[int, int, str], None] | None = None,
) -> dict[str, Any]:
    """Background export from a collection."""
    if progress_callback:
        progress_callback(0, 0, "Loading image set...")
    imageset = imageset_load(input_dir, date_source=date_source, progress_callback=progress_callback)

    if progress_callback:
        progress_callback(0, 0, "Filtering images by schedule...")
    trigger = CronTrigger(hour=hour or "*", minute=minute or "*", second=second or "0")
    matched = cron_image_filter(imageset.imageindex, trigger, fuzzy=5)

    outindex = imageset.filter_index(matched)
    image_count = sum(len(v) for v in outindex.values())

    # Derive output ext from video_pattern (e.g. "*.jpg" -> "jpg")
    out_ext = video_pattern.lstrip("*.") if video_pattern else "jpg"

    if image_count > 0:
        if progress_callback:
            progress_callback(0, image_count, f"Writing {image_count} images...")
        prepare_output_dir(output_dir, ext=out_ext)

        io = ImageIO()
        io.write_imageset(
            outindex,
            output_dir,
            resize=resize,
            quality=quality,
            optimize=optimize,
            resolution=(resolution_w, resolution_h),
            keep_aspect=keep_aspect,
            drawtimestamp=drawtimestamp,
            timestampformat=timestampformat or "%Y-%m-%d %I:%M:%S %p",
            timestampfont=timestampfont or None,
            timestampfontsize=timestampfontsize,
            timestampcolor=timestampcolor,
            timestamppos=timestamppos,
            prefix=prefix,
            zeropadding=zeropadding,
            ext=out_ext,
            timestamp_source_tz=timestamp_source_tz,
            timestamp_display_tz=timestamp_display_tz,
            progress_callback=progress_callback,
        )
    else:
        if progress_callback:
            progress_callback(0, 0, "No images matched the time filter.")

    # Record to history
    record = history_store.add_export({
        "name": coll_name or os.path.basename(input_dir),
        "input_dir": input_dir,
        "output_dir": output_dir,
        "date_source": date_source,
        "hour": hour,
        "minute": minute,
        "image_count": image_count,
    })
    result: dict[str, Any] = {"image_count": image_count, "output_dir": output_dir, "export_id": record}

    # Chain video render if enabled (only if images were written)
    if create_video and image_count > 0:
        if progress_callback:
            progress_callback(0, 0, "Starting video render...")
        vid_output = video_output or (output_dir.rstrip("/\\") + ".mp4")
        ffmpeg = _get_ffmpeg_path()
        try:
            result_path = render_sequence_to_video(
                input_dir=output_dir,
                output_path=vid_output,
                fps=video_fps,
                pattern=video_pattern,
                codec=video_codec,
                ffmpeg_path=ffmpeg,
                progress=False,
                progress_callback=progress_callback,
            )
            file_size = 0
            try:
                file_size = os.path.getsize(result_path)
            except OSError:
                pass
            video_id = history_store.add_video({
                "name": coll_name or os.path.splitext(os.path.basename(vid_output))[0],
                "input_dir": output_dir,
                "output_path": str(result_path),
                "fps": video_fps,
                "codec": video_codec,
                "file_size": file_size,
            })
            result["video_created"] = True
            result["video_path"] = str(result_path)
            result["video_id"] = video_id
            result["video_size"] = file_size
        except Exception as exc:
            result["video_created"] = False
            result["video_error"] = str(exc)

    return result


@router.post("/export", response_class=HTMLResponse)
async def collections_export(
    request: Request,
    input_dir: str = Form(...),
    output_dir: str = Form(...),
    date_source: str = Form("filename"),
    coll_name: str = Form(""),
    hour: str = Form("*"),
    minute: str = Form("*"),
    second: str = Form("0"),
    resize: bool = Form(False),
    keep_aspect: bool = Form(True),
    resolution_w: int = Form(1920),
    resolution_h: int = Form(1080),
    quality: int = Form(50),
    optimize: bool = Form(False),
    drawtimestamp: bool = Form(False),
    timestampformat: str = Form("%Y-%m-%d %I:%M:%S %p"),
    timestampfont: str = Form(""),
    timestampfontsize: int = Form(36),
    ts_r: int = Form(255),
    ts_g: int = Form(255),
    ts_b: int = Form(255),
    ts_x: int = Form(0),
    ts_y: int = Form(0),
    prefix: str = Form(""),
    zeropadding: int = Form(5),
    create_video: bool = Form(False),
    video_fps: int = Form(24),
    video_pattern: str = Form("*.jpg"),
    video_codec: str = Form("libx264"),
    video_output: str = Form(""),
) -> HTMLResponse:
    """Start an export from a collection as a background task."""
    name = coll_name or os.path.basename(input_dir)
    label = f"Export {name}" + (" + Video" if create_video else "")

    # Look up source timezone from collection (what TZ the file timestamps are in)
    timestamp_source_tz = ""
    for _cid, coll in collections_store.get_all().items():
        if coll.get("path") == input_dir:
            timestamp_source_tz = coll.get("timezone", "")
            break

    task = task_manager.create_task(
        label,
        _run_collection_export,
        input_dir=input_dir,
        output_dir=output_dir,
        date_source=date_source,
        hour=hour,
        minute=minute,
        second=second,
        resize=resize,
        keep_aspect=keep_aspect,
        resolution_w=resolution_w,
        resolution_h=resolution_h,
        quality=quality,
        optimize=optimize,
        drawtimestamp=drawtimestamp,
        timestampformat=timestampformat,
        timestampfont=timestampfont or None,
        timestampfontsize=timestampfontsize,
        timestampcolor=(ts_r, ts_g, ts_b),
        timestamppos=(ts_x, ts_y),
        prefix=prefix,
        zeropadding=zeropadding,
        coll_name=coll_name,
        create_video=create_video,
        video_fps=video_fps,
        video_pattern=video_pattern,
        video_codec=video_codec,
        video_output=video_output,
        timestamp_source_tz=timestamp_source_tz,
    )
    return templates.TemplateResponse("partials/task_progress.html", {
        "request": request,
        "task": task.to_dict(),
        "result_url": f"/collections/export-result/{task.id}",
    })


@router.get("/export-result/{task_id}", response_class=HTMLResponse)
async def collections_export_result(request: Request, task_id: str) -> HTMLResponse:
    """Return the export result HTML after an export task completes."""
    task = task_manager.get_task(task_id)
    if not task:
        return HTMLResponse('<p class="error">Task not found.</p>')
    if task.status != "completed":
        return HTMLResponse(f'<p class="error">Task not ready: {task.status}</p>')

    result = task.result
    if not isinstance(result, dict):
        return HTMLResponse('<p class="success">Export completed.</p>')

    return templates.TemplateResponse("partials/export_complete.html", {
        "request": request,
        "result": result,
    })
