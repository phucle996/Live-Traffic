#!/usr/bin/env bash
# ==============================================================================
# Offline Ingestion Runner Script (scripts/run_offline_ingestion.sh)
# Executes Offline Lab Data Ingestion to HDFS Partitioned Storage
# ==============================================================================

set -eo pipefail

echo "======================================================================"
echo "[INFO] Running Offline Lab Data Ingestion Pipeline..."
echo "[INFO] Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
echo "======================================================================"

# Resolve project root directory
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${PROJECT_ROOT}"

export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH}"

# Force offline mode
export DATA_SOURCE_MODE=offline

# Execute Offline Ingestion Python Module
python3 -c "
from src.ingestion.offline_lab_source import OfflineLabSource
source = OfflineLabSource()
counts = source.run_ingestion()
print('Partition Summary:', counts)
"

echo "======================================================================"
echo "[SUCCESS] Offline Lab Data Ingestion Completed Successfully!"
echo "======================================================================"
