"""Export routes — CRUD for export configs + run exports with progress."""
from __future__ import annotations

import json
import os
from typing import Any, Callable

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse

from apscheduler.triggers.cron import CronTrigger

from pyLapse.web.app import templates
from pyLapse.web.collections_store import collections_store
from pyLapse.web.history_store import history_store
from pyLapse.web.scheduler import capture_scheduler
from pyLapse.web.tasks import task_manager
from pyLapse.img_seq.fonts import list_available_fonts
from pyLapse.img_seq.image import imageset_load, ImageIO, prepare_output_dir
from pyLapse.img_seq.lapsetime import cron_image_filter
from pyLapse.img_seq.video import render_sequence_to_video

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _render_export_grid(request: Request) -> HTMLResponse:
    """Return all export view cards grouped by collection."""
    all_exports = collections_store.get_all_exports()
    if not all_exports:
        return HTMLResponse(
            '<p id="no-exports-msg" class="muted">No export configs. '
            'Go to <a href="/collections">Collections</a> to create one.</p>'
        )
    html_parts = []
    for item in all_exports:
        html_parts.append(
            templates.get_template("partials/export_view.html").render(
                request=request,
                exp_id=item["exp_id"],
                coll_id=item["coll_id"],
                coll_name=item["coll_name"],
                exp=item,
            )
        )
    return HTMLResponse("".join(html_parts))


def _parse_export_form(form) -> dict[str, Any]:
    """Extract export config dict from form data."""
    return {
        "name": form.get("name", ""),
        "input_dir": form.get("input_dir", ""),
        "output_dir": form.get("output_dir", ""),
        "date_source": form.get("date_source", "filename"),
        "hour": form.get("hour", "*"),
        "minute": form.get("minute", "*"),
        "second": form.get("second", "0"),
        "resize": form.get("resize", "") == "true",
        "resolution_w": int(form.get("resolution_w", 1920)),
        "resolution_h": int(form.get("resolution_h", 1080)),
        "quality": int(form.get("quality", 50)),
        "optimize": form.get("optimize", "") == "true",
        "drawtimestamp": form.get("drawtimestamp", "") == "true",
        "timestampformat": form.get("timestampformat", "%Y-%m-%d %I:%M:%S %p"),
        "timestampfont": form.get("timestampfont", ""),
        "timestampfontsize": int(form.get("timestampfontsize", 36)),
        "ts_r": int(form.get("ts_r", 255)),
        "ts_g": int(form.get("ts_g", 255)),
        "ts_b": int(form.get("ts_b", 255)),
        "ts_x": int(form.get("ts_x", 0)),
        "ts_y": int(form.get("ts_y", 0)),
        "prefix": form.get("prefix", ""),
        "zeropadding": int(form.get("zeropadding", 5)),
        # Video creation settings
        "create_video": form.get("create_video", "") == "true",
        "video_fps": int(form.get("video_fps", 24)),
        "video_pattern": form.get("video_pattern", "*.jpg"),
        "video_codec": form.get("video_codec", "libx264"),
        "video_output": form.get("video_output", ""),
        "date_from": form.get("date_from", ""),
        "date_to": form.get("date_to", ""),
    }


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------


@router.get("/", response_class=HTMLResponse)
async def exports_page(request: Request) -> HTMLResponse:
    all_exports = collections_store.get_all_exports()
    all_history = history_store.get_exports()
    return templates.TemplateResponse("exports.html", {
        "request": request,
        "all_exports": all_exports,
        "export_history": all_history[:10],
        "history_limit": 10,
        "history_total": len(all_history),
    })


# ---------------------------------------------------------------------------
# Picker (shown from collections page)
# ---------------------------------------------------------------------------


@router.get("/picker", response_class=HTMLResponse)
async def export_picker(
    request: Request,
    coll_id: str = "",
) -> HTMLResponse:
    """Return a picker partial: existing exports for this collection + create new."""
    coll = collections_store.get(coll_id) if coll_id else None
    exports = collections_store.get_exports(coll_id) if coll_id else {}
    return templates.TemplateResponse("partials/export_picker.html", {
        "request": request,
        "coll_id": coll_id,
        "coll": coll or {},
        "exports": exports,
    })


