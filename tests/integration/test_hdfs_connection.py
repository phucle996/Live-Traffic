# ==============================================================================
# Integration Test for HDFS Connectivity (tests/integration/test_hdfs_connection.py)
# Verifies HDFS URI Resolution, Path Formatting, & Connectivity Utility Mechanics
# ==============================================================================

try:
    import pytest
except ImportError:
    pytest = None

from src.common.config import settings
from src.ingestion.upload_to_hdfs import upload_file_to_hdfs


def test_hdfs_uri_configuration():
    """
    Verifies HDFS URI configuration endpoints are non-empty and well-formed.
    """
    assert settings.HDFS_URI.startswith("hdfs://")
    assert ":9000" in settings.HDFS_URI or "namenode" in settings.HDFS_URI
    assert settings.HDFS_RAW_PATH.startswith("/traffic_project/")


def test_hdfs_upload_nonexistent_file():
    """
    Verifies that uploader fails gracefully (returns False) when target local file does not exist.
    """
    result = upload_file_to_hdfs("non_existent_file.csv", "/traffic_project/raw")
    assert result is False


if __name__ == "__main__":
    test_hdfs_uri_configuration()
    test_hdfs_upload_nonexistent_file()
    print("All test_hdfs_connection integration tests PASSED!")
