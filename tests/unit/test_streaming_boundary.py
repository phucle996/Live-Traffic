# ==============================================================================
# Streaming Boundary Unit Tests (tests/unit/test_streaming_boundary.py)
# Verifies Watermarking, Event Deduplication (event_id), & Quarantine Contracts
# ==============================================================================

from src.streaming.stream_schema import get_traffic_stream_schema
from src.streaming.checkpoint_manager import CheckpointManager
from src.streaming.dead_letter_handler import DeadLetterHandler


def test_streaming_schema_has_event_id_and_timestamp():
    """
    Verifies that StructStream schema includes event_id and Timestamp for Watermarking & Deduplication.
    """
    schema = get_traffic_stream_schema()
    field_names = [f.name for f in schema.fields]

    assert "event_id" in field_names
    assert "Timestamp" in field_names
    assert "CurrentSpeed" in field_names


def test_quarantine_formatting_and_isolation():
    """
    Verifies Quarantine payload formatting for corrupt stream records.
    """
    corrupted_data = '{"invalid_json": true}'
    dlq_item = DeadLetterHandler.format_dead_letter_payload(corrupted_data, "SchemaMismatchError")

    assert dlq_item["error_reason"] == "SchemaMismatchError"
    assert dlq_item["raw_payload"] == corrupted_data
    assert "dlq_timestamp" in dlq_item


def test_checkpoint_isolation_path():
    """
    Verifies checkpoint path location generator for PySpark Structured Streaming.
    """
    cp_path = CheckpointManager.get_checkpoint_location("streaming_traffic_v1")
    assert "/checkpoints/streaming_traffic_v1" in cp_path
