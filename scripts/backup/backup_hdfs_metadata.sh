#!/usr/bin/env bash
# ==============================================================================
# HDFS Metadata Backup Script (scripts/backup/backup_hdfs_metadata.sh)
# Backs up HDFS NameNode FsImage and edit logs to off-cluster storage.
# Encrypted with AES-256 before upload. Retention enforced automatically.
#
# Usage: bash scripts/backup/backup_hdfs_metadata.sh
# Env:
#   BACKUP_DEST       — off-cluster destination (e.g. /mnt/nfs/backups or s3://bucket)
#   BACKUP_ENCRYPTION_KEY — AES-256 passphrase from Kubernetes Secret / CI secret
#   HDFS_NN_HTTP_ADDR — Active NameNode HTTP address (default: namenode1:9870)
#   RETENTION_DAYS    — How many days to retain backups (default: 30)
# ==============================================================================

set -euo pipefail

TIMESTAMP=$(date -u +"%Y%m%d_%H%M%SZ")
BACKUP_DEST="${BACKUP_DEST:-/tmp/backups}"
BACKUP_ENCRYPTION_KEY="${BACKUP_ENCRYPTION_KEY:?ERROR: BACKUP_ENCRYPTION_KEY must be set}"
HDFS_NN_HTTP_ADDR="${HDFS_NN_HTTP_ADDR:-localhost:9870}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
WORK_DIR="/tmp/hdfs_backup_${TIMESTAMP}"
ARCHIVE_NAME="hdfs_metadata_${TIMESTAMP}.tar.gz"
ENCRYPTED_NAME="${ARCHIVE_NAME}.enc"

echo "========================================================"
echo "  HDFS Metadata Backup — ${TIMESTAMP}"
echo "  Destination: ${BACKUP_DEST}"
echo "  Retention: ${RETENTION_DAYS} days"
echo "========================================================"

# Step 1: Create temp working directory
mkdir -p "${WORK_DIR}"

# Step 2: Force NameNode to checkpoint (flush edit logs into FsImage)
# This ensures the FsImage is up-to-date before copying
echo "[INFO] Triggering NameNode saveNamespace checkpoint..."
hdfs dfsadmin -safemode enter || echo "[WARN] Could not enter safe mode — continuing"
hdfs dfsadmin -saveNamespace || echo "[WARN] saveNamespace failed — copying latest available FsImage"
hdfs dfsadmin -safemode leave || true

# Step 3: Copy FsImage and edit logs from NameNode data directory to local temp
# Uses HDFS HTTP API to fetch the latest FsImage
echo "[INFO] Fetching FsImage from NameNode HTTP..."
curl -s -L "http://${HDFS_NN_HTTP_ADDR}/imagetransfer?getimage=1&txid=latest" \
    -o "${WORK_DIR}/fsimage_latest" || {
    echo "[WARN] HTTP fetch failed — falling back to local namenode dir"
    cp -r "${HADOOP_HOME:-/opt/hadoop}/dfs/name/current/" "${WORK_DIR}/namenode_current/"
}

# Step 4: Also export HDFS directory listing as JSON for audit trail
echo "[INFO] Exporting HDFS root directory listing..."
hdfs dfs -ls -R / 2>/dev/null > "${WORK_DIR}/hdfs_listing_${TIMESTAMP}.txt" || \
    echo "[WARN] Could not fetch HDFS listing (HDFS may be offline)"

# Step 5: Create compressed tarball of all collected metadata
echo "[INFO] Creating archive: ${ARCHIVE_NAME}..."
tar -czf "/tmp/${ARCHIVE_NAME}" -C "/tmp" "hdfs_backup_${TIMESTAMP}/"

# Step 6: Encrypt archive with AES-256-CBC using passphrase from env
# Security: -pass env: reads passphrase from environment variable, not CLI argument
echo "[INFO] Encrypting archive with AES-256-CBC..."
openssl enc -aes-256-cbc -salt -pbkdf2 \
    -pass env:BACKUP_ENCRYPTION_KEY \
    -in "/tmp/${ARCHIVE_NAME}" \
    -out "/tmp/${ENCRYPTED_NAME}"

# Remove unencrypted archive immediately after encryption
rm -f "/tmp/${ARCHIVE_NAME}"

# Step 7: Move encrypted backup to off-cluster destination
mkdir -p "${BACKUP_DEST}/hdfs_metadata"
mv "/tmp/${ENCRYPTED_NAME}" "${BACKUP_DEST}/hdfs_metadata/${ENCRYPTED_NAME}"
echo "[SUCCESS] Encrypted backup written: ${BACKUP_DEST}/hdfs_metadata/${ENCRYPTED_NAME}"

# Step 8: Enforce retention — delete backups older than RETENTION_DAYS
echo "[INFO] Enforcing ${RETENTION_DAYS}-day retention..."
find "${BACKUP_DEST}/hdfs_metadata" -name "*.enc" -mtime "+${RETENTION_DAYS}" -delete
echo "[INFO] Retention cleanup complete."

# Step 9: Cleanup working directory
rm -rf "${WORK_DIR}"

echo "[DONE] HDFS metadata backup complete: ${ENCRYPTED_NAME}"
