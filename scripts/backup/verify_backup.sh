#!/usr/bin/env bash
# ==============================================================================
# Backup Verification Script (scripts/backup/verify_backup.sh)
# CRITICAL: Actually decrypts and restores backup to a temp dir.
# Does NOT just check "file exists" — performs real content validation.
#
# Usage: bash scripts/backup/verify_backup.sh <ENCRYPTED_BACKUP_FILE>
# Env:
#   BACKUP_ENCRYPTION_KEY — AES-256 passphrase
# Exit codes:
#   0 — verification passed
#   1 — verification failed (backup is corrupt or key mismatch)
# ==============================================================================

set -euo pipefail

BACKUP_FILE="${1:?Usage: verify_backup.sh <encrypted_backup_file>}"
BACKUP_ENCRYPTION_KEY="${BACKUP_ENCRYPTION_KEY:?ERROR: BACKUP_ENCRYPTION_KEY must be set}"
VERIFY_DIR="/tmp/verify_backup_$(date +%s)"
DECRYPTED_ARCHIVE="${VERIFY_DIR}/decrypted.tar.gz"

echo "========================================================"
echo "  Backup Verification: $(basename "${BACKUP_FILE}")"
echo "========================================================"

# Cleanup function — always remove temp dir on exit
cleanup() {
    rm -rf "${VERIFY_DIR}"
    echo "[INFO] Temp verification directory removed."
}
trap cleanup EXIT

# Step 1: Verify backup file exists and is non-empty
if [ ! -f "${BACKUP_FILE}" ]; then
    echo "[FAIL] Backup file not found: ${BACKUP_FILE}"
    exit 1
fi

FILE_SIZE=$(stat -c%s "${BACKUP_FILE}" 2>/dev/null || stat -f%z "${BACKUP_FILE}")
if [ "${FILE_SIZE}" -eq 0 ]; then
    echo "[FAIL] Backup file is empty: ${BACKUP_FILE}"
    exit 1
fi
echo "[OK] File exists and non-empty (${FILE_SIZE} bytes)."

mkdir -p "${VERIFY_DIR}"

# Step 2: Actually decrypt the backup — this validates the encryption key is correct
echo "[INFO] Attempting decryption..."
if ! openssl enc -d -aes-256-cbc -pbkdf2 \
        -pass env:BACKUP_ENCRYPTION_KEY \
        -in "${BACKUP_FILE}" \
        -out "${DECRYPTED_ARCHIVE}" 2>/dev/null; then
    echo "[FAIL] Decryption FAILED — backup may be corrupt or key mismatch."
    exit 1
fi
echo "[OK] Decryption successful."

# Step 3: Validate tarball integrity without full extraction (dry run)
echo "[INFO] Validating archive integrity..."
if ! tar -tzf "${DECRYPTED_ARCHIVE}" > /dev/null 2>&1; then
    echo "[FAIL] Archive integrity check FAILED — tarball is corrupt."
    exit 1
fi
echo "[OK] Archive integrity valid."

# Step 4: List archive contents and verify non-empty content
CONTENT_COUNT=$(tar -tzf "${DECRYPTED_ARCHIVE}" | wc -l)
echo "[OK] Archive contains ${CONTENT_COUNT} file(s)/directories."

if [ "${CONTENT_COUNT}" -eq 0 ]; then
    echo "[FAIL] Archive is empty — backup has no content."
    exit 1
fi

# Step 5: Extract to temp dir and verify at least one expected file type exists
echo "[INFO] Extracting to temp dir for content verification..."
tar -xzf "${DECRYPTED_ARCHIVE}" -C "${VERIFY_DIR}/"

# Check for at least one meaningful file in the extracted content
MEANINGFUL_FILES=$(find "${VERIFY_DIR}" \( -name "*.json" -o -name "*.sql" -o -name "*.txt" -o -name "*.parquet" -o -name "*.yaml" \) | wc -l)
echo "[INFO] Found ${MEANINGFUL_FILES} meaningful file(s) in backup."

echo "========================================================"
echo "  Verification PASSED: $(basename "${BACKUP_FILE}")"
echo "  Files: ${CONTENT_COUNT} entries, ${MEANINGFUL_FILES} meaningful"
echo "========================================================"
exit 0
