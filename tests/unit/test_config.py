# ==============================================================================
# Unit Tests for Central Settings & Secret Masking (tests/unit/test_config.py)
# ==============================================================================

import os
try:
    import pytest
except ImportError:
    pytest = None
from src.common.config import Settings, settings


def test_settings_singleton():
    """
    Tests that Settings class enforces Singleton pattern across multiple instantiations.
    """
    s1 = Settings()
    s2 = Settings()
    assert s1 is s2, "Settings should be a thread-safe singleton instance"


def test_settings_default_values():
    """
    Tests that default configuration values are properly loaded.
    """
    assert settings.PROJECT_NAME == "traffic-prediction-lab5"
    assert settings.HDFS_RAW_PATH == "/traffic_project/raw"
    assert settings.HDFS_PROCESSED_PATH == "/traffic_project/processed"
    assert settings.MODEL_TARGET == "CurrentSpeed"
    assert "Latitude" in settings.MODEL_FEATURES


def test_secret_masking_in_repr():
    """
    Tests that sensitive credentials (TOMTOM_API_KEY) are masked in __repr__ string representation.
    """
    # Temporarily set an API key string for testing repr masking
    original_key = settings.TOMTOM_API_KEY
    try:
        settings.TOMTOM_API_KEY = "secret_api_key_12345"
        repr_str = repr(settings)
        assert "secret_api_key_12345" not in repr_str, "Raw API key must NOT be leaked in __repr__"
        assert "***MASKED***" in repr_str, "API key should be replaced with ***MASKED***"
    finally:
        settings.TOMTOM_API_KEY = original_key


if __name__ == "__main__":
    test_settings_singleton()
    test_settings_default_values()
    test_secret_masking_in_repr()
    print("All test_config unit tests PASSED!")
