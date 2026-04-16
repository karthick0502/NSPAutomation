from __future__ import annotations

import logging
import os
import sys


def configure_logging(level: str | int | None = None) -> None:
    """
    Initialise root logging once. Safe to call from CLI and server.
    Defaults to LOG_LEVEL env (or INFO). Logs go to stderr so stdout stays clean for JSON.
    """
    if level is None:
        level = os.environ.get("LOG_LEVEL", "INFO")
    if isinstance(level, str):
        numeric = getattr(logging, level.upper(), None)
        if numeric is None:
            numeric = logging.INFO
        level = numeric

    root = logging.getLogger()
    if root.handlers:
        root.setLevel(level)
        for handler in root.handlers:
            handler.setLevel(level)
        return

    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    root.setLevel(level)
    root.addHandler(handler)

    # Keep OpenAI/HTTP client libraries quiet unless you opt in.
    for name in ("openai", "httpx", "httpcore", "urllib3"):
        logging.getLogger(name).setLevel(logging.WARNING)
