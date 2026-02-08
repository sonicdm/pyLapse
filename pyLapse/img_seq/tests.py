"""Unit tests for the img_seq package.

Run with: ``pytest pyLapse/img_seq/tests.py -v``
"""
from __future__ import annotations

import datetime
import os
import re
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from apscheduler.triggers.cron import CronTrigger
from PIL import Image

from pyLapse.img_seq.lapsetime import (
    dayslice,
    find_nearest,
    find_nearest_dt,
    get_fire_times,
    get_timestamp_from_file,
    cron_image_filter,
)
from pyLapse.img_seq.utils import is_image_url, clear_target, ParallelExecutor
from pyLapse.img_seq.image import (
    ImageSet,
    ImageIO,
    save_image,
    prepare_output_dir,
    imageset_load,
    FORMATS,
)


# ---------------------------------------------------------------------------
# Helpers to build mock image indices
# ---------------------------------------------------------------------------


def _make_image_index(
    days: list[str],
    hours: list[int],
    minutes: list[int],
) -> dict[str, dict[str, datetime.datetime]]:
    """Build a synthetic image index for testing.

    Returns ``{day_str: {filepath: datetime}}``.
    """
    index: dict[str, dict[str, datetime.datetime]] = {}
    for day_str in days:
        year, month, day = (int(x) for x in day_str.split("-"))
        day_files: dict[str, datetime.datetime] = {}
        for h in hours:
            for m in minutes:
                ts = datetime.datetime(year, month, day, h, m, 0)
                filename = f"/images/{day_str}/cam-{ts:%Y-%m-%d-%H%M%S}.jpg"
                day_files[filename] = ts
        index[day_str] = day_files
    return index


# ---------------------------------------------------------------------------
# Tests: lapsetime.find_nearest
# ---------------------------------------------------------------------------


class TestFindNearest:
    def test_exact_match(self) -> None:
        result = find_nearest([0, 15, 30, 45], 15, fuzzyness=5)
        assert result == (15, 1)

    def test_fuzzy_match(self) -> None:
        result = find_nearest([0, 15, 30, 45], 17, fuzzyness=5)
        assert result == (15, 1)

    def test_no_match_outside_fuzzy(self) -> None:
        result = find_nearest([0, 30], 15, fuzzyness=5)
        assert result is None

    def test_empty_array(self) -> None:
        result = find_nearest([], 10, fuzzyness=5)
        assert result is None

    def test_picks_closest(self) -> None:
        result = find_nearest([0, 10, 20, 30], 12, fuzzyness=5)
        assert result == (10, 1)


# ---------------------------------------------------------------------------
# Tests: lapsetime.find_nearest_dt
# ---------------------------------------------------------------------------


class TestFindNearestDt:
    def test_exact_match(self) -> None:
        target = datetime.datetime(2024, 1, 1, 12, 0)
        candidates = [
            datetime.datetime(2024, 1, 1, 12, 0),
            datetime.datetime(2024, 1, 1, 12, 5),
        ]
        assert find_nearest_dt(target, candidates, fuzzy=5) == target

    def test_within_fuzzy(self) -> None:
        target = datetime.datetime(2024, 1, 1, 12, 0)
        close = datetime.datetime(2024, 1, 1, 12, 3)
        result = find_nearest_dt(target, [close], fuzzy=5)
        assert result == close

    def test_no_match(self) -> None:
        target = datetime.datetime(2024, 1, 1, 12, 0)
        far = datetime.datetime(2024, 1, 1, 12, 30)
        result = find_nearest_dt(target, [far], fuzzy=5)
        assert result is None


# ---------------------------------------------------------------------------
# Tests: lapsetime.dayslice
# ---------------------------------------------------------------------------


