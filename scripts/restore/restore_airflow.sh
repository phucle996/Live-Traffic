#!/usr/bin/env bash
# ==============================================================================
# Airflow Restore Script (scripts/restore/restore_airflow.sh)
# Restores Airflow metadata DB and config from encrypted backup.
#
# Usage: bash scripts/restore/restore_airflow.sh <ENCRYPTED_BACKUP_FILE>
# Env:
#   BACKUP_ENCRYPTION_KEY — AES-256 passphrase
#   AIRFLOW_HOME          — Airflow home directory
#   AIRFLOW_DB_URI        — Airflow DB URI
# ==============================================================================

set -euo pipefail

BACKUP_FILE="${1:?Usage: restore_airflow.sh <encrypted_backup_file>}"
BACKUP_ENCRYPTION_KEY="${BACKUP_ENCRYPTION_KEY:?ERROR: BACKUP_ENCRYPTION_KEY must be set}"
AIRFLOW_HOME="${AIRFLOW_HOME:-/opt/airflow}"
AIRFLOW_DB_URI="${AIRFLOW_DB_URI:-sqlite:///airflow.db}"
RESTORE_DIR="/tmp/airflow_restore_$(date +%s)"

echo "========================================================"
echo "  Airflow Restore"
echo "  Source: ${BACKUP_FILE}"
echo "========================================================"

# Step 1: Stop Airflow scheduler and webserver before restore
echo "[INFO] Stopping Airflow services..."
pkill -f "airflow scheduler" 2>/dev/null || true
pkill -f "airflow webserver" 2>/dev/null || true
sleep 5

mkdir -p "${RESTORE_DIR}"

# Step 2: Decrypt and extract backup
echo "[INFO] Decrypting backup..."
openssl enc -d -aes-256-cbc -pbkdf2 \
    -pass env:BACKUP_ENCRYPTION_KEY \
    -in "${BACKUP_FILE}" \
    -out "${RESTORE_DIR}/databases.tar.gz"
tar -xzf "${RESTORE_DIR}/databases.tar.gz" -C "${RESTORE_DIR}/"

# Step 3: Restore Airflow metadata database
if find "${RESTORE_DIR}" -name "airflow_dump.sql" | grep -q .; then
    SQL_FILE=$(find "${RESTORE_DIR}" -name "airflow_dump.sql" | head -1)
    if echo "${AIRFLOW_DB_URI}" | grep -q "sqlite:///"; then
        AIRFLOW_DB="${AIRFLOW_DB_URI#sqlite:///}"
        [ -f "${AIRFLOW_DB}" ] && cp "${AIRFLOW_DB}" "${AIRFLOW_DB}.pre_restore"
        sqlite3 "${AIRFLOW_DB}" < "${SQL_FILE}"
        echo "[INFO] Airflow SQLite DB restored."
    elif echo "${AIRFLOW_DB_URI}" | grep -q "postgresql://"; then
        psql "${AIRFLOW_DB_URI}" < "${SQL_FILE}"
        echo "[INFO] Airflow PostgreSQL DB restored."
    fi
fi

# Step 4: Restore application config if present
if find "${RESTORE_DIR}" -type d -name "config" | grep -q .; then
    CONFIG_SRC=$(find "${RESTORE_DIR}" -maxdepth 3 -type d -name "config" | head -1)
    echo "[INFO] Restoring application config from backup..."
    cp -r "${CONFIG_SRC}" /app/config
fi

# Step 5: Restart Airflow
echo "[INFO] Starting Airflow scheduler and webserver..."
airflow scheduler -D 2>/dev/null || echo "[WARN] Could not auto-start scheduler — start manually."

rm -rf "${RESTORE_DIR}"
echo "[DONE] Airflow restore complete."