# ---------------------------------------------------------------------------
# CRUD (collection-scoped)
# ---------------------------------------------------------------------------


@router.get("/add-form", response_class=HTMLResponse)
async def export_add_form(
    request: Request,
    coll_id: str = "",
) -> HTMLResponse:
    coll = collections_store.get(coll_id) if coll_id else None
    fonts = list_available_fonts()
    exp: dict[str, Any] = {}
    if coll:
        exp["input_dir"] = coll.get("path", "")
        exp["name"] = coll.get("name", "")
        exp["date_source"] = coll.get("date_source", "filename")
        ext = coll.get("ext", "jpg")
        exp["video_pattern"] = f"*.{ext}"
    all_collections = collections_store.get_all()
    return templates.TemplateResponse("partials/export_edit.html", {
        "request": request,
        "coll_id": coll_id,
        "exp_id": "",
        "exp": exp,
        "fonts": fonts,
        "is_new": True,
        "collections": all_collections,
    })


@router.get("/{coll_id}/{exp_id}/edit", response_class=HTMLResponse)
async def export_edit(request: Request, coll_id: str, exp_id: str) -> HTMLResponse:
    exp = collections_store.get_export(coll_id, exp_id) or {}
    fonts = list_available_fonts()
    return templates.TemplateResponse("partials/export_edit.html", {
        "request": request,
        "coll_id": coll_id,
        "exp_id": exp_id,
        "exp": exp,
        "fonts": fonts,
        "is_new": False,
    })


@router.post("/add", response_class=HTMLResponse)
async def export_add(request: Request) -> HTMLResponse:
    form = await request.form()
    coll_id = str(form.get("coll_id", "")).strip()
    data = _parse_export_form(form)

    # Auto-create a collection from the input dir if none specified
    if not coll_id or not collections_store.get(coll_id):
        input_dir = data.get("input_dir", "")
        if not input_dir:
            return HTMLResponse('<p class="error">Input directory is required.</p>')
        # Check if a collection already exists for this path
        for existing_id, existing_coll in collections_store.get_all().items():
            if existing_coll.get("path") == input_dir:
                coll_id = existing_id
                break
        else:
            name = data.get("name") or os.path.basename(input_dir)
            ext = data.get("video_pattern", "*.jpg").lstrip("*.")
            coll_id = collections_store.save(None, {
                "name": name,
                "path": input_dir,
                "date_source": data.get("date_source", "filename"),
                "ext": ext,
            })

    collections_store.save_export(coll_id, None, data)
    return _render_export_grid(request)


@router.post("/{coll_id}/{exp_id}/save", response_class=HTMLResponse)
async def export_save(request: Request, coll_id: str, exp_id: str) -> HTMLResponse:
    form = await request.form()
    data = _parse_export_form(form)
    collections_store.save_export(coll_id, exp_id, data)
    return _render_export_grid(request)


@router.post("/{coll_id}/{exp_id}/remove", response_class=HTMLResponse)
async def export_remove(request: Request, coll_id: str, exp_id: str) -> HTMLResponse:
    collections_store.delete_export(coll_id, exp_id)
    return _render_export_grid(request)


# ---------------------------------------------------------------------------
# Run export
# ---------------------------------------------------------------------------


def _get_ffmpeg_path() -> str | None:
    """Read ffmpeg_path from capture_config.json if set."""
    path = capture_scheduler.config_path
    if not path or not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        ffmpeg = data.get("ffmpeg_path", "")
        return ffmpeg if ffmpeg else None
    except Exception:
        return None


