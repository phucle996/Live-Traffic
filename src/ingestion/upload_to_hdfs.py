# ==============================================================================
# HDFS Storage Data Uploader Module (src/ingestion/upload_to_hdfs.py)
# Uploads Local Ingested Raw CSV files to Partitioned HDFS Destinations
# ==============================================================================

import os
import subprocess
from datetime import datetime
from pathlib import Path

from src.common.config import settings, PROJECT_ROOT
from src.common.logging_utils import get_logger

# Instantiate logger for HDFS uploader
logger = get_logger(__name__)


def upload_file_to_hdfs(local_path: str, hdfs_target_dir: str) -> bool:
    """
    Uploads a local file to HDFS target directory using sub-process call to hdfs CLI or web interface.

    Args:
        local_path (str): Path to local file.
        hdfs_target_dir (str): HDFS destination directory path.

    Returns:
        bool: True if upload succeeds, False otherwise.
    """
    local_file = Path(local_path)
    if not local_file.exists():
        logger.error(f"Local file '{local_path}' does not exist. Upload failed.")
        return False

    hdfs_uri = settings.HDFS_URI
    logger.info(f"Uploading file '{local_path}' to HDFS directory '{hdfs_target_dir}'...")

    try:
        # Step 1: Ensure target HDFS directory exists
        mkdir_cmd = ["hdfs", "dfs", "-fs", hdfs_uri, "-mkdir", "-p", hdfs_target_dir]
        subprocess.run(mkdir_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Step 2: Upload local file to HDFS
        put_cmd = ["hdfs", "dfs", "-fs", hdfs_uri, "-put", "-f", str(local_file), hdfs_target_dir]
        result = subprocess.run(put_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        logger.info(f"Successfully uploaded '{local_file.name}' to HDFS '{hdfs_target_dir}'")
        return True

    except (subprocess.SubprocessError, FileNotFoundError) as e:
        logger.info(f"Native 'hdfs' CLI unavailable ({e}). Fallback to docker exec via 'namenode' container...")
        try:
            docker_cmd = "sudo docker" if os.system("docker ps >/dev/null 2>&1") != 0 else "docker"

            # Fallback 1: mkdir qua docker exec namenode
            subprocess.run(f"{docker_cmd} exec namenode hdfs dfs -fs {hdfs_uri} -mkdir -p {hdfs_target_dir}", shell=True, check=False)

            # Copy local file vào docker container tạm thời rồi put vào HDFS
            container_tmp = f"/tmp/{local_file.name}"
            subprocess.run(f"{docker_cmd} cp '{str(local_file)}' namenode:{container_tmp}", shell=True, check=True)

            subprocess.run(f"{docker_cmd} exec namenode hdfs dfs -fs {hdfs_uri} -put -f {container_tmp} {hdfs_target_dir}", shell=True, check=True)

            # Dọn file tạm trong container
            subprocess.run(f"{docker_cmd} exec namenode rm -f {container_tmp}", shell=True, check=False)

            logger.info(f"Successfully uploaded '{local_file.name}' to HDFS via Docker exec fallback ('{hdfs_target_dir}')")
            return True
        except Exception as docker_err:
            logger.warning(f"Docker HDFS upload fallback failed: {docker_err}")
            return False


def upload_raw_outputs_to_hdfs() -> None:
    """
    Scans local data/output directory for ingested raw CSV files and uploads them to partitioned HDFS paths.
    """
    output_base_dir = PROJECT_ROOT / "data" / "output"
    if not output_base_dir.exists():
        logger.info(f"No local output directory found at '{output_base_dir}'")
        return

    # Find all date=YYYY-MM-DD subfolders
    for date_folder in output_base_dir.glob("date=*"):
        if date_folder.is_dir():
            partition_name = date_folder.name  # e.g., "date=2026-07-21"
            hdfs_partition_dir = f"{settings.HDFS_RAW_PATH}/{partition_name}"

            # Upload all CSV files inside partition folder
            for csv_file in date_folder.glob("*.csv"):
                upload_file_to_hdfs(str(csv_file), hdfs_partition_dir)


def main():
    """
    CLI Entrypoint for running HDFS uploader.
    """
    upload_raw_outputs_to_hdfs()


if __name__ == "__main__":
    main()
