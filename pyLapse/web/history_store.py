"""Persistent storage for export and video render history."""
from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

_DEFAULT_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "history.json"
)


class HistoryStore:
    """Read/write export and video history to a JSON file."""

    def __init__(self, path: str | None = None) -> None:
        self._path = os.path.abspath(path or _DEFAULT_PATH)
        self._data: dict[str, list[dict[str, Any]]] = {"exports": [], "videos": []}
        self._load()

    def _load(self) -> None:
        if os.path.isfile(self._path):
            try:
                with open(self._path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Failed to load history: %s", exc)
                self._data = {"exports": [], "videos": []}
        if "exports" not in self._data:
            self._data["exports"] = []
        if "videos" not in self._data:
            self._data["videos"] = []

    def _save(self) -> None:
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2)

    # -- Exports ---------------------------------------------------------------

    def add_export(self, record: dict[str, Any]) -> str:
        """Add an export record. Returns the record ID."""
        record_id = record.get("id") or uuid.uuid4().hex[:8]
        record["id"] = record_id
        record.setdefault("created_at", datetime.now().isoformat())
        self._data["exports"].insert(0, record)
        self._save()
        return record_id

    def get_exports(self) -> list[dict[str, Any]]:
        return list(self._data["exports"])

    def get_export(self, export_id: str) -> dict[str, Any] | None:
        for rec in self._data["exports"]:
            if rec.get("id") == export_id:
                return rec
        return None

    def delete_export(self, export_id: str) -> bool:
        before = len(self._data["exports"])
        self._data["exports"] = [
            r for r in self._data["exports"] if r.get("id") != export_id
        ]
        if len(self._data["exports"]) < before:
            self._save()
            return True
        return False

    # -- Videos ----------------------------------------------------------------

    def add_video(self, record: dict[str, Any]) -> str:
        """Add a video record. Returns the record ID."""
        record_id = record.get("id") or uuid.uuid4().hex[:8]
        record["id"] = record_id
        record.setdefault("created_at", datetime.now().isoformat())
        self._data["videos"].insert(0, record)
        self._save()
        return record_id

    def get_videos(self) -> list[dict[str, Any]]:
        return list(self._data["videos"])

    def get_video(self, video_id: str) -> dict[str, Any] | None:
        for rec in self._data["videos"]:
            if rec.get("id") == video_id:
                return rec
        return None

    def delete_video(self, video_id: str) -> bool:
        before = len(self._data["videos"])
        self._data["videos"] = [
            r for r in self._data["videos"] if r.get("id") != video_id
        ]
        if len(self._data["videos"]) < before:
            self._save()
            return True
        return False

    def reload(self) -> None:
        self._load()


# Module-level singleton
history_store = HistoryStore()
