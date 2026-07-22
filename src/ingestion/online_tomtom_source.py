# ==============================================================================
# Online TomTom Real Traffic Ingestion Source (src/ingestion/online_tomtom_source.py)
# Fetches Real-Time Traffic Speeds via TomTom Flow Segment API for Target Locations
# ==============================================================================

import uuid
from datetime import datetime
from typing import Dict, Any, List

from src.common.config import settings
from src.common.logging_utils import get_logger
from src.ingestion.base_source import TrafficDataSource
from src.ingestion.data_normalizer import DataNormalizer
from src.ingestion.hdfs_writer import PartitionedRawDataWriter
from src.ingestion.location_loader import LocationLoader
from src.ingestion.request_budget import RequestBudgetGuard
from src.ingestion.tomtom_client import TomTomTrafficClient

# Instantiate logger for online TomTom source
logger = get_logger(__name__)


class OnlineTomTomSource(TrafficDataSource):
    """
    Ingests real-time traffic flow data from TomTom API for target location coordinates.
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.TOMTOM_API_KEY
        self.client = TomTomTrafficClient(api_key=self.api_key)
        self.budget_guard = RequestBudgetGuard()

    def read(self) -> List[Dict[str, Any]]:
        """
        Reads location targets from data_converted.csv, executes TomTom API requests,
        and normalizes payloads into unified Data Contract structure.

        Returns:
            List[Dict[str, Any]]: Normalized real-time traffic records.
        """
        if not self.api_key or self.api_key in ("dummy_api_key_for_testing", "NOT_SET", ""):
            logger.error("DATA_SOURCE_MODE=online requested but TOMTOM_API_KEY is missing!")
            raise RuntimeError("DATA_SOURCE_MODE=online requires valid TOMTOM_API_KEY environment variable.")

        # Load location targets
        locations = LocationLoader.load_locations_list()
        if not locations:
            logger.warning("No location targets found for online crawling.")
            return []

        # Check daily API budget
        if not self.budget_guard.can_make_requests(len(locations)):
            logger.error(f"Online crawl halted: Daily request budget exceeded!")
            raise RuntimeError("Daily TomTom API request budget exceeded.")

        batch_id = str(uuid.uuid4())
        normalized_records: List[Dict[str, Any]] = []

        logger.info(f"Executing online TomTom API crawl batch for {len(locations)} location(s)...")

        for loc in locations:
            street = loc.get("Location/Street", "Unknown")
            district = loc.get("District", "Unknown")
            lat = float(loc["Latitude"])
            lon = float(loc["Longitude"])

            try:
                # Execute TomTom API call
                payload = self.client.get_flow_segment(lat, lon)
                self.budget_guard.record_requests(1)

                if payload and "flowSegmentData" in payload:
                    norm_row = DataNormalizer.normalize_tomtom_api_response(
                        payload, street=street, district=district, lat=lat, lon=lon, batch_id=batch_id
                    )
                    normalized_records.append(norm_row)
            except Exception as e:
                logger.error(f"Failed to crawl traffic for location '{street}': {e}")

        logger.info(f"Online Crawl Complete! Successfully collected {len(normalized_records)} real-time record(s).")
        return normalized_records

    def run_ingestion(self) -> Dict[str, int]:
        """
        Executes online ingestion and writes partitioned output to HDFS under /traffic_project/raw/source=tomtom_live/.

        Returns:
            Dict[str, int]: Date partition count summary.
        """
        records = self.read()
        if not records:
            return {}

        return PartitionedRawDataWriter.write_partitioned_records(records, source_label="tomtom_live")
