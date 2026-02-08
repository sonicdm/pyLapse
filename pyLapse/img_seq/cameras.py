"""IP camera abstraction for fetching and saving images."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Optional

from pyLapse.img_seq.image import ImageIO, save_image
from pyLapse.img_seq.utils import is_image_url

logger = logging.getLogger(__name__)


class Camera:
    """Represents an IP camera that serves still images over HTTP.

    Parameters
    ----------
    name : str
        Human-readable camera name.
    image_url : str
        Direct URL to the camera's image endpoint (must end with an image extension).
    location : str or None
        Optional location identifier.
    """

    def __init__(
        self, name: str, image_url: str, location: Optional[str] = None
    ) -> None:
        self.name = name
        if not is_image_url(image_url):
            raise ValueError(f"{image_url!r} does not appear to be an image URL")
        self._image_url = image_url
        self.location = location

    def __repr__(self) -> str:
        return f"<Camera: {self.name}>"

    def __str__(self) -> str:
        return f"Camera: {self.name} {self._image_url}"

    @property
    def imageurl(self) -> str:
        """The camera's image URL."""
        return self._image_url

    @imageurl.setter
    def imageurl(self, value: str) -> None:
        if not is_image_url(value):
            raise ValueError(f"{value!r} does not appear to be an image URL")
        self._image_url = value

    def fetch_image(self) -> Any:
        """Download the current image from the camera and return a PIL Image."""
        return ImageIO.fetch_image_from_url(self.imageurl)

    def save_image(self, outputdir: str, **kwargs: Any) -> str:
        """Fetch the current image and save it to *outputdir*."""
        image = self.fetch_image()
        timestamp = datetime.now()
        return save_image(image, outputdir, timestamp, **kwargs)
