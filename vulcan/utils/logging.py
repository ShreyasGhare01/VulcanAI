"""Structured logger configuration for Vulcan AI OS."""

import sys
from typing import Any

from loguru import logger

from vulcan.config import LoggingConfig


def setup_logger(config: LoggingConfig) -> None:
    """Configures structured Loguru logger."""
    logger.remove()

    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{extra[subsystem]}</cyan> - "
        "<level>{message}</level>"
    )

    logger.add(
        sys.stderr,
        level=config.level,
        format=log_format,
        colorize=True,
        enqueue=True,
    )

    if config.log_to_file:
        logger.add(
            config.log_file_path,
            level=config.level,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {extra[subsystem]} - {message}",
            rotation=config.rotation,
            retention=config.retention,
            enqueue=True,
            serialize=config.structured,
        )


class SubsystemLogger:
    """Convenience wrapper to automatically bind a subsystem name to all logs."""

    def __init__(self, name: str):
        self.name = name
        self._logger = logger.bind(subsystem=name)

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._logger.debug(msg, *args, **kwargs)

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._logger.error(msg, *args, **kwargs)

    def exception(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._logger.exception(msg, *args, **kwargs)


def get_logger(subsystem: str) -> SubsystemLogger:
    """Retrieves an instance of SubsystemLogger for a given subsystem."""
    return SubsystemLogger(subsystem)
