"""Time-lapse auto capture: grab images from configured cameras on a schedule.

Configure cameras and schedules in ``capture_config.json``
(or set the ``PYLAPSE_CAPTURE_CONFIG`` environment variable to its path).
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Any

import colorama
from apscheduler.schedulers.blocking import BlockingScheduler

from pyLapse.img_seq.cameras import Camera

logger = logging.getLogger(__name__)


def _config_path() -> str:
    """Return the path to the capture configuration file."""
    default = os.path.join(os.path.dirname(os.path.abspath(__file__)), "capture_config.json")
    return os.environ.get("PYLAPSE_CAPTURE_CONFIG", default)


def load_config(path: str | None = None) -> dict[str, Any]:
    """Load and return the JSON capture configuration."""
    path = path or _config_path()
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def grab_one(camera: Camera, output_dir: str, prefix: str) -> None:
    """Fetch one image from *camera* and save to *output_dir*."""
    name = camera.name
    url = camera.imageurl
    print(
        colorama.Fore.YELLOW
        + f"{datetime.now()}: Grabbing {name} from {url}\n"
    )
    try:
        camera.save_image(output_dir, prefix=prefix)
        print(
            colorama.Fore.GREEN
            + f"{datetime.now()}: Success - grabbed {name} from {url}\n"
        )
    except Exception as exc:
        print(
            colorama.Fore.RED
            + f"{datetime.now()}: Failed to grab {name}: {exc}\n"
        )


def main() -> None:
    """Entry point: load config, create cameras, start the scheduler."""
    colorama.init(autoreset=True)

    config = load_config()
    cameras_config = config.get("cameras", {})
    if not cameras_config:
        print(colorama.Fore.RED + "No cameras defined in config.")
        return

    scheduler = BlockingScheduler()

    for camera_id, cam in cameras_config.items():
        name = cam.get("name", camera_id)
        url = cam.get("url")
        output_dir = cam.get("output_dir")
        prefix = cam.get("prefix", "")
        schedules = cam.get("schedules", [])

        if not url or not output_dir:
            print(colorama.Fore.RED + f"Camera '{camera_id}' missing url or output_dir, skipping.")
            continue

        camera = Camera(name, url, location=camera_id)

        for i, rule in enumerate(schedules):
            job_id = rule.get("id", f"{camera_id}_schedule_{i}")
            cron_kwargs = {
                k: v for k, v in rule.items()
                if k in ("hour", "minute", "second", "day", "week", "month", "year", "day_of_week")
                and v is not None
            }
            scheduler.add_job(
                grab_one, "cron",
                id=job_id,
                args=(camera, output_dir, prefix),
                **cron_kwargs,
            )

    scheduler.add_job(scheduler.print_jobs, "cron", minute="*", id="next_job")

    print(colorama.Fore.GREEN + "Starting Time Lapse Auto Capture")
    print(colorama.Fore.CYAN + "Starting Jobs:")
    scheduler.print_jobs()
    scheduler.start()


if __name__ == "__main__":
    main()
