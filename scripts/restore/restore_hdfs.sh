#!/usr/bin/env bash
# ==============================================================================
# HDFS Restore Script (scripts/restore/restore_hdfs.sh)
# Restores HDFS NameNode metadata from encrypted backup.
# WARNING: This procedure requires stopping HDFS services first.
#
# Usage: bash scripts/restore/restore_hdfs.sh <ENCRYPTED_BACKUP_FILE>
# Env:
#   BACKUP_ENCRYPTION_KEY — AES-256 passphrase
#   HADOOP_HOME           — Hadoop installation directory
# ==============================================================================

set -euo pipefail

BACKUP_FILE="${1:?Usage: restore_hdfs.sh <encrypted_backup_file>}"
BACKUP_ENCRYPTION_KEY="${BACKUP_ENCRYPTION_KEY:?ERROR: BACKUP_ENCRYPTION_KEY must be set}"
HADOOP_HOME="${HADOOP_HOME:-/opt/hadoop}"
RESTORE_DIR="/tmp/hdfs_restore_$(date +%s)"

echo "========================================================"
echo "  HDFS Metadata Restore"
echo "  Source: ${BACKUP_FILE}"
echo "========================================================"

# SAFETY CHECK: Require explicit confirmation before restoring
read -r -p "[CONFIRM] This will OVERWRITE current HDFS metadata. Type 'YES' to proceed: " CONFIRM
if [ "${CONFIRM}" != "YES" ]; then
    echo "[ABORTED] Restore cancelled by operator."
    exit 1
fi

mkdir -p "${RESTORE_DIR}"

# Step 1: Stop HDFS services before restore
echo "[INFO] Stopping HDFS services..."
"${HADOOP_HOME}/sbin/stop-dfs.sh" || echo "[WARN] HDFS may already be stopped."

# Step 2: Decrypt the backup archive
echo "[INFO] Decrypting backup..."
openssl enc -d -aes-256-cbc -pbkdf2 \
    -pass env:BACKUP_ENCRYPTION_KEY \
    -in "${BACKUP_FILE}" \
    -out "${RESTORE_DIR}/hdfs_metadata.tar.gz"

# Step 3: Extract to restore directory
echo "[INFO] Extracting archive..."
tar -xzf "${RESTORE_DIR}/hdfs_metadata.tar.gz" -C "${RESTORE_DIR}/"

# Step 4: Replace NameNode current/ directory with restored metadata
NN_DATA_DIR="${HADOOP_HOME}/dfs/name/current"
if [ -d "${NN_DATA_DIR}" ]; then
    echo "[INFO] Backing up current NameNode metadata (pre-restore safety copy)..."
    mv "${NN_DATA_DIR}" "${NN_DATA_DIR}.pre_restore_$(date +%s)"
fi

# Copy restored namenode metadata back
if [ -d "${RESTORE_DIR}/namenode_current" ]; then
    cp -r "${RESTORE_DIR}/namenode_current" "${NN_DATA_DIR}"
    echo "[INFO] NameNode metadata restored to ${NN_DATA_DIR}"
fi

# Step 5: Start HDFS services
echo "[INFO] Starting HDFS services..."
"${HADOOP_HOME}/sbin/start-dfs.sh"

# Step 6: Verify HDFS is accessible
echo "[INFO] Verifying HDFS health..."
sleep 15
hdfs dfsadmin -report 2>/dev/null | head -20 || echo "[WARN] HDFS report unavailable yet."

rm -rf "${RESTORE_DIR}"
echo "[DONE] HDFS metadata restore complete. Verify DataNode connectivity."
