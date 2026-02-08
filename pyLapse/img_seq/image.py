"""Image loading, indexing, and batch processing for time-lapse sequences."""
from __future__ import annotations

import fnmatch
import logging
import os
import re
from datetime import datetime
from io import BytesIO
from typing import Any, Callable, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from PIL import Image, ImageDraw, ImageFont

from pyLapse.img_seq.fonts import get_default_font
from pyLapse.img_seq.lapsetime import cron_image_filter, dayslice
from pyLapse.img_seq.utils import ParallelExecutor, clear_target

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Format mappings
# ---------------------------------------------------------------------------

FORMATS: dict[str, str] = {
    "jpg": "JPEG",
    "jpeg": "JPEG",
    "png": "PNG",
}

WRITER_OPTIONS: tuple[str, ...] = (
    "resize",
    "quality",
    "optimize",
    "resolution",
    "drawtimestamp",
    "timestampformat",
    "timestampfont",
    "timestampfontsize",
    "timestampcolor",
    "timestamppos",
    "prefix",
    "zeropadding",
)

# Default font — bundled Roboto, falls back to Pillow's built-in if missing.
_DEFAULT_FONT: str | None = get_default_font()


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def imageset_load(
    inputdir: str,
    ext: str = "jpg",
    mask: str = "*",
    filematch: Optional[re.Pattern[str]] = None,
    date_source: str = "filename",
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
) -> ImageSet:
    """Load an image set from a directory of timestamped images.

    Parameters
    ----------
    date_source:
        ``"filename"`` (default) parses timestamps from filenames.
        ``"created"`` uses the file's creation / modification time.
    progress_callback:
        Optional ``(completed, total, message)`` callback for progress tracking.
    """
    return ImageSet(date_source=date_source).import_folder(
        inputdir, ext, mask, filematch, progress_callback=progress_callback,
    )


def imageset_from_names(
    filelist: list[str],
    ext: str = "jpg",
    mask: str = "*",
    filematch: Optional[re.Pattern[str]] = None,
) -> ImageSet:
    """Create an image set from an explicit list of file paths."""
    return ImageSet().import_from_list(filelist, ext, mask, filematch)


def download_image(
    url: str,
    outputdir: str,
    ext: str = "jpg",
    resize: bool = False,
    quality: int = 50,
    optimize: bool = False,
    resolution: tuple[int, int] = (1920, 1080),
    drawtimestamp: bool = False,
    timestampformat: Optional[str] = None,
    filenameformat: Optional[str] = None,
    timestampfontsize: int = 36,
    timestampcolor: tuple[int, int, int] = (255, 255, 255),
    timestamppos: tuple[int, int] = (0, 0),
    timestampfont: Optional[str] = None,
    prefix: str = "",
    zeropadding: int = 5,
) -> str:
    """Download an image from *url*, process it, and save to *outputdir*."""
    timestamp = datetime.now()
    image = ImageIO().fetch_image_from_url(url)
    return save_image(
        image,
        outputdir,
        timestamp,
        ext=ext,
        filenameformat=filenameformat,
        resize=resize,
        quality=quality,
        optimize=optimize,
        resolution=resolution,
        drawtimestamp=drawtimestamp,
        timestampformat=timestampformat,
        timestampfontsize=timestampfontsize,
        timestampcolor=timestampcolor,
        timestamppos=timestamppos,
        timestampfont=timestampfont,
        prefix=prefix,
        zeropadding=zeropadding,
    )


