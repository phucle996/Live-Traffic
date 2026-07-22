# ==============================================================================
# Partitioned HDFS & Local Raw Data Writer (src/ingestion/hdfs_writer.py)
# Writes Ingested Records Partitioned by Source & Event Date to HDFS
# ==============================================================================

import csv
import os
import uuid
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from src.common.config import settings, PROJECT_ROOT
from src.common.logging_utils import get_logger
from src.ingestion.upload_to_hdfs import upload_file_to_hdfs

# Instantiate logger for HDFS writer
logger = get_logger(__name__)


class PartitionedRawDataWriter:
    """
    Groups raw normalized traffic records by event_date and writes partitioned CSV outputs.
    """

    @staticmethod
    def extract_event_date(ts_str: str) -> str:
        """
        Extracts YYYY-MM-DD date string from timestamp input.
        """
        if not ts_str:
            return datetime.utcnow().strftime("%Y-%m-%d")
        
        # Take first 10 characters (YYYY-MM-DD)
        return str(ts_str).strip()[:10]

    @classmethod
    def write_partitioned_records(
        cls, records: List[Dict[str, Any]], source_label: str = "lab_offline"
    ) -> Dict[str, int]:
        """
        Groups records by event_date and writes partitioned CSV files.

        Args:
            records (List[Dict[str, Any]]): List of normalized traffic dictionaries.
            source_label (str): Source identifier ("lab_offline" or "tomtom_live").

        Returns:
            Dict[str, int]: Dictionary mapping event_date to count of written records.
        """
        if not records:
            logger.warning("No records provided to HDFS Partition Writer.")
            return {}

        logger.info(f"Partitioning {len(records)} record(s) for source '{source_label}'...")

        # Group records by event_date
        partition_map = defaultdict(list)
        for r in records:
            dt_key = cls.extract_event_date(r.get("Timestamp"))
            partition_map[dt_key].append(r)

        batch_uuid = str(uuid.uuid4())[:8]
        date_counts: Dict[str, int] = {}

        # Fields header for output CSV
        fields = [
            "Timestamp", "Location/Street", "District", "Latitude", "Longitude",
            "CurrentSpeed", "FreeFlowSpeed", "Confidence", "CurrentTravelTime",
            "FreeFlowTravelTime", "RoadClosure", "DataSource", "IngestedAtUtc", "IngestionBatchId"
        ]

        # Write local partition files under data/output/raw/
        out_base_dir = PROJECT_ROOT / "data" / "output" / "raw" / f"source={source_label}"

        for event_date, partition_records in partition_map.items():
            date_dir = out_base_dir / f"event_date={event_date}"
            date_dir.mkdir(parents=True, exist_ok=True)

            local_file = date_dir / f"batch_{batch_uuid}.csv"

            with open(local_file, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fields)
                writer.writeheader()
                writer.writerows(partition_records)

            date_counts[event_date] = len(partition_records)
            logger.info(f"Wrote {len(partition_records)} record(s) to local partition file '{local_file.name}' (Date: {event_date})")

            # Upload local partition file to HDFS path: /traffic_project/raw/source=<source>/event_date=<date>/
            hdfs_target_dir = f"{settings.HDFS_RAW_PATH}/source={source_label}/event_date={event_date}"
            upload_file_to_hdfs(str(local_file), hdfs_target_dir)

        return date_counts
