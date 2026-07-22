#!/usr/bin/env bash
# ==============================================================================
# Ingestion Pipeline Script (scripts/run_ingestion.sh)
# Triggers Data Ingestion (API/Seed mode) & Uploads Raw Outputs to HDFS
# ==============================================================================

set -eo pipefail

echo "======================================================================"
echo "[INFO] Starting Traffic Data Ingestion Pipeline..."
echo "======================================================================"

# Resolve project root directory
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${PROJECT_ROOT}"

# Set PYTHONPATH to project root
export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH}"

# Execute ingestion crawler runner
"${PROJECT_ROOT}/venv/bin/python" -m src.ingestion.crawl_traffic

# Upload raw CSV outputs to HDFS
"${PROJECT_ROOT}/venv/bin/python" -m src.ingestion.upload_to_hdfs

echo "======================================================================"
echo "[SUCCESS] Data Ingestion Pipeline executed successfully!"
echo "======================================================================"
