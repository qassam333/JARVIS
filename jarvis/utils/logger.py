"""Structured logging with security filtering."""

import logging
import sys
import json
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Any, Optional


class SensitiveFilter(logging.Filter):
    """Filter out sensitive data from logs."""

    SENSITIVE_PATTERNS = [
        "password",
        "passwd",
        "pwd",
        "token",
        "api_key",
        "apikey",
        "secret",
        "credential",
        "auth",
        "authorization",
        "private_key",
        "access_token",
        "refresh_token",
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage().lower()

        for pattern in self.SENSITIVE_PATTERNS:
            if pattern in message:
                record.msg = "[SENSITIVE DATA REDACTED]"
                return True

        if hasattr(record, "extra"):
            extra = record.extra
            if isinstance(extra, dict):
                for key in list(extra.keys()):
                    if any(p in key.lower() for p in self.SENSITIVE_PATTERNS):
                        extra[key] = "[REDACTED]"

        return True


class JSONFormatter(logging.Formatter):
    """Format logs as JSON for file output."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "source": record.name,
        }

        if record.name:
            log_data["logger"] = record.name

        if record.filename:
            log_data["file"] = f"{record.filename}:{record.lineno}"

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        if hasattr(record, "extra") and record.extra:
            log_data.update(record.extra)

        return json.dumps(log_data, default=str)


class ColoredFormatter(logging.Formatter):
    """Color-coded formatter for console output."""

    COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[35m",
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, "")
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logger(
    name: str = "jarvis",
    level: str = "INFO",
    log_dir: Optional[Path] = None,
    debug: bool = False,
) -> logging.Logger:
    """
    Setup and return a configured logger.

    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files
        debug: Enable debug mode with more verbose output

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    if logger.hasHandlers():
        logger.handlers.clear()

    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.addFilter(SensitiveFilter())

    if debug:
        logger.setLevel(logging.DEBUG)

    log_format = "%(asctime)s [%(levelname)s] %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if debug else logging.INFO)

    if sys.stdout.isatty():
        console_handler.setFormatter(ColoredFormatter(log_format, datefmt=date_format))
    else:
        console_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))

    logger.addHandler(console_handler)

    if log_dir:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_dir / "jarvis.log",
            maxBytes=10_000_000,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get or create a logger for a module."""
    return logging.getLogger(f"jarvis.{name}")
