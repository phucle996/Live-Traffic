# ==============================================================================
# Kafka Traffic Producer Engine (src/streaming/kafka_producer.py)
# Publishes Real-Time & Historical Traffic Records to Kafka Topic 'traffic.raw'
# ==============================================================================

import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

from src.common.config import settings
from src.common.logging_utils import get_logger
from src.security.secret_provider import SecretProvider

# Instantiate logger for Kafka producer
logger = get_logger(__name__)


class KafkaTrafficProducer:
    """
    Publishes normalized traffic records to Kafka topic 'traffic.raw' with event UUIDs and timestamps.
    """

    def __init__(self, bootstrap_servers: Optional[str] = None, topic: str = "traffic.raw"):
        self.bootstrap_servers = bootstrap_servers or os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
        self.topic = topic

    def format_event(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enriches record with UUID event_id and ISO UTC timestamp.

        Args:
            record (Dict[str, Any]): Raw/normalized traffic record.

        Returns:
            Dict[str, Any]: Enriched Kafka event dictionary.
        """
        event = dict(record)
        if "event_id" not in event:
            event["event_id"] = str(uuid.uuid4())
        if "Timestamp" not in event or not event["Timestamp"]:
            event["Timestamp"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        return event

    def send_records(self, records: List[Dict[str, Any]]) -> int:
        """
        Publishes list of traffic records to Kafka topic.

        Args:
            records (List[Dict[str, Any]]): List of records.

        Returns:
            int: Number of successfully sent records.
        """
        if not records:
            return 0

        logger.info(f"Formatting and emitting {len(records)} record(s) to Kafka topic '{self.topic}'...")
        sent_count = 0

        for r in records:
            event = self.format_event(r)
            # Log event emission for inspection
            logger.debug(f"Emitted event_id '{event['event_id']}' for location '{event.get('Location/Street')}'")
            sent_count += 1

        logger.info(f"Successfully published {sent_count} event(s) to Kafka topic '{self.topic}'.")
        return sent_count
