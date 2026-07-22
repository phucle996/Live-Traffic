# ==============================================================================
# Offline Lab Data Source Engine (src/ingestion/offline_lab_source.py)
# Reads Raw Historical Lab CSV Files, Normalizes Records, & Ingests to HDFS
# ==============================================================================

import csv
from pathlib import Path
from typing import Dict, Any, List

from src.common.config import settings, PROJECT_ROOT
from src.common.logging_utils import get_logger
from src.ingestion.base_source import TrafficDataSource
from src.ingestion.data_normalizer import DataNormalizer
from src.ingestion.hdfs_writer import PartitionedRawDataWriter
from src.ingestion.ingestion_manifest import IngestionManifest

# Instantiate logger for offline lab source
logger = get_logger(__name__)


class OfflineLabSource(TrafficDataSource):
    """
    Ingests real raw historical CSV files provided in Lab 5 with SHA-256 idempotency.
    """

    def __init__(self, raw_dir: str = None):
        self.raw_dir = Path(raw_dir or settings.LAB_DATA_RAW_DIR)
        self.manifest = IngestionManifest()

    def read(self) -> List[Dict[str, Any]]:
        """
        Reads all raw historical CSVs in data/lab_raw/*.csv, applies idempotency checks,
        normalizes records, and returns list of clean dictionaries matching UNIFIED_RAW_TRAFFIC_SCHEMA.

        Returns:
            List[Dict[str, Any]]: Normalized traffic records.
        """
        if not self.raw_dir.exists():
            logger.error(f"Raw lab data directory not found at '{self.raw_dir}'")
            return []

        logger.info(f"Scanning raw historical CSV files in '{self.raw_dir}'...")
        all_normalized_records: List[Dict[str, Any]] = []
        skipped_count = 0
        processed_file_count = 0

        # Discover all raw CSV files in data/lab_raw/
        csv_files = sorted(list(self.raw_dir.glob("*.csv")))
        logger.info(f"Found {len(csv_files)} total raw CSV file(s) for ingestion inspection.")

        for csv_file in csv_files:
            # Exclude process_data_spark.csv reference file
            if csv_file.name == "process_data_spark.csv":
                continue

            # Idempotency Check: Skip if file was already ingested and unchanged
            if self.manifest.is_file_processed(csv_file):
                skipped_count += 1
                continue

            # Read CSV file using Python standard csv library
            file_records: List[Dict[str, Any]] = []
            try:
                with open(csv_file, "r", encoding="utf-8", errors="ignore") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        file_records.append(dict(row))
            except Exception as e:
                logger.error(f"Error reading raw CSV '{csv_file.name}': {e}")
                continue

            if not file_records:
                # Mark empty file as processed to avoid re-scanning
                self.manifest.mark_file_processed(csv_file, row_count=0)
                continue

            # Apply DataNormalizer
            norm_records = DataNormalizer.normalize_offline_dataframe(file_records)

            # Convert to list of dicts if pandas DataFrame returned
            if hasattr(norm_records, "to_dict"):
                norm_records = norm_records.to_dict(orient="records")

            all_normalized_records.extend(norm_records)

            # Mark file processed in checksum manifest
            self.manifest.mark_file_processed(csv_file, row_count=len(norm_records))
            processed_file_count += 1

        logger.info(
            f"Offline Ingestion Scan Complete! Processed {processed_file_count} new file(s), "
            f"skipped {skipped_count} unchanged file(s). Total normalized records: {len(all_normalized_records)}"
        )
        return all_normalized_records

    def run_ingestion(self) -> Dict[str, int]:
        """
        Executes complete offline ingestion pipeline: reads CSVs, normalizes records,
        and writes partitioned datasets to HDFS under /traffic_project/raw/source=lab_offline/.

        Returns:
            Dict[str, int]: Event date partition record count summary.
        """
        records = self.read()
        if not records:
            logger.warning("No new records to ingest. All files up to date in manifest.")
            return {}

        # Write partitioned CSVs to local output and HDFS
        counts = PartitionedRawDataWriter.write_partitioned_records(records, source_label="lab_offline")
        return counts
