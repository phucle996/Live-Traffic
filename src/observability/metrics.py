# ==============================================================================
# Prometheus Metrics Registry (src/observability/metrics.py)
# Exports Metrics Counters, Histograms, & Gauges for System Observability
# ==============================================================================

from typing import Dict, Any
from src.common.logging_utils import get_logger

# Instantiate logger for metrics registry
logger = get_logger(__name__)


class MetricsRegistry:
    """
    Registry managing Prometheus metrics counters, gauges, and histograms.
    """

    _counters: Dict[str, float] = {
        "tomtom_requests_total": 0.0,
        "tomtom_request_errors_total": 0.0,
        "tomtom_rate_limit_total": 0.0,
        "ingested_rows_total": 0.0,
        "invalid_rows_total": 0.0,
        "prediction_errors_total": 0.0,
        "api_http_requests_total": 0.0,
    }

    _gauges: Dict[str, float] = {
        "model_rmse": 0.0,
        "model_data_age_seconds": 0.0,
        "hdfs_capacity_usage": 0.0,
    }

    @classmethod
    def inc_counter(cls, name: str, value: float = 1.0) -> None:
        """
        Increments named counter metric by value.
        """
        if name in cls._counters:
            cls._counters[name] += value
            logger.debug(f"Metric Counter '{name}' incremented to {cls._counters[name]}")

    @classmethod
    def set_gauge(cls, name: str, value: float) -> None:
        """
        Sets named gauge metric value.
        """
        if name in cls._gauges:
            cls._gauges[name] = value
            logger.debug(f"Metric Gauge '{name}' set to {value}")

    @classmethod
    def get_all_metrics(cls) -> Dict[str, Any]:
        """
        Returns snapshot dictionary of all registered counters and gauges.
        """
        return {
            "counters": dict(cls._counters),
            "gauges": dict(cls._gauges),
        }
