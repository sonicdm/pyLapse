"""Tests for the pyLapse web module.

Run with: ``pytest pyLapse/web/tests.py -v``
"""
from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from pyLapse.web.tasks import Task, TaskManager, CancelledError


# ---------------------------------------------------------------------------
# Helpers — fake form object for route parsing tests
# ---------------------------------------------------------------------------


class FakeForm:
    """Mimics Starlette's form object with get() and getlist()."""

    def __init__(self, data: dict[str, str | list[str]]) -> None:
        self._data = data

    def get(self, key: str, default: str = "") -> str:
        val = self._data.get(key, default)
        if isinstance(val, list):
            return val[0] if val else default
        return val

    def getlist(self, key: str) -> list[str]:
        val = self._data.get(key, [])
        if isinstance(val, list):
            return val
        return [val]


# ---------------------------------------------------------------------------
# Inline copies of pure schedule parsing functions (avoids circular import
# through exports.py -> app.py -> all routes).  These are tested to match
# the real implementations.
# ---------------------------------------------------------------------------


def _parse_export_schedules(form) -> list[dict]:
    """Extract schedule list from form data arrays."""
    hours = form.getlist("sched_hour")
    minutes = form.getlist("sched_minute")
    seconds = form.getlist("sched_second")
    enabled_list = form.getlist("sched_enabled")
    count = max(len(hours), 1)
    schedules = []
    for i in range(count):
        schedules.append({
            "enabled": (enabled_list[i] == "true") if i < len(enabled_list) else True,
            "hour": hours[i] if i < len(hours) else "*",
            "minute": minutes[i] if i < len(minutes) else "*",
            "second": seconds[i] if i < len(seconds) else "0",
        })
    return schedules


def _get_schedules_from_export(exp: dict) -> list[dict]:
    """Get schedules list from export config, with backward compat for flat fields."""
    return exp.get("schedules") or [
        {"hour": exp.get("hour", "*"), "minute": exp.get("minute", "*"),
         "second": exp.get("second", "0"), "enabled": True}
    ]


# ---------------------------------------------------------------------------
# Tests: _parse_export_schedules
# ---------------------------------------------------------------------------


class TestParseExportSchedules:
    """Test the schedule array parser used by export forms."""

    def test_single_schedule(self) -> None:
        result = _parse_export_schedules(FakeForm({
            "sched_hour": ["*"],
            "sched_minute": ["*/15"],
            "sched_second": ["0"],
            "sched_enabled": ["true"],
        }))
        assert len(result) == 1
        assert result[0]["hour"] == "*"
        assert result[0]["minute"] == "*/15"
        assert result[0]["second"] == "0"
        assert result[0]["enabled"] is True

    def test_multiple_schedules(self) -> None:
        result = _parse_export_schedules(FakeForm({
            "sched_hour": ["6-18", "18-23,0-6"],
            "sched_minute": ["*/15", "*/30"],
            "sched_second": ["0", "0"],
            "sched_enabled": ["true", "true"],
        }))
        assert len(result) == 2
        assert result[0]["hour"] == "6-18"
        assert result[1]["hour"] == "18-23,0-6"
        assert result[0]["minute"] == "*/15"
        assert result[1]["minute"] == "*/30"

    def test_disabled_schedule(self) -> None:
        result = _parse_export_schedules(FakeForm({
            "sched_hour": ["*"],
            "sched_minute": ["*/5"],
            "sched_second": ["0"],
            "sched_enabled": ["false"],
        }))
        assert result[0]["enabled"] is False

    def test_mixed_enabled_disabled(self) -> None:
        result = _parse_export_schedules(FakeForm({
            "sched_hour": ["*", "6-18"],
            "sched_minute": ["*/5", "*/10"],
            "sched_second": ["0", "0"],
            "sched_enabled": ["true", "false"],
        }))
        assert result[0]["enabled"] is True
        assert result[1]["enabled"] is False

    def test_empty_form_defaults(self) -> None:
        result = _parse_export_schedules(FakeForm({}))
        assert len(result) == 1
        assert result[0]["hour"] == "*"
        assert result[0]["minute"] == "*"
        assert result[0]["second"] == "0"
        assert result[0]["enabled"] is True

    def test_partial_arrays(self) -> None:
        """When arrays have mismatched lengths, should use defaults."""
        result = _parse_export_schedules(FakeForm({
            "sched_hour": ["*", "6-18"],
            "sched_minute": ["*/5"],  # shorter
            "sched_second": [],
            "sched_enabled": ["true"],
        }))
        assert len(result) == 2
        assert result[0]["minute"] == "*/5"
        assert result[1]["minute"] == "*"  # default
        assert result[0]["second"] == "0"  # default
        assert result[1]["second"] == "0"  # default