class TestDayslice:
    def test_basic_hourly(self) -> None:
        index = _make_image_index(
            ["2024-01-01"], hours=list(range(24)), minutes=[0, 15, 30, 45]
        )
        result = dayslice(index, hourlist=[6, 12, 18], minutelist=[0])
        assert len(result) == 3
        for path in result:
            assert "06" in path or "12" in path or "18" in path

    def test_multiple_minutes(self) -> None:
        index = _make_image_index(
            ["2024-01-01"], hours=[10], minutes=[0, 15, 30, 45]
        )
        result = dayslice(index, hourlist=[10], minutelist=[0, 30])
        assert len(result) == 2

    def test_multi_day(self) -> None:
        index = _make_image_index(
            ["2024-01-01", "2024-01-02"],
            hours=[8, 12],
            minutes=[0],
        )
        result = dayslice(index, hourlist=[8, 12], minutelist=[0])
        assert len(result) == 4

    def test_no_match(self) -> None:
        index = _make_image_index(["2024-01-01"], hours=[10], minutes=[0])
        result = dayslice(index, hourlist=[22], minutelist=[0])
        assert result == []

    def test_defaults_to_all_hours(self) -> None:
        index = _make_image_index(["2024-01-01"], hours=[0, 6, 12, 18], minutes=[0])
        result = dayslice(index)
        assert len(result) == 4


# ---------------------------------------------------------------------------
# Tests: lapsetime.cron_image_filter
# ---------------------------------------------------------------------------


class TestCronImageFilter:
    def test_every_hour(self) -> None:
        index = _make_image_index(
            ["2024-06-15"], hours=list(range(24)), minutes=[0, 15, 30, 45]
        )
        trigger = CronTrigger(minute="0")
        result = cron_image_filter(index, trigger, fuzzy=5)
        # Should pick ~24 images (one per hour at minute 0)
        assert len(result) >= 20  # Allow some fuzzy margin

    def test_limited_hours(self) -> None:
        index = _make_image_index(
            ["2024-06-15"], hours=list(range(24)), minutes=[0, 30]
        )
        trigger = CronTrigger(hour="6-12", minute="0")
        result = cron_image_filter(index, trigger, fuzzy=5)
        assert len(result) >= 5


# ---------------------------------------------------------------------------
# Tests: utils.is_image_url
# ---------------------------------------------------------------------------


class TestIsImageUrl:
    def test_valid_jpg(self) -> None:
        assert is_image_url("http://192.168.1.100/photo.jpg") is True

    def test_valid_png_https(self) -> None:
        assert is_image_url("https://example.com/image.png") is True

    def test_valid_jpeg(self) -> None:
        assert is_image_url("http://cam.local/snap.jpeg") is True

    def test_valid_with_query(self) -> None:
        assert is_image_url("https://example.com/photo.jpg?width=1920") is True

    def test_invalid_no_extension(self) -> None:
        assert is_image_url("http://example.com/video") is False

    def test_invalid_non_image(self) -> None:
        assert is_image_url("http://example.com/file.txt") is False

    def test_invalid_no_protocol(self) -> None:
        assert is_image_url("example.com/photo.jpg") is False


# ---------------------------------------------------------------------------
# Tests: image.ImageSet.index_files
# ---------------------------------------------------------------------------


class TestImageSetIndexFiles:
    def test_parses_standard_filenames(self) -> None:
        imgset = ImageSet()
        files = [
            "/images/Outside 2024-01-15-120000.jpg",
            "/images/Outside 2024-01-15-130500.jpg",
            "/images/Outside 2024-01-16-080000.jpg",
        ]
        result = imgset.index_files(files)
        assert "2024-01-15" in result
        assert "2024-01-16" in result
        assert imgset.imagecount == 3

    def test_skips_non_matching(self) -> None:
        imgset = ImageSet()
        files = [
            "/images/random_file.jpg",
            "/images/Outside 2024-01-15-120000.jpg",
        ]
        imgset.index_files(files)
        assert imgset.imagecount == 1

    def test_custom_pattern(self) -> None:
        custom_re = re.compile(
            r"(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})_"
            r"(?P<hour>\d{2})(?P<minute>\d{2})(?P<seconds>\d{2})"
        )
        imgset = ImageSet()
        files = ["/images/20240115_120000.jpg"]
        result = imgset.index_files(files, filematch=custom_re)
        assert "2024-01-15" in result
        assert imgset.imagecount == 1

    def test_no_seconds_defaults_to_zero(self) -> None:
        imgset = ImageSet()
        files = ["/images/cam-2024-01-15-1200.jpg"]
        result = imgset.index_files(files)
        assert imgset.imagecount == 1
        ts = list(result["2024-01-15"].values())[0]
        assert ts.second == 0