def save_image(
    image: Image.Image,
    outputdir: str,
    timestamp: datetime,
    ext: str = "jpg",
    resize: bool = False,
    quality: int = 50,
    optimize: bool = False,
    resolution: tuple[int, int] = (1920, 1080),
    drawtimestamp: bool = False,
    timestampformat: Optional[str] = None,
    filenameformat: Optional[str] = None,
    timestampfontsize: int = 36,
    timestampcolor: tuple[int, int, int] = (255, 255, 255),
    timestamppos: tuple[int, int] = (0, 0),
    timestampfont: Optional[str] = None,
    prefix: str = "",
    zeropadding: int = 5,
) -> str:
    """Process and save a PIL *image* to *outputdir* with the given options."""
    if not timestampformat:
        timestampformat = "%Y-%m-%d %I:%M:%S %p"
    if not filenameformat:
        filenameformat = "{prefix}{timestamp:%Y-%m-%d_%H-%M-%S}.{ext}"

    imgformat = FORMATS.get(ext, "JPEG")

    if resize:
        image.thumbnail(resolution)
    if drawtimestamp:
        image = ImageIO.timestamp_image(
            image,
            timestamp,
            timestampformat=timestampformat,
            color=timestampcolor,
            size=timestampfontsize,
            font=timestampfont,
        )

    outputfile = os.path.join(
        outputdir,
        filenameformat.format(prefix=prefix, timestamp=timestamp, ext=ext),
    )
    os.makedirs(outputdir, exist_ok=True)
    image.save(outputfile, imgformat, quality=quality, optimize=optimize)
    return f"Saved {outputfile}"


# ---------------------------------------------------------------------------
# Convenience pipeline
# ---------------------------------------------------------------------------


def make_image_sequence(
    inputdir: str,
    outputdir: str,
    ext: str = "jpg",
    mask: str = "*",
    filematch: Optional[re.Pattern[str]] = None,
    allframes: bool = False,
    hourlist: Optional[list[int]] = None,
    minutelist: Optional[list[int]] = None,
    fuzzy: int = 5,
    resize: bool = True,
    quality: int = 50,
    optimize: bool = False,
    resolution: tuple[int, int] = (1920, 1080),
    drawtimestamp: bool = False,
    timestampformat: Optional[str] = None,
    timestampfontsize: int = 36,
    timestampcolor: tuple[int, int, int] = (255, 255, 255),
    timestamppos: tuple[int, int] = (0, 0),
    timestampfont: Optional[str] = None,
    prefix: str = "",
    zeropadding: int = 5,
) -> None:
    """Load images from *inputdir*, filter by time, and write a processed sequence to *outputdir*."""
    if hourlist is None:
        hourlist = list(range(0, 24))

    imageset = imageset_load(inputdir, ext, mask, filematch)
    io = ImageIO()
    prepare_output_dir(outputdir, ext)

    if allframes:
        fileindex = imageset.imageindex
    else:
        imageset.filter_images(hourlist, minutelist, fuzzy)
        fileindex = imageset.filtered_images_index

    logger.info("Writing files from %s to %s", inputdir, outputdir)
    io.write_imageset(
        fileindex,
        outputdir,
        resize=resize,
        quality=quality,
        optimize=optimize,
        resolution=resolution,
        drawtimestamp=drawtimestamp,
        timestampformat=timestampformat,
        timestampfontsize=timestampfontsize,
        timestampcolor=timestampcolor,
        timestamppos=timestamppos,
        timestampfont=timestampfont,
        prefix=prefix,
        zeropadding=zeropadding,
    )


def prepare_output_dir(outputdir: str, ext: str, mask: str = "*") -> None:
    """Ensure *outputdir* exists, clearing old files if it already does."""
    if os.path.isdir(outputdir):
        logger.info("Clearing out files from %s", outputdir)
        pattern = f"{mask}.{ext}"
        clear_target(outputdir, pattern)
    else:
        logger.info("Creating %s", outputdir)
        os.makedirs(outputdir)


# ---------------------------------------------------------------------------
# ImageIO - image reading/writing with parallel processing
# ---------------------------------------------------------------------------


