# ==============================================================================
# Raw Data Validation Module (src/processing/validate_raw_data.py)
# Enforces Data Quality Contracts, Segregates Quarantine Records, & Generates Reports
# ==============================================================================

import argparse
import json
import sys
from typing import Tuple, Dict, Any

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from src.common.logging_utils import get_logger
from src.common.schemas import validate_raw_traffic_df, RAW_TRAFFIC_SCHEMA
from src.common.spark_session import get_spark_session

# Instantiate logger for data validation module
logger = get_logger(__name__)


def validate_traffic_dataframe(df: DataFrame) -> Tuple[DataFrame, DataFrame, Dict[str, Any]]:
    """
    Public wrapper function for validating raw traffic PySpark DataFrame.
    Segregates valid records from quarantine records based on physical bounds contracts.

    Args:
        df (DataFrame): Input PySpark raw traffic DataFrame.

    Returns:
        Tuple[DataFrame, DataFrame, Dict[str, Any]]: Valid DataFrame, Quarantine DataFrame, and Summary Statistics.
    """
    logger.info("Executing raw traffic DataFrame validation rules...")
    # Invoke schema validation helper from common schemas module
    valid_df, quarantine_df, stats = validate_raw_traffic_df(df)

    logger.info(
        f"Validation Complete - Total: {stats['total_rows']}, "
        f"Valid: {stats['valid_rows']} ({stats['valid_percentage']:.2f}%), "
        f"Quarantine: {stats['invalid_rows']}"
    )

    return valid_df, quarantine_df, stats


def run_standalone_validation(input_csv_path: str, spark: SparkSession) -> Dict[str, Any]:
    """
    Loads raw CSV file with explicit schema, executes validation, and returns summary stats.

    Args:
        input_csv_path (str): File path to raw traffic CSV dataset.
        spark (SparkSession): Active PySpark session instance.

    Returns:
        Dict[str, Any]: Dictionary containing validation summary metrics.
    """
    logger.info(f"Loading raw CSV data for validation from path: '{input_csv_path}'")

    # Read CSV using explicit RAW_TRAFFIC_SCHEMA to prevent schema drift
    raw_df = (
        spark.read.option("header", "true")
        .schema(RAW_TRAFFIC_SCHEMA)
        .csv(input_csv_path)
    )

    # Perform validation checks
    valid_df, quarantine_df, stats = validate_traffic_dataframe(raw_df)

    # Return calculated validation statistics
    return stats


def main() -> None:
    """
    CLI Entrypoint for running standalone data validation checks.
    """
    parser = argparse.ArgumentParser(description="Validate Raw Traffic Data Quality Contracts")
    parser.add_argument("--input", type=str, required=True, help="Path to input raw CSV file or HDFS directory")
    args = parser.parse_args()

    # Get active Spark session
    spark = get_spark_session(app_name="data-validation-job")

    try:
        # Run validation pipeline
        stats = run_standalone_validation(args.input, spark)
        print(json.dumps(stats, indent=2))
    except Exception as e:
        logger.error(f"Data validation job failed with error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
