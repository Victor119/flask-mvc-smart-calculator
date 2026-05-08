"""
logging_config.py
-----------------
Centralized logging setup for the Calculator Application.
Call `setup_enhanced_logging()` once at startup before importing anything else.
"""

import logging
import os


def setup_enhanced_logging() -> tuple:
    """
    Configure application-wide logging with separate handlers for:
      - All levels  → logs/calculator_app.log
      - INFO+        → logs/calculations.log  (calculation-specific events)
      - ERROR+       → logs/errors.log
      - INFO+        → stdout

    Returns
    -------
    (root_logger, calc_logger)
    """
    logs_dir = "logs"
    os.makedirs(logs_dir, exist_ok=True)

    # Remove existing handlers to avoid duplication on hot-reload
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    detailed_fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)-20s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    simple_fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    def _file_handler(filename: str, level: int, formatter: logging.Formatter):
        h = logging.FileHandler(os.path.join(logs_dir, filename))
        h.setLevel(level)
        h.setFormatter(formatter)
        return h

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(_file_handler("calculator_app.log", logging.DEBUG, detailed_fmt))
    root_logger.addHandler(_file_handler("errors.log", logging.ERROR, detailed_fmt))

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_fmt)
    root_logger.addHandler(console_handler)

    # Dedicated calculation logger (does NOT propagate to root)
    calc_logger = logging.getLogger("calculations")
    calc_logger.setLevel(logging.INFO)
    calc_logger.addHandler(_file_handler("calculations.log", logging.INFO, simple_fmt))
    calc_logger.propagate = False

    return root_logger, calc_logger