class ImageIO:
    """Batch image I/O with optional parallel processing and progress bars.

    Parameters
    ----------
    workers : int or None
        Number of worker threads. Defaults to CPU count.
    debug : bool
        When True, log individual results instead of a progress bar.
    """

    def __init__(self, workers: int | None = None, debug: bool = False) -> None:
        self.workers = workers
        self.debug = debug

    def write_imageset(
        self,
        imageset: dict[str, dict[str, datetime]],
        outputdir: str,
        resize: bool = True,
        quality: int = 50,
        optimize: bool = False,
        resolution: tuple[int, int] = (1920, 1080),
        drawtimestamp: bool = False,
        timestampformat: Optional[str] = None,
        timestampfontsize: int = 36,
        timestampcolor: tuple[int, int, int] = (255, 255, 255),
        timestamppos: tuple[int, int] = (0, 0),
        timestampfont: Optional[str] = None,
        prefix: str = "",
        zeropadding: int = 5,
        progress_callback: Callable[[int, int, str], None] | None = None,
    ) -> None:
        """Write all images from *imageset* to *outputdir* with processing options.

        If *progress_callback* is provided it is called as
        ``progress_callback(completed, total, "")`` after each image is written.
        """
        os.makedirs(outputdir, exist_ok=True)

        if not timestampformat:
            timestampformat = "%Y-%m-%d %I:%M:%S %p"
        if not prefix:
            prefix = os.path.basename(outputdir)

        # Flatten the day-grouped index into a sorted list of (filepath, timestamp)
        files: list[tuple[str, datetime]] = []
        for day, images in imageset.items():
            for image_path, timestamp in images.items():
                files.append((os.path.normpath(image_path), timestamp))
        output_files = sorted(files, key=lambda x: x[1])

        writer_kwargs: dict[str, Any] = dict(
            outputdir=outputdir,
            resize=resize,
            quality=quality,
            optimize=optimize,
            resolution=resolution,
            drawtimestamp=drawtimestamp,
            timestampformat=timestampformat,
            timestampfont=timestampfont,
            timestampfontsize=timestampfontsize,
            timestampcolor=timestampcolor,
            timestamppos=timestamppos,
            prefix=prefix,
            zeropadding=zeropadding,
        )

        executor = ParallelExecutor(workers=self.workers, debug=self.debug)
        executor.run_threaded(
            self._write_single_image,
            output_files,
            progress_callback=progress_callback,
            **writer_kwargs,
        )

    @staticmethod
    def _write_single_image(
        image_input: tuple[str, datetime],
        idx: int,
        outputdir: str,
        resize: bool = False,
        quality: int = 50,
        optimize: bool = False,
        resolution: tuple[int, int] = (1920, 1080),
        drawtimestamp: bool = False,
        timestampformat: Optional[str] = None,
        timestampfontsize: int = 36,
        timestampcolor: tuple[int, int, int] = (255, 255, 255),
        timestamppos: tuple[int, int] = (0, 0),
        timestampfont: Optional[str] = None,
        prefix: Optional[str] = None,
        zeropadding: int = 5,
    ) -> str:
        """Process and save a single image (called by the thread pool)."""
        input_path, timestamp = image_input
        im = Image.open(input_path)

        if resize:
            im.thumbnail(resolution)
        if drawtimestamp:
            im = ImageIO.timestamp_image(
                im,
                timestamp,
                timestampformat=timestampformat,
                color=timestampcolor,
                size=timestampfontsize,
                font=timestampfont,
            )

        seq_label = str(idx + 1).zfill(zeropadding)
        outputfile = os.path.join(outputdir, f"{prefix} {seq_label}.jpg")
        im.save(outputfile, "JPEG", quality=quality, optimize=optimize)
        return f"saved {outputfile}"

    @staticmethod
    def fetch_image_from_url(url: str, timeout: int = 10) -> Image.Image:
        """Download an image from *url* and return a PIL Image.

        Parameters
        ----------
        timeout : int
            Socket timeout in seconds (default 10).
        """
        try:
            request = Request(url)
            imgdata = urlopen(request, timeout=timeout).read()
        except (HTTPError, URLError) as exc:
            logger.error("Failed to fetch image from %s: %s", url, exc)
            raise
        return Image.open(BytesIO(imgdata))

    @staticmethod
    def timestamp_image(
        imageobj: Image.Image,
        datetimestamp: datetime,
        font: Optional[str] = None,
        timestampformat: Optional[str] = None,
        pos: tuple[int, int] = (0, 0),
        color: tuple[int, int, int] = (255, 255, 255),
        size: int = 72,
    ) -> Image.Image:
        """Overlay a timestamp on *imageobj* and return the modified image.

        Parameters
        ----------
        imageobj : PIL.Image.Image
            The image to stamp.
        datetimestamp : datetime
            Timestamp to render.
        font : str or None
            Path to a TrueType font file. Falls back to the bundled font.
        timestampformat : str or None
            ``strftime`` format string. Defaults to ``'%Y-%m-%d %I:%M:%S %p'``.
        pos : tuple[int, int]
            ``(x, y)`` coordinates for the text.
        color : tuple[int, int, int]
            RGB colour for the text.
        size : int
            Font size in points.
        """
        if not font:
            font = _DEFAULT_FONT
        if not timestampformat:
            timestampformat = "%Y-%m-%d %I:%M:%S %p"

        overlay_text = datetimestamp.strftime(timestampformat)
        draw = ImageDraw.Draw(imageobj)
        if font:
            timestamp_font = ImageFont.truetype(font, size)
        else:
            timestamp_font = ImageFont.load_default()
        draw.text(pos, overlay_text, color, font=timestamp_font)
        return imageobj


