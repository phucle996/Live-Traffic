# ==============================================================================
# Spark ETL Processing Job (src/processing/process_spark.py)
# Cleans Raw Traffic Ingestion Data, Generates Features, & Writes Parquet Datasets
# ==============================================================================

import os
import sys
from datetime import datetime
from typing import Tuple

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F

from src.common.config import settings
from src.common.logging_utils import get_logger
from src.common.schemas import (
    RAW_TRAFFIC_SCHEMA,
    PROCESSED_TRAFFIC_SCHEMA,
    convert_spark_day_of_week,
    is_weekend,
)
from src.common.spark_session import get_spark_session
from src.processing.data_quality_report import generate_data_quality_metrics

# Instantiate logger for Spark ETL job
logger = get_logger(__name__)


def process_traffic_data(raw_df: DataFrame) -> Tuple[DataFrame, dict]:
    """
    Executes core Spark ETL transformations: cleaning, filtering, and feature engineering.

    Args:
        raw_df (DataFrame): Input PySpark raw traffic DataFrame.

    Returns:
        Tuple[DataFrame, dict]: Transformed feature DataFrame and ETL statistics dictionary.
    """
    # Step 1: Count raw input rows
    raw_rows = raw_df.count()
    logger.info(f"[ETL Stage 1] Raw Input Rows: {raw_rows}")

    # Step 2: Remove exact duplicate records
    dedup_df = raw_df.dropDuplicates()
    dedup_rows = dedup_df.count()
    duplicates_removed = raw_rows - dedup_rows
    logger.info(f"[ETL Stage 2] Removed {duplicates_removed} duplicate row(s). Remaining: {dedup_rows}")

    # Step 3: Parse Timestamp string to PySpark TimestampType
    parsed_df = dedup_df.withColumn(
        "ParsedTimestamp",
        F.coalesce(
            F.to_timestamp(F.col("Timestamp"), "yyyy-MM-dd HH:mm:ss"),
            F.to_timestamp(F.col("Timestamp"), "yyyy-MM-dd'T'HH:mm:ss"),
            F.to_timestamp(F.col("Timestamp")),
        ),
    )

    # Step 4: Apply Physical Bounds Contract Filtering
    valid_bounds_condition = (
        F.col("ParsedTimestamp").isNotNull()
        & F.col("Latitude").isNotNull()
        & (F.col("Latitude") >= -90.0)
        & (F.col("Latitude") <= 90.0)
        & F.col("Longitude").isNotNull()
        & (F.col("Longitude") >= -180.0)
        & (F.col("Longitude") <= 180.0)
        & F.col("CurrentSpeed").isNotNull()
        & (F.col("CurrentSpeed") >= 0.0)
        & F.col("FreeFlowSpeed").isNotNull()
        & (F.col("FreeFlowSpeed") > 0.0)
    )

    valid_df = parsed_df.filter(valid_bounds_condition)
    valid_rows = valid_df.count()
    invalid_rows = dedup_rows - valid_rows
    logger.info(f"[ETL Stage 3] Physical Bounds Filtered {invalid_rows} row(s). Remaining: {valid_rows}")

    # Step 5: Apply Sensor Confidence Threshold Filter (Confidence >= 0.9)
    high_conf_df = valid_df.filter(F.col("Confidence") >= 0.9)
    conf_rows = high_conf_df.count()
    low_conf_dropped = valid_rows - conf_rows
    logger.info(f"[ETL Stage 4] Confidence Filter (>=0.9) Dropped {low_conf_dropped} row(s). Remaining: {conf_rows}")

    # Step 6: Feature Engineering Transformations
    # Extract Hour, Minute, and calculate TimeInMinutes (Hour * 60 + Minute)
    engineered_df = (
        high_conf_df.withColumn("Hour", F.hour(F.col("ParsedTimestamp")))
        .withColumn("Minute", F.minute(F.col("ParsedTimestamp")))
        .withColumn("TimeInMinutes", F.col("Hour") * 60 + F.col("Minute"))
    )

    # Convert Spark dayofweek() to Python standard DayOfWeek (0=Mon .. 6=Sun)
    engineered_df = engineered_df.withColumn(
        "DayOfWeek", convert_spark_day_of_week(F.dayofweek(F.col("ParsedTimestamp")))
    )

    # Compute Weekend binary indicator (1 if Sat/Sun else 0)
    engineered_df = engineered_df.withColumn("Weekend", is_weekend(F.col("DayOfWeek")))

    # Compute CongestionRatio = CurrentSpeed / FreeFlowSpeed
    engineered_df = engineered_df.withColumn(
        "CongestionRatio", F.round(F.col("CurrentSpeed") / F.col("FreeFlowSpeed"), 4)
    )

    # Step 7: Select and cast final feature columns matching PROCESSED_TRAFFIC_SCHEMA
    processed_df = engineered_df.select(
        F.col("ParsedTimestamp").alias("Timestamp"),
        F.col("Location/Street"),
        F.col("District"),
        F.col("Latitude").cast("double"),
        F.col("Longitude").cast("double"),
        F.col("CurrentSpeed").cast("double"),
        F.col("FreeFlowSpeed").cast("double"),
        F.col("Confidence").cast("double"),
        F.col("Hour").cast("int"),
        F.col("Minute").cast("int"),
        F.col("TimeInMinutes").cast("int"),
        F.col("DayOfWeek").cast("int"),
        F.col("Weekend").cast("int"),
        F.col("CongestionRatio").cast("double"),
    )

    etl_stats = {
        "raw_rows": raw_rows,
        "duplicates_removed": duplicates_removed,
        "invalid_rows_filtered": invalid_rows,
        "low_confidence_rows_filtered": low_conf_dropped,
        "processed_rows": processed_df.count(),
    }

    return processed_df, etl_stats


