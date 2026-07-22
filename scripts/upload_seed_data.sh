#!/usr/bin/env bash
# ==============================================================================
# Seed Data Upload Script (scripts/upload_seed_data.sh)
# Forces INGESTION_MODE=seed and uploads sample seed data to HDFS
# ==============================================================================

set -eo pipefail

echo "======================================================================"
echo "[INFO] Running Ingestion in SEED Mode & Uploading to HDFS..."
echo "======================================================================"

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${PROJECT_ROOT}"

# Set environment variables for seed mode
export INGESTION_MODE=seed
export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH}"

# Execute ingestion in seed mode
python3 -m src.ingestion.crawl_traffic

# Upload seed data to HDFS
python3 -m src.ingestion.upload_to_hdfs

echo "======================================================================"
echo "[SUCCESS] Seed data upload pipeline finished!"
echo "======================================================================"
