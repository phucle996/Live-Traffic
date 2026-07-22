#!/usr/bin/env bash
# ==============================================================================
# Model Artifacts & MLflow DB Backup (scripts/backup/backup_models.sh)
# Backs up: model artifacts dir + MLflow SQLite/Postgres DB + registry.json
# Encrypted with AES-256. Retains last 10 versions (configurable).
#
# Usage: bash scripts/backup/backup_models.sh
# Env:
#   BACKUP_DEST           — off-cluster destination
#   BACKUP_ENCRYPTION_KEY — AES-256 passphrase
#   PROJECT_ROOT          — project root directory (default: /app)
#   MLFLOW_BACKEND_URI    — MLflow tracking URI (default: sqlite:///mlflow.db)
#   RETENTION_VERSIONS    — max backup versions to retain (default: 10)
# ==============================================================================

set -euo pipefail

TIMESTAMP=$(date -u +"%Y%m%d_%H%M%SZ")
BACKUP_DEST="${BACKUP_DEST:-/tmp/backups}"
BACKUP_ENCRYPTION_KEY="${BACKUP_ENCRYPTION_KEY:?ERROR: BACKUP_ENCRYPTION_KEY must be set}"
PROJECT_ROOT="${PROJECT_ROOT:-/app}"
MLFLOW_BACKEND_URI="${MLFLOW_BACKEND_URI:-sqlite:///artifacts/mlflow/mlflow.db}"
RETENTION_VERSIONS="${RETENTION_VERSIONS:-10}"
WORK_DIR="/tmp/models_backup_${TIMESTAMP}"
ARCHIVE_NAME="models_${TIMESTAMP}.tar.gz"
ENCRYPTED_NAME="${ARCHIVE_NAME}.enc"

echo "========================================================"
echo "  Model Artifacts & MLflow Backup — ${TIMESTAMP}"
echo "========================================================"

mkdir -p "${WORK_DIR}"

# Step 1: Copy model artifacts directory (GBT model, metrics, MLOps registry)
echo "[INFO] Copying model artifacts..."
if [ -d "${PROJECT_ROOT}/artifacts" ]; then
    cp -r "${PROJECT_ROOT}/artifacts" "${WORK_DIR}/artifacts"
    echo "[INFO] Copied artifacts/ ($(du -sh "${PROJECT_ROOT}/artifacts" | cut -f1))"
else
    echo "[WARN] artifacts/ directory not found — skipping"
fi

# Step 2: Dump MLflow DB (supports SQLite and PostgreSQL)
echo "[INFO] Backing up MLflow database..."
if echo "${MLFLOW_BACKEND_URI}" | grep -q "sqlite:///"; then
    # Extract SQLite file path from URI
    SQLITE_PATH="${PROJECT_ROOT}/${MLFLOW_BACKEND_URI#sqlite:///}"
    if [ -f "${SQLITE_PATH}" ]; then
        # Use .dump to export schema + data as SQL text (portable across versions)
        sqlite3 "${SQLITE_PATH}" ".dump" > "${WORK_DIR}/mlflow_dump.sql"
        echo "[INFO] MLflow SQLite dump complete: ${WORK_DIR}/mlflow_dump.sql"
    else
        echo "[WARN] MLflow SQLite file not found: ${SQLITE_PATH}"
    fi
elif echo "${MLFLOW_BACKEND_URI}" | grep -q "postgresql://"; then
    # Dump PostgreSQL MLflow database
    pg_dump "${MLFLOW_BACKEND_URI}" > "${WORK_DIR}/mlflow_dump.sql"
    echo "[INFO] MLflow PostgreSQL dump complete."
fi

# Step 3: Also copy MLOps model registry JSON (SOT for version/stage tracking)
if [ -f "${PROJECT_ROOT}/artifacts/mlops/registry.json" ]; then
    cp "${PROJECT_ROOT}/artifacts/mlops/registry.json" "${WORK_DIR}/registry.json"
fi

# Step 4: Create compressed tarball
echo "[INFO] Creating archive: ${ARCHIVE_NAME}..."
tar -czf "/tmp/${ARCHIVE_NAME}" -C "/tmp" "models_backup_${TIMESTAMP}/"

# Step 5: Encrypt archive with AES-256-CBC
echo "[INFO] Encrypting archive..."
openssl enc -aes-256-cbc -salt -pbkdf2 \
    -pass env:BACKUP_ENCRYPTION_KEY \
    -in "/tmp/${ARCHIVE_NAME}" \
    -out "/tmp/${ENCRYPTED_NAME}"
rm -f "/tmp/${ARCHIVE_NAME}"

# Step 6: Move to off-cluster destination
mkdir -p "${BACKUP_DEST}/models"
mv "/tmp/${ENCRYPTED_NAME}" "${BACKUP_DEST}/models/${ENCRYPTED_NAME}"
echo "[SUCCESS] Encrypted backup: ${BACKUP_DEST}/models/${ENCRYPTED_NAME}"

# Step 7: Enforce version retention — delete oldest backups beyond RETENTION_VERSIONS
# Lists files sorted by time, removes files beyond retention count
BACKUP_COUNT=$(ls "${BACKUP_DEST}/models/"*.enc 2>/dev/null | wc -l)
if [ "${BACKUP_COUNT}" -gt "${RETENTION_VERSIONS}" ]; then
    EXCESS=$((BACKUP_COUNT - RETENTION_VERSIONS))
    echo "[INFO] Removing ${EXCESS} old model backup(s) beyond ${RETENTION_VERSIONS} retention..."
    ls -t "${BACKUP_DEST}/models/"*.enc | tail -n "${EXCESS}" | xargs rm -f
fi

rm -rf "${WORK_DIR}"
echo "[DONE] Model artifacts & MLflow backup complete."