# ---------------------------------------------------------------------------
# Tests: image.ImageSet
# ---------------------------------------------------------------------------


class TestImageSet:
    def test_import_from_list(self) -> None:
        files = [
            "/images/Outside 2024-01-15-120000.jpg",
            "/images/Outside 2024-01-15-130500.jpg",
        ]
        imgset = ImageSet().import_from_list(files)
        assert imgset.imagecount == 2
        assert "2024-01-15" in imgset.days

    def test_days_property(self) -> None:
        files = [
            "/images/cam-2024-01-15-120000.jpg",
            "/images/cam-2024-01-16-120000.jpg",
            "/images/cam-2024-01-14-120000.jpg",
        ]
        imgset = ImageSet().import_from_list(files)
        assert imgset.days == ["2024-01-14", "2024-01-15", "2024-01-16"]

    def test_get_day_files_by_string(self) -> None:
        files = ["/images/cam-2024-01-15-120000.jpg"]
        imgset = ImageSet().import_from_list(files)
        day_files = imgset.get_day_files("2024-01-15")
        assert len(day_files) == 1

    def test_get_day_files_by_index(self) -> None:
        files = [
            "/images/cam-2024-01-15-120000.jpg",
            "/images/cam-2024-01-16-120000.jpg",
        ]
        imgset = ImageSet().import_from_list(files)
        day_files = imgset.get_day_files(0)
        assert len(day_files) == 1

    def test_get_day_files_missing_raises(self) -> None:
        files = ["/images/cam-2024-01-15-120000.jpg"]
        imgset = ImageSet().import_from_list(files)
        with pytest.raises(KeyError):
            imgset.get_day_files("2099-01-01")


# ---------------------------------------------------------------------------
# Tests: cameras.Camera
# ---------------------------------------------------------------------------


class TestCamera:
    def test_valid_creation(self) -> None:
        from pyLapse.img_seq.cameras import Camera

        cam = Camera("Test", "http://192.168.1.1/photo.jpg")
        assert cam.name == "Test"
        assert cam.imageurl == "http://192.168.1.1/photo.jpg"

    def test_invalid_url_raises(self) -> None:
        from pyLapse.img_seq.cameras import Camera

        with pytest.raises(ValueError):
            Camera("Bad", "not-a-url")

    def test_set_invalid_url_raises(self) -> None:
        from pyLapse.img_seq.cameras import Camera

        cam = Camera("Test", "http://192.168.1.1/photo.jpg")
        with pytest.raises(ValueError):
            cam.imageurl = "invalid"


# ---------------------------------------------------------------------------
# Tests: utils.ParallelExecutor
# ---------------------------------------------------------------------------


class TestParallelExecutor:
    def test_run_threaded(self) -> None:
        def collect(item: int, _idx: int) -> int:
            return item * 2

        executor = ParallelExecutor(workers=2, debug=True)
        results = executor.run_threaded(collect, [1, 2, 3])
        assert sorted(results) == [2, 4, 6]

    def test_run_threaded_with_kwargs(self) -> None:
        def add(item: int, _idx: int, offset: int = 0) -> int:
            return item + offset

        executor = ParallelExecutor(workers=2, debug=True)
        results = executor.run_threaded(add, [10, 20], offset=5)
        assert sorted(results) == [15, 25]


# ---------------------------------------------------------------------------
# Tests: collections.Collection (unit-level)
# ---------------------------------------------------------------------------


