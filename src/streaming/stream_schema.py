# ==============================================================================
# Spark Streaming Schema V2 (src/streaming/stream_schema.py)
# Phase HERE-6 / ROAD-3 — Structural PySpark Schema cho Kafka Event Contract V2
# ==============================================================================

from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType, BooleanType, TimestampType
)

def get_traffic_event_v2_schema() -> StructType:
    """
    Trả về StructType PySpark tương thích hoàn toàn với TrafficEventV2 Protobuf/JSON Contract.
    """
    return StructType([
        StructField("event_id", StringType(), False),
        StructField("schema_version", StringType(), False),

        # Metadata Provider
        StructField("provider", StringType(), False),
        StructField("provider_request_id", StringType(), True),
        StructField("provider_segment_id", StringType(), True),
        StructField("provider_observed_at", StringType(), True),

        # Spatial Matching
        StructField("catalog_version", StringType(), True),
        StructField("segment_id", StringType(), True),
        StructField("matching_score", DoubleType(), True),

        # Timestamps & Batch
        StructField("event_time", StringType(), False),
        StructField("ingested_at", StringType(), True),
        StructField("batch_id", StringType(), True),
        StructField("cell_id", StringType(), True),

        # Traffic Metrics
        StructField("current_speed_kph", DoubleType(), True),
        StructField("free_flow_speed_kph", DoubleType(), True),
        StructField("travel_time_seconds", DoubleType(), True),
        StructField("free_flow_travel_time_seconds", DoubleType(), True),
        StructField("jam_factor", DoubleType(), True),
        StructField("confidence", DoubleType(), True),
        StructField("road_closed", BooleanType(), True),

        # Tọa độ & Hình học
        StructField("latitude", DoubleType(), True),
        StructField("longitude", DoubleType(), True),
        StructField("geometry_reference", StringType(), True),

        # Fallback tracking
        StructField("source_mode", StringType(), True),
        StructField("fallback_used", BooleanType(), True),
        StructField("fallback_reason", StringType(), True),
    ])
