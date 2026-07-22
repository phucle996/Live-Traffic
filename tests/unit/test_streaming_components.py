# ==============================================================================
# Unit Tests for Streaming Components (tests/unit/test_streaming_components.py)
# Verifies KafkaProducer event formatting, Stream Schema, Checkpoints, & DLQ
# ==============================================================================

from src.streaming.kafka_producer import KafkaTrafficProducer
from src.streaming.stream_schema import get_traffic_stream_schema
from src.streaming.checkpoint_manager import CheckpointManager
from src.streaming.dead_letter_handler import DeadLetterHandler


def test_kafka_producer_event_enrichment():
    """
    Verifies that KafkaTrafficProducer enriches raw records with UUID event_id and timestamp.
    """
    producer = KafkaTrafficProducer(bootstrap_servers="localhost:9092")
    raw_record = {"Location/Street": "Nam Ky Khoi Nghia", "CurrentSpeed": 32.5}

    event = producer.format_event(raw_record)
    assert "event_id" in event
    assert len(event["event_id"]) > 10
    assert "Timestamp" in event
    assert event["Location/Street"] == "Nam Ky Khoi Nghia"


def test_stream_schema_definition():
    """
    Verifies stream schema fields.
    """
    schema = get_traffic_stream_schema()
    if isinstance(schema, dict):
        field_names = schema["fields"]
    else:
        field_names = [f.name for f in schema.fields]

    assert "event_id" in field_names
    assert "Timestamp" in field_names
    assert "CurrentSpeed" in field_names
    assert "RoadClosure" in field_names


def test_checkpoint_manager_path():
    """
    Verifies CheckpointManager generates valid checkpoint storage path.
    """
    path = CheckpointManager.get_checkpoint_location("test_query")
    assert "test_query" in path
    assert "checkpoints" in path


def test_dead_letter_handler_formatting():
    """
    Verifies DeadLetterHandler formats malformed JSON payload into structured DLQ event.
    """
    raw_bad_payload = "{malformed_json: missing_quotes"
    dlq_event = DeadLetterHandler.format_dead_letter_payload(raw_bad_payload, "JSONDecodeError")

    assert dlq_event["error_reason"] == "JSONDecodeError"
    assert "raw_payload" in dlq_event
    assert "dlq_timestamp" in dlq_event


if __name__ == "__main__":
    test_kafka_producer_event_enrichment()
    test_stream_schema_definition()
    test_checkpoint_manager_path()
    test_dead_letter_handler_formatting()
    print("All test_streaming_components unit tests PASSED!")
