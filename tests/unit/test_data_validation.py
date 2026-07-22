# ==============================================================================
# Unit Tests for Data Validation & Schema Contracts (tests/unit/test_data_validation.py)
# ==============================================================================

import pytest
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType

from src.common.schemas import (
    RAW_TRAFFIC_SCHEMA,
    validate_raw_traffic_df,
    convert_spark_day_of_week,
    is_weekend,
)


@pytest.fixture(scope="module")
def spark():
    """
    Pytest fixture creating a local PySpark session for unit testing.
    """
    session = (
        SparkSession.builder.master("local[1]")
        .appName("unit-tests-data-validation")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )
    yield session
    session.stop()


def test_day_of_week_conversion(spark):
    """
    Tests PySpark to Python standard DayOfWeek conversion formula:
    python_day_of_week = (spark_day_of_week + 5) % 7
    """
    # Sample data representing Spark dayofweek values: 1=Sunday, 2=Monday, 7=Saturday
    data = [(1,), (2,), (3,), (4,), (5,), (6,), (7,)]
    schema = StructType([StructField("spark_dow", IntegerType(), True)])

    df = spark.createDataFrame(data, schema)
    result_df = df.withColumn("python_dow", convert_spark_day_of_week(F.col("spark_dow")))
    
    # Collect mapped values
    results = {row["spark_dow"]: row["python_dow"] for row in result_df.collect()}

    # Assert exact day-of-week mapping
    assert results[1] == 6  # Sunday -> 6
    assert results[2] == 0  # Monday -> 0
    assert results[3] == 1  # Tuesday -> 1
    assert results[4] == 2  # Wednesday -> 2
    assert results[5] == 3  # Thursday -> 3
    assert results[6] == 4  # Friday -> 4
    assert results[7] == 5  # Saturday -> 5


def test_is_weekend_classification(spark):
    """
    Tests weekend classifier logic: Saturday (5) and Sunday (6) map to 1, others map to 0.
    """
    data = [(0,), (1,), (2,), (3,), (4,), (5,), (6,)]
    schema = StructType([StructField("python_dow", IntegerType(), True)])

    df = spark.createDataFrame(data, schema)
    result_df = df.withColumn("is_wknd", is_weekend(F.col("python_dow")))

    results = {row["python_dow"]: row["is_wknd"] for row in result_df.collect()}

    # Weekdays (0-4) must be 0
    for day in range(5):
        assert results[day] == 0, f"Day {day} should be weekday (0)"

    # Saturday (5) and Sunday (6) must be 1
    assert results[5] == 1, "Saturday should be weekend (1)"
    assert results[6] == 1, "Sunday should be weekend (1)"


def test_raw_traffic_validation_bounds(spark):
    """
    Tests validation rules: valid rows pass, invalid bounds are routed to quarantine.
    """
    # Sample records: Row 1 is valid; Rows 2-5 violate physical bounds
    sample_data = [
        # Valid row
        ("2026-07-21 12:00:00", "Main St", "District 1", 10.77, 106.70, 30.0, 50.0, 0.95),
        # Invalid: Latitude out of bounds (> 90.0)
        ("2026-07-21 12:00:00", "Bad Lat", "District 1", 95.0, 106.70, 30.0, 50.0, 0.95),
        # Invalid: Negative CurrentSpeed (< 0.0)
        ("2026-07-21 12:00:00", "Bad Speed", "District 1", 10.77, 106.70, -10.0, 50.0, 0.95),
        # Invalid: Zero FreeFlowSpeed (<= 0.0)
        ("2026-07-21 12:00:00", "Zero FF", "District 1", 10.77, 106.70, 30.0, 0.0, 0.95),
        # Invalid: Confidence score out of bounds (> 1.0)
        ("2026-07-21 12:00:00", "High Conf", "District 1", 10.77, 106.70, 30.0, 50.0, 1.5),
    ]

    df = spark.createDataFrame(sample_data, RAW_TRAFFIC_SCHEMA)
    valid_df, quarantine_df, stats = validate_raw_traffic_df(df)

    # Verify counts
    assert stats["total_rows"] == 5
    assert stats["valid_rows"] == 1
    assert stats["invalid_rows"] == 4
    assert valid_df.count() == 1
    assert quarantine_df.count() == 4