class TestCollection:
    def test_add_export(self, tmp_path: Path) -> None:
        """Test that exports are registered correctly (uses empty dir)."""
        from pyLapse.img_seq.collections import Collection

        # Create a dummy collection dir with no images
        src = tmp_path / "source"
        src.mkdir()
        exp = tmp_path / "export"
        exp.mkdir()

        coll = Collection("test", str(exp), str(src))
        coll.add_export("hourly", "hourly", prefix="Test ", hour="*", minute="0")
        assert "hourly" in coll.exports
        assert coll.exports["hourly"].prefix == "Test "

    def test_str(self, tmp_path: Path) -> None:
        from pyLapse.img_seq.collections import Collection

        src = tmp_path / "source"
        src.mkdir()
        exp = tmp_path / "export"
        exp.mkdir()
        coll = Collection("My Cam", str(exp), str(src))
        s = str(coll)
        assert "My Cam" in s
        assert "Images: 0" in s

    def test_export_all_empty(self, tmp_path: Path) -> None:
        """export_all with no exports registered should not error."""
        from pyLapse.img_seq.collections import Collection

        src = tmp_path / "source"
        src.mkdir()
        exp = tmp_path / "export"
        exp.mkdir()
        coll = Collection("test", str(exp), str(src))
        coll.export_all()  # no-op, should not raise


# ---------------------------------------------------------------------------
# Tests: collections.Export
# ---------------------------------------------------------------------------


class TestExport:
    def test_str(self) -> None:
        from pyLapse.img_seq.collections import Export

        imgset = ImageSet()
        export = Export("Day", "day_subdir", imgset, prefix="Cam ", desc="Daytime")
        s = str(export)
        assert "Day" in s
        assert "day_subdir" in s
        assert "Daytime" in s
        assert "Cam " in s


# ---------------------------------------------------------------------------
# Tests: lapsetime.get_timestamp_from_file
# ---------------------------------------------------------------------------


class TestGetTimestampFromFile:
    def test_parses_timestamp(self) -> None:
        ts = get_timestamp_from_file("Outside 2024-01-15-120000.jpg")
        assert ts.year == 2024
        assert ts.month == 1
        assert ts.day == 15

    def test_parses_with_path(self) -> None:
        ts = get_timestamp_from_file("/images/cam-2024-06-30-083000.jpg")
        assert ts.year == 2024
        assert ts.month == 6
        assert ts.day == 30


# ---------------------------------------------------------------------------
# Tests: lapsetime.get_fire_times
# ---------------------------------------------------------------------------


class TestGetFireTimes:
    def test_hourly_trigger(self) -> None:
        trigger = CronTrigger(minute="0")
        day = datetime.datetime(2024, 6, 15)
        times = get_fire_times(trigger, day)
        # Includes 00:00 of the next day at the boundary, so 25
        assert len(times) == 25
        assert all(t.minute == 0 for t in times)

    def test_every_30min_trigger(self) -> None:
        trigger = CronTrigger(minute="*/30")
        day = datetime.datetime(2024, 6, 15)
        times = get_fire_times(trigger, day)
        # Includes 00:00 of the next day at the boundary, so 49
        assert len(times) == 49

    def test_limited_hours(self) -> None:
        trigger = CronTrigger(hour="9-17", minute="0")
        day = datetime.datetime(2024, 6, 15)
        times = get_fire_times(trigger, day)
        # 9 hours + wraps to 9:00 next day at boundary = 10
        assert len(times) == 10


# ---------------------------------------------------------------------------
# Tests: lapsetime edge cases
# ---------------------------------------------------------------------------


class TestFindNearestDtEdgeCases:
    def test_empty_list(self) -> None:
        target = datetime.datetime(2024, 1, 1, 12, 0)
        assert find_nearest_dt(target, [], fuzzy=5) is None

    def test_picks_closest_of_multiple(self) -> None:
        target = datetime.datetime(2024, 1, 1, 12, 0)
        candidates = [
            datetime.datetime(2024, 1, 1, 12, 1),
            datetime.datetime(2024, 1, 1, 12, 4),
        ]
        result = find_nearest_dt(target, candidates, fuzzy=5)
        assert result == datetime.datetime(2024, 1, 1, 12, 1)


