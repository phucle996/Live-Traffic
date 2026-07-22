# ==============================================================================
# Central Logging Utility Module (src/common/logging_utils.py)
# Cloud-Native Structured Logging Factory supporting Console and JSON Output
# ==============================================================================

import logging
import logging.config
import sys
from pathlib import Path
from typing import Optional
try:
    import yaml
except ImportError:
    yaml = None

from src.common.config import settings, PROJECT_ROOT


class JsonFormatter(logging.Formatter):
    """
    Cloud-native JSON formatter for structured logging streams.
    Compatible with log aggregation agents (Fluentd, Promtail/Loki, Elastic Beats).
    """

    def format(self, record: logging.LogRecord) -> str:
        # Build structured dictionary containing log context metadata
        log_entry = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "file": record.filename,
            "line": record.lineno,
            "message": record.getMessage(),
        }

        # Include exception tracebacks if error log includes exception info
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        import json

        # Return serialized JSON log entry
        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging(config_path: Optional[Path] = None) -> None:
    """
    Configures python standard logging globally based on log_config.yaml or environment settings.
    """
    # Use default log_config.yaml if path is not explicitly provided
    if config_path is None:
        config_path = PROJECT_ROOT / "config" / "log_config.yaml"

    # Attempt to load log_config.yaml if available and yaml library is installed
    if yaml is not None and config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            log_cfg = yaml.safe_load(f)
            logging.config.dictConfig(log_cfg)
    else:
        # Fallback manual configuration if log_config.yaml is absent
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, settings.LOG_LEVEL, logging.INFO))

        # Clear pre-existing log handlers to prevent duplicate entries
        if root_logger.hasHandlers():
            root_logger.handlers.clear()

        # Create stdout console handler
        handler = logging.StreamHandler(sys.stdout)

        # Apply appropriate log formatter based on LOG_FORMAT setting
        if settings.LOG_FORMAT == "JSON":
            formatter = JsonFormatter(datefmt="%Y-%m-%dT%H:%M:%SZ")
        else:
            formatter = logging.Formatter(
                fmt="%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )

        handler.setFormatter(formatter)
        root_logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """
    Returns a configured Logger instance for the specified module name.

    Args:
        name (str): The module name (usually __name__).

    Returns:
        logging.Logger: Thread-safe logger instance.
    """
    # Ensure root logging framework is setup
    setup_logging()

    # Obtain logger for module name
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.LOG_LEVEL, logging.INFO))

    return logger
