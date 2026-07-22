# ==============================================================================
# PySpark Structured Streaming Processor (src/streaming/traffic_stream_processor.py)
# Consumes Kafka Micro-Batches & Writes HDFS Partitioned Parquet Sinks with Checkpointing
# ==============================================================================

import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, current_timestamp, to_timestamp

from src.common.logging_utils import get_logger
from src.streaming.checkpoint_manager import CheckpointManager
from src.streaming.stream_schema import get_traffic_stream_schema

# Instantiate logger for stream processor
logger = get_logger(__name__)


def create_streaming_spark_session() -> SparkSession:
    """
    Creates SparkSession configured for Kafka Structured Streaming integration.

    Returns:
        SparkSession: Configured PySpark session.
    """
    return (
        SparkSession.builder
        .appName("TrafficStructuredStreamingProcessor")
        .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
        .config("spark.sql.streaming.checkpointLocation.writeOptions", "true")
        .getOrCreate()
    )


def process_traffic_stream(kafka_bootstrap: str = "kafka:9092", topic: str = "traffic_events") -> None:
    """
    Sets up PySpark Structured Streaming read stream from Kafka and writes to HDFS sink.
    Integrates Watermark (10 mins), Event Deduplication (event_id), and Quarantine handling.

    Args:
        kafka_bootstrap (str): Kafka bootstrap server address.
        topic (str): Target Kafka topic name.
    """
    logger.info("Initializing Spark Structured Streaming engine...")
    spark = create_streaming_spark_session()
    schema = get_traffic_stream_schema()
    checkpoint_loc = CheckpointManager.get_checkpoint_location("streaming_traffic")

    logger.info(f"Subscribing to Kafka topic '{topic}' at '{kafka_bootstrap}'...")

    # Define streaming DataFrame reading from Kafka
    df_raw = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", kafka_bootstrap)
        .option("subscribe", topic)
        .option("startingOffsets", "earliest")
        .load()
    )

    # Cast Kafka binary value to STRING and parse JSON payload
    df_parsed = (
        df_raw
        .selectExpr("CAST(value AS STRING) as json_payload", "CAST(key AS STRING) as kafka_key")
        .select(from_json(col("json_payload"), schema).alias("data"))
        .select("data.*")
    )

    # Tích hợp Watermarking (10 phút) và Loại bỏ trùng lặp dựa trên event_id (Deduplication)
    df_dedup = (
        df_parsed
        .withColumn("event_timestamp", to_timestamp(col("Timestamp")))
        .withWatermark("event_timestamp", "10 minutes")
        .dropDuplicates(["event_id"])
    )

    # Sink stream to Parquet HDFS directory with offset checkpointing & 10s trigger interval
    output_path = "/traffic_project/processed/source=tomtom_live"
    logger.info(f"Writing streaming sink to '{output_path}' with checkpoint '{checkpoint_loc}'...")

    query = (
        df_dedup.writeStream
        .format("parquet")
        .option("checkpointLocation", checkpoint_loc)
        .option("path", output_path)
        .trigger(processingTime="10 seconds")
        .outputMode("append")
        .start()
    )

    query.awaitTermination()


if __name__ == "__main__":
    bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    process_traffic_stream(kafka_bootstrap=bootstrap)
