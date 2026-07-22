# ==============================================================================
# PySpark Data Schemas & Validation Contracts Module (src/common/schemas.py)
# Data Contract Specifications, Column Validation Bounds, & DayOfWeek Converters
# ==============================================================================

from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    DoubleType,
    TimestampType,
    IntegerType,
    BooleanType,
)
from pyspark.sql import functions as F
from pyspark.sql import DataFrame
from typing import Tuple, Dict, Any


# ==============================================================================
# 1. PySpark Data Schema Definitions
# ==============================================================================

# Explicit PySpark Schema for Raw Traffic Ingestion Data (CSV / API payload)
RAW_TRAFFIC_SCHEMA = StructType(
    [
        StructField("Timestamp", StringType(), True),         # Original timestamp string
        StructField("Location/Street", StringType(), True),   # Street or location label
        StructField("District", StringType(), True),          # District / Area name
        StructField("Latitude", DoubleType(), True),          # Geo Latitude coordinate
        StructField("Longitude", DoubleType(), True),         # Geo Longitude coordinate
        StructField("CurrentSpeed", DoubleType(), True),      # Measured current speed (km/h)
        StructField("FreeFlowSpeed", DoubleType(), True),     # Baseline free-flow speed (km/h)
        StructField("Confidence", DoubleType(), True),        # Sensor confidence score (0.0 to 1.0)
    ]
)

# Unified PySpark Schema for Hybrid Raw Traffic Ingestion (Lab Offline + TomTom Live)
UNIFIED_RAW_TRAFFIC_SCHEMA = StructType(
    [
        StructField("Timestamp", TimestampType(), True),      # Parsed event timestamp
        StructField("Location/Street", StringType(), False),  # Street or location label
        StructField("District", StringType(), False),         # District / Area name
        StructField("Latitude", DoubleType(), False),         # Geo Latitude coordinate
        StructField("Longitude", DoubleType(), False),        # Geo Longitude coordinate
        StructField("CurrentSpeed", DoubleType(), False),     # Measured current speed (km/h)
        StructField("FreeFlowSpeed", DoubleType(), False),    # Baseline free-flow speed (km/h)
        StructField("Confidence", DoubleType(), False),       # Sensor confidence score
        StructField("CurrentTravelTime", IntegerType(), True), # Optional current travel time in seconds
        StructField("FreeFlowTravelTime", IntegerType(), True),# Optional free flow travel time in seconds
        StructField("RoadClosure", BooleanType(), True),      # Optional road closure boolean indicator
        StructField("DataSource", StringType(), False),       # Source identifier ("lab_offline" / "tomtom_live")
        StructField("IngestedAtUtc", TimestampType(), False), # System ingestion UTC timestamp
        StructField("IngestionBatchId", StringType(), False), # Ingestion batch UUID string
    ]
)

# PySpark Schema for Processed Feature Engineering Data (Parquet)
PROCESSED_TRAFFIC_SCHEMA = StructType(
    [
        StructField("Timestamp", TimestampType(), True),      # Parsed timestamp object
        StructField("Location/Street", StringType(), True),   # Street or location label
        StructField("District", StringType(), True),          # District / Area name
        StructField("Latitude", DoubleType(), False),         # Geo Latitude coordinate
        StructField("Longitude", DoubleType(), False),        # Geo Longitude coordinate
        StructField("CurrentSpeed", DoubleType(), False),     # Measured current speed (km/h)
        StructField("FreeFlowSpeed", DoubleType(), False),    # Baseline free-flow speed (km/h)
        StructField("Confidence", DoubleType(), False),       # Sensor confidence score
        StructField("Hour", IntegerType(), False),            # Hour of the day (0-23)
        StructField("Minute", IntegerType(), False),          # Minute of the hour (0-59)
        StructField("TimeInMinutes", IntegerType(), False),   # Total minutes past midnight (Hour*60 + Minute)
        StructField("DayOfWeek", IntegerType(), False),       # Python standard DayOfWeek (0=Mon .. 6=Sun)
        StructField("Weekend", IntegerType(), False),          # Weekend binary indicator (1 if Sat/Sun, 0 otherwise)
        StructField("CongestionRatio", DoubleType(), False),  # Speed ratio (CurrentSpeed / FreeFlowSpeed)
        StructField("DataSource", StringType(), True),        # Source identifier ("lab_offline" / "tomtom_live")
    ]
)


