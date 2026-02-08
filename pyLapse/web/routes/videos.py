"""Video routes — render image sequences to video with history and preview."""
from __future__ import annotations

import os
from typing import Any, Callable

from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import FileResponse, HTMLResponse

from pyLapse.web.app import templates
from pyLapse.web.history_store import history_store
from pyLapse.web.tasks import task_manager
from pyLapse.img_seq.video import render_sequence_to_video

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def videos_page(
    request: Request,
    input_dir: str = Query("", description="Pre-fill input directory"),
    name: str = Query("", description="Pre-fill video name"),
) -> HTMLResponse:
    all_videos = history_store.get_videos()
    return templates.TemplateResponse("videos.html", {
        "request": request,
        "video_history": all_videos[:10],
        "history_limit": 10,
        "history_total": len(all_videos),
        "prefill_input_dir": input_dir,
        "prefill_name": name,
    })


def _get_ffmpeg_path() -> str | None:
    """Read ffmpeg_path from capture_config.json if set."""
    from pyLapse.web.scheduler import capture_scheduler
    path = capture_scheduler.config_path
    if not path or not os.path.isfile(path):
        return None
    try:
        import json
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        ffmpeg = data.get("ffmpeg_path", "")
        return ffmpeg if ffmpeg else None
    except Exception:
        return None


def _run_render(
    input_dir: str,
    output_path: str,
    fps: int,
    pattern: str,
    codec: str,
    video_name: str = "",
    ffmpeg_path: str | None = None,
    progress_callback: Callable[[int, int, str], None] | None = None,
) -> dict[str, Any]:
    result_path = render_sequence_to_video(
        input_dir=input_dir,
        output_path=output_path,
        fps=fps,
        pattern=pattern,
        codec=codec,
        ffmpeg_path=ffmpeg_path,
        progress=False,
        progress_callback=progress_callback,
    )

    # Get file size
    file_size = 0
    try:
        file_size = os.path.getsize(result_path)
    except OSError:
        pass

    # Record to history
    video_id = history_store.add_video({
        "name": video_name or os.path.splitext(os.path.basename(output_path))[0],
        "input_dir": input_dir,
        "output_path": str(result_path),
        "fps": fps,
        "codec": codec,
        "file_size": file_size,
    })
    return {"output_path": str(result_path), "video_id": video_id, "file_size": file_size}


@router.post("/render", response_class=HTMLResponse)
async def videos_render(
    request: Request,
    input_dir: str = Form(...),
    output_path: str = Form(...),
    fps: int = Form(24),
    pattern: str = Form("*.jpg"),
    codec: str = Form("libx264"),
    name: str = Form(""),
) -> HTMLResponse:
    ffmpeg = _get_ffmpeg_path()
    task = task_manager.create_task(
        f"Render {name or os.path.basename(output_path)}",
        _run_render,
        input_dir=input_dir,
        output_path=output_path,
        fps=fps,
        pattern=pattern,
        codec=codec,
        video_name=name,
        ffmpeg_path=ffmpeg,
    )
    return templates.TemplateResponse("partials/task_progress.html", {
        "request": request,
        "task": task.to_dict(),
        "result_url": f"/videos/result/{task.id}",
    })


@router.get("/result/{task_id}", response_class=HTMLResponse)
async def videos_result(request: Request, task_id: str) -> HTMLResponse:
    """Return the render result HTML after completion."""
    task = task_manager.get_task(task_id)
    if not task:
        return HTMLResponse('<p class="error">Task not found.</p>')
    if task.status != "completed":
        return HTMLResponse(f'<p class="error">Task not ready: {task.status}</p>')

    result = task.result
    if not isinstance(result, dict):
        return HTMLResponse('<p class="success">Video rendered.</p>')

    video = history_store.get_video(result.get("video_id", ""))
    return templates.TemplateResponse("partials/video_complete.html", {
        "request": request,
        "video": video or result,
        "video_history": history_store.get_videos(),
    })


@router.get("/serve/{video_id}")
async def videos_serve(video_id: str) -> FileResponse:
    """Serve a rendered video file for in-browser playback."""
    video = history_store.get_video(video_id)
    if not video:
        return HTMLResponse('<p class="error">Video not found.</p>', status_code=404)

    path = video.get("output_path", "")
    if not os.path.isfile(path):
        return HTMLResponse(f'<p class="error">Video file not found: {path}</p>', status_code=404)

    return FileResponse(
        path,
        media_type="video/mp4",
        filename=os.path.basename(path),
    )


@router.post("/delete", response_class=HTMLResponse)
async def videos_delete(request: Request, video_id: str = Form(...)) -> HTMLResponse:
    """Delete a video history entry."""
    history_store.delete_video(video_id)
    return templates.TemplateResponse("partials/video_history.html", {
        "request": request,
        "video_history": history_store.get_videos(),
        "message": "Video record deleted.",
    })
