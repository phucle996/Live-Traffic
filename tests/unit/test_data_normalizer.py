# ==============================================================================
# Unit Tests for Unified Data Normalizer (tests/unit/test_data_normalizer.py)
# ==============================================================================

from src.ingestion.data_normalizer import DataNormalizer


def test_normalize_offline_dataframe():
    """
    Verifies offline Lab CSV row dictionary normalization into unified Data Contract fields.
    """
    try:
        import pandas as pd
        raw_df = pd.DataFrame([
            {
                "Timestamp": "2025-11-07 08:00:00",
                "Location/Street": "Nguyen Hue",
                "District": "District 1",
                "Latitude": 10.7769,
                "Longitude": 106.7009,
                "CurrentSpeed": 25.0,
                "FreeFlowSpeed": 45.0,
                "Confidence": 0.95,
            }
        ])
        norm_df = DataNormalizer.normalize_offline_dataframe(raw_df)
        assert not norm_df.empty
        assert norm_df.iloc[0]["DataSource"] == "lab_offline"
    except ImportError:
        pass


def test_normalize_tomtom_api_response():
    """
    Verifies online TomTom API payload normalization into unified Data Contract fields.
    """
    api_payload = {
        "flowSegmentData": {
            "currentSpeed": 30.5,
            "freeFlowSpeed": 45.0,
            "confidence": 0.98,
            "currentTravelTime": 120,
            "freeFlowTravelTime": 90,
            "roadClosure": False,
        }
    }

    norm_row = DataNormalizer.normalize_tomtom_api_response(
        api_payload, street="Le Loi", district="District 1", lat=10.7738, lon=106.6983
    )

    assert norm_row["DataSource"] == "tomtom_live"
    assert norm_row["CurrentSpeed"] == 30.5
    assert norm_row["CurrentTravelTime"] == 120
    assert norm_row["RoadClosure"] is False


if __name__ == "__main__":
    test_normalize_offline_dataframe()
    test_normalize_tomtom_api_response()
    print("All test_data_normalizer unit tests PASSED!")
