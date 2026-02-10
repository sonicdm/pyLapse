"""Concurrency utilities and helpers for image sequence processing."""
from __future__ import annotations

import fnmatch
import logging
import multiprocessing
import os
import re
import sys
import traceback
from concurrent.futures import (
    ThreadPoolExecutor,
    ProcessPoolExecutor,
    as_completed,
    wait,
    FIRST_COMPLETED,
)
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


def clear_target(
    directory: str | Path, mask: str = "*.jpg", retries: int = 5, delay: float = 1.0
) -> None:
    """Delete all files matching *mask* inside *directory*.

    On Windows, files held open by another process raise ``PermissionError``.
    This function retries up to *retries* times with *delay* seconds between
    attempts, collecting stubborn files each pass until all are removed.
    """
    import time

    dir_str = str(directory)

    # Collect files to delete
    targets: list[str] = []
    with os.scandir(dir_str) as it:
        for entry in it:
            if entry.is_file(follow_symlinks=False) and fnmatch.fnmatch(entry.name, mask):
                targets.append(entry.path)

    if not targets:
        return

    remaining = list(targets)
    for attempt in range(1 + retries):
        still_locked: list[str] = []
        for fpath in remaining:
            try:
                os.remove(fpath)
            except PermissionError:
                still_locked.append(fpath)
            except FileNotFoundError:
                pass  # already gone
        if not still_locked:
            if attempt > 0:
                logger.info("Cleared %d files from %s (after %d retries)", len(targets), dir_str, attempt)
            return
        remaining = still_locked
        if attempt < retries:
            logger.warning(
                "clear_target: %d file(s) locked in %s, retrying in %.1fs (%d/%d)",
                len(remaining), dir_str, delay, attempt + 1, retries,
            )
            time.sleep(delay)

    # Final failure — raise so the caller knows
    raise PermissionError(
        f"Could not delete {len(remaining)} file(s) in {dir_str} after {retries} retries. "
        f"First locked file: {remaining[0]}"
    )


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
# Shared state for process pool workers (progress counter + cancel flag)
# ---------------------------------------------------------------------------

_shared_progress: Any = None
_shared_cancel: Any = None


def _init_shared(counter: Any, cancel_flag: Any) -> None:
    """Worker initializer — stores shared memory values as module globals."""
    global _shared_progress, _shared_cancel
    _shared_progress = counter
    _shared_cancel = cancel_flag


# ---------------------------------------------------------------------------
# Batch helper for process pools
# ---------------------------------------------------------------------------


def _batch_run(
    func: Callable[..., Any],
    chunk: Sequence[Any],
    start_idx: int,
    *args: Any,
    **kwargs: Any,
) -> list[Any]:
    """Process a batch of items sequentially within one worker process.

    This is a module-level function so it can be pickled for
    ``ProcessPoolExecutor``.  After each item the shared progress
    counter is incremented and the cancel flag is checked.  When the
    parent sets the cancel flag, workers stop processing immediately.
    """
    results = []
    for i, item in enumerate(chunk):
        if _shared_cancel is not None and _shared_cancel.value:
            break
        results.append(func(item, start_idx + i, *args, **kwargs))
        if _shared_progress is not None:
            with _shared_progress.get_lock():
                _shared_progress.value += 1
    return results


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

        Items are batched into chunks to reduce IPC overhead.  A shared
        counter provides per-image progress regardless of chunk size.

        If *progress_callback* is provided it is called as
        ``progress_callback(completed, total, "")`` approximately every
        250 ms with the current image count.
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
        futures: list[Any] = []

        # Process pools: batch items into chunks to avoid 100K+ IPC round-trips.
        # A shared multiprocessing.Value counter gives per-image progress
        # without needing small chunks.
        # Thread pools: one future per item (negligible overhead, finer progress).
        batched = issubclass(executor_cls, ProcessPoolExecutor)

        counter: Any = None
        cancel_flag: Any = None
        extra_kw: dict[str, Any] = {}
        if batched:
            counter = multiprocessing.Value("i", 0)
            cancel_flag = multiprocessing.Value("b", 0)  # 0=run, 1=cancel
            extra_kw["initializer"] = _init_shared
            extra_kw["initargs"] = (counter, cancel_flag)

        executor = executor_cls(max_workers=max_workers, **extra_kw)
        try:
            if batched:
                chunk_size = max(1, -(-total // (max_workers * 4)))
                for i in range(0, total, chunk_size):
                    chunk = items[i:i + chunk_size]
                    futures.append(
                        executor.submit(_batch_run, func, chunk, i, *args, **kwargs)
                    )
            else:
                futures = [
                    executor.submit(func, item, idx, *args, **kwargs)
                    for idx, item in enumerate(items)
                ]

            if progress_callback:
                if counter is not None:
                    # Process pool — poll shared counter for per-image progress
                    self._collect_with_counter(
                        futures, results, counter, total, progress_callback, batched,
                    )
                else:
                    # Thread pool — report after each future
                    for future in as_completed(futures):
                        results.append(future.result())
                        completed += 1
                        progress_callback(completed, total, "")
            elif self.debug:
                for future in as_completed(futures):
                    if batched:
                        for r in future.result():
                            logger.debug(r)
                            results.append(r)
                    else:
                        result = future.result()
                        logger.debug(result)
                        results.append(result)
            else:
                if counter is not None:
                    # Process pool + tqdm — poll shared counter
                    pbar = tqdm.tqdm(
                        total=total,
                        unit=f" {self.unit}",
                        unit_scale=True,
                        leave=True,
                        ascii=True,
                    )
                    self._collect_with_counter(
                        futures, results, counter, total,
                        lambda c, t, m: pbar.update(c - pbar.n),
                        batched,
                    )
                    pbar.close()
                else:
                    # Thread pool + tqdm
                    pbar = tqdm.tqdm(
                        total=total,
                        unit=f" {self.unit}",
                        unit_scale=True,
                        leave=True,
                        ascii=True,
                    )
                    for future in as_completed(futures):
                        results.append(future.result())
                        pbar.update(1)
                    pbar.close()
        except BaseException:
            # Signal child processes to stop via shared memory — they check
            # the flag after each image so they exit within one iteration.
            if cancel_flag is not None:
                cancel_flag.value = 1
            # Cancel all pending futures and kill the pool immediately.
            for f in futures:
                f.cancel()
            executor.shutdown(wait=False, cancel_futures=True)
            raise
        else:
            executor.shutdown(wait=True)

        return results

    @staticmethod
    def _collect_with_counter(
        futures: list[Any],
        results: list[Any],
        counter: Any,
        total: int,
        callback: Callable[[int, int, str], None],
        batched: bool,
    ) -> None:
        """Collect results from *futures* while polling *counter* for progress.

        Uses ``concurrent.futures.wait`` with a 250 ms timeout so the shared
        counter is polled ~4 times per second regardless of how long each
        chunk takes.  This decouples progress granularity from chunk size.
        """
        pending = set(futures)
        last_reported = 0

        while pending:
            done, pending = wait(pending, timeout=0.25, return_when=FIRST_COMPLETED)

            for f in done:
                if batched:
                    results.extend(f.result())
                else:
                    results.append(f.result())

            current = counter.value
            if current != last_reported:
                callback(current, total, "")
                last_reported = current

        # Final update — counter may lag slightly behind chunk completion
        current = counter.value
        if current != last_reported:
            callback(current, total, "")
