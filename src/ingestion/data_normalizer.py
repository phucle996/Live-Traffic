# ==============================================================================
# Unified Data Normalizer Engine (src/ingestion/data_normalizer.py)
# Normalizes Offline Lab CSVs & Online TomTom API Payloads to Unified Schema
# ==============================================================================

import uuid
from datetime import datetime
from typing import Dict, Any, List, Union

from src.common.logging_utils import get_logger

# Instantiate logger for data normalizer
logger = get_logger(__name__)


class DataNormalizer:
    """
    Normalizes heterogeneous raw traffic data sources into a unified Data Contract schema.
    """

    @staticmethod
    def normalize_offline_dataframe(raw_df, batch_id: str = None):
        """
        Normalizes raw historical Lab CSV DataFrame into unified Data Contract structure.

        Args:
            raw_df: Raw offline CSV DataFrame or list of dicts.
            batch_id (str): Optional UUID batch identifier.

        Returns:
            Normalized DataFrame or list of dicts.
        """
        batch_id = batch_id or str(uuid.uuid4())
        now_utc = datetime.utcnow()

        normalized_rows: List[Dict[str, Any]] = []

        # Support both Pandas DataFrame and list of dicts
        try:
            import pandas as pd
            is_df = isinstance(raw_df, pd.DataFrame)
        except ImportError:
            is_df = False

        if is_df:
            for idx, row in raw_df.iterrows():
                ts_str = str(row.get("Timestamp", "")).strip()
                normalized_rows.append({
                    "Timestamp": ts_str,
                    "Location/Street": str(row.get("Location/Street", row.get("Street", "Unknown"))).strip(),
                    "District": str(row.get("District", "Unknown")).strip(),
                    "Latitude": float(row.get("Latitude", 0.0)),
                    "Longitude": float(row.get("Longitude", 0.0)),
                    "CurrentSpeed": float(row.get("CurrentSpeed", 0.0)),
                    "FreeFlowSpeed": float(row.get("FreeFlowSpeed", 45.0)),
                    "Confidence": float(row.get("Confidence", 1.0)),
                    "CurrentTravelTime": None,
                    "FreeFlowTravelTime": None,
                    "RoadClosure": None,
                    "DataSource": "lab_offline",
                    "IngestedAtUtc": now_utc,
                    "IngestionBatchId": batch_id,
                })
        else:
            for row in raw_df:
                ts_str = str(row.get("Timestamp", "")).strip()
                normalized_rows.append({
                    "Timestamp": ts_str,
                    "Location/Street": str(row.get("Location/Street", row.get("Street", "Unknown"))).strip(),
                    "District": str(row.get("District", "Unknown")).strip(),
                    "Latitude": float(row.get("Latitude", 0.0)),
                    "Longitude": float(row.get("Longitude", 0.0)),
                    "CurrentSpeed": float(row.get("CurrentSpeed", 0.0)),
                    "FreeFlowSpeed": float(row.get("FreeFlowSpeed", 45.0)),
                    "Confidence": float(row.get("Confidence", 1.0)),
                    "CurrentTravelTime": None,
                    "FreeFlowTravelTime": None,
                    "RoadClosure": None,
                    "DataSource": "lab_offline",
                    "IngestedAtUtc": now_utc,
                    "IngestionBatchId": batch_id,
                })

        logger.info(f"Normalized {len(normalized_rows)} offline record(s) into unified schema (Batch: {batch_id}).")
        try:
            import pandas as pd
            return pd.DataFrame(normalized_rows)
        except ImportError:
            return normalized_rows

    @staticmethod
    def normalize_tomtom_api_response(
        api_payload: dict,
        street: str,
        district: str,
        lat: float,
        lon: float,
        batch_id: str = None,
    ) -> Dict[str, Any]:
        """
        Normalizes single TomTom Traffic Flow Segment API JSON response into unified Data Contract row.

        Args:
            api_payload (dict): Raw JSON response from TomTom API.
            street (str): Street location name.
            district (str): District name.
            lat (float): Latitude coordinate.
            lon (float): Longitude coordinate.
            batch_id (str): Optional UUID batch identifier.

        Returns:
            Dict[str, Any]: Normalized dictionary row matching unified schema.
        """
        flow_data = api_payload.get("flowSegmentData", {})
        batch_id = batch_id or str(uuid.uuid4())
        now_utc = datetime.utcnow()

        current_speed = float(flow_data.get("currentSpeed", 0.0))
        free_flow_speed = float(flow_data.get("freeFlowSpeed", 45.0))
        confidence = float(flow_data.get("confidence", 1.0))
        current_travel_time = flow_data.get("currentTravelTime")
        free_flow_travel_time = flow_data.get("freeFlowTravelTime")
        road_closure = flow_data.get("roadClosure")

        return {
            "Timestamp": now_utc.strftime("%Y-%m-%d %H:%M:%S"),
            "Location/Street": street,
            "District": district,
            "Latitude": lat,
            "Longitude": lon,
            "CurrentSpeed": current_speed,
            "FreeFlowSpeed": free_flow_speed,
            "Confidence": confidence,
            "CurrentTravelTime": int(current_travel_time) if current_travel_time is not None else None,
            "FreeFlowTravelTime": int(free_flow_travel_time) if free_flow_travel_time is not None else None,
            "RoadClosure": bool(road_closure) if road_closure is not None else None,
            "DataSource": "tomtom_live",
            "IngestedAtUtc": now_utc,
            "IngestionBatchId": batch_id,
        }
