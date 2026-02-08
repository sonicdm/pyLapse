"""Font discovery and management for timestamp overlays.

Provides three font sources:
1. **Bundled** — Roboto ships with the package (works offline).
2. **System** — auto-detected from platform-specific directories.
3. **Google Fonts** — downloaded on demand to a local cache.
"""
from __future__ import annotations

import logging
import os
import platform
import re
from pathlib import Path
from typing import Optional
from urllib.error import URLError
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Bundled fonts
# ---------------------------------------------------------------------------

_FONTS_DIR = Path(__file__).resolve().parent / "fonts"

_BUNDLED_FONTS: list[dict[str, str]] = [
    {
        "name": "Roboto",
        "path": str(_FONTS_DIR / "Roboto-Regular.ttf"),
        "source": "bundled",
    },
]


def get_default_font() -> str:
    """Return the path to the bundled default font (Roboto)."""
    return _BUNDLED_FONTS[0]["path"]


def get_bundled_fonts() -> list[dict[str, str]]:
    """Return metadata for all bundled fonts."""
    return list(_BUNDLED_FONTS)


# ---------------------------------------------------------------------------
# System font enumeration
# ---------------------------------------------------------------------------

_system_font_cache: list[dict[str, str]] | None = None


def _display_name(filename: str) -> str:
    """Derive a human-readable name from a font filename."""
    stem = Path(filename).stem
    # "OpenSans-Bold" → "Open Sans Bold"
    name = re.sub(r"[-_]", " ", stem)
    # Insert space before internal capitals: "DejaVuSans" → "Deja Vu Sans"
    name = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", name)
    return name.strip()


def _system_font_dirs() -> list[str]:
    """Return platform-specific font directories."""
    system = platform.system()
    if system == "Windows":
        windir = os.environ.get("WINDIR", r"C:\Windows")
        dirs = [os.path.join(windir, "Fonts")]
        # Also check user fonts on Windows 10+
        local_app = os.environ.get("LOCALAPPDATA", "")
        if local_app:
            user_fonts = os.path.join(local_app, "Microsoft", "Windows", "Fonts")
            dirs.append(user_fonts)
        return dirs
    elif system == "Darwin":
        return [
            "/Library/Fonts",
            "/System/Library/Fonts",
            os.path.expanduser("~/Library/Fonts"),
        ]
    else:  # Linux / other Unix
        return [
            "/usr/share/fonts",
            "/usr/local/share/fonts",
            os.path.expanduser("~/.fonts"),
            os.path.expanduser("~/.local/share/fonts"),
        ]


def get_system_fonts(*, force_rescan: bool = False) -> list[dict[str, str]]:
    """Scan platform font directories for .ttf and .otf files.

    Results are cached after the first call. Pass *force_rescan=True* to
    refresh the cache.

    Returns a list of ``{"name": ..., "path": ..., "source": "system"}``.
    """
    global _system_font_cache
    if _system_font_cache is not None and not force_rescan:
        return list(_system_font_cache)

    fonts: list[dict[str, str]] = []
    seen_paths: set[str] = set()

    for font_dir in _system_font_dirs():
        if not os.path.isdir(font_dir):
            continue
        for root, _dirs, files in os.walk(font_dir):
            for filename in files:
                if not filename.lower().endswith((".ttf", ".otf")):
                    continue
                full_path = os.path.join(root, filename)
                norm = os.path.normcase(os.path.normpath(full_path))
                if norm in seen_paths:
                    continue
                seen_paths.add(norm)
                fonts.append({
                    "name": _display_name(filename),
                    "path": full_path,
                    "source": "system",
                })

    fonts.sort(key=lambda f: f["name"].lower())
    _system_font_cache = fonts
    return list(fonts)


# ---------------------------------------------------------------------------
# Google Fonts download
# ---------------------------------------------------------------------------

FONT_CACHE_DIR = Path.home() / ".cache" / "pylapse" / "fonts"

# Pattern to extract the .ttf URL from the CSS returned by Google Fonts
_GFONT_URL_RE = re.compile(r"url\((https://fonts\.gstatic\.com/[^)]+\.ttf)\)")


def get_google_font(family: str) -> Optional[str]:
    """Download a Google Font to the local cache and return the file path.

    Returns ``None`` on network errors (graceful fallback).
    """
    safe_name = re.sub(r"[^\w\s-]", "", family).strip().replace(" ", "_")
    cached = FONT_CACHE_DIR / f"{safe_name}.ttf"
    if cached.is_file():
        return str(cached)

    css_url = (
        f"https://fonts.googleapis.com/css2?family={family.replace(' ', '+')}"
        "&display=swap"
    )
    try:
        req = Request(css_url, headers={"User-Agent": "Mozilla/5.0"})
        css_text = urlopen(req, timeout=10).read().decode("utf-8")
    except (URLError, OSError) as exc:
        logger.warning("Failed to fetch Google Font CSS for %r: %s", family, exc)
        return None

    match = _GFONT_URL_RE.search(css_text)
    if not match:
        logger.warning("No .ttf URL found in Google Fonts CSS for %r", family)
        return None

    ttf_url = match.group(1)
    try:
        ttf_data = urlopen(Request(ttf_url), timeout=30).read()
    except (URLError, OSError) as exc:
        logger.warning("Failed to download Google Font %r: %s", family, exc)
        return None

    FONT_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cached.write_bytes(ttf_data)
    logger.info("Cached Google Font %r → %s", family, cached)
    return str(cached)


# ---------------------------------------------------------------------------
# Combined listing
# ---------------------------------------------------------------------------


def list_available_fonts() -> list[dict[str, str]]:
    """Return bundled + system fonts, sorted by name.

    Each entry is ``{"name": ..., "path": ..., "source": "bundled"|"system"}``.
    """
    combined = get_bundled_fonts() + get_system_fonts()
    combined.sort(key=lambda f: f["name"].lower())
    return combined
