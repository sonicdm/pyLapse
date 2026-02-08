# pyLapse

Automatically save images from IP cameras into collections for export and video rendering, with detailed scheduling and export options.

## Installation

```bash
pip install -r requirements.txt
```

**For video rendering:** download [ffmpeg](https://ffmpeg.org/download.html) and place the executable in the project's `bin/` directory, or set `ffmpeg_path` in `capture_config.json`.

## Quick Start

### Web Dashboard (FastAPI + htmx)

The easiest way to use pyLapse. A browser-based dashboard for managing cameras, scheduling captures, running exports, and rendering videos.

```bash
# Windows
start_ui.bat

# Linux / macOS
./start_ui.sh

# PowerShell
.\start_ui.ps1
```

Or run directly:

```bash
python web_ui.py [--host 0.0.0.0] [--port 8000] [--config capture_config.json]
```

The launcher scripts will create a virtual environment and install dependencies automatically on first run.

![Dashboard](screenshots/dashboard.png)

**Dashboard features:**
- Live camera preview and on-demand image grab
- Per-camera and per-schedule enable/disable toggles
- Auto-create collections from camera output directories
- Cron and interval-based capture scheduling
- Configurable filename formatting, image quality, and resize on capture
- Granular auto-refreshing dashboard sections (no full-page flicker)

![Cameras](screenshots/cameras.png)

**Collections & Exports:**
- Browse image collections with per-day counts
- Cron-filtered exports with real-time progress (SSE)
- Timestamp overlay with font picker (system, bundled Roboto, Google Fonts)
- Image resize, quality, and optimization options
- Paginated history lists (10, 25, 50, 100 items)

![Collections](screenshots/collections.png)

**Video rendering:**
- Render image sequences to MP4 (H.264, H.265, MPEG-4)
- In-browser video preview and playback
- Chain video creation directly after export

**Config:**
- Visual config editor with folder browser
- Scheduler reload without restart

![Config](screenshots/config.png)

### Auto-capture (headless)

Configure cameras and schedules in `capture_config.json` (see `capture_config.example.json`):

```bash
python autocapture.py
```

### Python API

```python
from pyLapse.img_seq import Collection

# Load images from a directory
collection = Collection("My Timelapse", "/path/to/output", "/path/to/images")
print(collection)
# Image Collection: My Timelapse, Location: /path/to/images, Image Count: 12020

# Create a cron-filtered export (every 15 minutes, every other hour)
collection.add_export("Day Export", subdir="day", minute="*/15", hour="*/2")

# Run the export
collection.export.run(
    "Day Export", "/path/to/export",
    prefix="Timelapse ", drawtimestamp=True, optimize=True,
)
```

### Camera operations

```python
from pyLapse.img_seq import Camera

webcam = Camera("Front Porch", "http://192.168.1.100:8080/photoaf.jpg")

# Grab and save a single image
webcam.save_image("/path/to/output", prefix="FrontPorch ")
```

### Video rendering (CLI)

```bash
python render_video.py /path/to/image/sequence output.mp4 --fps 24 --pattern "*.jpg"
```

```python
from pyLapse.img_seq import render_sequence_to_video

render_sequence_to_video(
    input_dir="/path/to/image/sequence",
    output_path="output.mp4",
    fps=24,
    pattern="*.jpg",
)
```

## Project Structure

```
pyLapse/
  img_seq/            Core library
    cameras.py          Camera class for IP camera image capture
    collections.py      Collection and Export classes for organizing/filtering images
    fonts.py            Font discovery (system, bundled, Google Fonts)
    fonts/              Bundled font files (Roboto-Regular.ttf)
    image.py            ImageIO, ImageSet - image loading, saving, timestamps
    lapsetime.py        Time-based filtering (cron-style, dayslice, nearest-match)
    settings.py         Example configuration templates
    utils.py            Threading helpers, URL validation, file utilities
    video.py            ffmpeg-based video rendering with progress
    tests.py            pytest test suite
  web/                Web dashboard (FastAPI + htmx)
    app.py              FastAPI app with lifespan scheduler management
    scheduler.py        BackgroundScheduler singleton, config loading, capture jobs
    tasks.py            Background task manager with progress tracking
    collections_store.py  Persistent collection storage (JSON)
    history_store.py    Persistent export/video history (JSON)
    routes/             Route modules (dashboard, cameras, collections, exports, videos, config, api)
    templates/          Jinja2 HTML templates with htmx partials
    static/             CSS (dark theme), JavaScript (schedule picker, folder browser, modals)
autocapture.py        CLI headless auto-capture scheduler
web_ui.py             Web dashboard entry point
render_video.py       CLI video renderer
start_ui.bat          Windows launcher (creates venv, installs deps, starts server)
start_ui.sh           Linux/macOS launcher
start_ui.ps1          PowerShell launcher
```

## Running Tests

```bash
pytest pyLapse/img_seq/tests.py -v
```
