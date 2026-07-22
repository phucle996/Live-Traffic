# ==============================================================================
# Unit Tests for Data Quality & Governance (tests/unit/test_data_quality.py)
# Verifies Expectations, QualityRunner, SchemaRegistry, AnomalyDetector, & LineageWriter
# ==============================================================================

from src.data_quality.expectations import QualityExpectations
from src.data_quality.schema_registry import SchemaRegistry
from src.data_quality.anomaly_detector import StatisticalAnomalyDetector
from src.data_quality.lineage_writer import LineageWriter
from src.data_quality.quality_runner import QualityRunner


def test_quality_expectations():
    """
    Tests QualityExpectations non-null and range assertions.
    """
    valid_rec = {
        "Location/Street": "Le Loi",
        "Timestamp": "2026-07-21 12:00:00",
        "Latitude": 10.77,
        "Longitude": 106.70,
        "CurrentSpeed": 35.0,
    }
    is_valid_null, _ = QualityExpectations.validate_non_null(valid_rec, ["Location/Street", "Timestamp"])
    assert is_valid_null is True

    invalid_rec = {"CurrentSpeed": 250.0}  # Exceeds max 150 km/h
    is_valid_range, failed_cols = QualityExpectations.validate_range(invalid_rec, {"CurrentSpeed": {"min": 0, "max": 150}})
    assert is_valid_range is False
    assert len(failed_cols) > 0


def test_schema_registry_compatibility():
    """
    Tests SchemaRegistry version compatibility checks.
    """
    cols = [
        "Location/Street", "District", "Latitude", "Longitude",
        "CurrentSpeed", "FreeFlowSpeed", "Confidence",
        "CurrentTravelTime", "FreeFlowTravelTime", "RoadClosure",
        "Timestamp", "DataSource", "IngestionBatchId"
    ]
    assert SchemaRegistry.is_compatible(cols, "v1.0") is True
    assert SchemaRegistry.is_compatible(["Location/Street"], "v1.0") is False


def test_anomaly_detector_zscore():
    """
    Tests StatisticalAnomalyDetector outlier detection.
    """
    normal_speeds = [30.0, 32.0, 31.0, 29.0, 33.0, 30.0, 31.0, 30.0, 32.0, 200.0]  # 200 is clear outlier
    outliers = StatisticalAnomalyDetector.detect_speed_outliers_zscore(normal_speeds, threshold=2.0)
    assert 9 in outliers


def test_lineage_writer():
    """
    Tests LineageWriter structured JSON metadata output.
    """
    rec = LineageWriter.record_lineage(
        batch_id="test_batch_123",
        source="test_source",
        raw_partition="/traffic_project/raw/test",
        processed_dataset="/data/processed.parquet"
    )
    assert rec["batch_id"] == "test_batch_123"
    assert rec["quality_gate_passed"] is True


def test_quality_runner_quarantine():
    """
    Tests QualityRunner filtering and quarantining invalid records.
    """
    runner = QualityRunner()
    records = [
        {"Location/Street": "Nguyen Hue", "Timestamp": "2026-07-21 12:00:00", "Latitude": 10.7, "Longitude": 106.7, "CurrentSpeed": 40.0},
        {"Location/Street": "", "Timestamp": None, "Latitude": 10.7, "Longitude": 106.7, "CurrentSpeed": -50.0},  # Invalid!
    ]

    all_passed, valid_recs, quarantined_recs = runner.run_quality_gate(records)
    assert all_passed is False
    assert len(valid_recs) == 1
    assert len(quarantined_recs) == 1


if __name__ == "__main__":
    test_quality_expectations()
    test_schema_registry_compatibility()
    test_anomaly_detector_zscore()
    test_lineage_writer()
    test_quality_runner_quarantine()
    print("All test_data_quality unit tests PASSED!")
