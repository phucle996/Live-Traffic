# ==============================================================================
# Unit Tests for Observability Modules (tests/unit/test_observability.py)
# Verifies MetricsRegistry, JSON Log Formatter, & Tracing Manager
# ==============================================================================

import json
import logging
from src.observability.metrics import MetricsRegistry
from src.observability.tracing import TracingManager
from src.observability.structured_logging import JSONStructuredLogFormatter


def test_metrics_registry_counters_and_gauges():
    """
    Tests incrementing metrics counters and gauges.
    """
    MetricsRegistry.inc_counter("ingested_rows_total", 100.0)
    MetricsRegistry.set_gauge("model_rmse", 8.45)

    data = MetricsRegistry.get_all_metrics()
    assert data["counters"]["ingested_rows_total"] >= 100.0
    assert data["gauges"]["model_rmse"] == 8.45


def test_tracing_manager_request_id():
    """
    Tests request_id generation and propagation in context.
    """
    TracingManager.set_request_id("unit_test_req_12345")
    req_id = TracingManager.get_current_request_id()
    assert req_id == "unit_test_req_12345"


def test_json_structured_log_formatter():
    """
    Tests JSON structured logging formatting and key masking.
    """
    formatter = JSONStructuredLogFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=42,
        msg="Executing request with key=secret_12345",
        args=(),
        exc_info=None
    )

    formatted_json_str = formatter.format(record)
    log_dict = json.loads(formatted_json_str)

    assert log_dict["level"] == "INFO"
    assert "request_id" in log_dict
    assert "secret_12345" not in log_dict["message"]  # Verify key is masked!


if __name__ == "__main__":
    test_metrics_registry_counters_and_gauges()
    test_tracing_manager_request_id()
    test_json_structured_log_formatter()
    print("All test_observability unit tests PASSED!")
