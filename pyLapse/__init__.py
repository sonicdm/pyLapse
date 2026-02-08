"""pyLapse - Time-lapse image capture and processing automation."""
from __future__ import annotations

import logging

__version__ = "0.2.0"

# Library-level NullHandler so users aren't forced to configure logging.
logging.getLogger(__name__).addHandler(logging.NullHandler())
