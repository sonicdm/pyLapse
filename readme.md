# pyLapse

Automatically save images from IP cameras into collections for export and video rendering, with detailed scheduling and export options.

## Installation

```bash
pip install -r requirements.txt
```

**For video rendering:** download [ffmpeg](https://ffmpeg.org/download.html) and place the executable in the project's `bin/` directory.

## Quick Start

### Auto-capture from IP cameras

Configure cameras and schedules in `capture_config.json` (see `capture_config.example.json` for the format):

```bash
python autocapture.py
```

### Load and export a collection

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

### Video rendering (ffmpeg)

Render an image sequence directory to a single video file.

**CLI:**
```bash
python render_video.py /path/to/image/sequence output.mp4 --fps 24 --pattern "*.jpg"
```

**Python:**
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
  img_seq/          Core library
    cameras.py        Camera class for IP camera image capture
    collections.py    Collection and Export classes for organizing/filtering images
    image.py          ImageIO, ImageSet - image loading, saving, timestamps
    lapsetime.py      Time-based filtering (cron-style, dayslice, nearest-match)
    settings.py       Example configuration templates
    utils.py          Threading helpers, URL validation, file utilities
    video.py          ffmpeg-based video rendering with progress bar
    tests.py          pytest test suite
autocapture.py      CLI auto-capture scheduler
render_video.py     CLI video renderer
```

## Running Tests

```bash
pytest pyLapse/img_seq/tests.py -v
```

