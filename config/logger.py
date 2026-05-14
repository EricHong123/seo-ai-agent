"""Structured logging with loguru — replaces all print() calls."""

import sys
from loguru import logger


def setup_logging():
    """Configure structured logging. Call once at application startup."""
    logger.remove()  # Remove default handler

    # Development: colored, human-readable
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <7}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> — <level>{message}</level>",
        level="DEBUG",
        colorize=True,
    )

    # Production: JSON to file
    logger.add(
        "data/logs/agent.log",
        format="{time} | {level} | {name}:{function}:{line} | {message}",
        level="INFO",
        rotation="10 MB",
        retention="7 days",
        compression="gz",
        serialize=False,
    )

    return logger


log = logger