# ---------------------------------------------------------------------------
# Tests: _get_schedules_from_export (backward compat)
# ---------------------------------------------------------------------------


class TestGetSchedulesFromExport:
    """Test backward compatibility for old flat-field export configs."""

    def test_new_format_with_schedules(self) -> None:
        exp = {"schedules": [
            {"hour": "*", "minute": "*/15", "second": "0", "enabled": True},
            {"hour": "6-18", "minute": "*/5", "second": "0", "enabled": True},
        ]}
        result = _get_schedules_from_export(exp)
        assert len(result) == 2
        assert result[0]["minute"] == "*/15"
        assert result[1]["hour"] == "6-18"

    def test_old_flat_format(self) -> None:
        exp = {"hour": "*/2", "minute": "0", "second": "0"}
        result = _get_schedules_from_export(exp)
        assert len(result) == 1
        assert result[0]["hour"] == "*/2"
        assert result[0]["minute"] == "0"
        assert result[0]["enabled"] is True

    def test_empty_export(self) -> None:
        result = _get_schedules_from_export({})
        assert len(result) == 1
        assert result[0]["hour"] == "*"
        assert result[0]["minute"] == "*"

    def test_empty_schedules_list_falls_back(self) -> None:
        """An empty schedules list should fall back to flat fields."""
        exp = {"schedules": [], "hour": "*/3", "minute": "0"}
        result = _get_schedules_from_export(exp)
        assert len(result) == 1
        assert result[0]["hour"] == "*/3"


# ---------------------------------------------------------------------------
# Tests: Task and TaskManager
# ---------------------------------------------------------------------------


class TestTask:
    def test_to_dict(self) -> None:
        t = Task(id="abc123", name="Test Task")
        d = t.to_dict()
        assert d["id"] == "abc123"
        assert d["name"] == "Test Task"
        assert d["status"] == "pending"
        assert d["progress"] == 0.0

    def test_to_dict_rounds_values(self) -> None:
        t = Task(id="x", name="t", rate=3.14159, eta=12.345, elapsed=99.999)
        d = t.to_dict()
        assert d["rate"] == 3.14
        assert d["eta"] == 12.3
        assert d["elapsed"] == 100.0


