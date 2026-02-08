#!/usr/bin/env python3
"""CLI to render an image sequence directory to a video file using ffmpeg.

Usage::

    python render_video.py <input_dir> <output_video> [--fps 24] [--pattern "*.jpg"]

Requires ffmpeg in the project's ``bin/`` directory.
"""
from __future__ import annotations

import argparse
import os
import sys

# Ensure project root is on path when run as script
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pyLapse.img_seq.video import render_sequence_to_video


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render an image sequence directory to a single video file (ffmpeg)."
    )
    parser.add_argument(
        "input_dir",
        help="Directory containing the image sequence (e.g. an export output folder).",
    )
    parser.add_argument(
        "output_video",
        help="Output video file path (e.g. timelapse.mp4).",
    )
    parser.add_argument(
        "--fps", type=int, default=24,
        help="Frames per second (default: 24).",
    )
    parser.add_argument(
        "--pattern", default="*.jpg",
        help="Glob pattern for image files (default: *.jpg).",
    )
    parser.add_argument(
        "--no-progress", action="store_true",
        help="Disable the progress bar.",
    )
    args = parser.parse_args()

    try:
        out = render_sequence_to_video(
            args.input_dir,
            args.output_video,
            fps=args.fps,
            pattern=args.pattern,
            progress=not args.no_progress,
        )
        print(f"Rendered video: {out}")
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
