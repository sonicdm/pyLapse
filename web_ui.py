"""pyLapse Web UI entry point.

Usage::

    python web_ui.py [--host 0.0.0.0] [--port 8000] [--config capture_config.json]
"""
from __future__ import annotations

import argparse
import os


def main() -> None:
    parser = argparse.ArgumentParser(description="pyLapse Web Dashboard")
    parser.add_argument("--host", default="127.0.0.1", help="Bind address (default 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port (default 8000)")
    parser.add_argument("--config", default=None, help="Path to capture_config.json")
    args = parser.parse_args()

    if args.config:
        os.environ["PYLAPSE_CAPTURE_CONFIG"] = os.path.abspath(args.config)

    import uvicorn
    uvicorn.run(
        "pyLapse.web.app:app",
        host=args.host,
        port=args.port,
        reload=False,
        timeout_graceful_shutdown=5,
    )


if __name__ == "__main__":
    main()
