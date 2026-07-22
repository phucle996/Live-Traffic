# ==============================================================================
# Data Quality Reporting Engine (src/processing/data_quality_report.py)
# Generates Structured JSON & Console Reports on Dataset Completeness & Quality
# ==============================================================================

import json
from typing import Dict, Any
from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from src.common.logging_utils import get_logger

# Instantiate logger for quality reporting engine
logger = get_logger(__name__)


def generate_data_quality_metrics(raw_df: DataFrame, processed_df: DataFrame) -> Dict[str, Any]:
    """
    Computes data quality statistics comparing raw ingested DataFrame and processed feature DataFrame.

    Args:
        raw_df (DataFrame): Raw PySpark DataFrame.
        processed_df (DataFrame): Processed PySpark feature DataFrame.

    Returns:
        Dict[str, Any]: Dictionary containing structured data quality metrics.
    """
    logger.info("Computing data quality statistics...")

    # Calculate row counts
    raw_count = raw_df.count()
    processed_count = processed_df.count()
    dropped_count = raw_count - processed_count

    # Calculate speed summary statistics on processed dataset
    speed_stats = processed_df.select(
        F.avg("CurrentSpeed").alias("avg_speed"),
        F.min("CurrentSpeed").alias("min_speed"),
        F.max("CurrentSpeed").alias("max_speed"),
        F.avg("FreeFlowSpeed").alias("avg_free_flow"),
        F.avg("CongestionRatio").alias("avg_congestion_ratio"),
    ).collect()[0]

    # Calculate confidence score distribution
    conf_stats = raw_df.select(
        F.avg("Confidence").alias("avg_confidence"),
        F.min("Confidence").alias("min_confidence"),
    ).collect()[0]

    metrics = {
        "summary": {
            "raw_rows": raw_count,
            "processed_rows": processed_count,
            "dropped_rows": dropped_count,
            "retention_rate_pct": (processed_count / raw_count * 100.0) if raw_count > 0 else 0.0,
        },
        "traffic_speed_metrics": {
            "avg_current_speed_kmh": round(float(speed_stats["avg_speed"] or 0), 2),
            "min_current_speed_kmh": round(float(speed_stats["min_speed"] or 0), 2),
            "max_current_speed_kmh": round(float(speed_stats["max_speed"] or 0), 2),
            "avg_free_flow_speed_kmh": round(float(speed_stats["avg_free_flow"] or 0), 2),
            "avg_congestion_ratio": round(float(speed_stats["avg_congestion_ratio"] or 0), 4),
        },
        "sensor_confidence": {
            "avg_confidence": round(float(conf_stats["avg_confidence"] or 0), 4),
            "min_confidence": round(float(conf_stats["min_confidence"] or 0), 4),
        },
    }

    logger.info(f"Data Quality Metrics Summary: {json.dumps(metrics['summary'])}")
    return metrics
