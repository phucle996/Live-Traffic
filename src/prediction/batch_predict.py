# ==============================================================================
# Batch Prediction CLI Engine (src/prediction/batch_predict.py)
# Executes Batch Traffic Speed Predictions for Target Datetime and Exports CSV
# ==============================================================================

import argparse
from datetime import datetime
from pathlib import Path
import pandas as pd

from src.common.config import settings, PROJECT_ROOT
from src.common.logging_utils import get_logger
from src.prediction.predictor import TrafficPredictor

# Instantiate logger for batch predictor
logger = get_logger(__name__)


from src.ingestion.location_loader import LocationLoader

def run_batch_prediction(datetime_str: str, locations_file: str = None) -> pd.DataFrame:
    """
    Executes batch traffic prediction for all locations at the specified target datetime.

    Args:
        datetime_str (str): Prediction datetime string (e.g. "2026-07-21 17:30:00").
        locations_file (str): Path to target locations CSV file.

    Returns:
        pd.DataFrame: Batch predictions DataFrame.
    """
    logger.info(f"Starting Batch Prediction Job for target datetime: '{datetime_str}'...")

    # Resolve locations CSV path
    loc_path = Path(locations_file or settings.LOCATIONS_FILE)
    if not loc_path.exists():
        logger.error(f"Locations file not found at '{loc_path}'. Aborting batch prediction.")
        return pd.DataFrame()

    logger.info(f"Reading target locations via LocationLoader from '{loc_path}'...")
    locations_df = LocationLoader.load_locations(loc_path)

    # Instantiate TrafficPredictor serving class
    predictor = TrafficPredictor()

    # Execute batch predictions
    results_df = predictor.predict_locations(locations_df, datetime_str)

    # Export prediction results CSV to artifacts/predictions/
    out_dir = PROJECT_ROOT / "artifacts" / "predictions"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = out_dir / f"batch_prediction_{timestamp_suffix}.csv"
    results_df.to_csv(out_file, index=False)
    logger.info(f"Exported batch predictions CSV to '{out_file}' with {len(results_df)} rows.")

    return results_df


def main():
    """
    CLI Entrypoint for batch prediction script.
    """
    parser = argparse.ArgumentParser(description="Run Batch Traffic Speed Prediction")
    parser.add_argument("--datetime", type=str, default=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), help="Target prediction datetime string")
    parser.add_argument("--locations", type=str, default=None, help="Path to locations CSV file")
    args = parser.parse_args()

    results_df = run_batch_prediction(args.datetime, args.locations)
    print("\n======================================================================")
    print(f"[SUCCESS] Batch Prediction Results for '{args.datetime}':")
    print(results_df.to_string(index=False))
    print("======================================================================\n")


if __name__ == "__main__":
    main()
