#!/usr/bin/env bash
# ==============================================================================
# Batch Prediction Runner Script (scripts/run_prediction.sh)
# Triggers Batch Prediction Job for Peak Hour (17:30:00) Smoke Test
# ==============================================================================

set -eo pipefail

echo "======================================================================"
echo "[INFO] Launching Batch Prediction Engine Smoke Test..."
echo "======================================================================"

# Resolve project root directory
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${PROJECT_ROOT}"

export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH}"

# Execute batch prediction CLI for peak evening hour
"${PROJECT_ROOT}/venv/bin/python" -m src.prediction.batch_predict --datetime "2026-07-21 17:30:00"

echo "======================================================================"
echo "[SUCCESS] Batch Prediction Engine Smoke Test Completed!"
echo "======================================================================"
