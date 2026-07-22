# ==============================================================================
# Unit Tests for Feature Builder & Predictor Serving Layer (tests/unit/test_feature_builder.py)
# ==============================================================================

import pytest
import pandas as pd
from datetime import datetime

from src.prediction.feature_builder import FeatureBuilder
from src.prediction.predictor import map_traffic_status, TrafficPredictor


def test_feature_builder_pandas_time_features():
    """
    Tests feature building logic for target datetime string:
    '2026-07-21 17:30:00' -> Hour=17, Minute=30, TimeInMinutes=1050, DayOfWeek=1 (Tuesday), Weekend=0
    """
    sample_locations = pd.DataFrame([
        {"Location/Street": "Nguyen Hue", "District": "District 1", "Latitude": 10.7769, "Longitude": 106.7009, "FreeFlowSpeed": 45.0}
    ])

    features_df = FeatureBuilder.build_pandas_features(sample_locations, "2026-07-21 17:30:00")

    assert "Hour" in features_df.columns
    assert "Minute" in features_df.columns
    assert "TimeInMinutes" in features_df.columns
    assert "DayOfWeek" in features_df.columns
    assert "Weekend" in features_df.columns

    row = features_df.iloc[0]
    assert row["Hour"] == 17
    assert row["Minute"] == 30
    assert row["TimeInMinutes"] == 1050
    assert row["DayOfWeek"] == 1  # 2026-07-21 is Tuesday (1)
    assert row["Weekend"] == 0


def test_map_traffic_status_thresholds():
    """
    Tests traffic status category mapping logic based on CongestionRatio thresholds:
    - ratio < 0.4 -> "Tắc nghẽn nghiêm trọng"
    - 0.4 <= ratio < 0.7 -> "Đông xe"
    - ratio >= 0.7 -> "Thông thoáng"
    """
    assert map_traffic_status(0.20) == "Tắc nghẽn nghiêm trọng"
    assert map_traffic_status(0.39) == "Tắc nghẽn nghiêm trọng"
    assert map_traffic_status(0.40) == "Đông xe"
    assert map_traffic_status(0.55) == "Đông xe"
    assert map_traffic_status(0.69) == "Đông xe"
    assert map_traffic_status(0.70) == "Thông thoáng"
    assert map_traffic_status(0.95) == "Thông thoáng"


def test_traffic_predictor_fallback_prediction():
    """
    Tests predictor fallback execution when trained model file is absent.
    """
    predictor = TrafficPredictor()
    sample_locations = pd.DataFrame([
        {"Location/Street": "Le Loi", "District": "District 1", "Latitude": 10.7738, "Longitude": 106.6983, "FreeFlowSpeed": 40.0}
    ])

    pred_df = predictor.predict_locations(sample_locations, "2026-07-21 17:30:00")

    assert not pred_df.empty
    assert "PredictedSpeed" in pred_df.columns
    assert "CongestionRatio" in pred_df.columns
    assert "TrafficStatus" in pred_df.columns
    assert pred_df.iloc[0]["PredictedSpeed"] >= 0.0
