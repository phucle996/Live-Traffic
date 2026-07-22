# ==============================================================================
# Exploratory Data Analysis Engine (src/processing/exploratory_analysis.py)
# Computes Traffic Velocity Aggregations, Spatial Bottleneck Ranks, & Exports Reports
# ==============================================================================

import json
import os
from pathlib import Path
from typing import Dict, Any

import pandas as pd
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F

from src.common.config import settings, PROJECT_ROOT
from src.common.logging_utils import get_logger
from src.common.spark_session import get_spark_session
from src.ingestion.seed_loader import load_seed_csv_files

# Instantiate logger for EDA engine
logger = get_logger(__name__)


def compute_hourly_aggregations(df: DataFrame) -> DataFrame:
    """
    Computes average speed, free-flow speed, and congestion ratio grouped by Hour.

    Args:
        df (DataFrame): Processed PySpark DataFrame.

    Returns:
        DataFrame: Hourly traffic speed summary DataFrame.
    """
    logger.info("Computing hourly traffic speed aggregations...")
    # Group by Hour and compute aggregate metrics
    hourly_df = (
        df.groupBy("Hour")
        .agg(
            F.count("*").alias("sample_count"),
            F.round(F.avg("CurrentSpeed"), 2).alias("avg_current_speed"),
            F.round(F.avg("FreeFlowSpeed"), 2).alias("avg_free_flow_speed"),
            F.round(F.min("CurrentSpeed"), 2).alias("min_current_speed"),
            F.round(F.max("CurrentSpeed"), 2).alias("max_current_speed"),
            F.round(F.avg("CongestionRatio"), 4).alias("avg_congestion_ratio"),
        )
        .orderBy("Hour")
    )
    return hourly_df


def compute_location_aggregations(df: DataFrame) -> DataFrame:
    """
    Computes average speed and congestion ratio grouped by Location/Street and District, ranked by bottleneck severity.

    Args:
        df (DataFrame): Processed PySpark DataFrame.

    Returns:
        DataFrame: Spatial bottleneck ranking DataFrame.
    """
    logger.info("Computing spatial location congestion ranking...")
    # Group by Location/Street and District
    location_df = (
        df.groupBy("Location/Street", "District", "Latitude", "Longitude")
        .agg(
            F.count("*").alias("observation_count"),
            F.round(F.avg("CurrentSpeed"), 2).alias("avg_current_speed"),
            F.round(F.avg("FreeFlowSpeed"), 2).alias("avg_free_flow_speed"),
            F.round(F.avg("CongestionRatio"), 4).alias("avg_congestion_ratio"),
        )
        .withColumn(
            "TrafficStatus",
            F.when(F.col("avg_congestion_ratio") < 0.4, "Severe Congestion")
            .when((F.col("avg_congestion_ratio") >= 0.4) & (F.col("avg_congestion_ratio") < 0.7), "Heavy Traffic")
            .otherwise("Free Flow"),
        )
        .orderBy("avg_congestion_ratio")
    )
    return location_df


def export_eda_reports(spark: SparkSession, processed_parquet_path: str = None) -> Dict[str, Any]:
    """
    Main orchestration function running EDA statistical aggregations and exporting CSV/JSON report artifacts.
    """
    reports_dir = PROJECT_ROOT / "artifacts" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting EDA processing. Reports destination: '{reports_dir}'")

    # Resolve input path
    parquet_path = processed_parquet_path or f"{settings.HDFS_URI}{settings.HDFS_PROCESSED_PATH}/*"

    try:
        # Attempt to read processed Parquet dataset from HDFS
        logger.info(f"Reading processed dataset from '{parquet_path}'...")
        df = spark.read.parquet(parquet_path)
    except Exception as e:
        logger.warning(f"Unable to read Parquet from HDFS ({str(e)}). Falling back to seed CSV data for EDA...")
        # Fallback to seed CSV loader for local EDA generation
        seed_pd = load_seed_csv_files(settings.SEED_FOLDER)
        if seed_pd.empty:
            logger.error("No data available for EDA generation.")
            return {}
        
        # Calculate derived columns for pandas fallback
        seed_pd["Hour"] = pd.to_datetime(seed_pd["Timestamp"]).dt.hour
        seed_pd["Minute"] = pd.to_datetime(seed_pd["Timestamp"]).dt.minute
        seed_pd["TimeInMinutes"] = seed_pd["Hour"] * 60 + seed_pd["Minute"]
        seed_pd["DayOfWeek"] = (pd.to_datetime(seed_pd["Timestamp"]).dt.dayofweek)
        seed_pd["Weekend"] = seed_pd["DayOfWeek"].apply(lambda x: 1 if x >= 5 else 0)
        seed_pd["CongestionRatio"] = (seed_pd["CurrentSpeed"] / seed_pd["FreeFlowSpeed"]).round(4)
        
        df = spark.createDataFrame(seed_pd)

    # Compute Hourly Aggregations
    hourly_df = compute_hourly_aggregations(df)
    hourly_pd = hourly_df.toPandas()
    hourly_csv = reports_dir / "speed_by_hour.csv"
    hourly_pd.to_csv(hourly_csv, index=False)
    logger.info(f"Exported '{hourly_csv}' ({len(hourly_pd)} rows)")

    # Compute Location Aggregations
    location_df = compute_location_aggregations(df)
    location_pd = location_df.toPandas()
    location_csv = reports_dir / "congestion_by_location.csv"
    location_pd.to_csv(location_csv, index=False)
    logger.info(f"Exported '{location_csv}' ({len(location_pd)} rows)")

    # Compute Overall Data Quality Metrics JSON
    total_count = df.count()
    overall_avg_speed = round(float(df.select(F.avg("CurrentSpeed")).collect()[0][0] or 0), 2)
    overall_free_flow = round(float(df.select(F.avg("FreeFlowSpeed")).collect()[0][0] or 0), 2)

    quality_json = {
        "eda_summary": {
            "total_observations": total_count,
            "overall_avg_speed_kmh": overall_avg_speed,
            "overall_avg_free_flow_kmh": overall_free_flow,
            "overall_congestion_ratio": round(overall_avg_speed / overall_free_flow, 4) if overall_free_flow > 0 else 0,
            "total_locations_tracked": len(location_pd),
        }
    }

    quality_json_path = reports_dir / "data_quality.json"
    with open(quality_json_path, "w", encoding="utf-8") as f:
        json.dump(quality_json, f, indent=2)
    logger.info(f"Exported '{quality_json_path}'")

    print("\n======================================================================")
    print(f"[SUCCESS] EDA Reports Successfully Generated in: {reports_dir}")
    print(f"Summary Metrics: {json.dumps(quality_json['eda_summary'], indent=2)}")
    print("======================================================================\n")

    return quality_json


def main():
    """
    CLI Entrypoint for EDA script.
    """
    spark = get_spark_session(app_name="exploratory-data-analysis")
    export_eda_reports(spark)


if __name__ == "__main__":
    main()
