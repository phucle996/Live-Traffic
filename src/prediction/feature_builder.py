# ==============================================================================
# Central Feature Builder Module (src/prediction/feature_builder.py)
# Decoupled Feature Construction for Training, Ingestion, and Online Dashboard Serving
# ==============================================================================

from datetime import datetime
from typing import Union
import pandas as pd
from pyspark.sql import DataFrame as SparkDataFrame, SparkSession
from pyspark.sql import functions as F

from src.common.schemas import convert_spark_day_of_week, is_weekend
from src.common.logging_utils import get_logger

# Instantiate logger for feature builder
logger = get_logger(__name__)


class FeatureBuilder:
    """
    Central Feature Builder rendering identical feature vectors for training, batch predictions, and online serving.
    Feature Order is governed by contracts/feature_contract.json (Single Source of Truth).
    """

    # Danh sách thứ tự đặc trưng chuẩn (Single Source of Truth khớp với contracts/feature_contract.json)
    FEATURE_COLS = [
        "Latitude",
        "Longitude",
        "FreeFlowSpeed",
        "Confidence",
        "Hour",
        "Minute",
        "TimeInMinutes",
        "DayOfWeek",
        "Weekend",
    ]


    @staticmethod
    def parse_datetime(dt_input: Union[str, datetime]) -> datetime:
        """
        Parses input string or datetime object into a Python datetime object.

        Args:
            dt_input (Union[str, datetime]): Datetime object or ISO string.

        Returns:
            datetime: Parsed datetime object.
        """
        if isinstance(dt_input, datetime):
            return dt_input
        
        # Try parsing ISO or standard format strings
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(str(dt_input), fmt)
            except ValueError:
                pass
        
        raise ValueError(f"Unable to parse datetime string: '{dt_input}'")

    @staticmethod
    def build_pandas_features(locations_df: pd.DataFrame, prediction_time: Union[str, datetime]) -> pd.DataFrame:
        """
        Attaches time features (Hour, Minute, TimeInMinutes, DayOfWeek, Weekend) to a Pandas locations DataFrame.

        Args:
            locations_df (pd.DataFrame): Locations DataFrame containing Latitude, Longitude, etc.
            prediction_time (Union[str, datetime]): Prediction timestamp.

        Returns:
            pd.DataFrame: Pandas DataFrame with attached feature columns.
        """
        dt = FeatureBuilder.parse_datetime(prediction_time)
        df = locations_df.copy()

        # Extract hour and minute features
        hour = dt.hour
        minute = dt.minute
        time_in_minutes = hour * 60 + minute

        # DayOfWeek Python standard (0=Monday .. 6=Sunday)
        day_of_week = dt.weekday()
        weekend = 1 if day_of_week >= 5 else 0

        # Assign feature columns
        df["PredictionTime"] = dt.strftime("%Y-%m-%d %H:%M:%S")
        df["Hour"] = hour
        df["Minute"] = minute
        df["TimeInMinutes"] = time_in_minutes
        df["DayOfWeek"] = day_of_week
        df["Weekend"] = weekend

        return df

    @staticmethod
    def build_spark_features(spark_df: SparkDataFrame, timestamp_col: str = "Timestamp") -> SparkDataFrame:
        """
        Attaches time features to a PySpark DataFrame using PySpark SQL functions.

        Args:
            spark_df (SparkDataFrame): PySpark input DataFrame.
            timestamp_col (str): Timestamp column name.

        Returns:
            SparkDataFrame: PySpark DataFrame with attached feature columns.
        """
        # Parse timestamp string to TimestampType if needed
        df = spark_df.withColumn(
            "ParsedTime",
            F.coalesce(
                F.to_timestamp(F.col(timestamp_col), "yyyy-MM-dd HH:mm:ss"),
                F.to_timestamp(F.col(timestamp_col), "yyyy-MM-dd'T'HH:mm:ss"),
                F.to_timestamp(F.col(timestamp_col)),
            ),
        )

        # Build Hour, Minute, TimeInMinutes
        df = (
            df.withColumn("Hour", F.hour(F.col("ParsedTime")))
            .withColumn("Minute", F.minute(F.col("ParsedTime")))
            .withColumn("TimeInMinutes", F.col("Hour") * 60 + F.col("Minute"))
        )

        # Build DayOfWeek (Python standard 0=Mon..6=Sun) and Weekend (0/1)
        df = df.withColumn("DayOfWeek", convert_spark_day_of_week(F.dayofweek(F.col("ParsedTime"))))
        df = df.withColumn("Weekend", is_weekend(F.col("DayOfWeek")))

        return df