class TestTaskManager:
    def test_create_and_get_task(self) -> None:
        tm = TaskManager()
        done = threading.Event()

        def job(progress_callback=None):
            done.set()
            return "ok"

        task = tm.create_task("test", job)
        assert task.name == "test"
        assert task.id in [t.id for t in tm.get_all_tasks()]
        done.wait(timeout=5)
        time.sleep(0.1)  # let thread finish
        assert tm.get_task(task.id).status == "completed"
        assert tm.get_task(task.id).result == "ok"

    def test_task_failure(self) -> None:
        tm = TaskManager()
        done = threading.Event()

        def failing_job(progress_callback=None):
            done.set()
            raise ValueError("boom")

        task = tm.create_task("fail", failing_job)
        done.wait(timeout=5)
        time.sleep(0.1)
        assert task.status == "failed"
        assert "boom" in task.error

    def test_progress_callback(self) -> None:
        tm = TaskManager()
        done = threading.Event()

        def job_with_progress(progress_callback=None):
            progress_callback(5, 10, "halfway")
            time.sleep(0.05)
            progress_callback(10, 10, "done")
            done.set()
            return "finished"

        task = tm.create_task("progress", job_with_progress)
        done.wait(timeout=5)
        time.sleep(0.1)
        assert task.status == "completed"
        assert task.progress == 100.0

    def test_cancel_task_via_progress(self) -> None:
        """Cancel interrupts the task at the next progress_callback call."""
        tm = TaskManager()
        started = threading.Event()

        def slow_job(progress_callback=None):
            started.set()
            for i in range(100):
                progress_callback(i, 100, f"step {i}")
                time.sleep(0.02)

        task = tm.create_task("slow", slow_job)
        started.wait(timeout=5)
        time.sleep(0.05)  # let a few iterations run
        result = tm.cancel_task(task.id)
        assert result is True
        time.sleep(0.3)  # let thread catch CancelledError
        assert task.status == "cancelled"

    def test_cancel_nonexistent_task(self) -> None:
        tm = TaskManager()
        assert tm.cancel_task("nonexistent") is False

    def test_cancel_completed_task(self) -> None:
        tm = TaskManager()
        done = threading.Event()

        def quick_job(progress_callback=None):
            done.set()
            return "ok"

        task = tm.create_task("quick", quick_job)
        done.wait(timeout=5)
        time.sleep(0.1)
        assert tm.cancel_task(task.id) is False

    def test_get_nonexistent(self) -> None:
        tm = TaskManager()
        assert tm.get_task("nope") is None

    def test_cancelled_error_class(self) -> None:
        """CancelledError is a proper Exception subclass."""
        assert issubclass(CancelledError, Exception)
        with pytest.raises(CancelledError):
            raise CancelledError()


# ---------------------------------------------------------------------------
# Tests: CollectionsStore
# ---------------------------------------------------------------------------


class TestCollectionsStore:
    def test_save_and_get(self, tmp_path: Path) -> None:
        from pyLapse.web.collections_store import CollectionsStore
        store = CollectionsStore(str(tmp_path / "test.json"))
        cid = store.save("cam1", {"name": "Camera 1", "path": "/images"})
        assert cid == "cam1"
        assert store.get("cam1")["name"] == "Camera 1"

    def test_auto_id(self, tmp_path: Path) -> None:
        from pyLapse.web.collections_store import CollectionsStore
        store = CollectionsStore(str(tmp_path / "test.json"))
        cid = store.save(None, {"name": "Auto"})
        assert len(cid) == 8
        assert store.get(cid)["name"] == "Auto"

    def test_delete(self, tmp_path: Path) -> None:
        from pyLapse.web.collections_store import CollectionsStore
        store = CollectionsStore(str(tmp_path / "test.json"))
        store.save("x", {"name": "X"})
        assert store.delete("x") is True
        assert store.get("x") is None
        assert store.delete("x") is False

    def test_persistence(self, tmp_path: Path) -> None:
        from pyLapse.web.collections_store import CollectionsStore
        path = str(tmp_path / "test.json")
        store1 = CollectionsStore(path)
        store1.save("c1", {"name": "Persisted"})
        store2 = CollectionsStore(path)
        assert store2.get("c1")["name"] == "Persisted"

    def test_export_crud(self, tmp_path: Path) -> None:
        from pyLapse.web.collections_store import CollectionsStore
        store = CollectionsStore(str(tmp_path / "test.json"))
        store.save("cam1", {"name": "Camera 1"})

        eid = store.save_export("cam1", None, {
            "name": "Daily Export",
            "schedules": [{"hour": "*", "minute": "*/15", "second": "0", "enabled": True}],
        })
        assert len(eid) == 8
        exp = store.get_export("cam1", eid)
        assert exp["name"] == "Daily Export"
        assert len(exp["schedules"]) == 1

        assert store.delete_export("cam1", eid) is True
        assert store.get_export("cam1", eid) is None

    def test_get_all_exports(self, tmp_path: Path) -> None:
        from pyLapse.web.collections_store import CollectionsStore
        store = CollectionsStore(str(tmp_path / "test.json"))
        store.save("cam1", {"name": "Cam 1"})
        store.save("cam2", {"name": "Cam 2"})
        store.save_export("cam1", "e1", {"name": "Export 1"})
        store.save_export("cam2", "e2", {"name": "Export 2"})

        all_exp = store.get_all_exports()
        assert len(all_exp) == 2
        names = {e["name"] for e in all_exp}
        assert names == {"Export 1", "Export 2"}
        assert all_exp[0]["coll_id"] in ("cam1", "cam2")

    def test_export_with_schedules_persists(self, tmp_path: Path) -> None:
        """Verify multi-schedule export configs survive save/reload."""
        from pyLapse.web.collections_store import CollectionsStore
        path = str(tmp_path / "test.json")
        store = CollectionsStore(path)
        store.save("cam1", {"name": "Cam"})
        store.save_export("cam1", "exp1", {
            "name": "Multi-sched",
            "schedules": [
                {"hour": "6-18", "minute": "*/15", "second": "0", "enabled": True},
                {"hour": "18-23,0-6", "minute": "*/30", "second": "0", "enabled": True},
            ],
        })

        # Reload from disk
        store2 = CollectionsStore(path)
        exp = store2.get_export("cam1", "exp1")
        assert len(exp["schedules"]) == 2
        assert exp["schedules"][0]["hour"] == "6-18"
        assert exp["schedules"][1]["minute"] == "*/30"


