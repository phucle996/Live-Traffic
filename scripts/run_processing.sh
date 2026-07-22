#!/usr/bin/env bash
# ==============================================================================
# Spark Processing Automation Script (scripts/run_processing.sh)
# Submits PySpark ETL Job to Spark Cluster & Processes Raw HDFS Data into Parquet
# ==============================================================================

set -eo pipefail

echo "======================================================================"
echo "[INFO] Launching Spark ETL Data Processing Job..."
echo "======================================================================"

# Resolve project root directory
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${PROJECT_ROOT}"

export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH}"

DOCKER_CMD="docker"
if ! docker ps >/dev/null 2>&1; then
    DOCKER_CMD="sudo docker"
fi

# Check if spark-submit command is available natively or inside docker
if command -v spark-submit &> /dev/null; then
    echo "[INFO] Running via local spark-submit..."
    spark-submit \
      --master "${SPARK_MASTER:-spark://spark-master:7077}" \
      --name "traffic-spark-etl" \
      src/processing/process_spark.py
elif ${DOCKER_CMD} compose ps | grep -q "spark-master"; then
    echo "[INFO] Submitting job inside spark-master container..."
    ${DOCKER_CMD} compose exec -e PYTHONPATH=/app spark-master /opt/spark/bin/spark-submit \
      --master spark://spark-master:7077 \
      --name "traffic-spark-etl" \
      /app/src/processing/process_spark.py
else
    echo "[INFO] Running Spark ETL script via venv python..."
    "${PROJECT_ROOT}/venv/bin/python" -m src.processing.process_spark
fi

echo "======================================================================"
echo "[SUCCESS] Spark ETL Data Processing Job Finished!"
echo "======================================================================"
