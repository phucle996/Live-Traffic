#!/usr/bin/env bash
# ==============================================================================
# End-to-End Master Pipeline Runner (scripts/run_pipeline.sh)
# Executes Sequential Big Data Pipeline with Timestamped Stage Logs & Fail-Fast Traps
# ==============================================================================

set -eo pipefail

START_TIME=$(date +%s)
echo "======================================================================"
echo "[INFO] Starting End-to-End Traffic Prediction Pipeline..."
echo "[INFO] Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
echo "======================================================================"

# Resolve project root directory
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${PROJECT_ROOT}"

export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH}"
export PYSPARK_PYTHON="${PROJECT_ROOT}/venv/bin/python"
export PYSPARK_DRIVER_PYTHON="${PROJECT_ROOT}/venv/bin/python"
export JAVA_HOME=/tmp/jdk17
export PATH=/tmp/jdk17/bin:${PATH}

# Stage Helper Function to Log Stage Execution & Timing
run_stage() {
    local stage_name="$1"
    local stage_cmd="$2"
    
    echo ""
    echo "----------------------------------------------------------------------"
    echo "[STAGE START] ${stage_name}"
    echo "----------------------------------------------------------------------"
    
    local stage_start=$(date +%s)
    
    # Execute stage command
    eval "${stage_cmd}"
    
    local stage_end=$(date +%s)
    local stage_duration=$((stage_end - stage_start))
    
    echo "[STAGE COMPLETE] ${stage_name} (Duration: ${stage_duration}s)"
}

# ------------------------------------------------------------------------------
# PIPELINE STAGE EXECUTION SEQUENCE
# ------------------------------------------------------------------------------

# Stage 1: Initialize HDFS Storage Structure
run_stage "Stage 1: HDFS Directory Initialization" "bash scripts/init_hdfs.sh || true"

# Stage 2: Data Ingestion (API / Seed Mode)
run_stage "Stage 2: Data Ingestion (TomTom API / Seed CSV)" "bash scripts/run_ingestion.sh"

# Stage 3: Spark ETL Data Cleaning & Feature Processing
run_stage "Stage 3: Spark ETL Processing (Parquet)" "bash scripts/run_processing.sh"

# Stage 4: Exploratory Data Analysis (EDA Aggregations)
run_stage "Stage 4: Exploratory Data Analysis & Report Artifacts" "\"${PROJECT_ROOT}/venv/bin/python\" -m src.processing.exploratory_analysis || true"

# Stage 5: Spark MLlib GBT Model Training
run_stage "Stage 5: Spark MLlib GBTRegressor Model Training" "bash scripts/run_training.sh"

# Stage 6: Batch Prediction Smoke Test
run_stage "Stage 6: Batch Prediction Engine Smoke Test" "bash scripts/run_prediction.sh"

END_TIME=$(date +%s)
TOTAL_DURATION=$((END_TIME - START_TIME))

echo ""
echo "======================================================================"
echo "[SUCCESS] END-TO-END PIPELINE COMPLETED SUCCESSFULLY!"
echo "[INFO] Total Execution Time: ${TOTAL_DURATION} seconds"
echo "======================================================================"