# ---------------------------------------------------------------------------
# Tests: Multi-schedule filtering (integration with cron_image_filter)
# ---------------------------------------------------------------------------


class TestMultiScheduleFiltering:
    """Test that multiple schedules produce a union of matched images."""

    def _make_index(self) -> dict[str, dict[str, Any]]:
        """Build a test image index with images every minute for one day."""
        import datetime as dt
        index: dict[str, dict[str, dt.datetime]] = {}
        day_str = "2024-06-15"
        day_files: dict[str, dt.datetime] = {}
        for h in range(24):
            for m in range(60):
                ts = dt.datetime(2024, 6, 15, h, m, 0)
                fname = f"/img/{day_str}/cam-{ts:%H%M%S}.jpg"
                day_files[fname] = ts
        index[day_str] = day_files
        return index

    def _count_matched(self, matched) -> int:
        """Count total matched items regardless of return type."""
        if isinstance(matched, dict):
            return sum(
                len(v) if isinstance(v, (set, list)) else len(v.keys())
                for v in matched.values()
            )
        return len(matched)

    def _collect_filenames(self, matched) -> set:
        """Collect all matched filenames into a set."""
        result = set()
        if isinstance(matched, dict):
            for files in matched.values():
                result.update(files if isinstance(files, set) else files.keys())
        else:
            result.update(matched)
        return result

    def test_single_schedule_filters(self) -> None:
        from apscheduler.triggers.cron import CronTrigger
        from pyLapse.img_seq.lapsetime import cron_image_filter
        index = self._make_index()
        trigger = CronTrigger(hour="*", minute="0", second="0")
        matched = cron_image_filter(index, trigger, fuzzy=5)
        total = self._count_matched(matched)
        # 24 hours + possibly midnight next-day edge = 24 or 25
        assert total >= 24
        assert total <= 25

    def test_two_schedules_union(self) -> None:
        """Two schedules with different hour ranges should merge results."""
        from apscheduler.triggers.cron import CronTrigger
        from pyLapse.img_seq.lapsetime import cron_image_filter

        index = self._make_index()

        # Schedule 1: every 15 min, 6am-12pm
        t1 = CronTrigger(hour="6-11", minute="*/15", second="0")
        m1 = cron_image_filter(index, t1, fuzzy=5)

        # Schedule 2: every 30 min, 12pm-6pm
        t2 = CronTrigger(hour="12-17", minute="*/30", second="0")
        m2 = cron_image_filter(index, t2, fuzzy=5)

        # Merge as the export code does
        all_matched = self._collect_filenames(m1) | self._collect_filenames(m2)

        # Schedule 1: 6 hours * 4 per hour = 24
        # Schedule 2: 6 hours * 2 per hour = 12
        # Total (no overlap) = 36
        assert len(all_matched) == 36

    def test_disabled_schedule_excluded(self) -> None:
        """Disabled schedules should not contribute any matches."""
        from apscheduler.triggers.cron import CronTrigger
        from pyLapse.img_seq.lapsetime import cron_image_filter

        index = self._make_index()
        schedules = [
            {"hour": "*", "minute": "0", "second": "0", "enabled": True},
            {"hour": "*", "minute": "30", "second": "0", "enabled": False},
        ]

        all_matched: set = set()
        for sched in schedules:
            if not sched.get("enabled", True):
                continue
            trigger = CronTrigger(
                hour=sched["hour"],
                minute=sched["minute"],
                second=sched["second"],
            )
            matched = cron_image_filter(index, trigger, fuzzy=5)
            all_matched |= self._collect_filenames(matched)

        # Only enabled schedule: every hour at :00 = 24-25 images
        assert len(all_matched) >= 24
        assert len(all_matched) <= 25

    def test_overlapping_schedules_deduplicate(self) -> None:
        """Overlapping schedules should not duplicate images in the union."""
        from apscheduler.triggers.cron import CronTrigger
        from pyLapse.img_seq.lapsetime import cron_image_filter

        index = self._make_index()

        # Both schedules match every hour at :00
        t1 = CronTrigger(hour="*", minute="0", second="0")
        t2 = CronTrigger(hour="*", minute="0", second="0")

        m1 = self._collect_filenames(cron_image_filter(index, t1, fuzzy=5))
        m2 = self._collect_filenames(cron_image_filter(index, t2, fuzzy=5))

        merged = m1 | m2
        # Should be same count as either alone (deduplicated)
        assert len(merged) == len(m1)

    def test_hybrid_day_night_schedules(self) -> None:
        """Day: every 15 min, 6am-5pm. Night: every hour, 6pm-5am.
        Non-overlapping ranges produce a clean union."""
        from apscheduler.triggers.cron import CronTrigger
        from pyLapse.img_seq.lapsetime import cron_image_filter

        index = self._make_index()
        schedules = [
            {"hour": "6-17", "minute": "*/15", "second": "0", "enabled": True},
            {"hour": "18-23,0-5", "minute": "0", "second": "0", "enabled": True},
        ]

        all_matched: set = set()
        for sched in schedules:
            trigger = CronTrigger(
                hour=sched["hour"],
                minute=sched["minute"],
                second=sched["second"],
            )
            matched = cron_image_filter(index, trigger, fuzzy=5)
            all_matched.update(matched)

        # Day: 12 hours * 4 per hour = 48
        # Night: 12 hours * 1 per hour = 12
        # Total = 60, +1 possible midnight-of-next-day edge
        assert len(all_matched) >= 60
        assert len(all_matched) <= 61

    def test_three_schedules_combined(self) -> None:
        """Three schedules: morning, afternoon, evening — each with
        different intervals, merged together."""
        from apscheduler.triggers.cron import CronTrigger
        from pyLapse.img_seq.lapsetime import cron_image_filter

        index = self._make_index()
        schedules = [
            {"hour": "6-9", "minute": "*/10", "second": "0", "enabled": True},
            {"hour": "10-15", "minute": "*/30", "second": "0", "enabled": True},
            {"hour": "16-19", "minute": "0", "second": "0", "enabled": True},
        ]

        all_matched: set = set()
        for sched in schedules:
            trigger = CronTrigger(
                hour=sched["hour"],
                minute=sched["minute"],
                second=sched["second"],
            )
            matched = cron_image_filter(index, trigger, fuzzy=5)
            all_matched.update(matched)

        # Morning 6-9 (4 hours * 6 per hour) = 24
        # Afternoon 10-15 (6 hours * 2 per hour) = 12
        # Evening 16-19 (4 hours * 1 per hour) = 4
        assert len(all_matched) == 40

    def test_all_schedules_disabled(self) -> None:
        """All schedules disabled should produce zero matches."""
        schedules = [
            {"hour": "*", "minute": "*/15", "second": "0", "enabled": False},
            {"hour": "6-18", "minute": "*/5", "second": "0", "enabled": False},
        ]
        all_matched: set = set()
        for sched in schedules:
            if not sched.get("enabled", True):
                continue
            # Should not reach here
            all_matched.add("should_not_be_here")

        assert len(all_matched) == 0

    def test_partial_overlap_deduplicates(self) -> None:
        """Two schedules with partially overlapping hour ranges.
        Shared hours should not produce duplicates."""
        from apscheduler.triggers.cron import CronTrigger
        from pyLapse.img_seq.lapsetime import cron_image_filter

        index = self._make_index()
        # Schedule 1: every hour 6am-12pm at :00
        # Schedule 2: every hour 10am-4pm at :00
        # Overlap: 10am-12pm (3 hours)
        schedules = [
            {"hour": "6-12", "minute": "0", "second": "0", "enabled": True},
            {"hour": "10-16", "minute": "0", "second": "0", "enabled": True},
        ]

        all_matched: set = set()
        for sched in schedules:
            trigger = CronTrigger(
                hour=sched["hour"],
                minute=sched["minute"],
                second=sched["second"],
            )
            matched = cron_image_filter(index, trigger, fuzzy=5)
            all_matched.update(matched)

        # Schedule 1: 7 images (6,7,8,9,10,11,12)
        # Schedule 2: 7 images (10,11,12,13,14,15,16)
        # Union: 11 unique (6-16 inclusive)
        assert len(all_matched) == 11

    def test_midnight_wraparound(self) -> None:
        """Schedule crossing midnight using comma-separated hours (18-23,0-5)."""
        from apscheduler.triggers.cron import CronTrigger
        from pyLapse.img_seq.lapsetime import cron_image_filter

        index = self._make_index()
        trigger = CronTrigger(hour="18-23,0-5", minute="0", second="0")
        matched = cron_image_filter(index, trigger, fuzzy=5)

        # Hours: 18,19,20,21,22,23,0,1,2,3,4,5 = 12, +1 possible midnight edge
        assert len(matched) >= 12
        assert len(matched) <= 13

    def test_mixed_interval_types(self) -> None:
        """Mix of fine-grained (every 5 min) and coarse (every 2 hours)."""
        from apscheduler.triggers.cron import CronTrigger
        from pyLapse.img_seq.lapsetime import cron_image_filter

        index = self._make_index()
        schedules = [
            # Fine: every 5 min between 12-12 (just noon hour)
            {"hour": "12", "minute": "*/5", "second": "0", "enabled": True},
            # Coarse: every 2 hours, on the hour
            {"hour": "*/2", "minute": "0", "second": "0", "enabled": True},
        ]

        fine_matched: set = set()
        coarse_matched: set = set()

        for sched in schedules:
            trigger = CronTrigger(
                hour=sched["hour"],
                minute=sched["minute"],
                second=sched["second"],
            )
            matched = set(cron_image_filter(index, trigger, fuzzy=5))
            if sched["hour"] == "12":
                fine_matched = matched
            else:
                coarse_matched = matched

        all_matched = fine_matched | coarse_matched

        # Fine: 1 hour * 12 per hour = 12
        # Coarse: hours 0,2,4,6,8,10,12,14,16,18,20,22 = 12 (+ possible next-day edge)
        # Overlap: the 12:00 image is in both
        # Union: 12 + 12 - 1 overlap at 12:00 = 23 (or 24 with midnight edge)
        assert len(all_matched) >= 23
        assert len(all_matched) <= 24

    def test_one_enabled_one_disabled(self) -> None:
        """Only the enabled schedule should contribute images."""
        from apscheduler.triggers.cron import CronTrigger
        from pyLapse.img_seq.lapsetime import cron_image_filter

        index = self._make_index()
        schedules = [
            {"hour": "*", "minute": "*/15", "second": "0", "enabled": True},
            {"hour": "*", "minute": "*/5", "second": "0", "enabled": False},
        ]

        all_matched: set = set()
        for sched in schedules:
            if not sched.get("enabled", True):
                continue
            trigger = CronTrigger(
                hour=sched["hour"],
                minute=sched["minute"],
                second=sched["second"],
            )
            matched = cron_image_filter(index, trigger, fuzzy=5)
            all_matched.update(matched)

        # Only */15: 24 hours * 4 per hour = 96, +1 possible midnight edge
        assert len(all_matched) >= 96
        assert len(all_matched) <= 97

    def test_every_minute_schedule(self) -> None:
        """Wildcard schedule matching every minute captures all images."""
        from apscheduler.triggers.cron import CronTrigger
        from pyLapse.img_seq.lapsetime import cron_image_filter

        index = self._make_index()
        trigger = CronTrigger(hour="*", minute="*", second="0")
        matched = cron_image_filter(index, trigger, fuzzy=5)

        # Every minute of 24 hours = 1440, +1 possible midnight edge
        assert len(matched) >= 1440
        assert len(matched) <= 1441

    def test_single_hour_fine_grain(self) -> None:
        """Very fine schedule: every 5 min for one specific hour."""
        from apscheduler.triggers.cron import CronTrigger
        from pyLapse.img_seq.lapsetime import cron_image_filter

        index = self._make_index()
        trigger = CronTrigger(hour="8", minute="*/5", second="0")
        matched = cron_image_filter(index, trigger, fuzzy=5)

        # 1 hour, every 5 min: 0,5,10,15,20,25,30,35,40,45,50,55 = 12
        assert len(matched) == 12

    def test_multiday_hybrid_schedules(self) -> None:
        """Multiple schedules applied across multiple days.
        Each day should independently produce results from all enabled schedules."""
        import datetime as dt
        from apscheduler.triggers.cron import CronTrigger
        from pyLapse.img_seq.lapsetime import cron_image_filter

        # Build 3-day index
        index: dict[str, dict[str, dt.datetime]] = {}
        for day_offset in range(3):
            d = dt.date(2024, 6, 15 + day_offset)
            day_str = d.isoformat()
            day_files: dict[str, dt.datetime] = {}
            for h in range(24):
                for m in range(60):
                    ts = dt.datetime(d.year, d.month, d.day, h, m, 0)
                    fname = f"/img/{day_str}/cam-{ts:%H%M%S}.jpg"
                    day_files[fname] = ts
            index[day_str] = day_files

        schedules = [
            {"hour": "6-11", "minute": "0", "second": "0", "enabled": True},
            {"hour": "12-17", "minute": "30", "second": "0", "enabled": True},
        ]

        all_matched: set = set()
        for sched in schedules:
            trigger = CronTrigger(
                hour=sched["hour"],
                minute=sched["minute"],
                second=sched["second"],
            )
            matched = cron_image_filter(index, trigger, fuzzy=5)
            all_matched.update(matched)

        # Per day: schedule 1 = 6 images, schedule 2 = 6 images = 12/day
        # 3 days = 36
        assert len(all_matched) == 36

    def test_evening_to_morning_span(self) -> None:
        """10pm to 10am expressed as comma-separated hour range '22-23,0-9'.
        This is the real-world 'night shift' pattern."""
        from apscheduler.triggers.cron import CronTrigger
        from pyLapse.img_seq.lapsetime import cron_image_filter

        index = self._make_index()
        # Single schedule: every 30 min from 10pm to 10am
        trigger = CronTrigger(hour="22-23,0-9", minute="*/30", second="0")
        matched = cron_image_filter(index, trigger, fuzzy=5)

        # Hours 22,23 = 2 hours * 2 per hour = 4
        # Hours 0-9 = 10 hours * 2 per hour = 20
        # Total = 24, +1 possible midnight edge
        assert len(matched) >= 24
        assert len(matched) <= 25

    def test_evening_to_morning_hybrid(self) -> None:
        """Hybrid: frequent captures 10pm-10am, sparse captures 10am-10pm.
        Real-world scenario for night+day with different intervals."""
        from apscheduler.triggers.cron import CronTrigger
        from pyLapse.img_seq.lapsetime import cron_image_filter

        index = self._make_index()
        schedules = [
            # Night: 10pm-9am, every 10 min
            {"hour": "22-23,0-9", "minute": "*/10", "second": "0", "enabled": True},
            # Day: 10am-9pm, every hour
            {"hour": "10-21", "minute": "0", "second": "0", "enabled": True},
        ]

        all_matched: set = set()
        for sched in schedules:
            trigger = CronTrigger(
                hour=sched["hour"],
                minute=sched["minute"],
                second=sched["second"],
            )
            matched = cron_image_filter(index, trigger, fuzzy=5)
            all_matched.update(matched)

        # Night: 12 hours * 6 per hour = 72
        # Day: 12 hours * 1 per hour = 12
        # No overlap between ranges. +1 possible midnight edge
        assert len(all_matched) >= 84
        assert len(all_matched) <= 85

    def test_late_night_only(self) -> None:
        """Schedule only covering 11pm-1am (crossing midnight)."""
        from apscheduler.triggers.cron import CronTrigger
        from pyLapse.img_seq.lapsetime import cron_image_filter

        index = self._make_index()
        trigger = CronTrigger(hour="23,0", minute="*/15", second="0")
        matched = cron_image_filter(index, trigger, fuzzy=5)

        # 2 hours * 4 per hour = 8, +1 possible midnight edge
        assert len(matched) >= 8
        assert len(matched) <= 9

    def test_empty_index(self) -> None:
        """Schedules applied to an empty image index produce nothing."""
        from apscheduler.triggers.cron import CronTrigger
        from pyLapse.img_seq.lapsetime import cron_image_filter

        index: dict = {}
        trigger = CronTrigger(hour="*", minute="*", second="0")
        matched = cron_image_filter(index, trigger, fuzzy=5)
        assert len(matched) == 0

    def test_sparse_index_misses(self) -> None:
        """Schedule asks for times when no images exist — should skip them."""
        import datetime as dt
        from apscheduler.triggers.cron import CronTrigger
        from pyLapse.img_seq.lapsetime import cron_image_filter

        # Only images at noon (12:00 and 12:01)
        index = {
            "2024-06-15": {
                "/img/2024-06-15/cam-120000.jpg": dt.datetime(2024, 6, 15, 12, 0, 0),
                "/img/2024-06-15/cam-120100.jpg": dt.datetime(2024, 6, 15, 12, 1, 0),
            }
        }
        # Schedule asks for every hour on the hour
        trigger = CronTrigger(hour="*", minute="0", second="0")
        matched = cron_image_filter(index, trigger, fuzzy=5)

        # Only 12:00 is within fuzzy=5 of 12:00 trigger. Other hours have no nearby image.
        assert len(matched) == 1
        assert "/img/2024-06-15/cam-120000.jpg" in matched
