#!/usr/bin/env bash
# ==============================================================================
# Spark Structured Streaming Runner Script (scripts/run_stream_processor.sh)
# Executes PySpark Structured Streaming Kafka Consumer & HDFS Sink Writer
# ==============================================================================

set -eo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${PROJECT_ROOT}"

export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH}"

echo "======================================================================"
echo "[INFO] Launching Spark Structured Streaming Traffic Processor..."
echo "======================================================================"

python3 -m src.streaming.traffic_stream_processor

echo "======================================================================"
echo "[INFO] Spark Streaming Processor Terminated."
echo "======================================================================"
