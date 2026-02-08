"""Background capture scheduler for the web UI.

Wraps APScheduler's BackgroundScheduler (non-blocking) and manages
Camera instances and capture history.
"""
from __future__ import annotations

import glob
import json
import logging
import os
from datetime import datetime
from typing import Any

from apscheduler.schedulers.background import BackgroundScheduler

from pyLapse.img_seq.cameras import Camera

logger = logging.getLogger(__name__)


class CaptureScheduler:
    """Singleton-style scheduler that manages cameras and capture jobs."""

    def __init__(self) -> None:
        self._scheduler = BackgroundScheduler()
        self.cameras: dict[str, Camera] = {}
        self._camera_config: dict[str, dict[str, Any]] = {}
        self.capture_history: list[dict[str, Any]] = []
        self._config_path: str | None = None
        self._max_history = 200
        # Track the last captured file path per camera for thumbnail serving
        self.last_capture_path: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Config
    # ------------------------------------------------------------------

    def load_config(self, path: str | None = None) -> dict[str, Any]:
        """Load ``capture_config.json`` and populate cameras."""
        if path is None:
            path = os.environ.get(
                "PYLAPSE_CAPTURE_CONFIG",
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "capture_config.json"),
            )
        path = os.path.abspath(path)
        self._config_path = path

        if not os.path.isfile(path):
            logger.warning("Config file not found: %s", path)
            return {}

        with open(path, "r", encoding="utf-8") as f:
            config: dict[str, Any] = json.load(f)

        self.cameras.clear()
        self._camera_config.clear()

        for cam_id, cam_cfg in config.get("cameras", {}).items():
            # Always store config so the camera is visible in the UI
            self._camera_config[cam_id] = cam_cfg
            name = cam_cfg.get("name", cam_id)
            url = cam_cfg.get("url")
            if not url:
                continue
            try:
                self.cameras[cam_id] = Camera(name, url, location=cam_id)
            except ValueError as exc:
                logger.error("Camera %r URL validation failed: %s", cam_id, exc)

        # Discover latest capture files for cameras with output dirs
        self._discover_latest_captures()

        return config

    def _discover_latest_captures(self) -> None:
        """Find the most recent image in each camera's output dir for thumbnails."""
        for cam_id, cfg in self._camera_config.items():
            if cam_id in self.last_capture_path:
                continue  # already tracked from a live capture
            output_dir = cfg.get("output_dir", "")
            if not output_dir or not os.path.isdir(output_dir):
                continue
            # Find the newest image file
            images = glob.glob(os.path.join(output_dir, "*.jpg"))
            images += glob.glob(os.path.join(output_dir, "*.png"))
            if images:
                newest = max(images, key=os.path.getmtime)
                self.last_capture_path[cam_id] = newest

    @property
    def config_path(self) -> str | None:
        return self._config_path

    # ------------------------------------------------------------------
    # Jobs
    # ------------------------------------------------------------------

    def setup_jobs(self) -> None:
        """Register cron jobs for every camera schedule."""
        # Remove existing capture jobs first
        for job in self._scheduler.get_jobs():
            if job.id != "__print_jobs__":
                self._scheduler.remove_job(job.id)

        cron_keys = {"hour", "minute", "second", "day", "week", "month", "year", "day_of_week"}

        for cam_id, cam_cfg in self._camera_config.items():
            camera = self.cameras.get(cam_id)
            if not camera:
                continue

            # Skip disabled cameras
            if not cam_cfg.get("enabled", True):
                logger.info("Camera %r is disabled, skipping schedules", cam_id)
                continue

            output_dir = cam_cfg.get("output_dir", "")

            # Build save_image kwargs from camera config
            save_kwargs: dict[str, Any] = {}
            if cam_cfg.get("prefix"):
                save_kwargs["prefix"] = cam_cfg["prefix"]
            if cam_cfg.get("filename_format"):
                save_kwargs["filenameformat"] = cam_cfg["filename_format"]
            if cam_cfg.get("ext"):
                save_kwargs["ext"] = cam_cfg["ext"]
            if cam_cfg.get("quality") is not None:
                save_kwargs["quality"] = int(cam_cfg["quality"])
            if cam_cfg.get("resize"):
                save_kwargs["resize"] = True
                w = int(cam_cfg.get("resize_width", 1920))
                h = int(cam_cfg.get("resize_height", 1080))
                save_kwargs["resolution"] = (w, h)

            for i, rule in enumerate(cam_cfg.get("schedules", [])):
                # Skip disabled schedules
                if not rule.get("enabled", True):
                    logger.info("Schedule %r for camera %r is disabled", rule.get("id", i), cam_id)
                    continue

                rule_id = rule.get("id", f"schedule_{i}")
                job_id = f"{cam_id}_{rule_id}"
                sched_type = rule.get("type", "cron")

                try:
                    if sched_type == "interval":
                        # Interval trigger — anchored to start_date, survives restarts
                        interval_amount = int(rule.get("interval_amount", 1))
                        interval_unit = rule.get("interval_unit", "minutes")
                        interval_kwargs: dict[str, int] = {interval_unit: interval_amount}

                        start_date_str = rule.get("start_date", "")
                        if start_date_str:
                            start_date = datetime.fromisoformat(start_date_str)
                        else:
                            start_date = datetime.now()

                        self._scheduler.add_job(
                            self._capture_image,
                            "interval",
                            id=job_id,
                            args=(cam_id, output_dir, save_kwargs),
                            start_date=start_date,
                            **interval_kwargs,
                        )
                    else:
                        # Cron trigger — aligned to clock boundaries
                        cron_kwargs = {
                            k: v for k, v in rule.items()
                            if k in cron_keys and v is not None
                        }
                        self._scheduler.add_job(
                            self._capture_image,
                            "cron",
                            id=job_id,
                            args=(cam_id, output_dir, save_kwargs),
                            **cron_kwargs,
                        )
                except (ValueError, KeyError) as exc:
                    logger.error("Invalid schedule %r for camera %r: %s", job_id, cam_id, exc)

    def _capture_image(self, camera_id: str, output_dir: str, save_kwargs: dict[str, Any]) -> None:
        """Capture a single image (called by the scheduler)."""
        camera = self.cameras.get(camera_id)
        if not camera:
            return

        entry: dict[str, Any] = {
            "camera_id": camera_id,
            "camera_name": camera.name,
            "time": datetime.now().isoformat(),
            "success": False,
            "error": None,
        }

        try:
            result = camera.save_image(output_dir, **save_kwargs)
            entry["success"] = True
            # Extract file path from "Saved /path/to/file" return value
            if result and result.startswith("Saved "):
                fpath = result[6:]
                entry["file_path"] = fpath
                self.last_capture_path[camera_id] = fpath
            logger.info("Captured %s", camera.name)
        except Exception as exc:
            entry["error"] = str(exc)
            logger.error("Capture failed for %s: %s", camera.name, exc)

        self.capture_history.insert(0, entry)
        if len(self.capture_history) > self._max_history:
            self.capture_history = self.capture_history[: self._max_history]

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        if not self._scheduler.running:
            self._scheduler.start()
            logger.info("Scheduler started")

    def stop(self) -> None:
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            logger.info("Scheduler stopped")

    @property
    def running(self) -> bool:
        return self._scheduler.running

    def get_jobs(self) -> list[dict[str, Any]]:
        """Return metadata for all scheduled jobs."""
        jobs: list[dict[str, Any]] = []
        for job in self._scheduler.get_jobs():
            next_run = job.next_run_time
            # Resolve camera name from job args (cam_id, output_dir, prefix)
            camera_name = ""
            if job.args and len(job.args) >= 1:
                cam_id = job.args[0]
                cam = self.cameras.get(cam_id)
                camera_name = cam.name if cam else cam_id
            jobs.append({
                "id": job.id,
                "name": job.name,
                "camera_name": camera_name,
                "next_run": next_run.isoformat() if next_run else None,
            })
        return jobs


# Module-level singleton
capture_scheduler = CaptureScheduler()
