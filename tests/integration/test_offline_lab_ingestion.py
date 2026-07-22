# ==============================================================================
# Integration Test for Offline Lab Data Ingestion (tests/integration/test_offline_lab_ingestion.py)
# ==============================================================================

import json
from pathlib import Path
from src.common.config import PROJECT_ROOT
from src.ingestion.offline_lab_source import OfflineLabSource


def test_offline_lab_source_reads_and_normalizes():
    """
    Verifies that OfflineLabSource reads historical CSV files and normalizes records.
    """
    source = OfflineLabSource()
    records = source.read()

    assert isinstance(records, list)

    # If new records exist, check schema fields
    if len(records) > 0:
        r0 = records[0]
        assert "Timestamp" in r0
        assert "Location/Street" in r0
        assert "DataSource" in r0
        assert r0["DataSource"] == "lab_offline"
        assert "IngestedAtUtc" in r0
        assert "IngestionBatchId" in r0

    # Verify ingestion manifest JSON was generated
    manifest_path = PROJECT_ROOT / "artifacts" / "manifests" / "ingestion_manifest.json"
    assert manifest_path.exists()


if __name__ == "__main__":
    test_offline_lab_source_reads_and_normalizes()
    print("All test_offline_lab_ingestion integration tests PASSED!")
