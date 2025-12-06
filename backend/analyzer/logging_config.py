"""
analyzer/logging_config.py

Centralized logging configuration for the analyzer pipeline.

Usage:
    from analyzer.logging_config import setup_logging

    # Call once at application startup
    setup_logging(level="INFO")

    # Then use in any module
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Message")
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    format_string: Optional[str] = None,
    use_colors: bool = True,
) -> None:
    """
    Configure logging for the entire analyzer package.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to write logs to file
        format_string: Custom format string (uses default if None)
        use_colors: Use colored output if coloredlogs is available

    Example:
        # Basic setup
        setup_logging(level="DEBUG")

        # With file output
        setup_logging(level="INFO", log_file=Path("logs/analyzer.log"))
    """
    # Default format
    if format_string is None:
        format_string = (
            "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s"
        )

    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)

    # Try to use coloredlogs for prettier output
    if use_colors:
        try:
            import coloredlogs

            coloredlogs.install(
                level=numeric_level,
                fmt=format_string,
                logger=root_logger,
            )
        except ImportError:
            # Fallback to standard formatting
            console_formatter = logging.Formatter(format_string)
            console_handler.setFormatter(console_formatter)
            root_logger.addHandler(console_handler)
    else:
        console_formatter = logging.Formatter(format_string)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
        file_handler.setLevel(numeric_level)
        file_formatter = logging.Formatter(format_string)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    # Suppress overly verbose third-party loggers
    logging.getLogger("numba").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("filelock").setLevel(logging.WARNING)

    root_logger.info(f"Logging configured: level={level}, file={log_file}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance

    Example:
        logger = get_logger(__name__)
        logger.info("Processing started")
    """
    return logging.getLogger(name)
