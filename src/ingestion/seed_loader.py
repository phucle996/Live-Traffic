# ==============================================================================
# Seed CSV Loader Module (src/ingestion/seed_loader.py)
# Loads Offline Traffic Data Seed CSV files for Resilience & Demo Capabilities
# ==============================================================================

import os
import glob
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd

from src.common.config import settings, PROJECT_ROOT
from src.common.logging_utils import get_logger

# Instantiate logger for seed loader
logger = get_logger(__name__)


def load_seed_csv_files(seed_folder: str = None) -> pd.DataFrame:
    """
    Reads all seed CSV files from the specified folder into a single pandas DataFrame.

    Args:
        seed_folder (str): Directory path containing seed CSV files.

    Returns:
        pd.DataFrame: Combined seed traffic DataFrame.
    """
    # Resolve seed folder directory path
    folder_path = Path(seed_folder or settings.SEED_FOLDER)

    if not folder_path.exists():
        logger.warning(f"Seed folder '{folder_path}' does not exist. Creating directory...")
        folder_path.mkdir(parents=True, exist_ok=True)
        return pd.DataFrame()

    # Search for all CSV files in seed folder
    csv_files = glob.glob(str(folder_path / "*.csv"))

    if not csv_files:
        logger.warning(f"No CSV seed files found in directory '{folder_path}'")
        return pd.DataFrame()

    logger.info(f"Found {len(csv_files)} seed CSV file(s) in '{folder_path}'")

    dfs = []
    # Read each CSV file
    for file_path in csv_files:
        try:
            logger.info(f"Reading seed file: '{file_path}'")
            df = pd.read_csv(file_path)
            dfs.append(df)
        except Exception as e:
            logger.error(f"Error reading seed CSV file '{file_path}': {str(e)}")

    if not dfs:
        return pd.DataFrame()

    # Combine all DataFrames
    combined_df = pd.concat(dfs, ignore_index=True)
    logger.info(f"Successfully loaded total {len(combined_df)} seed records.")

    return combined_df


def main():
    """
    CLI Entrypoint for running seed loader.
    """
    logger.info("Executing Seed Loader job...")
    df = load_seed_csv_files()
    print(df.head())


if __name__ == "__main__":
    main()
