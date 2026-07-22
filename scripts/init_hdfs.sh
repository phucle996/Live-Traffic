#!/usr/bin/env bash
# ==============================================================================
# HDFS Initial Folder Structure Provisioner (scripts/init_hdfs.sh)
# Creates required system paths on HDFS after NameNode Safemode is OFF
# ==============================================================================

set -eo pipefail

# Read HDFS URI from environment or default
HDFS_URI="${HDFS_URI:-hdfs://namenode:9000}"

echo "======================================================================"
echo "[INFO] Initializing HDFS directory structure on ${HDFS_URI}..."
echo "======================================================================"

# Wait for HDFS Safemode to clear before issuing mkdir commands
bash "$(dirname "$0")/wait_for_hdfs.sh"

# Define required HDFS directory paths
HDFS_PATHS=(
    "/traffic_project/raw"
    "/traffic_project/processed"
    "/traffic_project/models"
    "/traffic_project/predictions"
    "/traffic_project/metrics"
)

DOCKER_CMD="docker"
if ! docker ps >/dev/null 2>&1; then
    DOCKER_CMD="sudo docker"
fi

run_hdfs_cmd() {
    if command -v hdfs &>/dev/null; then
        hdfs "$@"
    else
        ${DOCKER_CMD} exec namenode hdfs "$@"
    fi
}

# Loop through paths and create directories on HDFS if they do not exist
for path in "${HDFS_PATHS[@]}"; do
    echo "[HDFS] Creating directory: ${path}"
    run_hdfs_cmd dfs -fs "${HDFS_URI}" -mkdir -p "${path}" || true
    echo "[HDFS] Granting full access permissions to: ${path}"
    run_hdfs_cmd dfs -fs "${HDFS_URI}" -chmod -R 777 "${path}" || true
done

echo "======================================================================"
echo "[SUCCESS] HDFS initialization complete! Directory status:"
run_hdfs_cmd dfs -fs "${HDFS_URI}" -ls -R /traffic_project || true
echo "======================================================================"
