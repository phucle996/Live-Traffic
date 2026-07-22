#!/usr/bin/env bash
# ==============================================================================
# MLflow Restore Script (scripts/restore/restore_mlflow.sh)
# Restores MLflow metadata DB and model artifacts from encrypted backup.
#
# Usage: bash scripts/restore/restore_mlflow.sh <ENCRYPTED_BACKUP_FILE>
# Env:
#   BACKUP_ENCRYPTION_KEY — AES-256 passphrase
#   PROJECT_ROOT          — project root directory
#   MLFLOW_BACKEND_URI    — MLflow DB URI
# ==============================================================================

set -euo pipefail

BACKUP_FILE="${1:?Usage: restore_mlflow.sh <encrypted_backup_file>}"
BACKUP_ENCRYPTION_KEY="${BACKUP_ENCRYPTION_KEY:?ERROR: BACKUP_ENCRYPTION_KEY must be set}"
PROJECT_ROOT="${PROJECT_ROOT:-/app}"
MLFLOW_BACKEND_URI="${MLFLOW_BACKEND_URI:-sqlite:///artifacts/mlflow/mlflow.db}"
RESTORE_DIR="/tmp/mlflow_restore_$(date +%s)"

echo "========================================================"
echo "  MLflow Restore"
echo "  Source: ${BACKUP_FILE}"
echo "========================================================"

mkdir -p "${RESTORE_DIR}"

# Step 1: Decrypt backup
echo "[INFO] Decrypting backup..."
openssl enc -d -aes-256-cbc -pbkdf2 \
    -pass env:BACKUP_ENCRYPTION_KEY \
    -in "${BACKUP_FILE}" \
    -out "${RESTORE_DIR}/models.tar.gz"

# Step 2: Extract
tar -xzf "${RESTORE_DIR}/models.tar.gz" -C "${RESTORE_DIR}/"

# Step 3: Restore MLflow SQLite database
if [ -f "${RESTORE_DIR}/models_backup_"*/mlflow_dump.sql ]; then
    SQL_FILE=$(find "${RESTORE_DIR}" -name "mlflow_dump.sql" | head -1)
    if echo "${MLFLOW_BACKEND_URI}" | grep -q "sqlite:///"; then
        SQLITE_PATH="${PROJECT_ROOT}/${MLFLOW_BACKEND_URI#sqlite:///}"
        mkdir -p "$(dirname "${SQLITE_PATH}")"
        # Backup current DB before overwrite
        [ -f "${SQLITE_PATH}" ] && cp "${SQLITE_PATH}" "${SQLITE_PATH}.pre_restore"
        sqlite3 "${SQLITE_PATH}" < "${SQL_FILE}"
        echo "[INFO] MLflow SQLite DB restored to ${SQLITE_PATH}"
    elif echo "${MLFLOW_BACKEND_URI}" | grep -q "postgresql://"; then
        psql "${MLFLOW_BACKEND_URI}" < "${SQL_FILE}"
        echo "[INFO] MLflow PostgreSQL DB restored."
    fi
fi

# Step 4: Restore model artifacts directory
if [ -d "${RESTORE_DIR}/models_backup_"*/artifacts ]; then
    ARTIFACTS_SRC=$(find "${RESTORE_DIR}" -maxdepth 2 -type d -name "artifacts" | head -1)
    # Backup current artifacts before overwrite
    [ -d "${PROJECT_ROOT}/artifacts" ] && mv "${PROJECT_ROOT}/artifacts" "${PROJECT_ROOT}/artifacts.pre_restore"
    cp -r "${ARTIFACTS_SRC}" "${PROJECT_ROOT}/artifacts"
    echo "[INFO] Model artifacts restored to ${PROJECT_ROOT}/artifacts"
fi

# Step 5: Restore MLOps registry.json
if find "${RESTORE_DIR}" -name "registry.json" | grep -q .; then
    REG_SRC=$(find "${RESTORE_DIR}" -name "registry.json" | head -1)
    mkdir -p "${PROJECT_ROOT}/artifacts/mlops"
    cp "${REG_SRC}" "${PROJECT_ROOT}/artifacts/mlops/registry.json"
    echo "[INFO] MLOps registry.json restored."
fi

rm -rf "${RESTORE_DIR}"
echo "[DONE] MLflow restore complete. Restart the API server to reload the model."
