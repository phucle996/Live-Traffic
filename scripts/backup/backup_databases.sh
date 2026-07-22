#!/usr/bin/env bash
# ==============================================================================
# Database & Dashboard Backup Script (scripts/backup/backup_databases.sh)
# Backs up: Airflow metadata DB + App config + Grafana dashboard JSONs
# Encrypted with AES-256. Enforces retention policy automatically.
#
# Usage: bash scripts/backup/backup_databases.sh
# Env:
#   BACKUP_DEST           — off-cluster destination
#   BACKUP_ENCRYPTION_KEY — AES-256 passphrase from Kubernetes Secret
#   AIRFLOW_DB_URI        — Airflow DB URI (sqlite or postgresql)
#   GRAFANA_URL           — Grafana API base URL (default: http://localhost:3000)
#   GRAFANA_TOKEN         — Grafana API token (from environment secret)
#   PROJECT_ROOT          — project root directory
#   RETENTION_DAYS        — retention period in days (default: 30)
# ==============================================================================

set -euo pipefail

TIMESTAMP=$(date -u +"%Y%m%d_%H%M%SZ")
BACKUP_DEST="${BACKUP_DEST:-/tmp/backups}"
BACKUP_ENCRYPTION_KEY="${BACKUP_ENCRYPTION_KEY:?ERROR: BACKUP_ENCRYPTION_KEY must be set}"
AIRFLOW_DB_URI="${AIRFLOW_DB_URI:-sqlite:///airflow.db}"
GRAFANA_URL="${GRAFANA_URL:-http://localhost:3000}"
GRAFANA_TOKEN="${GRAFANA_TOKEN:-}"
PROJECT_ROOT="${PROJECT_ROOT:-/app}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
WORK_DIR="/tmp/db_backup_${TIMESTAMP}"
ARCHIVE_NAME="databases_${TIMESTAMP}.tar.gz"
ENCRYPTED_NAME="${ARCHIVE_NAME}.enc"

echo "========================================================"
echo "  Databases & Dashboards Backup — ${TIMESTAMP}"
echo "========================================================"

mkdir -p "${WORK_DIR}"

# Step 1: Dump Airflow metadata database
echo "[INFO] Backing up Airflow metadata database..."
if echo "${AIRFLOW_DB_URI}" | grep -q "sqlite:///"; then
    AIRFLOW_DB_FILE="${AIRFLOW_DB_URI#sqlite:///}"
    if [ -f "${AIRFLOW_DB_FILE}" ]; then
        sqlite3 "${AIRFLOW_DB_FILE}" ".dump" > "${WORK_DIR}/airflow_dump.sql"
        echo "[INFO] Airflow SQLite dump complete."
    else
        echo "[WARN] Airflow SQLite file not found: ${AIRFLOW_DB_FILE}"
    fi
elif echo "${AIRFLOW_DB_URI}" | grep -q "postgresql://"; then
    pg_dump "${AIRFLOW_DB_URI}" > "${WORK_DIR}/airflow_dump.sql"
    echo "[INFO] Airflow PostgreSQL dump complete."
fi

# Step 2: Backup application config directory (non-secret YAML configs)
echo "[INFO] Backing up application configuration..."
if [ -d "${PROJECT_ROOT}/config" ]; then
    cp -r "${PROJECT_ROOT}/config" "${WORK_DIR}/config"
    echo "[INFO] Config directory backed up."
fi

# Step 3: Export Grafana dashboards via HTTP API
# Only runs if GRAFANA_TOKEN is set — skip gracefully if Grafana is offline
if [ -n "${GRAFANA_TOKEN}" ]; then
    echo "[INFO] Exporting Grafana dashboards..."
    mkdir -p "${WORK_DIR}/grafana_dashboards"

    # Fetch list of all dashboard UIDs
    DASHBOARD_UIDS=$(curl -s -H "Authorization: Bearer ${GRAFANA_TOKEN}" \
        "${GRAFANA_URL}/api/search?type=dash-db" \
        2>/dev/null | python3 -c "
import json, sys
data = json.load(sys.stdin)
for d in data: print(d.get('uid',''))
" 2>/dev/null || true)

    # Export each dashboard JSON
    for UID in ${DASHBOARD_UIDS}; do
        curl -s -H "Authorization: Bearer ${GRAFANA_TOKEN}" \
            "${GRAFANA_URL}/api/dashboards/uid/${UID}" \
            -o "${WORK_DIR}/grafana_dashboards/${UID}.json" 2>/dev/null || true
    done
    echo "[INFO] Grafana dashboard export complete."
else
    echo "[WARN] GRAFANA_TOKEN not set — skipping Grafana export."
    # Copy local dashboard JSON files as fallback
    if [ -d "${PROJECT_ROOT}/monitoring/grafana/dashboards" ]; then
        cp -r "${PROJECT_ROOT}/monitoring/grafana/dashboards" "${WORK_DIR}/grafana_dashboards"
    fi
fi

# Step 4: Create compressed tarball
echo "[INFO] Creating archive: ${ARCHIVE_NAME}..."
tar -czf "/tmp/${ARCHIVE_NAME}" -C "/tmp" "db_backup_${TIMESTAMP}/"

# Step 5: Encrypt with AES-256-CBC
echo "[INFO] Encrypting archive..."
openssl enc -aes-256-cbc -salt -pbkdf2 \
    -pass env:BACKUP_ENCRYPTION_KEY \
    -in "/tmp/${ARCHIVE_NAME}" \
    -out "/tmp/${ENCRYPTED_NAME}"
rm -f "/tmp/${ARCHIVE_NAME}"

# Step 6: Move to off-cluster destination
mkdir -p "${BACKUP_DEST}/databases"
mv "/tmp/${ENCRYPTED_NAME}" "${BACKUP_DEST}/databases/${ENCRYPTED_NAME}"
echo "[SUCCESS] Encrypted backup: ${BACKUP_DEST}/databases/${ENCRYPTED_NAME}"

# Step 7: Enforce retention
echo "[INFO] Enforcing ${RETENTION_DAYS}-day retention..."
find "${BACKUP_DEST}/databases" -name "*.enc" -mtime "+${RETENTION_DAYS}" -delete

rm -rf "${WORK_DIR}"
echo "[DONE] Database & dashboard backup complete."
