#!/usr/bin/env bash
# ==============================================================================
# GBT Model Training Automation Script (scripts/run_training.sh)
# Triggers PySpark MLlib GBTRegressor Model Training Job
# ==============================================================================

set -eo pipefail

echo "======================================================================"
echo "[INFO] Launching Spark MLlib GBTRegressor Model Training Job..."
echo "======================================================================"

# Resolve project root directory
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${PROJECT_ROOT}"

export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH}"
export PYSPARK_PYTHON="${PROJECT_ROOT}/venv/bin/python"
export PYSPARK_DRIVER_PYTHON="${PROJECT_ROOT}/venv/bin/python"
export JAVA_HOME=/tmp/jdk17
export PATH=/tmp/jdk17/bin:${PATH}

echo "[INFO] Running GBT training job via venv python..."
"${PROJECT_ROOT}/venv/bin/python" -m src.training.train_gbt

echo "======================================================================"
echo "[SUCCESS] GBT Model Training Job Completed!"
echo "======================================================================"
