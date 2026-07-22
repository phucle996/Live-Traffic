#!/usr/bin/env bash
# ==============================================================================
# HDFS Safemode Waiter Script (scripts/wait_for_hdfs.sh)
# Polls HDFS NameNode until Safe mode is turned OFF to prevent race conditions
# ==============================================================================

set -eo pipefail

# Read NameNode host and port from environment or set defaults
HDFS_HOST="${HDFS_HOST:-namenode}"
HDFS_PORT="${HDFS_PORT:-9000}"
MAX_RETRIES=30
RETRY_INTERVAL=5

echo "======================================================================"
echo "[INFO] Polling HDFS NameNode at hdfs://${HDFS_HOST}:${HDFS_PORT}..."
echo "======================================================================"

DOCKER_CMD="docker"
if ! docker ps >/dev/null 2>&1; then
    DOCKER_CMD="sudo docker"
fi

check_safemode() {
    if command -v hdfs &>/dev/null; then
        hdfs dfsadmin -fs "hdfs://${HDFS_HOST}:${HDFS_PORT}" -safemode get 2>/dev/null
    else
        ${DOCKER_CMD} exec namenode hdfs dfsadmin -fs "hdfs://${HDFS_HOST}:${HDFS_PORT}" -safemode get 2>/dev/null
    fi
}

# Loop until NameNode is reachable and Safemode is OFF
retry_count=0
until check_safemode | grep -q "Safe mode is OFF"; do
    retry_count=$((retry_count + 1))
    
    # Check if max retries exceeded
    if [ "$retry_count" -ge "$MAX_RETRIES" ]; then
        echo "[ERROR] HDFS NameNode did not exit Safemode after $((MAX_RETRIES * RETRY_INTERVAL)) seconds. Exiting."
        exit 1
    fi
    
    echo "[WAIT] HDFS NameNode is starting up or in Safemode... Retry ${retry_count}/${MAX_RETRIES}. Waiting ${RETRY_INTERVAL}s."
    sleep "$RETRY_INTERVAL"
done

echo "======================================================================"
echo "[SUCCESS] HDFS NameNode is healthy and Safe mode is OFF!"
echo "======================================================================"
