"""Background task manager with progress tracking."""
from __future__ import annotations

import logging
import threading
import traceback
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass
class Task:
    """A tracked background task."""

    id: str
    name: str
    status: str = "pending"  # pending | running | completed | failed
    progress: float = 0.0
    current: int = 0
    total: int = 0
    message: str = ""
    error: str | None = None
    result: Any = None
    meta: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: str | None = None
    finished_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status,
            "progress": self.progress,
            "current": self.current,
            "total": self.total,
            "message": self.message,
            "error": self.error,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }


class TaskManager:
    """Run and track background tasks with progress callbacks."""

    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}
        self._lock = threading.Lock()

    def create_task(
        self,
        name: str,
        func: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Task:
        """Create and start a background task.

        *func* is called as ``func(*args, progress_callback=cb, **kwargs)``
        where *cb* is a ``(completed, total, message)`` callback.
        """
        task_id = uuid.uuid4().hex[:12]
        task = Task(id=task_id, name=name)

        with self._lock:
            self._tasks[task_id] = task

        def _progress(completed: int, total: int, message: str) -> None:
            task.current = completed
            task.total = total
            task.message = message
            task.progress = (completed / total * 100) if total else 0

        def _run() -> None:
            task.status = "running"
            task.started_at = datetime.now().isoformat()
            try:
                task.result = func(*args, progress_callback=_progress, **kwargs)
                task.status = "completed"
                task.progress = 100.0
            except Exception as exc:
                task.status = "failed"
                task.error = traceback.format_exc()
                logger.error("Task %s failed: %s", task_id, exc)
            finally:
                task.finished_at = datetime.now().isoformat()

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        return task

    def get_task(self, task_id: str) -> Task | None:
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> list[Task]:
        return list(self._tasks.values())


# Module-level singleton
task_manager = TaskManager()