class TestCronImageFilterMultiDay:
    def test_multi_day_filter(self) -> None:
        index = _make_image_index(
            ["2024-06-15", "2024-06-16", "2024-06-17"],
            hours=list(range(24)),
            minutes=[0],
        )
        trigger = CronTrigger(hour="12", minute="0")
        result = cron_image_filter(index, trigger, fuzzy=5)
        # One match per day at noon (plus possible boundary duplicates)
        assert len(result) >= 3
        assert all("120000" in r for r in result)

    def test_no_matching_day(self) -> None:
        """A trigger that doesn't fire on the index's day yields nothing."""
        index = _make_image_index(["2024-06-15"], hours=[10], minutes=[0])
        # day_of_week=0 is Monday; 2024-06-15 is Saturday
        trigger = CronTrigger(day_of_week="0", minute="0")
        result = cron_image_filter(index, trigger, fuzzy=5)
        assert result == []


# ---------------------------------------------------------------------------
# Tests: ImageSet.filter_images
# ---------------------------------------------------------------------------


class TestImageSetFilterImages:
    def test_filter_reduces_count(self) -> None:
        files = [
            f"/img/cam-2024-01-15-{h:02d}0000.jpg"
            for h in range(24)
        ]
        imgset = ImageSet().import_from_list(files)
        assert imgset.imagecount == 24

        imgset.filter_images(hourlist=[8, 12, 16])
        assert len(imgset.filtered_images) == 3

    def test_filter_with_minutes(self) -> None:
        files = [
            f"/img/cam-2024-01-15-10{m:02d}00.jpg"
            for m in [0, 15, 30, 45]
        ]
        imgset = ImageSet().import_from_list(files)
        imgset.filter_images(hourlist=[10], minutelist=[0, 30])
        assert len(imgset.filtered_images) == 2


# ---------------------------------------------------------------------------
# Tests: ImageSet with real filesystem (import_folder / refresh_folder)
# ---------------------------------------------------------------------------


class TestImageSetFilesystem:
    def test_import_folder(self, tmp_path: Path) -> None:
        for h in [8, 12, 16]:
            (tmp_path / f"cam-2024-03-10-{h:02d}0000.jpg").write_bytes(b"fake")
        imgset = imageset_load(str(tmp_path))
        assert imgset.imagecount == 3
        assert imgset.inputdir == str(tmp_path)

    def test_import_folder_empty(self, tmp_path: Path) -> None:
        imgset = imageset_load(str(tmp_path))
        assert imgset.imagecount == 0

    def test_refresh_folder(self, tmp_path: Path) -> None:
        (tmp_path / "cam-2024-03-10-120000.jpg").write_bytes(b"fake")
        imgset = imageset_load(str(tmp_path))
        assert imgset.imagecount == 1

        # Add another file and refresh
        (tmp_path / "cam-2024-03-10-140000.jpg").write_bytes(b"fake")
        imgset.refresh_folder()
        assert imgset.imagecount == 2

    def test_refresh_folder_noop_without_import(self) -> None:
        imgset = ImageSet()
        imgset.refresh_folder()  # should not raise


# ---------------------------------------------------------------------------
# Tests: ImageSet.__str__ / __repr__
# ---------------------------------------------------------------------------


class TestImageSetRepr:
    def test_str(self) -> None:
        imgset = ImageSet()
        imgset.inputdir = "/some/path"
        assert "ImageSet(/some/path)" == str(imgset)

    def test_repr(self) -> None:
        files = ["/img/cam-2024-01-15-120000.jpg"]
        imgset = ImageSet().import_from_list(files)
        r = repr(imgset)
        assert "1 images" in r

    def test_get_day_files_bad_type(self) -> None:
        files = ["/img/cam-2024-01-15-120000.jpg"]
        imgset = ImageSet().import_from_list(files)
        with pytest.raises(TypeError):
            imgset.get_day_files(3.14)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Tests: Camera extras
# ---------------------------------------------------------------------------


