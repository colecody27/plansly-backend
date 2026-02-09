import logging
import os
from logging import Formatter, StreamHandler


DEFAULT_LOGGER_NAME = "plansly"


def _get_level():
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    return getattr(logging, level_name, logging.INFO)


def init_app(app):
    level = _get_level()
    formatter = Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    handler = StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    if not any(isinstance(h, StreamHandler) for h in root_logger.handlers):
        root_logger.addHandler(handler)

    # Let Flask propagate to root handlers for consistent formatting.
    app.logger.handlers = []
    app.logger.propagate = True
    app.logger.setLevel(level)


def get_logger(name=None):
    return logging.getLogger(name or DEFAULT_LOGGER_NAME)
