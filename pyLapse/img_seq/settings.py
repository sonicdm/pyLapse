"""Example configuration presets for common camera setups.

These are sample configurations showing how to define collection exports.
Replace the placeholder paths with your actual directories before use.
"""
from __future__ import annotations

from pyLapse.img_seq.lapsetime import FIFTEEN_MINUTES, NIGHT_HOURS

# ---------------------------------------------------------------------------
# Example: "Outside" camera
# ---------------------------------------------------------------------------

outside: dict = dict(
    name="Outside 1",
    sequence_storage=r"F:\Timelapse\Image Sequences\Outside 1",  # TODO: update path
    inputdir=r"F:\Timelapse\2016\Outside 1",  # TODO: update path
    exports=dict(
        full=dict(
            subdir="Full",
            minutelist=[0],
            span="Full Time Span 15 Minute Intervals - Outside",
            drawtimestamp=True,
            optimize=True,
            prefix="Outside ",
            enabled=True,
        ),
        all=dict(
            subdir="All Frames",
            allframes=True,
            span="Every Frame - Outside",
            drawtimestamp=True,
            optimize=True,
            prefix="Outside ",
            enabled=False,
        ),
        day=dict(
            subdir="Day",
            hourlist=list(range(5, 22)),
            minutelist=FIFTEEN_MINUTES,
            span="Day Time Only 5am to 9pm - 15 minute intervals - Outside",
            drawtimestamp=True,
            optimize=True,
            prefix="Outside ",
            enabled=True,
        ),
        night=dict(
            subdir="Night",
            hourlist=NIGHT_HOURS,
            minutelist=FIFTEEN_MINUTES,
            span="Night Time Only 9pm to 5am - 15 minute intervals - Outside",
            drawtimestamp=True,
            optimize=True,
            prefix="Outside ",
            enabled=True,
        ),
    ),
)

# ---------------------------------------------------------------------------
# Example: "Seed Closet" camera
# ---------------------------------------------------------------------------

seed_closet: dict = dict(
    name="Seed Closet",
    sequence_storage=r"F:\Timelapse\Image Sequences\Seed Closet",  # TODO: update path
    inputdir=r"F:\Timelapse\2016\Seedling Closet",  # TODO: update path
    exports=dict(
        full=dict(
            subdir="Full",
            minutelist=[0],
            span="Full Time Span 15 Minute Intervals - Seed Closet",
            drawtimestamp=True,
            optimize=True,
            prefix="Seed Closet ",
            enabled=True,
        ),
        all=dict(
            subdir="All Frames",
            allframes=True,
            span="Every Frame - Seed Closet",
            drawtimestamp=True,
            optimize=True,
            prefix="Seed Closet ",
            enabled=False,
        ),
        day=dict(
            subdir="Day",
            hourlist=list(range(5, 22)),
            minutelist=FIFTEEN_MINUTES,
            span="Day Time Only 5am to 9pm - Seed Closet",
            drawtimestamp=True,
            optimize=True,
            prefix="Seed Closet ",
            enabled=True,
        ),
        night=dict(
            subdir="Night",
            hourlist=NIGHT_HOURS,
            minutelist=FIFTEEN_MINUTES,
            span="Night Time Only 9pm to 5am - Seed Closet",
            drawtimestamp=True,
            optimize=True,
            prefix="Seed Closet ",
            enabled=True,
        ),
    ),
)
