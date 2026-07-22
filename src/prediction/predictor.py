# ==============================================================================
# Serving Layer Traffic Predictor Engine (src/prediction/predictor.py)
# Loads Fitted Model Once (Singleton Cache), Runs Batch Inference, & Classifies Traffic Status
# ==============================================================================

import threading
from pathlib import Path
from typing import Union, Optional
import pandas as pd
from pyspark.ml import PipelineModel
from pyspark.sql import SparkSession, DataFrame as SparkDataFrame
from pyspark.sql import functions as F

from src.common.config import settings, PROJECT_ROOT
from src.common.logging_utils import get_logger
from src.common.spark_session import get_spark_session
from src.prediction.feature_builder import FeatureBuilder

# Instantiate logger for traffic predictor
logger = get_logger(__name__)


def map_traffic_status(ratio: float) -> str:
    """
    Classifies CongestionRatio into human-readable Vietnamese traffic status categories.

    Args:
        ratio (float): Ratio of PredictedSpeed to FreeFlowSpeed.

    Returns:
        str: Traffic status description string.
    """
    if ratio < 0.4:
        return "Tắc nghẽn nghiêm trọng"
    elif ratio < 0.7:
        return "Đông xe"
    else:
        return "Thông thoáng"


class TrafficPredictor:
    """
    Thread-safe model serving class caching the trained Spark ML Pipeline model in memory.
    """

    _model: Optional[PipelineModel] = None
    _lock = threading.Lock()

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self._ensure_model_loaded()

    def _ensure_model_loaded(self) -> None:
        """
        Loads fitted Spark ML Pipeline model into memory if not already cached.
        """
        if TrafficPredictor._model is None:
            with TrafficPredictor._lock:
                if TrafficPredictor._model is None:
                    # Resolve model directory path
                    local_model_dir = PROJECT_ROOT / "artifacts" / "models" / "gbt" / "latest"
                    hdfs_model_uri = f"{settings.HDFS_URI}{settings.HDFS_MODEL_PATH}/latest"
                    
                    target_path = self.model_path or str(local_model_dir)

                    try:
                        logger.info(f"Loading trained GBT PipelineModel from '{target_path}'...")
                        TrafficPredictor._model = PipelineModel.load(target_path)
                        logger.info("Fitted GBT PipelineModel loaded successfully into predictor cache!")
                    except Exception as e:
                        logger.warning(f"Could not load local model from '{target_path}' ({str(e)}). Attempting HDFS...")
                        try:
                            TrafficPredictor._model = PipelineModel.load(hdfs_model_uri)
                            logger.info("Fitted GBT PipelineModel loaded from HDFS!")
                        except Exception as ex:
                            logger.warning(f"No trained model found on HDFS either ({str(ex)}). Predictor will use fallback baseline.")
                            TrafficPredictor._model = None

    def predict_locations(self, locations_df: pd.DataFrame, prediction_time: str) -> pd.DataFrame:
        """
        Predicts traffic speed and congestion status for target locations at specified prediction_time.

        Args:
            locations_df (pd.DataFrame): Locations DataFrame containing Street, District, Latitude, Longitude, FreeFlowSpeed.
            prediction_time (str): Datetime string (e.g. "2026-07-21 17:30:00").

        Returns:
            pd.DataFrame: DataFrame containing PredictedSpeed, CongestionRatio, and TrafficStatus.
        """
        logger.info(f"Executing batch location predictions for time '{prediction_time}' ({len(locations_df)} locations)...")

        # Step 1: Build time features via FeatureBuilder
        feature_df = FeatureBuilder.build_pandas_features(locations_df, prediction_time)

        # Ensure FreeFlowSpeed column exists (default 45.0 km/h if missing)
        if "FreeFlowSpeed" not in feature_df.columns:
            feature_df["FreeFlowSpeed"] = 45.0

        # Step 2: Run inference using cached PySpark ML model if available
        if TrafficPredictor._model is not None:
            spark = get_spark_session(app_name="predictor-inference")
            
            # Convert Pandas DataFrame to PySpark DataFrame
            spark_df = spark.createDataFrame(feature_df)
            
            # Execute model transform()
            raw_predictions = TrafficPredictor._model.transform(spark_df)
            
            # Extract predictions to Pandas
            pred_pd = raw_predictions.select("prediction").toPandas()
            feature_df["PredictedSpeed"] = pred_pd["prediction"].clip(lower=0.0).round(2)
        else:
            # Fallback when model is not yet trained: use baseline speed logic
            logger.info("Predictor using heuristic speed estimation baseline (Model file absent).")
            # Factor peak hour congestion reduction heuristic
            hour = feature_df["Hour"].iloc[0] if not feature_df.empty else 12
            if hour in (8, 17, 18):
                speed_factor = 0.35  # Peak hour congestion
            elif hour in (7, 9, 12, 16, 19):
                speed_factor = 0.60  # Moderate traffic
            else:
                speed_factor = 0.90  # Free flow
                
            feature_df["PredictedSpeed"] = (feature_df["FreeFlowSpeed"] * speed_factor).round(2)

        # Step 3: Compute CongestionRatio = PredictedSpeed / FreeFlowSpeed
        feature_df["CongestionRatio"] = (feature_df["PredictedSpeed"] / feature_df["FreeFlowSpeed"]).round(4)

        # Step 4: Map TrafficStatus string description
        feature_df["TrafficStatus"] = feature_df["CongestionRatio"].apply(map_traffic_status)

        # Select final output presentation columns
        output_cols = [
            "Location/Street", "District", "Latitude", "Longitude",
            "PredictionTime", "PredictedSpeed", "FreeFlowSpeed",
            "CongestionRatio", "TrafficStatus"
        ]
        
        # Keep only available columns
        existing_cols = [c for c in output_cols if c in feature_df.columns]
        return feature_df[existing_cols]
