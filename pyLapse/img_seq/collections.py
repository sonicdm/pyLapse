"""Image collections and cron-based export definitions."""
from __future__ import annotations

import logging
import os
import re
from os.path import basename, join
from typing import Any, Optional

from apscheduler.triggers.cron import CronTrigger

from pyLapse.img_seq.image import ImageIO, ImageSet, imageset_load, prepare_output_dir
from pyLapse.img_seq.lapsetime import cron_image_filter

logger = logging.getLogger(__name__)

CRON_ARG_NAMES: tuple[str, ...] = (
    "year", "month", "day", "week", "day_of_week", "hour", "minute", "second",
)

WRITER_OPTIONS: tuple[str, ...] = (
    "resize", "quality", "optimize", "resolution", "drawtimestamp",
    "timestampformat", "timestampfont", "timestampfontsize", "timestampcolor",
    "timestamppos", "prefix", "zeropadding",
)


class Collection:
    """A named group of timestamped images with configurable export presets.

    Parameters
    ----------
    name : str
        Human-readable collection name.
    export_dir : str
        Root directory for exported image sequences.
    collection_dir : str
        Source directory containing the raw captured images.
    ext : str
        Image file extension to match (default ``'jpg'``).
    mask : str
        Glob mask for filenames (default ``'*'``).
    filematch : re.Pattern or None
        Optional compiled regex for parsing timestamps from filenames.
    """

    def __init__(
        self,
        name: str,
        export_dir: str,
        collection_dir: str,
        ext: str = "jpg",
        mask: str = "*",
        filematch: Optional[re.Pattern[str]] = None,
    ) -> None:
        self.name = name
        self.collection_dir = collection_dir
        self.export_dir = export_dir
        self.exports: dict[str, Export] = {}
        self.images: ImageSet = imageset_load(self.collection_dir, ext, mask, filematch)

    def __str__(self) -> str:
        return (
            f"Collection: {self.name}, "
            f"Location: {self.collection_dir}, "
            f"Images: {self.images.imagecount}"
        )

    def add_export(
        self,
        name: str,
        subdir: str,
        prefix: str = "",
        desc: str = "",
        **kwargs: Any,
    ) -> None:
        """Register a named export preset with cron-style time filtering."""
        cron_args = {
            k: v for k, v in kwargs.items()
            if k in CRON_ARG_NAMES and v is not None
        }
        self.exports[name] = Export(
            name, subdir, self.images, prefix=prefix, desc=desc, **cron_args
        )

    def export(self, export_name: str, **writer_args: Any) -> None:
        """Run a single named export."""
        self.exports[export_name].run(self.export_dir, **writer_args)

    def export_all(self, **writer_args: Any) -> None:
        """Run all registered exports."""
        for name, export in self.exports.items():
            logger.info("Running export: %s", export)
            export.run(self.export_dir, **writer_args)


class Export(CronTrigger):
    """A cron-based export definition that filters and writes an image subset.

    Inherits from :class:`apscheduler.triggers.cron.CronTrigger` so it can
    be used directly as a cron filter for image selection.

    Parameters
    ----------
    name : str
        Export preset name.
    subdir : str
        Subdirectory under the collection's export_dir for output.
    imageset : ImageSet
        The source image set to filter from.
    prefix : str
        Filename prefix for exported images.
    desc : str
        Human-readable description of this export.
    """

    def __init__(
        self,
        name: str,
        subdir: str,
        imageset: ImageSet,
        prefix: Optional[str] = None,
        desc: Optional[str] = None,
        year: Optional[str] = None,
        month: Optional[str] = None,
        day: Optional[str] = None,
        week: Optional[str] = None,
        day_of_week: Optional[str] = None,
        hour: Optional[str] = None,
        minute: Optional[str] = None,
        second: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        timezone: Optional[str] = None,
    ) -> None:
        cron_args = {
            k: v
            for k, v in {
                "year": year, "month": month, "day": day, "week": week,
                "day_of_week": day_of_week, "hour": hour, "minute": minute,
                "second": second,
            }.items()
            if v is not None
        }
        self.imageset = imageset
        self.name = name
        self.subdir = subdir
        self.desc = desc
        self.prefix = prefix
        super().__init__(**cron_args)

    def __str__(self) -> str:
        cron_str = super().__str__()
        return (
            f"Export: {self.name} - Subdir: {self.subdir} - "
            f"Desc: {self.desc} - Prefix: {self.prefix} - {cron_str}"
        )

    def run(self, outputdir: str, **kwargs: Any) -> None:
        """Execute this export: filter images and write to *outputdir*/*subdir*."""
        writer_args = {
            k: v for k, v in kwargs.items()
            if k in WRITER_OPTIONS and v is not None
        }
        imageindex = self.imageset.imageindex
        imagelist = cron_image_filter(imageindex, self, fuzzy=5)

        ext = basename(next(iter(imageindex.keys()))).split(".")[-1]
        target_dir = join(outputdir, self.subdir)
        prepare_output_dir(target_dir, ext="jpg")

        outindex = self.imageset.index_files(imagelist)
        io = ImageIO()
        io.write_imageset(outindex, target_dir, prefix=self.prefix, **writer_args)
