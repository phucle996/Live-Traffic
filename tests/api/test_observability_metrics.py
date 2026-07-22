# ==============================================================================
# Observability Metrics Integration Tests (tests/api/test_observability_metrics.py)
# Verifies /metrics Prometheus Endpoints cho Go Live API, Go Collector & Rust Inference
# ==============================================================================

import requests
import pytest

GO_COLLECTOR_URL = "http://localhost:8083"
GO_LIVE_API_URL = "http://localhost:8084"
RUST_INFERENCE_URL = "http://localhost:8090"


def is_service_up(url: str, path: str = "/health/live") -> bool:
    """
    Helper function checking if service health probe endpoint is active.
    """
    try:
        r = requests.get(f"{url}{path}", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


@pytest.mark.skipif(not is_service_up(GO_LIVE_API_URL), reason="Go Live API is not running on port 8084")
def test_go_live_api_prometheus_metrics_endpoint():
    """
    Verifies GET /metrics trên Go Live API trả về Prometheus text format hợp lệ.
    """
    resp = requests.get(f"{GO_LIVE_API_URL}/metrics", timeout=5)
    assert resp.status_code == 200
    assert "go_info" in resp.text or "# HELP" in resp.text


@pytest.mark.skipif(not is_service_up(GO_COLLECTOR_URL), reason="Go Collector is not running on port 8083")
def test_go_collector_prometheus_metrics_endpoint():
    """
    Verifies GET /metrics trên Go Traffic Collector trả về Prometheus text format hợp lệ.
    """
    resp = requests.get(f"{GO_COLLECTOR_URL}/metrics", timeout=5)
    assert resp.status_code == 200
    assert "# HELP" in resp.text


@pytest.mark.skipif(not is_service_up(RUST_INFERENCE_URL, "/health/live"), reason="Rust API is not running on port 8090")
def test_rust_inference_api_health_live():
    """
    Verifies Rust Inference API liveness health probe.
    """
    resp = requests.get(f"{RUST_INFERENCE_URL}/health/live", timeout=5)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "UP"


def test_python_mlops_metrics_exporter_lifecycle():
    """
    Verifies Python MLOpsMetricsExporter records training metrics correctly.
    """
    import time
    from src.observability.metrics_exporter import MLOpsMetricsExporter

    exporter = MLOpsMetricsExporter()
    exporter.training_start()
    time.sleep(0.01)
    exporter.training_complete(rmse=7.2, mae=4.1, r2=0.72)

    metrics = exporter.get_all_metrics()
    assert metrics["training_duration_seconds"] >= 0.01
    assert metrics["model_rmse"] == 7.2
    assert metrics["model_mae"] == 4.1
    assert metrics["model_r2"] == 0.72

    exporter.record_data_quality_failure()
    exporter.record_spark_job_duration(15.5)
    metrics = exporter.get_all_metrics()
    assert metrics["data_quality_failures_total"] == 1
    assert metrics["spark_job_duration_seconds"] == 15.5
