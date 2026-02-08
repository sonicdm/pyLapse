"""Persistent storage for saved collections."""
from __future__ import annotations

import json
import logging
import os
import uuid
from typing import Any

logger = logging.getLogger(__name__)

_DEFAULT_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "collections.json"
)


class CollectionsStore:
    """Read/write saved collections to a JSON file."""

    def __init__(self, path: str | None = None) -> None:
        self._path = os.path.abspath(path or _DEFAULT_PATH)
        self._data: dict[str, dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        if os.path.isfile(self._path):
            try:
                with open(self._path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Failed to load collections: %s", exc)
                self._data = {}
        else:
            self._data = {}

    def _save(self) -> None:
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2)

    def get_all(self) -> dict[str, dict[str, Any]]:
        return dict(self._data)

    def get(self, coll_id: str) -> dict[str, Any] | None:
        return self._data.get(coll_id)

    def save(self, coll_id: str | None, data: dict[str, Any]) -> str:
        """Save or update a collection. Returns the collection ID."""
        if not coll_id:
            coll_id = uuid.uuid4().hex[:8]
        self._data[coll_id] = data
        self._save()
        return coll_id

    def delete(self, coll_id: str) -> bool:
        if coll_id in self._data:
            del self._data[coll_id]
            self._save()
            return True
        return False

    # ------------------------------------------------------------------
    # Export configs (nested under each collection)
    # ------------------------------------------------------------------

    def get_exports(self, coll_id: str) -> dict[str, dict[str, Any]]:
        """Return export configs for a collection."""
        coll = self._data.get(coll_id)
        if not coll:
            return {}
        return coll.get("exports", {})

    def get_export(self, coll_id: str, exp_id: str) -> dict[str, Any] | None:
        """Return a single export config."""
        return self.get_exports(coll_id).get(exp_id)

    def save_export(self, coll_id: str, exp_id: str | None, data: dict[str, Any]) -> str:
        """Save or update an export config under a collection. Returns exp_id."""
        coll = self._data.get(coll_id)
        if not coll:
            return ""
        if "exports" not in coll:
            coll["exports"] = {}
        if not exp_id:
            exp_id = uuid.uuid4().hex[:8]
        coll["exports"][exp_id] = data
        self._save()
        return exp_id

    def delete_export(self, coll_id: str, exp_id: str) -> bool:
        """Delete an export config from a collection."""
        coll = self._data.get(coll_id)
        if not coll:
            return False
        exports = coll.get("exports", {})
        if exp_id in exports:
            del exports[exp_id]
            self._save()
            return True
        return False

    def get_all_exports(self) -> list[dict[str, Any]]:
        """Return all exports across all collections, with coll_id/name attached."""
        result = []
        for coll_id, coll in self._data.items():
            for exp_id, exp in coll.get("exports", {}).items():
                result.append({
                    **exp,
                    "coll_id": coll_id,
                    "coll_name": coll.get("name", coll_id),
                    "exp_id": exp_id,
                })
        return result

    def reload(self) -> None:
        self._load()


# Module-level singleton
collections_store = CollectionsStore()
