"""Concurrency utilities and helpers for image sequence processing."""
from __future__ import annotations

import fnmatch
import logging
import os
import re
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable, Sequence

import tqdm

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# URL validation
# ---------------------------------------------------------------------------

_IMAGE_URL_RE = re.compile(
    r"https?://[^\s\"']+",
    re.IGNORECASE,
)


def is_image_url(url: str) -> bool:
    """Return True if *url* looks like an HTTP(S) image endpoint."""
    return _IMAGE_URL_RE.match(url) is not None


# ---------------------------------------------------------------------------
# File helpers
# ---------------------------------------------------------------------------


def clear_target(directory: str | Path, mask: str = "*.jpg") -> None:
    """Delete all files matching *mask* inside *directory*."""
    dir_str = str(directory)
    with os.scandir(dir_str) as it:
        for entry in it:
            if entry.is_file(follow_symlinks=False) and fnmatch.fnmatch(entry.name, mask):
                os.remove(entry.path)


# ---------------------------------------------------------------------------
# Stack-traced executors
# ---------------------------------------------------------------------------


class _StackTracedMixin:
    """Mixin that preserves full tracebacks from worker threads/processes."""

    def submit(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        return super().submit(self._wrapper, fn, *args, **kwargs)  # type: ignore[misc]

    @staticmethod
    def _wrapper(fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        try:
            return fn(*args, **kwargs)
        except Exception:
            raise type(sys.exc_info()[1])(traceback.format_exc()) from None


class TracedThreadPoolExecutor(_StackTracedMixin, ThreadPoolExecutor):
    """ThreadPoolExecutor that preserves worker tracebacks."""


class TracedProcessPoolExecutor(_StackTracedMixin, ProcessPoolExecutor):
    """ProcessPoolExecutor that preserves worker tracebacks."""


# ---------------------------------------------------------------------------
# Parallel executor
# ---------------------------------------------------------------------------


class ParallelExecutor:
    """Run a function over an iterable with threading/multiprocessing and a progress bar.

    Parameters
    ----------
    workers : int or None
        Max worker count. Defaults to ``os.cpu_count()``.
    debug : bool
        When True, print individual results instead of showing a progress bar.
    unit : str
        Unit label for the progress bar.
    """

    def __init__(
        self,
        workers: int | None = None,
        debug: bool = False,
        unit: str = "images",
    ) -> None:
        self.workers = workers or os.cpu_count() or 4
        self.debug = debug
        self.unit = unit

    def run_threaded(
        self,
        func: Callable[..., Any],
        items: Sequence[Any],
        *args: Any,
        progress_callback: Callable[[int, int, str], None] | None = None,
        **kwargs: Any,
    ) -> list[Any]:
        """Execute *func* for each item using a thread pool.

        *func* is called as ``func(item, index, *args, **kwargs)`` for every
        ``(index, item)`` pair in *items*.

        If *progress_callback* is provided it is called as
        ``progress_callback(completed, total, "")`` after each item finishes.
        """
        return self._run(
            TracedThreadPoolExecutor,
            self.workers * 5,
            func,
            items,
            *args,
            progress_callback=progress_callback,
            **kwargs,
        )

    def run_multiprocess(
        self,
        func: Callable[..., Any],
        items: Sequence[Any],
        *args: Any,
        progress_callback: Callable[[int, int, str], None] | None = None,
        **kwargs: Any,
    ) -> list[Any]:
        """Execute *func* for each item using a process pool.

        *func* is called as ``func(item, index, *args, **kwargs)``.

        If *progress_callback* is provided it is called as
        ``progress_callback(completed, total, "")`` after each item finishes.
        """
        return self._run(
            TracedProcessPoolExecutor,
            self.workers,
            func,
            items,
            *args,
            progress_callback=progress_callback,
            **kwargs,
        )

    # ------------------------------------------------------------------

    def _run(
        self,
        executor_cls: type,
        max_workers: int,
        func: Callable[..., Any],
        items: Sequence[Any],
        *args: Any,
        progress_callback: Callable[[int, int, str], None] | None = None,
        **kwargs: Any,
    ) -> list[Any]:
        total = len(items)
        results: list[Any] = []
        completed = 0
        with executor_cls(max_workers=max_workers) as executor:
            futures = [
                executor.submit(func, item, idx, *args, **kwargs)
                for idx, item in enumerate(items)
            ]

            if progress_callback:
                for future in as_completed(futures, timeout=300):
                    results.append(future.result())
                    completed += 1
                    progress_callback(completed, total, "")
            elif self.debug:
                for future in as_completed(futures, timeout=300):
                    result = future.result()
                    logger.debug(result)
                    results.append(result)
            else:
                pbar = tqdm.tqdm(
                    as_completed(futures),
                    total=total,
                    unit=f" {self.unit}",
                    unit_scale=True,
                    leave=True,
                    ascii=True,
                )
                for future in pbar:
                    results.append(future.result())

        return results
