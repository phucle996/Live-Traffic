# ==============================================================================
# Dead-Letter Queue (DLQ) Handler (src/streaming/dead_letter_handler.py)
# Quarantines Unparseable or Malformed JSON Payloads into traffic.dead-letter
# ==============================================================================

import json
from datetime import datetime
from typing import Dict, Any

from src.common.logging_utils import get_logger

# Instantiate logger for dead letter handler
logger = get_logger(__name__)


class DeadLetterHandler:
    """
    Quarantines malformed payload records to dead-letter queue topic 'traffic.dead-letter'.
    """

    @staticmethod
    def format_dead_letter_payload(raw_payload: Any, error_reason: str) -> Dict[str, Any]:
        """
        Formats malformed payload with error context metadata.

        Args:
            raw_payload (Any): Raw incoming payload that failed parsing.
            error_reason (str): Cause of parsing failure.

        Returns:
            Dict[str, Any]: Structured dead-letter event.
        """
        dlq_event = {
            "dlq_timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "error_reason": error_reason,
            "raw_payload": str(raw_payload),
        }
        logger.warning(f"Quarantining payload to DLQ: {error_reason}")
        return dlq_event