# ---------------------------------------------------------------------------
# ImageSet - indexing and filtering a folder of timestamped images
# ---------------------------------------------------------------------------

_DEFAULT_FILENAME_RE = re.compile(
    r".*?(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})-"
    r"(?P<hour>\d{2})(?P<minute>\d{2})(?P<seconds>\d{0,2})"
)


class ImageSet:
    """Index and filter a collection of timestamped image files.

    Images are grouped by day and indexed by their parsed timestamps.
    """

    def __init__(self, date_source: str = "filename") -> None:
        self.imageindex: dict[str, dict[str, datetime]] = {}
        self.filematch: Optional[re.Pattern[str]] = None
        self.images: list[str] = []
        self.inputdir: Optional[str] = None
        self.filtered_images: list[str] = []
        self.filtered_images_index: dict[str, dict[str, datetime]] = {}
        self._ext: str = "jpg"
        self._mask: str = "*"
        self._date_source: str = date_source
        self.imagecount: int = 0

    def __str__(self) -> str:
        return f"ImageSet({self.inputdir})"

    def __repr__(self) -> str:
        return f"<ImageSet: {self.inputdir!r} ({self.imagecount} images)>"

    def import_folder(
        self,
        inputdir: str,
        ext: str = "jpg",
        mask: str = "*",
        filematch: Optional[re.Pattern[str]] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> ImageSet:
        """Load all images matching *mask*.*ext* from *inputdir*."""
        self.inputdir = inputdir
        self._ext = ext
        self._mask = mask or "*"
        self.images = sorted(self._scandir(inputdir, self._mask, ext))
        self.filematch = filematch
        self.imageindex = self._build_index(self.images, self.filematch, progress_callback=progress_callback)
        return self

    def refresh_folder(self) -> None:
        """Re-scan the source directory for new images."""
        if not self.inputdir:
            return
        self.images = sorted(self._scandir(self.inputdir, self._mask, self._ext))
        self.imageindex = self._build_index(self.images, self.filematch)

    def import_from_list(
        self,
        imagelist: list[str],
        ext: str = "jpg",
        mask: str = "*",
        filematch: Optional[re.Pattern[str]] = None,
    ) -> ImageSet:
        """Create an image set from an explicit list of file paths."""
        self.images = sorted(imagelist)
        self.filematch = filematch
        self.imageindex = self._build_index(self.images, filematch)
        return self

    def index_files(
        self,
        files: list[str],
        filematch: Optional[re.Pattern[str]] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> dict[str, dict[str, datetime]]:
        """Parse timestamps from filenames and group by day.

        Returns ``{day_str: {filepath: datetime}}``.
        """
        self.imagecount = 0
        pattern = filematch or _DEFAULT_FILENAME_RE
        total = len(files)

        days: dict[str, dict[str, datetime]] = {}
        for i, f in enumerate(files):
            image_name = os.path.basename(f)
            match = pattern.match(image_name)
            if not match:
                if progress_callback and (i + 1) % 500 == 0:
                    progress_callback(i + 1, total, "Indexing filenames")
                continue

            dateargs = list(match.groups())
            if not match.group("seconds"):
                dateargs[5] = "00"

            timestamp = datetime(*[int(arg) for arg in dateargs])
            day = timestamp.strftime("%Y-%m-%d")

            if day not in days:
                days[day] = {}
            days[day][f] = timestamp
            self.imagecount += 1

            if progress_callback and (i + 1) % 500 == 0:
                progress_callback(i + 1, total, "Indexing filenames")

        if progress_callback:
            progress_callback(total, total, "Indexing complete")
        return days

    def _index_by_created(
        self,
        files: list[str],
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> dict[str, dict[str, datetime]]:
        """Group files by day using file creation/modification time."""
        self.imagecount = 0
        total = len(files)
        days: dict[str, dict[str, datetime]] = {}
        for i, f in enumerate(files):
            try:
                stat = os.stat(f)
                # Use birth time if available (Windows), else mtime
                ctime = getattr(stat, "st_birthtime", None) or stat.st_ctime
                timestamp = datetime.fromtimestamp(ctime)
            except OSError:
                if progress_callback and (i + 1) % 200 == 0:
                    progress_callback(i + 1, total, "Reading file dates")
                continue

            day = timestamp.strftime("%Y-%m-%d")
            if day not in days:
                days[day] = {}
            days[day][f] = timestamp
            self.imagecount += 1

            if progress_callback and (i + 1) % 200 == 0:
                progress_callback(i + 1, total, "Reading file dates")

        if progress_callback:
            progress_callback(total, total, "Indexing complete")
        return days

    def _build_index(
        self,
        files: list[str],
        filematch: Optional[re.Pattern[str]] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> dict[str, dict[str, datetime]]:
        """Route to the appropriate indexing method based on ``_date_source``."""
        if self._date_source == "created":
            return self._index_by_created(files, progress_callback=progress_callback)
        return self.index_files(files, filematch, progress_callback=progress_callback)

    def filter_index(
        self,
        files: list[str],
    ) -> dict[str, dict[str, datetime]]:
        """Return a subset of :attr:`imageindex` containing only *files*.

        More efficient than re-indexing from disk because timestamps are
        already cached, and works correctly regardless of ``date_source``.
        """
        matched = set(os.path.normpath(f) for f in files)
        result: dict[str, dict[str, datetime]] = {}
        for day, day_files in self.imageindex.items():
            day_matched = {
                f: ts for f, ts in day_files.items()
                if os.path.normpath(f) in matched
            }
            if day_matched:
                result[day] = day_matched
        return result

    def filter_images(
        self,
        hourlist: Optional[list[int]] = None,
        minutelist: Optional[list[int]] = None,
        fuzzy: int = 5,
    ) -> None:
        """Filter the loaded images by hour/minute ranges using :func:`dayslice`."""
        if hourlist is None:
            hourlist = list(range(0, 24))
        self.filtered_images = dayslice(
            self.imageindex,
            hourlist=hourlist,
            minutelist=minutelist,
            fuzzy=fuzzy,
        )
        self.filtered_images_index = self.filter_index(self.filtered_images)

    @property
    def days(self) -> list[str]:
        """Sorted list of day strings present in the image index."""
        return sorted(self.imageindex.keys())

    def get_day_files(self, day: str | int) -> dict[str, datetime]:
        """Return the file index for a specific day (by date string or position)."""
        if isinstance(day, str):
            if day not in self.imageindex:
                raise KeyError(f"Day '{day}' not found in image index: {self.days}")
            return self.imageindex[day]
        if isinstance(day, int):
            return self.imageindex[self.days[day]]
        raise TypeError("day must be a string or int")

    @staticmethod
    def _scandir(directory: str, mask: str, ext: str) -> list[str]:
        """Scan *directory* for files matching ``mask.ext`` using os.scandir.

        Much faster than glob.glob on network shares (UNC paths).
        """
        pattern = f"{mask}.{ext}"
        results: list[str] = []
        with os.scandir(directory) as it:
            for entry in it:
                if entry.is_file(follow_symlinks=False) and fnmatch.fnmatch(entry.name, pattern):
                    results.append(os.path.join(directory, entry.name))
        return results