def run_spark_etl_pipeline(input_hdfs_path: str = None, output_hdfs_path: str = None) -> None:
    """
    Executes end-to-end Spark ETL pipeline reading from raw HDFS path and writing Parquet to processed path.
    """
    # Get active SparkSession
    spark = get_spark_session(app_name="spark-etl-processing")

    # Resolve HDFS input and output paths
    raw_path = input_hdfs_path or f"{settings.HDFS_URI}{settings.HDFS_RAW_PATH}/*/*.csv"
    date_str = datetime.now().strftime("%Y-%m-%d")
    output_path = output_hdfs_path or f"{settings.HDFS_URI}{settings.HDFS_PROCESSED_PATH}/date={date_str}"

    logger.info(f"Starting Spark ETL Job - Input Path: '{raw_path}'")

    try:
        # Read raw CSV using explicit schema
        raw_df = spark.read.option("header", "true").schema(RAW_TRAFFIC_SCHEMA).csv(raw_path)

        if raw_df.rdd.isEmpty():
            logger.warning(f"Raw dataset at '{raw_path}' is empty. ETL job exiting.")
            return

        # Execute processing pipeline
        processed_df, etl_stats = process_traffic_data(raw_df)

        # Generate Data Quality Report
        generate_data_quality_metrics(raw_df, processed_df)

        # Write output in Snappy-compressed Parquet format
        logger.info(f"Writing Snappy Parquet dataset to: '{output_path}'...")
        (
            processed_df.write.mode("overwrite")
            .option("compression", "snappy")
            .parquet(output_path)
        )

        logger.info(f"[SUCCESS] Spark ETL completed! Processed Parquet written to '{output_path}'.")

    except Exception as e:
        logger.error(f"Spark ETL Processing Pipeline failed with error: {str(e)}", exc_info=True)
        raise e


def main():
    """
    CLI Entrypoint for Spark ETL job.
    """
    run_spark_etl_pipeline()


if __name__ == "__main__":
    main()