# ==============================================================================
# 2. Schema Validation & Data Quality Contract Functions
# ==============================================================================

LATITUDE_MIN, LATITUDE_MAX = 8.0, 24.0      # Valid geographical latitude bounds for Vietnam
LONGITUDE_MIN, LONGITUDE_MAX = 102.0, 110.0 # Valid geographical longitude bounds for Vietnam
SPEED_MIN, SPEED_MAX = 0.0, 150.0           # Valid traffic speed bounds in km/h
CONFIDENCE_MIN, CONFIDENCE_MAX = 0.0, 1.0   # Valid confidence score bounds


def convert_spark_day_of_week(col):
    """
    Converts PySpark timestamp column or dayofweek integer (1=Sun .. 7=Sat) to Python standard convention (0=Mon .. 6=Sun).
    Formula: (dayofweek + 5) % 7
    """
    # 1. Kiểm tra nếu cột là số nguyên 1..7 (spark_dow) thì lấy col, nếu là Timestamp thì chuyển sang Timestamp rồi gọi F.dayofweek
    dow = F.when(col.cast("string").rlike("^[1-7]$"), col.cast("int")).otherwise(F.dayofweek(F.to_timestamp(col)))

    # 2. Áp dụng công thức quy đổi chuẩn Python DayOfWeek (0=Thứ hai .. 6=Chủ nhật)
    return (dow + 5) % 7



def is_weekend(day_col):
    """
    Returns 1 if day_col is Saturday (5) or Sunday (6), else 0.
    """
    # Trả về 1 nếu là thứ 7 (5) hoặc chủ nhật (6), ngược lại trả về 0
    return F.when(day_col >= 5, 1).otherwise(0)


def validate_raw_traffic_df(df: DataFrame) -> Tuple[DataFrame, DataFrame, Dict[str, int]]:
    """
    Validates a raw traffic PySpark DataFrame against domain constraints and bounds.
    Separates valid records from quarantine records and returns statistics.
    """
    # 1. Định nghĩa điều kiện lọc dữ liệu hợp lệ (Latitude, Longitude, CurrentSpeed, FreeFlowSpeed, Confidence)
    valid_cond = (
        (F.col("Latitude").between(LATITUDE_MIN, LATITUDE_MAX)) & # Vĩ độ thuộc Việt Nam (8..24)
        (F.col("Longitude").between(LONGITUDE_MIN, LONGITUDE_MAX)) & # Kinh độ thuộc Việt Nam (102..110)
        (F.col("CurrentSpeed").between(SPEED_MIN, SPEED_MAX)) & # Tốc độ hiện tại từ 0 đến 150 km/h
        (F.col("FreeFlowSpeed") > 0.0) & (F.col("FreeFlowSpeed") <= SPEED_MAX) & # Tốc độ tự do > 0 và <= 150 km/h
        (F.col("Confidence").between(CONFIDENCE_MIN, CONFIDENCE_MAX)) # Độ tin cậy từ 0.0 đến 1.0
    )

    # 2. Tách DataFrame thành bản ghi hợp lệ (valid_df) và bản ghi lỗi (quarantine_df)
    valid_df = df.filter(valid_cond) # Lọc các bản ghi thỏa mãn tất cả các điều kiện
    quarantine_df = df.filter(~valid_cond) # Các bản ghi vi phạm ít nhất 1 điều kiện sẽ đưa vào quarantine

    # 3. Tính toán thống kê số lượng bản ghi
    total_count = df.count() # Tổng số bản ghi ban đầu
    valid_count = valid_df.count() # Số bản ghi hợp lệ
    quarantine_count = quarantine_df.count() # Số bản ghi bị cách ly

    # 4. Gom thống kê thành dictionary hỗ trợ đầy đủ alias tên key
    stats = {
        "total_records": total_count,
        "valid_records": valid_count,
        "quarantine_records": quarantine_count,
        "total_rows": total_count,
        "valid_rows": valid_count,
        "invalid_rows": quarantine_count,
    }

    return valid_df, quarantine_df, stats


