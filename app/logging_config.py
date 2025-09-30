# -*- coding: utf-8 -*-
"""
Centralized logging configuration for the Stackademy application.
"""

import logging
import sys


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """
    Configure logging for the application.

    Args:
        level: The logging level (default: logging.INFO)

    Returns:
        Logger instance for the calling module
    """
    # Only configure if not already configured
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)],  # This logs to console
        )

    return logging.getLogger(__name__)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the specified module.

    Args:
        name: The name of the module (usually __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
