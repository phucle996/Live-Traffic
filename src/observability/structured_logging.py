# ==============================================================================
# JSON Structured Logging Formatter (src/observability/structured_logging.py)
# Formats Log Messages as JSON & Masks API Keys and Sensitive Credentials
# ==============================================================================

import json
import logging
from datetime import datetime
from typing import Dict, Any

from src.observability.tracing import TracingManager
from src.security.secret_provider import SecretProvider


class JSONStructuredLogFormatter(logging.Formatter):
    """
    Custom logging Formatter emitting structured JSON records with masked secrets.
    """

    def format(self, record: logging.LogRecord) -> str:
        raw_msg = record.getMessage()

        # Mask secrets in log message string
        masked_msg = raw_msg
        if "key=" in masked_msg or "password=" in masked_msg:
            masked_msg = SecretProvider.mask_secret(masked_msg)

        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "level": record.levelname,
            "logger": record.name,
            "request_id": TracingManager.get_current_request_id(),
            "message": masked_msg,
            "filename": record.filename,
            "line_number": record.lineno,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)
