"""FastAPI application with lifespan management."""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from pyLapse.web.scheduler import capture_scheduler

_HERE = os.path.dirname(os.path.abspath(__file__))


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Start the capture scheduler on startup; stop on shutdown."""
    config_path = os.environ.get("PYLAPSE_CAPTURE_CONFIG")
    capture_scheduler.load_config(config_path)
    capture_scheduler.setup_jobs()
    capture_scheduler.start()
    yield
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
