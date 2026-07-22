# ==============================================================================
# Live Traffic Ingestion & Crawler Engine (src/ingestion/crawl_traffic.py)
# Fetches Real-Time Speeds from TomTom API or Loads Seed Data Based on INGESTION_MODE
# ==============================================================================

import os
from datetime import datetime
from pathlib import Path
import pandas as pd

from src.common.config import settings, PROJECT_ROOT
from src.common.logging_utils import get_logger
from src.ingestion.tomtom_client import TomTomTrafficClient
from src.ingestion.seed_loader import load_seed_csv_files

# Instantiate logger for crawler engine
logger = get_logger(__name__)


from src.ingestion.location_loader import LocationLoader

def run_api_ingestion(locations_file: str) -> pd.DataFrame:
    """
    Crawls live traffic segment flow data for all target locations using TomTom Traffic API.

    Args:
        locations_file (str): Path to target locations CSV file.

    Returns:
        pd.DataFrame: Normalized ingested records DataFrame.
    """
    # Verify locations CSV exists
    loc_path = Path(locations_file)
    if not loc_path.exists():
        logger.error(f"Locations file not found at '{locations_file}'. Ingestion aborted.")
        return pd.DataFrame()

    logger.info(f"Reading target location coordinates via LocationLoader from '{locations_file}'...")
    locations_list = LocationLoader.load_locations_list(locations_file)

    # Initialize TomTom client
    client = TomTomTrafficClient()
    current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    records = []
    success_count = 0
    failure_count = 0

    # Iterate through locations and query API
    for idx, row in enumerate(locations_list):
        street = row.get("Location/Street", "Unknown")
        district = row.get("District", "Unknown")
        lat = float(row["Latitude"])
        lon = float(row["Longitude"])

        # Fetch flow data from TomTom API
        res = client.get_flow_segment(lat, lon)

        if res:
            success_count += 1
            records.append(
                {
                    "Timestamp": current_time_str,
                    "Location/Street": street,
                    "District": district,
                    "Latitude": lat,
                    "Longitude": lon,
                    "CurrentSpeed": res["current_speed"],
                    "FreeFlowSpeed": res["free_flow_speed"],
                    "Confidence": res["confidence"],
                }
            )
        else:
            failure_count += 1

    logger.info(f"API Crawl Completed - Success: {success_count}, Failures: {failure_count}")

    if not records:
        return pd.DataFrame()

    return pd.DataFrame(records)


def run_ingestion_pipeline() -> pd.DataFrame:
    """
    Main orchestration entrypoint executing ingestion based on settings.INGESTION_MODE ('api' vs 'seed').

    Returns:
        pd.DataFrame: Normalized ingested DataFrame.
    """
    mode = settings.INGESTION_MODE.lower()
    logger.info(f"Starting Traffic Data Ingestion Pipeline - Mode: '{mode}'")

    if mode in ("api", "online"):
        # Execute live TomTom API crawler
        df = run_api_ingestion(settings.LOCATIONS_FILE)
    else:
        # Fallback to offline seed loader
        logger.info("INGESTION_MODE is 'seed'. Loading offline seed CSV datasets...")
        df = load_seed_csv_files(settings.SEED_FOLDER)

    # Save output to local raw directory first
    if not df.empty:
        date_str = datetime.now().strftime("%Y-%m-%d")
        timestamp_str = datetime.now().strftime("%H%M%S")
        
        output_dir = PROJECT_ROOT / "data" / "output" / f"date={date_str}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / f"traffic_data_{timestamp_str}.csv"
        df.to_csv(output_file, index=False)
        logger.info(f"Saved local ingested raw file to '{output_file}' with {len(df)} rows.")

    return df


def main():
    """
    CLI Entrypoint for running ingestion pipeline.
    """
    run_ingestion_pipeline()


if __name__ == "__main__":
    main()