class TestCameraExtras:
    def test_repr(self) -> None:
        from pyLapse.img_seq.cameras import Camera

        cam = Camera("FrontDoor", "http://10.0.0.1/snap.jpg", location="porch")
        assert "<Camera: FrontDoor>" == repr(cam)

    def test_str(self) -> None:
        from pyLapse.img_seq.cameras import Camera

        cam = Camera("FrontDoor", "http://10.0.0.1/snap.jpg")
        s = str(cam)
        assert "FrontDoor" in s
        assert "http://10.0.0.1/snap.jpg" in s

    def test_location(self) -> None:
        from pyLapse.img_seq.cameras import Camera

        cam = Camera("Test", "http://10.0.0.1/snap.jpg", location="garage")
        assert cam.location == "garage"

    def test_url_setter_valid(self) -> None:
        from pyLapse.img_seq.cameras import Camera

        cam = Camera("Test", "http://10.0.0.1/snap.jpg")
        cam.imageurl = "https://other.cam/photo.png"
        assert cam.imageurl == "https://other.cam/photo.png"


# ---------------------------------------------------------------------------
# Tests: image.save_image (with real PIL images)
# ---------------------------------------------------------------------------


class TestSaveImage:
    def test_saves_jpg(self, tmp_path: Path) -> None:
        img = Image.new("RGB", (100, 100), color=(255, 0, 0))
        ts = datetime.datetime(2024, 6, 15, 12, 0, 0)
        result = save_image(img, str(tmp_path), ts)
        assert "Saved" in result
        saved_files = list(tmp_path.glob("*.jpg"))
        assert len(saved_files) == 1
        assert "2024-06-15" in saved_files[0].name

    def test_saves_with_prefix(self, tmp_path: Path) -> None:
        img = Image.new("RGB", (100, 100))
        ts = datetime.datetime(2024, 1, 1, 8, 30, 0)
        save_image(img, str(tmp_path), ts, prefix="OutCam ")
        saved = list(tmp_path.glob("*.jpg"))
        assert len(saved) == 1
        assert saved[0].name.startswith("OutCam ")

    def test_saves_with_resize(self, tmp_path: Path) -> None:
        img = Image.new("RGB", (4000, 3000))
        ts = datetime.datetime(2024, 1, 1, 12, 0)
        save_image(img, str(tmp_path), ts, resize=True, resolution=(200, 150))
        saved = list(tmp_path.glob("*.jpg"))
        reopened = Image.open(saved[0])
        assert reopened.width <= 200
        assert reopened.height <= 150

    def test_creates_output_dir(self, tmp_path: Path) -> None:
        nested = tmp_path / "a" / "b" / "c"
        img = Image.new("RGB", (10, 10))
        ts = datetime.datetime(2024, 1, 1, 12, 0)
        save_image(img, str(nested), ts)
        assert nested.is_dir()
        assert len(list(nested.glob("*.jpg"))) == 1


# ---------------------------------------------------------------------------
# Tests: ImageIO.timestamp_image
# ---------------------------------------------------------------------------


class TestTimestampImage:
    def test_draws_text(self) -> None:
        img = Image.new("RGB", (400, 100), color=(0, 0, 0))
        ts = datetime.datetime(2024, 6, 15, 14, 30)
        result = ImageIO.timestamp_image(img, ts, size=20)
        assert isinstance(result, Image.Image)
        # The image should have been modified (not all black anymore)
        pixels = list(result.getdata()) if not hasattr(result, "get_flattened_data") else list(result.get_flattened_data())
        non_black = [p for p in pixels if p != (0, 0, 0)]
        assert len(non_black) > 0

    def test_custom_format(self) -> None:
        img = Image.new("RGB", (200, 50), color=(0, 0, 0))
        ts = datetime.datetime(2024, 12, 25, 0, 0)
        result = ImageIO.timestamp_image(
            img, ts, timestampformat="%Y", size=20
        )
        assert isinstance(result, Image.Image)


# ---------------------------------------------------------------------------
# Tests: ImageIO.fetch_image_from_url (mocked)
# ---------------------------------------------------------------------------


