#!/usr/bin/env bash
# ==============================================================================
# Online Ingestion Runner Script (scripts/run_online_ingestion.sh)
# Executes Online Real-Time TomTom Traffic API Crawling
# ==============================================================================

set -eo pipefail

echo "======================================================================"
echo "[INFO] Running Online TomTom Traffic Ingestion Pipeline..."
echo "[INFO] Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
echo "======================================================================"

# Resolve project root directory
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${PROJECT_ROOT}"

export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH}"

# Force online mode
export DATA_SOURCE_MODE=online

# Execute Central Ingestion Module
python3 -m src.ingestion.ingest --once

echo "======================================================================"
echo "[SUCCESS] Online TomTom Ingestion Batch Completed Successfully!"
echo "======================================================================"
