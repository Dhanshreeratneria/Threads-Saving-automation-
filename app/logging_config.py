"""Logging configuration for the application."""

import logging
import sys
from typing import Optional
from app.config import get_settings


def setup_logging() -> logging.Logger:
    """Configure and return the application logger."""
    logger = logging.getLogger("thread_saving_mcp")
    level = get_settings().log_level.upper()
    logger.setLevel(getattr(logging, level))
    logger.handlers.clear()
    handler = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


logger: Optional[logging.Logger] = None


def get_logger() -> logging.Logger:
    """Get or create logger instance."""
    global logger
    if logger is None:
        logger = logging.getLogger("thread_saving_mcp")
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))
        logger.addHandler(handler)
    return logger
