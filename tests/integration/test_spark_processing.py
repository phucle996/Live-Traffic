# ==============================================================================
# Integration Test for PySpark Data Processing (tests/integration/test_spark_processing.py)
# Verifies End-to-End Raw-to-Feature Transformations, Filtering, & Column Contracts
# ==============================================================================

import pytest
from pyspark.sql import SparkSession
from src.common.schemas import RAW_TRAFFIC_SCHEMA
from src.processing.process_spark import process_traffic_data


@pytest.fixture(scope="module")
def spark():
    """
    Pytest fixture creating local PySpark session for ETL integration testing.
    """
    session = (
        SparkSession.builder.master("local[1]")
        .appName("integration-test-spark-processing")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )
    yield session
    session.stop()


def test_spark_processing_transformation(spark):
    """
    Verifies end-to-end process_traffic_data transformation pipeline.
    """
    # Sample input records (1 valid high conf, 1 valid low conf, 1 duplicate)
    raw_data = [
        ("2026-07-21 08:30:00", "Main St", "District 1", 10.7769, 106.7009, 25.0, 50.0, 0.95),
        ("2026-07-21 08:30:00", "Main St", "District 1", 10.7769, 106.7009, 25.0, 50.0, 0.95),  # Duplicate
        ("2026-07-21 17:45:00", "Le Loi", "District 1", 10.7738, 106.6983, 10.0, 40.0, 0.80),   # Low confidence < 0.9
        ("2026-07-21 18:00:00", "Pasteur", "District 3", 10.7812, 106.6945, 30.0, 45.0, 0.92),  # Valid
    ]

    raw_df = spark.createDataFrame(raw_data, RAW_TRAFFIC_SCHEMA)

    # Execute Spark processing function
    processed_df, etl_stats = process_traffic_data(raw_df)

    # Verify row counts: 4 total -> 1 duplicate removed -> 1 low conf dropped -> 2 processed rows
    assert etl_stats["raw_rows"] == 4
    assert etl_stats["duplicates_removed"] == 1
    assert etl_stats["low_confidence_rows_filtered"] == 1
    assert etl_stats["processed_rows"] == 2

    # Verify column existence
    expected_columns = [
        "Timestamp", "Location/Street", "District", "Latitude", "Longitude",
        "CurrentSpeed", "FreeFlowSpeed", "Confidence", "Hour", "Minute",
        "TimeInMinutes", "DayOfWeek", "Weekend", "CongestionRatio"
    ]
    for col_name in expected_columns:
        assert col_name in processed_df.columns, f"Missing feature column '{col_name}'"

    # Collect processed rows to verify calculated values
    rows = processed_df.collect()
    row_main_st = [r for r in rows if r["Location/Street"] == "Main St"][0]

    # Row for Main St: 08:30:00 -> Hour=8, Minute=30, TimeInMinutes=510
    assert row_main_st["Hour"] == 8
    assert row_main_st["Minute"] == 30
    assert row_main_st["TimeInMinutes"] == 510
    assert row_main_st["CongestionRatio"] == 0.5  # 25.0 / 50.0 = 0.5
    assert 0 <= row_main_st["DayOfWeek"] <= 6
    assert row_main_st["Weekend"] in (0, 1)