def _run_export(
    input_dir: str,
    output_dir: str,
    date_source: str,
    hour: str,
    minute: str,
    second: str,
    resize: bool,
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
    create_video: bool = False,
    video_fps: int = 24,
    video_pattern: str = "*.jpg",
    video_codec: str = "libx264",
    video_output: str = "",
    export_name: str = "",
    timestamp_source_tz: str = "",
    timestamp_display_tz: str = "",
    date_from: str = "",
    date_to: str = "",
    progress_callback: Callable[[int, int, str], None] | None = None,
) -> dict[str, Any]:
    """Background export function invoked by the task manager."""
    if progress_callback:
        progress_callback(0, 0, "Loading image set...")
    imageset = imageset_load(input_dir, date_source=date_source, progress_callback=progress_callback)

    # Filter by date range (if specified)
    if date_from or date_to:
        filtered_index = {}
        for day_str, files in imageset.imageindex.items():
            if date_from and day_str < date_from:
                continue
            if date_to and day_str > date_to:
                continue
            filtered_index[day_str] = files
        imageset.imageindex = filtered_index
        if progress_callback:
            day_count = len(filtered_index)
            img_count = sum(len(v) for v in filtered_index.values())
            range_label = f"{date_from or 'start'} to {date_to or 'end'}"
            progress_callback(0, 0, f"Date range {range_label}: {day_count} days, {img_count} images")

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

    record = history_store.add_export({
        "name": export_name or os.path.basename(input_dir),
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
                "name": export_name or os.path.splitext(os.path.basename(vid_output))[0],
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


@router.post("/{coll_id}/{exp_id}/run", response_class=HTMLResponse)
async def export_run(request: Request, coll_id: str, exp_id: str) -> HTMLResponse:
    """Run an export using its saved config."""
    exp = collections_store.get_export(coll_id, exp_id)
    if not exp:
        return HTMLResponse(f'<p class="error">Export config not found.</p>')

    # Source TZ = what timezone the image timestamps are in (set on the camera).
    # Display TZ = what timezone to render on the overlay (if different from source).
    coll = collections_store.get(coll_id)
    timestamp_source_tz = coll.get("timezone", "") if coll else ""

    task_name = f"Export {exp.get('name', exp_id)}"
    if exp.get("create_video"):
        task_name += " + Video"
    task = task_manager.create_task(
        task_name,
        _run_export,
        input_dir=exp["input_dir"],
        output_dir=exp["output_dir"],
        date_source=exp.get("date_source", "filename"),
        hour=exp.get("hour", "*"),
        minute=exp.get("minute", "*"),
        second=exp.get("second", "0"),
        resize=exp.get("resize", False),
        resolution_w=exp.get("resolution_w", 1920),
        resolution_h=exp.get("resolution_h", 1080),
        quality=exp.get("quality", 50),
        optimize=exp.get("optimize", False),
        drawtimestamp=exp.get("drawtimestamp", False),
        timestampformat=exp.get("timestampformat", "%Y-%m-%d %I:%M:%S %p"),
        timestampfont=exp.get("timestampfont") or None,
        timestampfontsize=exp.get("timestampfontsize", 36),
        timestampcolor=(exp.get("ts_r", 255), exp.get("ts_g", 255), exp.get("ts_b", 255)),
        timestamppos=(exp.get("ts_x", 0), exp.get("ts_y", 0)),
        prefix=exp.get("prefix", ""),
        zeropadding=exp.get("zeropadding", 5),
        create_video=exp.get("create_video", False),
        video_fps=exp.get("video_fps", 24),
        video_pattern=exp.get("video_pattern", "*.jpg"),
        video_codec=exp.get("video_codec", "libx264"),
        video_output=exp.get("video_output", ""),
        export_name=exp.get("name", exp_id),
        timestamp_source_tz=timestamp_source_tz,
        timestamp_display_tz=exp.get("display_tz", ""),
        date_from=exp.get("date_from", ""),
        date_to=exp.get("date_to", ""),
    )
    return templates.TemplateResponse("partials/task_progress.html", {
        "request": request,
        "task": task.to_dict(),
        "result_url": f"/exports/result/{task.id}",
    })


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------


@router.post("/delete", response_class=HTMLResponse)
async def exports_delete(request: Request, export_id: str = Form(...)) -> HTMLResponse:
    """Delete an export history entry."""
    history_store.delete_export(export_id)
    return templates.TemplateResponse("partials/export_history.html", {
        "request": request,
        "export_history": history_store.get_exports(),
    })


@router.get("/result/{task_id}", response_class=HTMLResponse)
async def exports_result(request: Request, task_id: str) -> HTMLResponse:
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
        "export_history": history_store.get_exports(),
    })
