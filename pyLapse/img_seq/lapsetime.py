"""Time-based filtering and scheduling for image sets.

Provides utilities to select subsets of timestamped images based on
hour/minute ranges or APScheduler cron triggers with fuzzy matching.
"""
from __future__ import annotations

import datetime
import logging
import os
from typing import Optional

from dateutil import parser
from tzlocal import get_localzone

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Common time-span constants
# ---------------------------------------------------------------------------

NIGHT_HOURS: list[int] = [21, 22, 23, 0, 1, 2, 3, 4, 5]
DAWN_TO_DUSK: list[int] = list(range(6, 21))
EVERY_DAY_HOUR: list[int] = list(range(6, 20))
EVERY_TWO_HOURS: list[int] = list(range(0, 25, 2))
EVERY_DAY_TWO_HOURS: list[int] = [8, 10, 12, 14, 16, 20]
EVERY_TEN_MINUTES: list[int] = list(range(0, 51, 10))
EVERY_FIVE_MINUTES: list[int] = list(range(0, 56, 5))
EVERY_TWO_MINUTES: list[int] = list(range(0, 59, 2))
FIFTEEN_MINUTES: list[int] = [0, 15, 30, 45]


# Keep the class for backwards compatibility
class TimeSpans:
    """Legacy container for common time-frame constants.

    Prefer using the module-level constants (e.g. ``NIGHT_HOURS``) directly.
    """

    night = NIGHT_HOURS
    everytenmins = EVERY_TEN_MINUTES
    everytwohours = EVERY_TWO_HOURS
    everyfivemins = EVERY_FIVE_MINUTES
    everytwomins = EVERY_TWO_MINUTES
    everydayhour = EVERY_DAY_HOUR
    everyday2hours = EVERY_DAY_TWO_HOURS
    fifteenminutes = FIFTEEN_MINUTES
    dawntodusk = DAWN_TO_DUSK


# ---------------------------------------------------------------------------
# Dayslice filtering
# ---------------------------------------------------------------------------

ImageIndex = dict[str, dict[str, datetime.datetime]]
"""Type alias: ``{day_str: {filepath: datetime}}``."""


def dayslice(
    fileindex: ImageIndex,
    hourlist: list[int] | None = None,
    minutelist: list[int] | None = None,
    fuzzy: int = 5,
) -> list[str]:
    """Select images from *fileindex* matching the given hour/minute ranges.

    For each day in the index, picks the image closest to each target
    hour + minute combination within *fuzzy* minutes tolerance.

    Parameters
    ----------
    fileindex:
        Nested dict ``{day_str: {filepath: datetime}}``.
    hourlist:
        Hours to include (0-23). Defaults to all 24 hours.
    minutelist:
        Minutes within each hour to target. Defaults to ``[0]``.
    fuzzy:
        Maximum minute deviation allowed when matching.
    """
    if hourlist is None:
        hourlist = list(range(0, 24))
    if not minutelist:
        minutelist = [0]

    hourlist.sort()
    minutelist.sort()

    logger.debug("hour list: %s", hourlist)
    logger.debug("minute list: %s", minutelist)

    imageset: list[str] = []

    for day, files in fileindex.items():
        sorted_files = dict(sorted(files.items(), key=lambda x: (x[1], x[0])))

        for target_hour in hourlist:
            hour_minutes: list[int] = []
            hour_filenames: list[str] = []

            logger.debug("Looking for target hour: %d", target_hour)

            for filename, timestamp in sorted(sorted_files.items()):
                if timestamp.hour == target_hour:
                    hour_minutes.append(timestamp.minute)
                    hour_filenames.append(filename)

            logger.debug("hour filenames: %s", hour_filenames)
            logger.debug("hour minutes: %s", hour_minutes)

            if not hour_minutes:
                continue

            for target_minute in minutelist:
                logger.debug(
                    "Looking for minute %d in %s", target_minute, hour_minutes
                )
                match = find_nearest(hour_minutes, target_minute, fuzzyness=fuzzy)
                if match:
                    minute, idx = match
                    filename = hour_filenames[idx]
                    logger.debug(
                        "%s: %d is close enough to %d", filename, minute, target_minute
                    )
                    imageset.append(filename)

    imageset.sort()
    return imageset


# ---------------------------------------------------------------------------
# Timestamp helpers
# ---------------------------------------------------------------------------


def get_timestamp_from_file(filepath: str, fuzzy: bool = True) -> datetime.datetime:
    """Parse a timestamp from a file's basename using ``dateutil``."""
    filename = os.path.basename(filepath)
    return parser.parse(filename, fuzzy=fuzzy)


def find_nearest(
    array: list[int], value: int, fuzzyness: int = 5
) -> Optional[tuple[int, int]]:
    """Find the element in *array* nearest to *value* within *fuzzyness*.

    Returns ``(element, index)`` or ``None`` if nothing is close enough.
    """
    if not array:
        return None
    idx, item = min(enumerate(array), key=lambda x: abs(x[1] - value))
    if abs(value - item) <= fuzzyness:
        return item, idx
    return None


def find_nearest_dt(
    target_dt: datetime.datetime,
    dtlist: list[datetime.datetime],
    fuzzy: int = 5,
) -> Optional[datetime.datetime]:
    """Find the datetime in *dtlist* closest to *target_dt* within *fuzzy* minutes."""
    candidates = [x for x in dtlist if (x - target_dt).seconds <= fuzzy * 60]
    if not candidates:
        return None
    return min(candidates, key=lambda x: x - target_dt)


# ---------------------------------------------------------------------------
# Cron-based filtering
# ---------------------------------------------------------------------------


def get_fire_times(
    crontrigger: object, day: datetime.datetime
) -> list[datetime.datetime]:
    """Return all fire times for *crontrigger* on the given *day*."""
    day = datetime.datetime(day.year, day.month, day.day).replace(
        tzinfo=get_localzone()
    )
    last_fire = day - datetime.timedelta(microseconds=1)
    times: list[datetime.datetime] = []

    cur_day = day
    while cur_day.date() == day.date():
        now = last_fire + datetime.timedelta(microseconds=1)
        next_fire = crontrigger.get_next_fire_time(last_fire, now)
        times.append(next_fire.replace(tzinfo=None))
        cur_day = next_fire
        last_fire = next_fire

    return times


def cron_image_filter(
    imageindex: ImageIndex,
    cron_trigger: object,
    fuzzy: int = 5,
) -> list[str]:
    """Filter images using an APScheduler *cron_trigger*.

    For each day in *imageindex*, determines the trigger's fire times and
    picks the closest matching image within *fuzzy* minutes.
    """
    images: list[str] = []

    for day, files in sorted(imageindex.items()):
        dt_day = datetime.datetime.strptime(day, "%Y-%m-%d").replace(
            tzinfo=get_localzone()
        )
        next_day = cron_trigger.get_next_fire_time(dt_day, dt_day)
        if next_day.date() != dt_day.date():
            continue

        fire_times = get_fire_times(cron_trigger, dt_day)
        day_set = dict(sorted(files.items(), key=lambda x: (x[1], x[0])))
        reverse_day_set = {v: k for k, v in day_set.items()}
        day_timestamps = list(day_set.values())

        time_keys = [find_nearest_dt(ft, day_timestamps, fuzzy) for ft in fire_times]
        for key in time_keys:
            if key is not None:
                images.append(reverse_day_set[key])

    return images
