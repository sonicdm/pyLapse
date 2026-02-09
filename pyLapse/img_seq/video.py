"""Render an image sequence directory to a video file using ffmpeg.

Expects the ffmpeg executable in the project's ``bin/`` directory, or
accepts an explicit path via the *ffmpeg_path* parameter.
"""
from __future__ import annotations

import fnmatch
import logging
import os
import re
import subprocess
import sys
import tempfile
import threading
from pathlib import Path
from typing import Callable, Optional

from tqdm import tqdm

logger = logging.getLogger(__name__)


def _get_ffmpeg_path() -> str:
    """Resolve ffmpeg from the project's ``bin/`` directory."""
    try:
        this_file = Path(__file__).resolve()
    except AttributeError:
        this_file = Path(os.path.abspath(__file__))

    project_root = this_file.parent.parent.parent
    bin_dir = project_root / "bin"
    exe_name = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"
    ffmpeg_path = bin_dir / exe_name

    if not ffmpeg_path.is_file():
        raise FileNotFoundError(
            f"ffmpeg not found at {ffmpeg_path}. "
            "Download ffmpeg and place the executable in the project's bin/ directory."
        )
    return str(ffmpeg_path)


def render_sequence_to_video(
    input_dir: str | Path,
    output_path: str | Path,
    fps: int = 24,
    pattern: str = "*.jpg",
    codec: str = "libx264",
    pixel_fmt: str = "yuv420p",
    ffmpeg_path: Optional[str] = None,
    progress: bool = True,
    progress_callback: Callable[[int, int, str], None] | None = None,
) -> str:
    """Render a directory of ordered images to a single video file.

    Parameters
    ----------
    input_dir : str or Path
        Directory containing the image sequence.
    output_path : str or Path
        Destination path for the output video (e.g. ``timelapse.mp4``).
    fps : int
        Frames per second (default 24).
    pattern : str
        Glob pattern for image files (default ``'*.jpg'``).
    codec : str
        Video codec (default ``'libx264'``).
    pixel_fmt : str
        Pixel format for compatibility (default ``'yuv420p'``).
    ffmpeg_path : str or None
        Override path to the ffmpeg binary. Defaults to ``bin/ffmpeg``.
    progress : bool
        Show a tqdm progress bar (default ``True``).

    Returns
    -------
    str
        The *output_path* on success.

    Raises
    ------
    FileNotFoundError
        If *input_dir* doesn't exist or ffmpeg is not found.
    ValueError
        If no images match the pattern.
    RuntimeError
        If ffmpeg exits with a non-zero return code.
    """
    dir_str = str(input_dir)
    if not os.path.isdir(dir_str):
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")

    # Scan with os.scandir + fnmatch — much faster than Path.glob on network shares
    names: list[str] = []
    with os.scandir(dir_str) as it:
        for entry in it:
            if entry.is_file(follow_symlinks=False) and fnmatch.fnmatch(entry.name, pattern):
                names.append(entry.name)

    if not names:
        raise ValueError(f"No images matching '{pattern}' in {input_dir}")

    names.sort()
    total_frames = len(names)
    print(f"Found {total_frames} images.")

    ffmpeg_bin = ffmpeg_path or _get_ffmpeg_path()
    logger.info(
        "Rendering %d images from %s to %s at %d fps",
        total_frames, input_dir, output_path, fps,
    )

    # Build a concat demuxer file — use os.path.join instead of .resolve()
    # to avoid an extra network round-trip per file on UNC paths
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8",
    ) as concat_file:
        for name in names:
            full = os.path.join(dir_str, name).replace("'", "'\\''")
            concat_file.write(f"file '{full}'\n")
        concat_path = concat_file.name

    try:
        cmd = [
            ffmpeg_bin,
            "-y",
            "-r", str(fps),       # input framerate: 1 image = 1 frame
            "-f", "concat",
            "-safe", "0",
            "-i", concat_path,
            "-c:v", codec,
            "-pix_fmt", pixel_fmt,
        ]
        if progress or progress_callback:
            # -progress pipe:1 outputs machine-readable stats to stdout
            cmd += ["-progress", "pipe:1"]
        cmd.append(str(Path(output_path).resolve()))

        logger.debug("Running: %s", " ".join(cmd))

        if progress or progress_callback:
            _run_ffmpeg_with_progress(cmd, total_frames, progress_callback)
        else:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(
                    f"ffmpeg failed (exit {result.returncode}): "
                    f"{result.stderr or result.stdout}"
                )
    finally:
        try:
            os.unlink(concat_path)
        except OSError:
            pass

    return str(output_path)


_FRAME_RE = re.compile(r"^frame=(\d+)")


def _run_ffmpeg_with_progress(
    cmd: list[str],
    total_frames: int,
    progress_callback: Callable[[int, int, str], None] | None = None,
) -> None:
    """Run an ffmpeg command while tracking progress.

    Parses ``frame=N`` lines from ffmpeg's ``-progress pipe:1`` output.
    When *progress_callback* is provided it is called instead of (or in
    addition to) the tqdm progress bar.  A background thread drains stderr
    to prevent the pipe buffer from filling up and deadlocking ffmpeg.
    """
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Drain stderr on a background thread to prevent pipe-buffer deadlock
    stderr_chunks: list[str] = []

    def _drain_stderr() -> None:
        assert proc.stderr is not None
        for line in proc.stderr:
            stderr_chunks.append(line)

    drain_thread = threading.Thread(target=_drain_stderr, daemon=True)
    drain_thread.start()

    bar = None if progress_callback else tqdm(total=total_frames, unit="frame", desc="Rendering")
    try:
        assert proc.stdout is not None
        for line in proc.stdout:
            m = _FRAME_RE.match(line.strip())
            if m:
                frame = int(m.group(1))
                if progress_callback:
                    progress_callback(frame, total_frames, "Encoding")
                if bar is not None:
                    bar.update(frame - bar.n)
        proc.wait()
        drain_thread.join(timeout=5)
    finally:
        if bar is not None:
            bar.close()

    if proc.returncode != 0:
        raise RuntimeError(
            f"ffmpeg failed (exit {proc.returncode}): {''.join(stderr_chunks)}"
        )
