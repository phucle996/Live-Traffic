# ==============================================================================
# Location Loader Module (src/ingestion/location_loader.py)
# Reads data_converted.csv, Splits Combined Coordinates, & Enforces Boundary Rules
# ==============================================================================

import csv
from pathlib import Path
from typing import Dict, Any, List, Union

from src.common.config import settings
from src.common.logging_utils import get_logger

# Instantiate logger for location loader
logger = get_logger(__name__)


class LocationLoader:
    """
    Parses and validates location target coordinates from data_converted.csv.
    """

    @staticmethod
    def load_locations_list(file_path: str = None) -> List[Dict[str, Any]]:
        """
        Loads location target CSV, splits combined 'Latitude,Longitude' column,
        validates coordinate bounds (-90 to 90 lat, -180 to 180 lon), and returns list of dictionaries.

        Args:
            file_path (str): Optional path to locations CSV.

        Returns:
            List[Dict[str, Any]]: List of clean location dictionaries with separate Latitude and Longitude.
        """
        path = Path(file_path or settings.LOCATIONS_FILE)
        if not path.exists():
            logger.error(f"Locations file not found at '{path}'")
            raise FileNotFoundError(f"Locations file not found: {path}")

        logger.info(f"Loading and parsing locations from '{path}'...")

        cleaned_rows: List[Dict[str, Any]] = []
        rejected_count = 0

        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader):
                street = str(row.get("Location/Street", row.get("Street", f"Location_{idx}"))).strip()
                district = str(row.get("District", "Unknown")).strip()

                lat, lon = None, None

                # Case A: Separate Latitude and Longitude columns
                if "Latitude" in row and "Longitude" in row and row["Latitude"] and row["Longitude"]:
                    try:
                        lat = float(row["Latitude"])
                        lon = float(row["Longitude"])
                    except ValueError:
                        pass

                # Case B: Combined "Latitude,Longitude" column in Lab 5 data_converted.csv
                elif "Latitude,Longitude" in row and row["Latitude,Longitude"]:
                    coord_str = str(row["Latitude,Longitude"]).strip()
                    parts = [p.strip() for p in coord_str.split(",") if p.strip()]
                    if len(parts) == 2:
                        try:
                            lat = float(parts[0])
                            lon = float(parts[1])
                        except ValueError:
                            pass

                # Validate coordinate boundaries (-90 <= lat <= 90 and -180 <= lon <= 180)
                if lat is not None and lon is not None and (-90.0 <= lat <= 90.0) and (-180.0 <= lon <= 180.0):
                    cleaned_rows.append({
                        "Location/Street": street,
                        "District": district,
                        "Latitude": lat,
                        "Longitude": lon,
                        "FreeFlowSpeed": float(row.get("FreeFlowSpeed", 45.0) or 45.0),
                    })
                else:
                    rejected_count += 1
                    logger.warning(f"Rejected invalid location row at index {idx}: '{street}' (lat={lat}, lon={lon})")

        logger.info(f"Loaded {len(cleaned_rows)} valid location(s). Rejected {rejected_count} malformed row(s).")
        return cleaned_rows

    @classmethod
    def load_locations(cls, file_path: str = None):
        """
        Loads locations and returns DataFrame if pandas is available, or list of dicts.
        """
        rows = cls.load_locations_list(file_path)
        try:
            import pandas as pd
            return pd.DataFrame(rows)
        except ImportError:
            return rows
