"""FastAPI application with lifespan management."""
from __future__ import annotations

import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from pyLapse.web.scheduler import capture_scheduler

_HERE = os.path.dirname(os.path.abspath(__file__))
logger = logging.getLogger(__name__)

# Shutdown signal for long-lived connections (SSE streams)
shutdown_event = asyncio.Event()


def _suppress_connection_reset(loop: asyncio.AbstractEventLoop, context: dict) -> None:
    """Suppress ConnectionResetError noise on Windows ProactorEventLoop.

    When a browser navigates away from a page with streaming connections
    (video, SSE), the dropped connection triggers a harmless exception in
    the ProactorEventLoop transport layer.  We silently discard it.
    """
    exc = context.get("exception")
    if isinstance(exc, (ConnectionResetError, ConnectionAbortedError)):
        return
    loop.default_exception_handler(context)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Start the capture scheduler on startup; stop on shutdown."""
    shutdown_event.clear()

    # Suppress noisy Windows ProactorEventLoop errors
    if sys.platform == "win32":
        loop = asyncio.get_running_loop()
        loop.set_exception_handler(_suppress_connection_reset)

    config_path = os.environ.get("PYLAPSE_CAPTURE_CONFIG")
    capture_scheduler.load_config(config_path)
    capture_scheduler.setup_jobs()
    capture_scheduler.start()
    yield
    shutdown_event.set()
    capture_scheduler.stop()


app = FastAPI(title="pyLapse", lifespan=lifespan)

# Static files and templates
app.mount("/static", StaticFiles(directory=os.path.join(_HERE, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(_HERE, "templates"))

# -----------------------------------------------------------------------
# Import and include route modules
# -----------------------------------------------------------------------
from pyLapse.web.routes import dashboard, cameras, collections, exports, videos, config, api  # noqa: E402

app.include_router(dashboard.router)
app.include_router(cameras.router, prefix="/cameras", tags=["cameras"])
app.include_router(collections.router, prefix="/collections", tags=["collections"])
app.include_router(exports.router, prefix="/exports", tags=["exports"])
app.include_router(videos.router, prefix="/videos", tags=["videos"])
app.include_router(config.router, prefix="/config", tags=["config"])
app.include_router(api.router, prefix="/api", tags=["api"])
