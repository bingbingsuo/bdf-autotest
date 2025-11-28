"""
Logging utilities for BDF Auto Test Framework
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any


def setup_logger(name: str = "bdf_autotest", config: Optional[Dict[str, Any]] = None) -> logging.Logger:
    """
    Configure and return a logger instance.
    Logs to both console and rotating file inside logs directory.
    """
    log_config = config.get("logging", {}) if config else {}
    level_name = log_config.get("level", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    logger = logging.getLogger(name)
    if logger.handlers:
        logger.setLevel(level)
        return logger

    logger.setLevel(level)
    logger.propagate = False

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    log_dir = Path(log_config.get("log_dir", "./logs"))
    log_dir.mkdir(parents=True, exist_ok=True)

    timestamp_format = log_config.get("timestamp_format", "%Y-%m-%d_%H-%M-%S")
    timestamp = datetime.now().strftime(timestamp_format)
    log_file_pattern = log_config.get("log_file", "autotest_{timestamp}.log")
    log_filename = log_file_pattern.format(timestamp=timestamp)

    file_handler = logging.FileHandler(log_dir / log_filename)
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