class TestFetchImageFromUrl:
    def test_success(self) -> None:
        fake_img = Image.new("RGB", (10, 10))
        import io

        buf = io.BytesIO()
        fake_img.save(buf, "JPEG")
        fake_bytes = buf.getvalue()

        with patch("pyLapse.img_seq.image.urlopen") as mock_urlopen:
            mock_urlopen.return_value.read.return_value = fake_bytes
            result = ImageIO.fetch_image_from_url("http://fake.cam/photo.jpg")
        assert isinstance(result, Image.Image)

    def test_network_error_raises(self) -> None:
        from urllib.error import URLError

        with patch("pyLapse.img_seq.image.urlopen", side_effect=URLError("timeout")):
            with pytest.raises(URLError):
                ImageIO.fetch_image_from_url("http://fake.cam/photo.jpg")


# ---------------------------------------------------------------------------
# Tests: image.prepare_output_dir
# ---------------------------------------------------------------------------


class TestPrepareOutputDir:
    def test_creates_new_dir(self, tmp_path: Path) -> None:
        target = tmp_path / "new_output"
        prepare_output_dir(str(target), "jpg")
        assert target.is_dir()

    def test_clears_existing_dir(self, tmp_path: Path) -> None:
        target = tmp_path / "output"
        target.mkdir()
        (target / "old1.jpg").write_bytes(b"fake")
        (target / "old2.jpg").write_bytes(b"fake")
        assert len(list(target.glob("*.jpg"))) == 2

        prepare_output_dir(str(target), "jpg")
        assert len(list(target.glob("*.jpg"))) == 0

    def test_only_clears_matching_ext(self, tmp_path: Path) -> None:
        target = tmp_path / "output"
        target.mkdir()
        (target / "keep.png").write_bytes(b"fake")
        (target / "remove.jpg").write_bytes(b"fake")

        prepare_output_dir(str(target), "jpg")
        assert (target / "keep.png").exists()
        assert not (target / "remove.jpg").exists()


# ---------------------------------------------------------------------------
# Tests: utils.clear_target
# ---------------------------------------------------------------------------


class TestClearTarget:
    def test_deletes_matching_files(self, tmp_path: Path) -> None:
        for i in range(5):
            (tmp_path / f"img_{i}.jpg").write_bytes(b"data")
        (tmp_path / "keep.txt").write_bytes(b"data")

        clear_target(str(tmp_path), "*.jpg")
        assert len(list(tmp_path.glob("*.jpg"))) == 0
        assert (tmp_path / "keep.txt").exists()

    def test_noop_on_empty_dir(self, tmp_path: Path) -> None:
        clear_target(str(tmp_path), "*.jpg")  # should not raise


# ---------------------------------------------------------------------------
# Tests: FORMATS constant
# ---------------------------------------------------------------------------


class TestFormats:
    def test_jpg_maps_to_jpeg(self) -> None:
        assert FORMATS["jpg"] == "JPEG"
        assert FORMATS["jpeg"] == "JPEG"

    def test_png(self) -> None:
        assert FORMATS["png"] == "PNG"

    def test_unknown_defaults(self) -> None:
        assert FORMATS.get("bmp", "JPEG") == "JPEG"


# ---------------------------------------------------------------------------
# Tests: video module error paths
# ---------------------------------------------------------------------------


class TestVideoErrors:
    def test_missing_input_dir(self, tmp_path: Path) -> None:
        from pyLapse.img_seq.video import render_sequence_to_video

        with pytest.raises(FileNotFoundError):
            render_sequence_to_video(
                str(tmp_path / "nonexistent"), str(tmp_path / "out.mp4")
            )

    def test_no_matching_images(self, tmp_path: Path) -> None:
        from pyLapse.img_seq.video import render_sequence_to_video

        with pytest.raises(ValueError, match="No images matching"):
            render_sequence_to_video(str(tmp_path), str(tmp_path / "out.mp4"))

    def test_ffmpeg_not_found(self) -> None:
        from pyLapse.img_seq.video import _get_ffmpeg_path

        with patch("pyLapse.img_seq.video.Path.is_file", return_value=False):
            with pytest.raises(FileNotFoundError, match="ffmpeg not found"):
                _get_ffmpeg_path()
