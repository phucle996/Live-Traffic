# ==============================================================================
# Phase 2 Verification Script (scripts/verify_phase_2.py)
# Runs lightweight contract validation tests for DayOfWeek formulas and Schemas
# ==============================================================================

import sys
from src.common.schemas import (
    RAW_TRAFFIC_SCHEMA,
    PROCESSED_TRAFFIC_SCHEMA,
)

def test_schema_definitions():
    print("[TEST 1/2] Verifying PySpark Schema definitions...")
    
    # Verify RAW_TRAFFIC_SCHEMA field names
    raw_fields = [f.name for f in RAW_TRAFFIC_SCHEMA.fields]
    expected_raw = ["Timestamp", "Location/Street", "District", "Latitude", "Longitude", "CurrentSpeed", "FreeFlowSpeed", "Confidence"]
    assert raw_fields == expected_raw, f"RAW_TRAFFIC_SCHEMA mismatch: {raw_fields} != {expected_raw}"
    
    # Verify PROCESSED_TRAFFIC_SCHEMA field names
    processed_fields = [f.name for f in PROCESSED_TRAFFIC_SCHEMA.fields]
    assert "DayOfWeek" in processed_fields, "DayOfWeek missing from PROCESSED_TRAFFIC_SCHEMA"
    assert "Weekend" in processed_fields, "Weekend missing from PROCESSED_TRAFFIC_SCHEMA"
    assert "TimeInMinutes" in processed_fields, "TimeInMinutes missing from PROCESSED_TRAFFIC_SCHEMA"
    assert "CongestionRatio" in processed_fields, "CongestionRatio missing from PROCESSED_TRAFFIC_SCHEMA"
    
    print(" -> Schema Definitions PASSED!")


def test_day_of_week_formula_logic():
    print("[TEST 2/2] Verifying DayOfWeek conversion formula logic...")
    
    # Formula: python_day_of_week = (spark_day_of_week + 5) % 7
    # Spark dayofweek mapping: 1=Sunday, 2=Monday, 3=Tuesday, 4=Wednesday, 5=Thursday, 6=Friday, 7=Saturday
    spark_to_python = {spark_dow: (spark_dow + 5) % 7 for spark_dow in range(1, 8)}
    
    assert spark_to_python[1] == 6, "Sunday mapping failed (expected 6)"
    assert spark_to_python[2] == 0, "Monday mapping failed (expected 0)"
    assert spark_to_python[3] == 1, "Tuesday mapping failed (expected 1)"
    assert spark_to_python[4] == 2, "Wednesday mapping failed (expected 2)"
    assert spark_to_python[5] == 3, "Thursday mapping failed (expected 3)"
    assert spark_to_python[6] == 4, "Friday mapping failed (expected 4)"
    assert spark_to_python[7] == 5, "Saturday mapping failed (expected 5)"
    
    print(" -> DayOfWeek Conversion Formula PASSED!")


if __name__ == "__main__":
    try:
        test_schema_definitions()
        test_day_of_week_formula_logic()
        print("\n======================================================================")
        print("[SUCCESS] All Phase 2 Schema & Contract Logic Tests Passed!")
        print("======================================================================")
    except Exception as e:
        print(f"\n[FAIL] Test failed with error: {str(e)}")
        sys.exit(1)
